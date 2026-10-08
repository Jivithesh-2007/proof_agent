import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from backend.models.analysis_contract import AnalysisContract

class ContractExecutor:
    """
    Deterministic Analytics Engine.
    Evaluates an AnalysisContract strictly based on contract fields
    (datasets, joins, filters, group_by, aggregations, sorting, limit).
    
    DOES NOT parse natural language.
    DOES NOT silently convert operations to SUM.
    DOES NOT truncate GROUP_AGGREGATE to a single row.
    """

    @classmethod
    def execute(
        cls,
        contract: AnalysisContract,
        dataset_files: Dict[str, Union[pd.DataFrame, Path, str]]
    ) -> Dict[str, Any]:
        try:
            from backend.data.dataset_resolver import DatasetResolver, DatasetResolverError
            from backend.services.storage import storage_service

            dfs: Dict[str, pd.DataFrame] = {}
            datasets_used: List[str] = []

            def get_df_by_key(key_name: str) -> Optional[pd.DataFrame]:
                if key_name in dfs:
                    return dfs[key_name]
                if dataset_files and key_name in dataset_files:
                    item = dataset_files[key_name]
                    if isinstance(item, pd.DataFrame):
                        return item.copy()
                    fp = Path(item)
                    if fp.exists():
                        return pd.read_csv(fp)
                try:
                    res_art = DatasetResolver.resolve_dataset(key_name)
                    df_resolved = storage_service.get_dataframe(res_art.dataset_id)
                    if df_resolved is not None:
                        return df_resolved.copy()
                    wpath = Path(res_art.workspace_path)
                    if wpath.exists():
                        return pd.read_csv(wpath)
                except DatasetResolverError:
                    pass
                return None

            for ds_id in contract.datasets_required:
                df = get_df_by_key(ds_id)
                if df is not None:
                    dfs[ds_id] = df
                    datasets_used.append(ds_id)
                else:
                    return {
                        "success": False,
                        "error": f"Required dataset '{ds_id}' could not be resolved strictly."
                    }

            if not dfs:
                return {
                    "success": False,
                    "error": "No required datasets found for contract execution."
                }

            columns_used: List[str] = []
            operations_executed: List[Dict[str, Any]] = []
            join_evidence: List[Dict[str, Any]] = []

            # 0. Return Rate Special Semantics
            if contract.return_definition:
                ret_def = contract.return_definition
                df_ord = get_df_by_key("orders")
                df_ret = get_df_by_key("returns")

                if ret_def in ("highest_return_rate_category", "category_return_rate") or contract.expected_metric == "highest_return_rate_category":
                    df_prods = get_df_by_key("products")
                    df_items = get_df_by_key("order_items")
                    if df_ret is not None and df_prods is not None and df_items is not None:
                        ret_m = pd.merge(df_ret, df_prods, on="product_id", how="inner")
                        item_m = pd.merge(df_items, df_prods, on="product_id", how="inner")
                        r_cnt = ret_m.groupby("category")["return_id"].count()
                        i_cnt = item_m.groupby("category")["order_item_id"].count()
                        rates = (r_cnt / i_cnt * 100.0).reset_index(name="rate")
                        top = rates.sort_values(by="rate", ascending=False).iloc[0]
                        cat_label = str(top["category"])
                        return {
                            "success": True,
                            "result": round(float(top["rate"]), 2),
                            "metric": cat_label,
                            "label": cat_label,
                            "unit": contract.expected_unit or "percent",
                            "result_type": "ranked_item",
                            "datasets_used": list(set(datasets_used)),
                            "columns_used": ["product_id", "category", "return_id", "order_item_id"],
                            "runtime_operations": [{"operation": "aggregate", "function": "return_rate", "column": "category"}],
                            "join_evidence": []
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
                            "result_type": "percentage",
                            "datasets_used": list(set(datasets_used)),
                            "columns_used": ["order_id"],
                            "runtime_operations": [
                                {"operation": "join", "left_column": "order_id", "right_column": "order_id"},
                                {"operation": "aggregate", "function": "return_rate", "column": "order_id"}
                            ],
                            "join_evidence": []
                        }

            # 1. Base DataFrame
            main_ds = contract.datasets_required[0]
            current_df = dfs[main_ds].copy()

            # 2. Joins
            for join_spec in contract.joins:
                left_name = join_spec.left_dataset
                right_name = join_spec.right_dataset
                left_col = join_spec.left_column
                right_col = join_spec.right_column
                how = join_spec.how or "inner"

                right_df = get_df_by_key(right_name)
                if right_df is None:
                    return {
                        "success": False,
                        "error": f"Join right dataset '{right_name}' could not be resolved strictly."
                    }

                left_df = current_df
                rows_before = len(left_df)
                if left_col == right_col:
                    current_df = pd.merge(left_df, right_df, on=left_col, how=how)
                else:
                    current_df = pd.merge(left_df, right_df, left_on=left_col, right_on=right_col, how=how)

                rows_after = len(current_df)
                columns_used.extend([left_col, right_col])
                operations_executed.append({
                    "operation": "join",
                    "left_dataset": left_name,
                    "right_dataset": right_name,
                    "left_column": left_col,
                    "right_column": right_col,
                    "how": how
                })
                join_evidence.append({
                    "left_dataset": left_name,
                    "right_dataset": right_name,
                    "left_column": left_col,
                    "right_column": right_col,
                    "how": how,
                    "rows_before": rows_before,
                    "rows_after": rows_after,
                    "duplication_factor": round(rows_after / rows_before, 2) if rows_before > 0 else 1.0
                })

            # 3. Filters
            for f in contract.filters:
                col = f.column
                val = f.value
                op = f.operator or "=="

                if col in current_df.columns:
                    columns_used.append(col)
                    operations_executed.append({
                        "operation": "filter",
                        "dataset": f.dataset or main_ds,
                        "column": col,
                        "operator": op,
                        "value": val
                    })

                    # Perform type-safe filter comparison
                    col_series = current_df[col]
                    if op == "==":
                        if pd.api.types.is_numeric_dtype(col_series) and isinstance(val, (int, float)):
                            current_df = current_df[col_series == val]
                        else:
                            current_df = current_df[col_series.astype(str).str.lower() == str(val).lower()]
                    elif op == "!=":
                        if pd.api.types.is_numeric_dtype(col_series) and isinstance(val, (int, float)):
                            current_df = current_df[col_series != val]
                        else:
                            current_df = current_df[col_series.astype(str).str.lower() != str(val).lower()]
                    elif op == ">":
                        current_df = current_df[pd.to_numeric(col_series, errors='coerce') > float(val)]
                    elif op == "<":
                        current_df = current_df[pd.to_numeric(col_series, errors='coerce') < float(val)]
                    elif op == ">=":
                        current_df = current_df[pd.to_numeric(col_series, errors='coerce') >= float(val)]
                    elif op == "<=":
                        current_df = current_df[pd.to_numeric(col_series, errors='coerce') <= float(val)]
                    elif op in ["in", "contains"]:
                        val_list = val if isinstance(val, (list, tuple, set)) else [val]
                        str_vals = [str(v).lower() for v in val_list]
                        current_df = current_df[col_series.astype(str).str.lower().isin(str_vals)]
                    else:
                        return {
                            "success": False,
                            "error": f"Unsupported filter operator: '{op}'"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"Filter column '{col}' does not exist in dataset."
                    }

            # 4. Aggregations & Groupings
            group_cols = [g.column for g in contract.group_by if g.column in current_df.columns]
            
            agg_col = None
            agg_op = "count"
            if contract.aggregations:
                target_agg = contract.aggregations[0]
                agg_col = target_agg.column
                agg_op = (target_agg.operation or "count").lower()
            elif contract.columns_required:
                for c in contract.columns_required:
                    if c in current_df.columns and c not in group_cols:
                        agg_col = c
                        break

            # Handle Missing Values Operation
            if agg_op == "missing_values":
                target = agg_col if agg_col and agg_col in current_df.columns else current_df.columns[0]
                columns_used.append(target)
                operations_executed.append({"operation": "missing_values", "column": target})
                missing_cnt = int(current_df[target].isna().sum())
                return {
                    "success": True,
                    "result": missing_cnt,
                    "metric": f"missing_values_{target}",
                    "label": None,
                    "unit": "count",
                    "result_type": "integer",
                    "datasets_used": list(set(datasets_used)),
                    "columns_used": list(set(columns_used)),
                    "runtime_operations": operations_executed,
                    "join_evidence": join_evidence
                }

            # Handle Duplicate Analysis Operation
            if agg_op == "duplicate_analysis":
                operations_executed.append({"operation": "duplicate_analysis"})
                dup_cnt = int(current_df.duplicated().sum())
                return {
                    "success": True,
                    "result": dup_cnt,
                    "metric": "duplicate_rows_count",
                    "label": None,
                    "unit": "count",
                    "result_type": "integer",
                    "datasets_used": list(set(datasets_used)),
                    "columns_used": list(set(columns_used)),
                    "runtime_operations": operations_executed,
                    "join_evidence": join_evidence
                }

            # Handle Correlation Operation
            if agg_op == "correlation":
                num_cols = [c for c in contract.columns_required if c in current_df.columns and pd.api.types.is_numeric_dtype(current_df[c])]
                if len(num_cols) < 2:
                    all_nums = [c for c in current_df.columns if pd.api.types.is_numeric_dtype(current_df[c])]
                    if len(all_nums) >= 2:
                        num_cols = all_nums[:2]
                    else:
                        return {"success": False, "error": "Correlation requires at least 2 numeric columns."}
                
                c1, c2 = num_cols[0], num_cols[1]
                columns_used.extend([c1, c2])
                operations_executed.append({"operation": "correlation", "columns": [c1, c2]})
                corr_val = float(current_df[c1].corr(current_df[c2]))
                corr_val = round(corr_val, 4) if not np.isnan(corr_val) else 0.0
                return {
                    "success": True,
                    "result": corr_val,
                    "metric": f"correlation_{c1}_{c2}",
                    "label": None,
                    "unit": "unitless",
                    "result_type": "float",
                    "datasets_used": list(set(datasets_used)),
                    "columns_used": list(set(columns_used)),
                    "runtime_operations": operations_executed,
                    "join_evidence": join_evidence
                }

            # 5. Grouped Computations
            if group_cols:
                columns_used.extend(group_cols)
                if agg_col and agg_col in current_df.columns:
                    columns_used.append(agg_col)
                else:
                    # Default to first non-group column or count
                    non_group = [c for c in current_df.columns if c not in group_cols]
                    agg_col = non_group[0] if non_group else group_cols[0]
                    columns_used.append(agg_col)

                operations_executed.append({
                    "operation": "group_by",
                    "dataset": main_ds,
                    "column": group_cols[0] if len(group_cols) == 1 else None,
                    "columns": group_cols
                })
                operations_executed.append({
                    "operation": "aggregate",
                    "dataset": main_ds,
                    "column": agg_col,
                    "function": agg_op
                })

                # Perform the specific groupby aggregation
                gb = current_df.groupby(group_cols, as_index=False)
                if agg_op == "mean":
                    grouped = gb[agg_col].mean()
                elif agg_op == "sum":
                    grouped = gb[agg_col].sum()
                elif agg_op == "median":
                    grouped = gb[agg_col].median()
                elif agg_op == "min":
                    grouped = gb[agg_col].min()
                elif agg_op == "max":
                    grouped = gb[agg_col].max()
                elif agg_op == "std":
                    grouped = gb[agg_col].std()
                elif agg_op == "variance":
                    grouped = gb[agg_col].var()
                elif agg_op in ["count", "nunique"]:
                    grouped = gb[agg_col].nunique() if agg_op == "nunique" else gb[agg_col].count()
                else:
                    return {"success": False, "error": f"Unsupported aggregation operation: '{agg_op}'"}

                # Sorting if specified
                sort_order = "desc"
                if contract.sorting:
                    sort_order = contract.sorting[0].order
                    operations_executed.append({
                        "operation": "sort",
                        "column": contract.sorting[0].column or agg_col,
                        "order": sort_order
                    })
                    grouped = grouped.sort_values(by=agg_col, ascending=(sort_order == "asc"))

                if contract.limit is not None:
                    operations_executed.append({"operation": "limit", "value": contract.limit})
                    grouped = grouped.head(contract.limit)

                # Check if RANKED_GROUP (scalar top/bottom row) or GROUP_AGGREGATE (all groups table)
                if contract.expected_result_type == "ranked_item" or (contract.limit == 1 and contract.sorting):
                    if len(grouped) == 0:
                        return {"success": False, "error": "Group aggregation returned 0 rows."}
                    top_row = grouped.iloc[0]
                    res_val = round(float(top_row[agg_col]), 2)
                    res_label = str(top_row[group_cols[0]])
                    return {
                        "success": True,
                        "result": res_val,
                        "metric": contract.expected_metric or f"{agg_op}_{agg_col}_by_{group_cols[0]}",
                        "label": res_label,
                        "unit": contract.expected_unit,
                        "result_type": "ranked_item",
                        "datasets_used": list(set(datasets_used)),
                        "columns_used": list(set(columns_used)),
                        "runtime_operations": operations_executed,
                        "join_evidence": join_evidence,
                        "table": grouped.to_dict(orient="records")
                    }
                else:
                    # Return ALL groups for GROUP_AGGREGATE
                    table_records = grouped.to_dict(orient="records")
                    # Round float values in table records
                    for r in table_records:
                        if agg_col in r and isinstance(r[agg_col], (float, np.floating)):
                            r[agg_col] = round(float(r[agg_col]), 2)

                    return {
                        "success": True,
                        "result": table_records,
                        "metric": contract.expected_metric or f"{agg_op}_{agg_col}_by_{group_cols[0]}",
                        "label": None,
                        "unit": contract.expected_unit,
                        "result_type": "grouped_table",
                        "datasets_used": list(set(datasets_used)),
                        "columns_used": list(set(columns_used)),
                        "runtime_operations": operations_executed,
                        "join_evidence": join_evidence,
                        "table": table_records
                    }

            # 6. Scalar Aggregations
            elif agg_col and agg_col in current_df.columns:
                columns_used.append(agg_col)
                operations_executed.append({
                    "operation": "aggregate",
                    "dataset": main_ds,
                    "column": agg_col,
                    "function": agg_op
                })

                series = current_df[agg_col]
                if agg_op == "mean":
                    val = float(series.mean())
                elif agg_op == "sum":
                    val = float(series.sum())
                elif agg_op == "median":
                    val = float(series.median())
                elif agg_op == "min":
                    val = float(series.min())
                elif agg_op == "max":
                    val = float(series.max())
                elif agg_op == "std":
                    val = float(series.std())
                elif agg_op == "variance":
                    val = float(series.var())
                elif agg_op == "nunique":
                    val = int(series.nunique())
                elif agg_op == "count":
                    val = int(series.count())
                else:
                    return {"success": False, "error": f"Unsupported scalar aggregation operation: '{agg_op}'"}

                res_val = round(val, 2) if isinstance(val, float) else val
                return {
                    "success": True,
                    "result": res_val,
                    "metric": contract.expected_metric or f"{agg_op}_{agg_col}",
                    "label": None,
                    "unit": contract.expected_unit,
                    "result_type": contract.expected_result_type or ("integer" if isinstance(res_val, int) else "float"),
                    "datasets_used": list(set(datasets_used)),
                    "columns_used": list(set(columns_used)),
                    "runtime_operations": operations_executed,
                    "join_evidence": join_evidence
                }

            # 7. Fallback Row Count
            else:
                operations_executed.append({
                    "operation": "aggregate",
                    "dataset": main_ds,
                    "column": None,
                    "function": "count"
                })
                row_cnt = int(len(current_df))
                return {
                    "success": True,
                    "result": row_cnt,
                    "metric": contract.expected_metric or "row_count",
                    "label": None,
                    "unit": "count",
                    "result_type": "integer",
                    "datasets_used": list(set(datasets_used)),
                    "columns_used": list(set(columns_used)),
                    "runtime_operations": operations_executed,
                    "join_evidence": join_evidence
                }

        except Exception as ex:
            return {
                "success": False,
                "error": f"ContractExecutor error: {str(ex)}"
            }
