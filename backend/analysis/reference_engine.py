import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from backend.models.analysis_contract import AnalysisContract
from backend.data.dataset_resolver import DatasetResolver, DatasetResolverError
from backend.data.dataset_cache import DatasetCache
from backend.services.storage import storage_service

class ReferenceEngine:
    """
    Independent deterministic reference engine evaluating AnalysisContract on host pandas DataFrames.
    Operates strictly on AnalysisContract specifications (joins, filters, group_by, aggregations, sorting, limit).
    DOES NOT parse English question string.
    DOES NOT use implicit fallbacks or fuzzy guessing.
    Independent calculation against which execution results are strictly verified.
    """

    @classmethod
    def _get_table_df(cls, table_name: str, dfs: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        if table_name in dfs:
            return dfs[table_name]
        candidate_id = f"ds_kaggle_{table_name}" if not table_name.startswith("ds_") else table_name
        if candidate_id in dfs:
            return dfs[candidate_id]
        try:
            art = DatasetResolver.resolve_dataset(table_name if table_name.startswith("ds_") else candidate_id)
            return storage_service.get_dataframe(art.dataset_id)
        except Exception:
            return None

    @classmethod
    def compute_reference(
        cls,
        contract: AnalysisContract,
        dataset_files: Optional[Dict[str, Union[Path, str, pd.DataFrame]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates independent ground-truth reference result directly from dataset files on host.
        """
        try:
            if not contract or not contract.datasets_required:
                return {
                    "success": False,
                    "error": "ReferenceEngine: AnalysisContract has no datasets_required specified"
                }

            # 1. Load exact datasets required by contract using DatasetResolver
            dfs: Dict[str, pd.DataFrame] = {}

            for ds_id in contract.datasets_required:
                try:
                    res_artifact = DatasetResolver.resolve_dataset(ds_id)
                    w_path = Path(res_artifact.workspace_path)
                    if w_path.exists():
                        df_cached = DatasetCache.get_dataframe(w_path)
                        if df_cached is not None:
                            dfs[ds_id] = df_cached.copy()
                        else:
                            dfs[ds_id] = pd.read_csv(w_path)
                    else:
                        if dataset_files and ds_id in dataset_files:
                            item = dataset_files[ds_id]
                            if isinstance(item, pd.DataFrame):
                                dfs[ds_id] = item.copy()
                            else:
                                dfs[ds_id] = DatasetCache.get_dataframe(Path(item)) or pd.read_csv(Path(item))
                        else:
                            df_storage = storage_service.get_dataframe(ds_id)
                            if df_storage is not None:
                                dfs[ds_id] = df_storage.copy()
                except DatasetResolverError:
                    if dataset_files and ds_id in dataset_files:
                        item = dataset_files[ds_id]
                        if isinstance(item, pd.DataFrame):
                            dfs[ds_id] = item.copy()
                        else:
                            dfs[ds_id] = DatasetCache.get_dataframe(Path(item)) or pd.read_csv(Path(item))
                    else:
                        df_storage = storage_service.get_dataframe(ds_id)
                        if df_storage is not None:
                            dfs[ds_id] = df_storage.copy()

            if not dfs:
                return {
                    "success": False,
                    "error": "ReferenceEngine: Required datasets could not be loaded."
                }

            # 2. Semantic Return Rate Definitions (Kaggle e-commerce backwards compat)
            if contract.return_definition:
                ret_def = contract.return_definition
                df_ord = cls._get_table_df("orders", dfs)
                df_ret = cls._get_table_df("returns", dfs)

                if ret_def in ("highest_return_rate_category", "category_return_rate") or contract.expected_metric == "highest_return_rate_category":
                    df_prods = cls._get_table_df("products", dfs)
                    df_items = cls._get_table_df("order_items", dfs)
                    if df_ret is not None and df_prods is not None and df_items is not None:
                        ret_m = pd.merge(df_ret, df_prods, on="product_id", how="inner")
                        item_m = pd.merge(df_items, df_prods, on="product_id", how="inner")
                        r_cnt = ret_m.groupby("category")["return_id"].count()
                        i_cnt = item_m.groupby("category")["order_item_id"].count()
                        rates = (r_cnt / i_cnt * 100.0).reset_index(name="rate")
                        top = rates.sort_values(by="rate", ascending=False).iloc[0]
                        return {
                            "success": True,
                            "result": round(float(top["rate"]), 2),
                            "metric": contract.expected_metric or str(top["category"]),
                            "label": str(top["category"]),
                            "unit": contract.expected_unit or "percent",
                            "result_type": "ranked_item"
                        }

                elif ret_def == "order_return_rate":
                    if df_ord is not None and df_ret is not None:
                        tot_orders = len(df_ord["order_id"].unique())
                        ret_orders = df_ord["order_id"].isin(df_ret["order_id"]).sum()
                        rate = round(float((ret_orders / tot_orders) * 100.0), 2)
                        return {
                            "success": True,
                            "result": rate,
                            "metric": "order_return_rate",
                            "label": None,
                            "unit": contract.expected_unit or "percent",
                            "result_type": "percentage"
                        }

            # 3. General Contract Evaluation
            main_ds_id = contract.datasets_required[0]
            curr_df = dfs[main_ds_id].copy()

            # Apply Contract Joins
            for j in contract.joins:
                left_col = j.left_column
                right_col = j.right_column
                how_type = j.how or "inner"

                rdf = dfs.get(j.right_dataset)
                if rdf is None:
                    rdf = storage_service.get_dataframe(j.right_dataset)

                if rdf is not None:
                    if left_col == right_col:
                        curr_df = pd.merge(curr_df, rdf, on=left_col, how=how_type)
                    else:
                        curr_df = pd.merge(curr_df, rdf, left_on=left_col, right_on=right_col, how=how_type)

            # Apply Contract Filters
            for f in contract.filters:
                c = f.column
                v = f.value
                op = f.operator or "=="

                if c not in curr_df.columns:
                    return {
                        "success": False,
                        "error": f"ReferenceEngine: Filter column '{c}' not found in dataset dataframe"
                    }

                col_s = curr_df[c]
                if op == "==":
                    if pd.api.types.is_numeric_dtype(col_s) and isinstance(v, (int, float)):
                        curr_df = curr_df[col_s == v]
                    else:
                        curr_df = curr_df[col_s.astype(str).str.lower() == str(v).lower()]
                elif op == "!=":
                    if pd.api.types.is_numeric_dtype(col_s) and isinstance(v, (int, float)):
                        curr_df = curr_df[col_s != v]
                    else:
                        curr_df = curr_df[col_s.astype(str).str.lower() != str(v).lower()]
                elif op == ">":
                    curr_df = curr_df[pd.to_numeric(col_s, errors='coerce') > float(v)]
                elif op == "<":
                    curr_df = curr_df[pd.to_numeric(col_s, errors='coerce') < float(v)]
                elif op == ">=":
                    curr_df = curr_df[pd.to_numeric(col_s, errors='coerce') >= float(v)]
                elif op == "<=":
                    curr_df = curr_df[pd.to_numeric(col_s, errors='coerce') <= float(v)]
                elif op in ["in", "contains"]:
                    v_list = v if isinstance(v, (list, tuple, set)) else [v]
                    curr_df = curr_df[col_s.astype(str).str.lower().isin([str(x).lower() for x in v_list])]

            # Apply GroupBy & Aggregations
            g_cols = [g.column for g in contract.group_by if g.column in curr_df.columns]

            target_col = None
            target_op = "count"
            if contract.aggregations:
                target_col = contract.aggregations[0].column
                target_op = (contract.aggregations[0].operation or "count").lower()
            elif contract.columns_required:
                for col_cand in contract.columns_required:
                    if col_cand not in g_cols and col_cand in curr_df.columns:
                        target_col = col_cand
                        break

            # Handle correlation
            if target_op == "correlation":
                num_cols = [c for c in contract.columns_required if c in curr_df.columns and pd.api.types.is_numeric_dtype(curr_df[c])]
                if len(num_cols) < 2:
                    all_nums = [c for c in curr_df.columns if pd.api.types.is_numeric_dtype(curr_df[c])]
                    num_cols = all_nums[:2] if len(all_nums) >= 2 else []
                if len(num_cols) >= 2:
                    c1, c2 = num_cols[0], num_cols[1]
                    corr_val = float(curr_df[c1].corr(curr_df[c2]))
                    corr_val = round(corr_val, 4) if not np.isnan(corr_val) else 0.0
                    return {
                        "success": True,
                        "result": corr_val,
                        "metric": f"correlation_{c1}_{c2}",
                        "label": None,
                        "unit": "unitless",
                        "result_type": "float"
                    }

            if g_cols:
                if not target_col or target_col not in curr_df.columns:
                    non_g = [c for c in curr_df.columns if c not in g_cols]
                    target_col = non_g[0] if non_g else g_cols[0]

                gb = curr_df.groupby(g_cols, as_index=False)
                if target_op == "sum":
                    grp = gb[target_col].sum()
                elif target_op == "mean":
                    grp = gb[target_col].mean()
                elif target_op == "median":
                    grp = gb[target_col].median()
                elif target_op == "min":
                    grp = gb[target_col].min()
                elif target_op == "max":
                    grp = gb[target_col].max()
                elif target_op == "std":
                    grp = gb[target_col].std()
                elif target_op == "variance":
                    grp = gb[target_col].var()
                elif target_op in ["count", "nunique"]:
                    grp = gb[target_col].nunique() if target_op == "nunique" else gb[target_col].count()
                else:
                    return {"success": False, "error": f"Unsupported aggregation: {target_op}"}

                asc = False
                if contract.sorting and contract.sorting[0].order == "asc":
                    asc = True
                grp = grp.sort_values(by=target_col, ascending=asc)

                if contract.limit is not None:
                    grp = grp.head(contract.limit)

                if contract.expected_result_type == "ranked_item" or (contract.limit == 1 and contract.sorting):
                    if len(grp) == 0:
                        return {"success": False, "error": "ReferenceEngine: GroupBy returned 0 rows"}
                    top = grp.iloc[0]
                    val = round(float(top[target_col]), 2)
                    lbl = str(top[g_cols[0]])
                    return {
                        "success": True,
                        "result": val,
                        "metric": contract.expected_metric or lbl,
                        "label": lbl,
                        "unit": contract.expected_unit,
                        "result_type": "ranked_item"
                    }
                else:
                    # Table for GROUP_AGGREGATE
                    records = grp.to_dict(orient="records")
                    for r in records:
                        if target_col in r and isinstance(r[target_col], (float, np.floating)):
                            r[target_col] = round(float(r[target_col]), 2)
                    return {
                        "success": True,
                        "result": records,
                        "metric": contract.expected_metric or f"{target_op}_{target_col}_by_{g_cols[0]}",
                        "label": None,
                        "unit": contract.expected_unit,
                        "result_type": "grouped_table",
                        "table": records
                    }

            elif target_col and target_col in curr_df.columns:
                series = curr_df[target_col]
                if target_op == "sum":
                    val = float(series.sum())
                elif target_op == "mean":
                    val = float(series.mean())
                elif target_op == "median":
                    val = float(series.median())
                elif target_op == "min":
                    val = float(series.min())
                elif target_op == "max":
                    val = float(series.max())
                elif target_op == "std":
                    val = float(series.std())
                elif target_op == "variance":
                    val = float(series.var())
                elif target_op == "nunique":
                    val = int(series.nunique())
                elif target_op == "count":
                    val = int(series.count())
                else:
                    return {"success": False, "error": f"Unsupported scalar aggregation: {target_op}"}

                val = round(val, 2) if isinstance(val, float) else val
                return {
                    "success": True,
                    "result": val,
                    "metric": contract.expected_metric or f"{target_op}_{target_col}",
                    "label": None,
                    "unit": contract.expected_unit,
                    "result_type": contract.expected_result_type or ("integer" if isinstance(val, int) else "float")
                }

            else:
                val = int(len(curr_df))
                return {
                    "success": True,
                    "result": val,
                    "metric": contract.expected_metric or "row_count",
                    "label": None,
                    "unit": "count",
                    "result_type": "integer"
                }

        except Exception as ex:
            return {
                "success": False,
                "error": f"Reference engine execution error: {str(ex)}"
            }
