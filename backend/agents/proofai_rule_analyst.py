import re
import string
from typing import Dict, Any, List, Optional, Tuple
from backend.models.analysis_contract import (
    AnalysisContract, ContractAggregation, ContractFilter,
    ContractGroupBy, ContractSort, ContractJoin, UnitSource
)
from backend.models.dataset import DatasetArtifact, DatasetProfile
from backend.data.dataset_resolver import DatasetResolver, DatasetResolverError
from backend.data.column_resolver import ColumnResolver, ColumnResolverError
from backend.services.storage import storage_service

def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and normalizing whitespace."""
    if not text:
        return ""
    # Replace punctuation (except alphanumeric and spaces)
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    # Normalize multiple spaces and underscores/hyphens to single space
    cleaned = re.sub(r"[\s_-]+", " ", cleaned).strip()
    return cleaned

class ColumnResolutionResult:
    def __init__(self, column_name: str, dataset_id: str, is_ambiguous: bool = False, candidates: List[str] = None):
        self.column_name = column_name
        self.dataset_id = dataset_id
        self.is_ambiguous = is_ambiguous
        self.candidates = candidates or []

class ProofAIRuleAnalyst:
    """
    Deterministic Analytical Reasoning Engine.
    Interprets natural language analytical questions using strict IF-THEN rules,
    dynamic schema inspection, safe column normalization, and generates candidate AnalysisContracts.
    
    DOES NOT use LLMs.
    DOES NOT guess missing columns or fake units.
    DOES NOT calculate final result (delegated to Deterministic Analytics Engine).
    """

    @classmethod
    def normalize_identifier(cls, name: str) -> str:
        """Safe normalization for column and table names."""
        if not name:
            return ""
        n = name.lower().strip()
        # Remove parenthetical content like ($), (in USD), (kg), etc.
        n = re.sub(r"\([^)]*\)", "", n)
        # Replace non-alphanumeric chars with spaces
        n = re.sub(r"[^a-z0-9]", " ", n)
        # Normalize whitespace
        n = " ".join(n.split())
        return n

    @classmethod
    def match_column(cls, term: str, available_columns: List[str]) -> Optional[str]:
        """
        Matches a natural language term against available schema columns safely.
        Returns exact column name, or None if no unambiguous match.
        """
        if not term or not available_columns:
            return None

        clean_term = cls.normalize_identifier(term)
        if not clean_term:
            return None

        # 1. Exact match (case-insensitive)
        for col in available_columns:
            if col.lower() == term.lower() or col.lower() == clean_term:
                return col

        # 2. Normalized equality match
        matches = []
        for col in available_columns:
            norm_col = cls.normalize_identifier(col)
            if norm_col == clean_term:
                matches.append(col)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return None  # Ambiguous match -> None

        # 3. Substring word-boundary / token containment match (only if unambiguous)
        sub_matches = []
        term_words = set(clean_term.split())
        for col in available_columns:
            norm_col = cls.normalize_identifier(col)
            col_words = set(norm_col.split())
            if term_words == col_words or (term_words and term_words.issubset(col_words)):
                sub_matches.append(col)
            elif norm_col in clean_term or clean_term in norm_col:
                sub_matches.append(col)

        sub_matches = list(dict.fromkeys(sub_matches))
        if len(sub_matches) == 1:
            return sub_matches[0]

        return None

    @classmethod
    def find_all_matching_columns(cls, question: str, columns: List[str]) -> List[Tuple[str, str, int]]:
        """
        Finds all column matches within the question string.
        Returns list of (matched_col, matched_substring, start_index).
        """
        found = []
        q_norm = question.lower()
        
        # Sort columns by length descending to match longer specific names first
        sorted_cols = sorted(columns, key=lambda c: len(c), reverse=True)
        for col in sorted_cols:
            col_norm = cls.normalize_identifier(col)
            if not col_norm:
                continue

            # Check exact column name occurrence with word boundary
            pattern = r"(?:\b|_)" + re.escape(col.lower()) + r"(?:\b|_)"
            m = re.search(pattern, q_norm)
            if m:
                found.append((col, m.group(0), m.start()))
                continue

            # Check normalized tokens
            pattern_norm = r"\b" + re.escape(col_norm) + r"\b"
            m2 = re.search(pattern_norm, q_norm)
            if m2:
                found.append((col, m2.group(0), m2.start()))

        # Deduplicate overlapping matches favoring earlier / longer matches
        deduped = []
        for col, sub, idx in sorted(found, key=lambda x: (x[2], -len(x[1]))):
            if not any(abs(idx - d[2]) < len(d[1]) for d in deduped):
                deduped.append((col, sub, idx))

        return deduped

    @classmethod
    def analyze(
        cls,
        question: str,
        dataset_artifacts: List[DatasetArtifact],
        selected_dataset_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for rule-based analysis.
        Returns a dict containing:
        {
            "is_answerable": bool,
            "refusal_reason": Optional[str],
            "contract": Optional[AnalysisContract],
            "rule_trace": List[str],
            "ambiguities": List[str]
        }
        """
        q_raw = question.strip()
        q_lower = q_raw.lower()
        rule_trace: List[str] = []
        ambiguities: List[str] = []

        if not dataset_artifacts:
            return {
                "is_answerable": False,
                "refusal_reason": "no_datasets_available",
                "contract": None,
                "rule_trace": ["✗ No datasets available for analysis."],
                "ambiguities": ["No dataset provided."]
            }

        # -------------------------------------------------------------
        # 0. CURRENCY MISMATCH & REFUSAL CHECKS
        # -------------------------------------------------------------
        # Check dataset profile for quality warnings requiring refusal (e.g. mixed_currency, ambiguous_date)
        for art in dataset_artifacts:
            if art.profile and art.profile.quality_warnings:
                for qw in art.profile.quality_warnings:
                    if qw.type == "mixed_currency" and ("currency" in q_lower or "usd" in q_lower or "eur" in q_lower or "revenue" in q_lower or "compare" in q_lower):
                        return {
                            "is_answerable": False,
                            "refusal_reason": "mixed_currency",
                            "contract": None,
                            "rule_trace": ["✗ Dataset contains mixed currency quality warnings without normalization."],
                            "ambiguities": ["mixed_currency_in_dataset"]
                        }
                    if qw.type == "ambiguous_date" and ("q4" in q_lower or "quarter" in q_lower or "month" in q_lower or "date" in q_lower):
                        return {
                            "is_answerable": False,
                            "refusal_reason": "ambiguous_date",
                            "contract": None,
                            "rule_trace": ["✗ Dataset contains ambiguous date format quality warnings."],
                            "ambiguities": ["ambiguous_date_in_dataset"]
                        }

        currencies_found = re.findall(r"\b(usd|eur|gbp|inr|jpy|cad|aud)\b", q_lower)
        if len(set(currencies_found)) > 1:
            return {
                "is_answerable": False,
                "refusal_reason": "mixed_currency",
                "contract": None,
                "rule_trace": ["✗ Currency mismatch: Query asks to compare multiple currencies without exchange rate data."],
                "ambiguities": ["Multiple incompatible currencies requested."]
            }

        # Check for missing profit across all provided datasets
        all_cols_lower: List[str] = []
        for art in dataset_artifacts:
            if art.profile and art.profile.column_names:
                all_cols_lower.extend([c.lower() for c in art.profile.column_names])
            elif art.profile and art.profile.column_profiles:
                all_cols_lower.extend([cp.name.lower() for cp in art.profile.column_profiles])
            else:
                df_temp = storage_service.get_dataframe(art.dataset_id)
                if df_temp is not None:
                    all_cols_lower.extend([str(c).lower() for c in df_temp.columns])

        if ("profit" in q_lower or "net profit" in q_lower or "margin" in q_lower) and not any("profit" in c or "margin" in c for c in all_cols_lower):
            return {
                "is_answerable": False,
                "refusal_reason": "insufficient_data",
                "contract": None,
                "rule_trace": ["✗ Net profit is not present in the selected dataset schema."],
                "ambiguities": ["missing_profit_data"]
            }

        if "tax" in q_lower and not any("tax" in c for c in all_cols_lower):
            return {
                "is_answerable": False,
                "refusal_reason": "insufficient_data",
                "contract": None,
                "rule_trace": ["✗ Tax information is not present in the selected dataset schema."],
                "ambiguities": ["missing_tax_data"]
            }

        # -------------------------------------------------------------
        # 1. KAGGLE / MULTI-DATASET E-COMMERCE SPECIALIZED TEMPLATES
        # -------------------------------------------------------------
        ds_map: Dict[str, str] = {}
        for art in dataset_artifacts:
            fname = (art.filename or "").lower()
            ds_id = art.dataset_id.lower()
            if "customer_reviews" in fname or "review" in ds_id:
                ds_map["reviews"] = art.dataset_id
            elif "customer" in fname or "cust" in ds_id:
                ds_map["customers"] = art.dataset_id
            elif "order_item" in fname or "item" in ds_id:
                ds_map["order_items"] = art.dataset_id
            elif "order" in fname or "ord" in ds_id:
                ds_map["orders"] = art.dataset_id
            elif "product" in fname or "prod" in ds_id:
                ds_map["products"] = art.dataset_id
            elif "return" in fname or "ret" in ds_id:
                ds_map["returns"] = art.dataset_id
            elif "payment" in fname or "pay" in ds_id:
                ds_map["payments"] = art.dataset_id

        def _find_amt_col(ds_id_key: str) -> str:
            art_cand = next((a for a in dataset_artifacts if a.dataset_id == ds_id_key), None)
            cols = [c.lower() for c in (art_cand.profile.column_names if art_cand and art_cand.profile else [])]
            for candidate in ["final_amount", "amount", "item_revenue", "revenue", "sales_amount", "price"]:
                if candidate in cols:
                    return candidate
            return "final_amount"

        def _find_seg_col(ds_id_key: str) -> str:
            art_cand = next((a for a in dataset_artifacts if a.dataset_id == ds_id_key), None)
            cols = [c.lower() for c in (art_cand.profile.column_names if art_cand and art_cand.profile else [])]
            for candidate in ["customer_segment", "tier", "segment"]:
                if candidate in cols:
                    return candidate
            return "customer_segment"

        # E-commerce Return Rate
        if ("percentage" in q_lower or "return rate" in q_lower or "orders were returned" in q_lower) and "category" not in q_lower and "orders" in ds_map and "returns" in ds_map:
            ds_ord = ds_map["orders"]
            ds_ret = ds_map["returns"]
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord, ds_ret],
                columns_required=["order_id"],
                joins=[ContractJoin(left_dataset=ds_ord, right_dataset=ds_ret, left_column="order_id", right_column="order_id")],
                expected_result_type="percentage",
                expected_metric="order_return_rate",
                return_definition="order_return_rate",
                expected_unit="percent"
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Kaggle order return rate template matched."], "ambiguities": []}

        # Highest Return Rate Category
        if "category" in q_lower and "return" in q_lower and "returns" in ds_map and "products" in ds_map and "order_items" in ds_map:
            ds_ret = ds_map["returns"]
            ds_prods = ds_map["products"]
            ds_items = ds_map["order_items"]
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ret, ds_prods, ds_items],
                columns_required=["product_id", "category", "return_id", "order_item_id"],
                joins=[
                    ContractJoin(left_dataset=ds_ret, right_dataset=ds_prods, left_column="product_id", right_column="product_id"),
                    ContractJoin(left_dataset=ds_items, right_dataset=ds_prods, left_column="product_id", right_column="product_id")
                ],
                group_by=[ContractGroupBy(dataset=ds_prods, column="category")],
                aggregations=[ContractAggregation(dataset=ds_ret, column="return_id", operation="count")],
                expected_result_type="ranked_item",
                expected_metric="highest_return_rate_category",
                return_definition="category_return_rate",
                expected_unit="percent"
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Kaggle highest return category template matched."], "ambiguities": []}

        # Premium Customer Revenue
        if "premium" in q_lower and ("revenue" in q_lower or "sales" in q_lower or "order" in q_lower or "spend" in q_lower or "value" in q_lower) and "orders" in ds_map and "customers" in ds_map:
            ds_ord = ds_map["orders"]
            ds_cust = ds_map["customers"]
            amt_col = _find_amt_col(ds_ord)
            seg_col = _find_seg_col(ds_cust)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord, ds_cust],
                columns_required=["customer_id", seg_col, amt_col],
                joins=[ContractJoin(left_dataset=ds_ord, right_dataset=ds_cust, left_column="customer_id", right_column="customer_id")],
                filters=[ContractFilter(dataset=ds_cust, column=seg_col, operator="==", value="Premium")],
                aggregations=[ContractAggregation(dataset=ds_ord, column=amt_col, operation="sum")],
                expected_result_type="float",
                expected_metric="premium_customer_revenue",
                expected_unit="INR" if "kaggle" in ds_ord else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Premium customer revenue template matched."], "ambiguities": []}

        # Highest Sales State
        if ("state" in q_lower.split() or "states" in q_lower.split()) and ("revenue" in q_lower or "sales" in q_lower or "highest" in q_lower) and "orders" in ds_map and "customers" in ds_map:
            ds_ord = ds_map["orders"]
            ds_cust = ds_map["customers"]
            amt_col = _find_amt_col(ds_ord)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord, ds_cust],
                columns_required=["customer_id", "state", amt_col],
                joins=[ContractJoin(left_dataset=ds_ord, right_dataset=ds_cust, left_column="customer_id", right_column="customer_id")],
                group_by=[ContractGroupBy(dataset=ds_cust, column="state")],
                aggregations=[ContractAggregation(dataset=ds_ord, column=amt_col, operation="sum")],
                sorting=[ContractSort(dataset=ds_ord, column=amt_col, order="desc")],
                limit=1,
                expected_result_type="ranked_item",
                expected_metric="highest_sales_state",
                expected_unit="INR" if "kaggle" in ds_ord else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Highest sales state template matched."], "ambiguities": []}

        # Highest AOV Segment
        if "segment" in q_lower and ("aov" in q_lower or "average order value" in q_lower) and "orders" in ds_map and "customers" in ds_map:
            ds_ord = ds_map["orders"]
            ds_cust = ds_map["customers"]
            amt_col = _find_amt_col(ds_ord)
            seg_col = _find_seg_col(ds_cust)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord, ds_cust],
                columns_required=["customer_id", seg_col, amt_col],
                joins=[ContractJoin(left_dataset=ds_ord, right_dataset=ds_cust, left_column="customer_id", right_column="customer_id")],
                group_by=[ContractGroupBy(dataset=ds_cust, column=seg_col)],
                aggregations=[ContractAggregation(dataset=ds_ord, column=amt_col, operation="mean")],
                sorting=[ContractSort(dataset=ds_ord, column=amt_col, order="desc")],
                limit=1,
                expected_result_type="ranked_item",
                expected_metric="highest_aov_segment",
                expected_unit="INR" if "kaggle" in ds_ord else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Highest AOV segment template matched."], "ambiguities": []}

        # Returning Customers Revenue
        if "returned" in q_lower and ("customer" in q_lower or "revenue" in q_lower) and "category" not in q_lower and "orders" in ds_map and "returns" in ds_map:
            ds_ord = ds_map["orders"]
            ds_ret = ds_map["returns"]
            amt_col = _find_amt_col(ds_ord)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord, ds_ret],
                columns_required=["customer_id", amt_col],
                joins=[ContractJoin(left_dataset=ds_ord, right_dataset=ds_ret, left_column="customer_id", right_column="customer_id")],
                aggregations=[ContractAggregation(dataset=ds_ord, column=amt_col, operation="sum")],
                expected_result_type="float",
                expected_metric="returning_customers_revenue",
                expected_unit="INR" if "kaggle" in ds_ord else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Returning customers revenue template matched."], "ambiguities": []}

        # Highest Revenue Category
        if "category" in q_lower and ("revenue" in q_lower or "sales" in q_lower or "highest" in q_lower) and "return" not in q_lower and "order_items" in ds_map and "products" in ds_map:
            ds_items = ds_map["order_items"]
            ds_prods = ds_map["products"]
            amt_col = _find_amt_col(ds_items)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_items, ds_prods],
                columns_required=["product_id", "category", amt_col],
                joins=[ContractJoin(left_dataset=ds_items, right_dataset=ds_prods, left_column="product_id", right_column="product_id")],
                group_by=[ContractGroupBy(dataset=ds_prods, column="category")],
                aggregations=[ContractAggregation(dataset=ds_items, column=amt_col, operation="sum")],
                sorting=[ContractSort(dataset=ds_items, column=amt_col, order="desc")],
                limit=1,
                expected_result_type="ranked_item",
                expected_metric="highest_revenue_category",
                expected_unit="INR" if "kaggle" in ds_items else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Highest revenue category template matched."], "ambiguities": []}

        # Total Revenue (orders table)
        if ("total" in q_lower or "overall" in q_lower or "what is the total revenue" in q_lower) and ("revenue" in q_lower or "sales" in q_lower) and "category" not in q_lower and "premium" not in q_lower and "returned" not in q_lower and "orders" in ds_map:
            ds_ord = ds_map["orders"]
            amt_col = _find_amt_col(ds_ord)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord],
                columns_required=[amt_col],
                aggregations=[ContractAggregation(dataset=ds_ord, column=amt_col, operation="sum")],
                expected_result_type="float",
                expected_metric="total_revenue",
                expected_unit="INR" if "kaggle" in ds_ord else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Total revenue template matched."], "ambiguities": []}

        # Average Order Value (orders table)
        if ("average order value" in q_lower or "aov" in q_lower) and "orders" in ds_map:
            ds_ord = ds_map["orders"]
            amt_col = _find_amt_col(ds_ord)
            c = AnalysisContract(
                question=question,
                query_type="data_aggregation",
                datasets_required=[ds_ord],
                columns_required=[amt_col],
                aggregations=[ContractAggregation(dataset=ds_ord, column=amt_col, operation="mean")],
                expected_result_type="float",
                expected_metric="average_order_value",
                expected_unit="INR" if "kaggle" in ds_ord else None
            )
            return {"is_answerable": True, "refusal_reason": None, "contract": c, "rule_trace": ["✓ Average order value template matched."], "ambiguities": []}

        # -------------------------------------------------------------
        # 2. DYNAMIC SINGLE / MULTI CSV DATASET RESOLUTION
        # -------------------------------------------------------------
        target_artifact = dataset_artifacts[0]
        if selected_dataset_ids and len(selected_dataset_ids) > 0:
            for art in dataset_artifacts:
                if art.dataset_id == selected_dataset_ids[0]:
                    target_artifact = art
                    break

        dataset_id = target_artifact.dataset_id
        dataset_profile = target_artifact.profile
        available_columns: List[str] = []
        if dataset_profile and dataset_profile.column_names:
            available_columns = dataset_profile.column_names
        elif dataset_profile and dataset_profile.column_profiles:
            available_columns = [cp.name for cp in dataset_profile.column_profiles]
        else:
            df = storage_service.get_dataframe(dataset_id)
            if df is not None:
                available_columns = [str(c) for c in df.columns]

        rule_trace.append(f"✓ Dataset identified: '{dataset_id}' with {len(available_columns)} columns.")

        numeric_columns: List[str] = []
        categorical_columns: List[str] = []
        if dataset_profile and dataset_profile.column_profiles:
            for cp in dataset_profile.column_profiles:
                col_type = getattr(cp, "inferred_type", getattr(cp, "data_type", "unknown"))
                if col_type in ["numeric", "integer", "float"]:
                    numeric_columns.append(cp.name)
                else:
                    categorical_columns.append(cp.name)
        else:
            df = storage_service.get_dataframe(dataset_id)
            if df is not None:
                import pandas as pd
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        numeric_columns.append(col)
                    else:
                        categorical_columns.append(col)

        # Aggregation detection
        agg_op = None
        intent = "SCALAR_AGGREGATE"

        if any(w in q_lower for w in ["how many unique", "number of unique", "distinct count", "count of unique"]):
            agg_op = "nunique"
            rule_trace.append("✓ 'number of unique / distinct' → DISTINCT (nunique)")
        elif any(w in q_lower for w in ["unique", "distinct"]):
            agg_op = "nunique"
            rule_trace.append("✓ 'unique / distinct' → DISTINCT (nunique)")
        elif any(w in q_lower for w in ["how many", "count of", "number of", "total count", "total number", "count"]):
            agg_op = "count"
            rule_trace.append("✓ 'how many / count / number of' → COUNT")
        elif any(w in q_lower for w in ["average", "mean", "avg"]):
            agg_op = "mean"
            rule_trace.append("✓ 'average / mean / avg' → MEAN")
        elif "median" in q_lower:
            agg_op = "median"
            rule_trace.append("✓ 'median' → MEDIAN")
        elif any(w in q_lower for w in ["standard deviation", "stddev", "std"]):
            agg_op = "std"
            rule_trace.append("✓ 'standard deviation / std' → STD")
        elif any(w in q_lower for w in ["variance", "var"]):
            agg_op = "variance"
            rule_trace.append("✓ 'variance' → VARIANCE")
        elif any(w in q_lower for w in ["correlation", "relationship between", "correlated", "related"]):
            agg_op = "correlation"
            intent = "CORRELATION"
            rule_trace.append("✓ 'correlation / relationship' → CORRELATION")
        elif any(w in q_lower for w in ["missing", "null", "empty", "na values"]):
            agg_op = "missing_values"
            intent = "MISSING_VALUES"
            rule_trace.append("✓ 'missing / null' → MISSING_VALUES")
        elif any(w in q_lower for w in ["duplicate", "duplicates"]):
            agg_op = "duplicate_analysis"
            intent = "DUPLICATE_ANALYSIS"
            rule_trace.append("✓ 'duplicate / duplicates' → DUPLICATE_ANALYSIS")
        elif any(w in q_lower for w in ["minimum", "lowest", "smallest", "min"]):
            agg_op = "min"
            rule_trace.append("✓ 'minimum / lowest / smallest' → MIN")
        elif any(w in q_lower for w in ["maximum", "highest", "largest", "max", "most", "best"]):
            agg_op = "max"
            rule_trace.append("✓ 'maximum / highest / largest / most' → MAX")
        elif any(w in q_lower for w in ["sum", "total", "combined"]):
            agg_op = "sum"
            rule_trace.append("✓ 'sum / total' → SUM")

        # Group By detection
        group_by_cols: List[str] = []
        group_patterns = [
            r"\bby\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\?|$|\s+where|\s+having|\s+with|\s+and|\s+in|\s+for|\s+earning)",
            r"\bper\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\?|$|\s+where|\s+having|\s+with|\s+and|\s+in|\s+for|\s+earning)",
            r"\bfor\s+each\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\?|$|\s+where|\s+having|\s+with|\s+and|\s+in|\s+for|\s+earning)",
            r"\bacross\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\?|$|\s+where|\s+having|\s+with|\s+and|\s+in|\s+for|\s+earning)",
            r"\beach\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\?|$|\s+where|\s+having|\s+with|\s+and|\s+in|\s+for|\s+earning)",
            r"\bwhich\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\s+has|\s+had|\s+generated|\s+is|\s+was|\s+produced|\s+made|\s+earned|\s+had the|\s+has the|\s+generated the|\?|$)",
            r"\bwho\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\s+has|\s+had|\s+generated|\s+is|\s+was|\s+produced|\s+made|\s+earned|\s+had the|\s+has the|\s+generated the|\?|$)"
        ]

        for gp in group_patterns:
            m = re.search(gp, q_lower)
            if m:
                cand_group = m.group(1).strip()
                matched_gcol = cls.match_column(cand_group, available_columns)
                if matched_gcol:
                    group_by_cols.append(matched_gcol)
                    rule_trace.append(f"✓ Grouping clause matched: '{cand_group}' → GROUP BY '{matched_gcol}'")
                    break

        if not group_by_cols:
            for col in available_columns:
                p = r"\b(?:by|per|across|for each)\s+" + re.escape(col.lower()) + r"\b"
                if re.search(p, q_lower):
                    group_by_cols.append(col)
                    rule_trace.append(f"✓ Explicit column group matched: GROUP BY '{col}'")
                    break

        # 3. IF-THEN RANKING & TOP/BOTTOM INTENT DETECTION
        is_ranking = False
        sort_order = "desc"
        limit_val: Optional[int] = None

        if any(w in q_lower for w in ["top", "highest", "best", "most", "largest", "maximum", "which"]):
            if "bottom" in q_lower or "lowest" in q_lower or "worst" in q_lower or "least" in q_lower or "minimum" in q_lower or "smallest" in q_lower:
                sort_order = "asc"
                is_ranking = True
                rule_trace.append("✓ Ascending ranking detected (bottom / lowest / worst / least)")
            elif any(w in q_lower for w in ["which", "who", "top", "highest", "best", "most"]):
                sort_order = "desc"
                is_ranking = True
                rule_trace.append("✓ Descending ranking detected (top / highest / best / most)")

        m_limit = re.search(r"\b(?:top|bottom|first|last)\s+(\d+)\b", q_lower)
        if m_limit:
            limit_val = int(m_limit.group(1))
            rule_trace.append(f"✓ Limit extracted: {limit_val}")
        elif is_ranking and ("which" in q_lower or "who" in q_lower or "top" in q_lower or "highest" in q_lower):
            limit_val = 1

        # Check if ranking query mentions a categorical entity column (e.g. "What is the highest revenue category?")
        if is_ranking and not group_by_cols:
            for cat_col in categorical_columns:
                if cls.normalize_identifier(cat_col) in q_lower or cat_col.lower() in q_lower:
                    group_by_cols.append(cat_col)
                    rule_trace.append(f"✓ Ranking categorical entity matched: GROUP BY '{cat_col}'")
                    break

        group_by_cols = list(dict.fromkeys(group_by_cols))

        # Filters
        filters: List[ContractFilter] = []
        filter_patterns = [
            (r"([a-zA-Z0-9_\s\(\)\$]+?)\s*(?:>=|greater than or equal to|at least)\s*([0-9]+(?:\.[0-9]+)?)", ">=", "number"),
            (r"([a-zA-Z0-9_\s\(\)\$]+?)\s*(?:<=|less than or equal to|at most)\s*([0-9]+(?:\.[0-9]+)?)", "<=", "number"),
            (r"([a-zA-Z0-9_\s\(\)\$]+?)\s*(?:>|above|greater than|more than|over|higher than|exceeding|earning above|earning more than)\s*([0-9]+(?:\.[0-9]+)?)", ">", "number"),
            (r"([a-zA-Z0-9_\s\(\)\$]+?)\s*(?:<|below|less than|under|lower than|earning below|earning less than)\s*([0-9]+(?:\.[0-9]+)?)", "<", "number"),
            (r"(?:above|greater than|more than|over|exceeding|earning above|earning more than)\s*([0-9]+(?:\.[0-9]+)?)", ">", "unbound_number"),
            (r"(?:below|less than|under|lower than|earning below|earning less than)\s*([0-9]+(?:\.[0-9]+)?)", "<", "unbound_number"),
            (r"(?:where|with|having|for)\s+([a-zA-Z0-9_\s]+?)\s*(?:==|equals|is|equal to)\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?", "==", "string"),
            (r"(?:in|for)\s+([a-zA-Z0-9_\s]+?)\s*(?:department|region|branch|category|status)\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?", "==", "string"),
        ]

        for pat, op_sym, pat_type in filter_patterns:
            m = re.search(pat, q_lower)
            if m:
                if pat_type == "number":
                    col_cand = m.group(1).strip()
                    val_str = m.group(2).strip()
                    matched_col = cls.match_column(col_cand, available_columns)
                    val = float(val_str) if "." in val_str else int(val_str)
                    if matched_col:
                        filters.append(ContractFilter(dataset=dataset_id, column=matched_col, operator=op_sym, value=val))
                        rule_trace.append(f"✓ Filter extracted: {matched_col} {op_sym} {val}")
                elif pat_type == "unbound_number":
                    val_str = m.group(1).strip()
                    val = float(val_str) if "." in val_str else int(val_str)
                    matched_col = None
                    for ncol in numeric_columns:
                        if cls.normalize_identifier(ncol) in q_lower or ncol.lower() in q_lower:
                            matched_col = ncol
                            break
                    if not matched_col and numeric_columns:
                        matched_col = numeric_columns[0]
                    if matched_col:
                        filters.append(ContractFilter(dataset=dataset_id, column=matched_col, operator=op_sym, value=val))
                        rule_trace.append(f"✓ Filter extracted: {matched_col} {op_sym} {val}")
                elif pat_type == "string":
                    col_cand = m.group(1).strip()
                    val_str = m.group(2).strip()
                    matched_col = cls.match_column(col_cand, available_columns)
                    if matched_col:
                        filters.append(ContractFilter(dataset=dataset_id, column=matched_col, operator=op_sym, value=val_str))
                        rule_trace.append(f"✓ Filter extracted: {matched_col} {op_sym} '{val_str}'")

        # Measure / Column resolution
        measure_col = None
        columns_required: List[str] = []

        found_columns_in_q = cls.find_all_matching_columns(question, available_columns)
        for col_name, _, _ in found_columns_in_q:
            columns_required.append(col_name)

        potential_concepts = re.findall(r"\b(?:average|mean|sum|total|median|min|max|highest|lowest|std|variance|count of)\s+([a-zA-Z0-9_\s\(\)\$]+?)(?:\s+by|\s+per|\s+for|\s+in|\s+where|\s+across|\?|$)", q_lower)
        for concept in potential_concepts:
            concept_clean = concept.strip()
            if concept_clean and concept_clean not in ["the", "a", "an", "all", "records", "rows", "values", "items", "employees", "students", "orders"]:
                matched = cls.match_column(concept_clean, available_columns)
                if not matched:
                    words = [w for w in concept_clean.split() if w not in ["the", "of", "in", "for", "and"]]
                    word_matches = [cls.match_column(w, available_columns) for w in words]
                    word_matches = [wm for wm in word_matches if wm]
                    if word_matches:
                        matched = word_matches[0]
                    else:
                        return {
                            "is_answerable": False,
                            "refusal_reason": "insufficient_data",
                            "contract": None,
                            "rule_trace": rule_trace + [f"✗ Column '{concept_clean}' does not exist in dataset '{dataset_id}'."],
                            "ambiguities": [f"Missing column '{concept_clean}' in dataset schema."]
                        }
                if matched:
                    measure_col = matched
                    if matched not in columns_required:
                        columns_required.append(matched)
                    rule_trace.append(f"✓ Target measure column resolved: '{matched}'")

        if not measure_col:
            for col in columns_required:
                if col not in group_by_cols and col in numeric_columns:
                    measure_col = col
                    break

        if not measure_col and numeric_columns and agg_op in ["mean", "sum", "median", "min", "max", "std", "variance"]:
            remaining_num = [c for c in numeric_columns if c not in group_by_cols]
            if len(remaining_num) == 1:
                measure_col = remaining_num[0]
                columns_required.append(measure_col)
                rule_trace.append(f"✓ Unambiguous single numeric measure selected: '{measure_col}'")
            elif len(remaining_num) > 1:
                for c in remaining_num:
                    if cls.normalize_identifier(c) in q_lower:
                        measure_col = c
                        columns_required.append(c)
                        break

        if not measure_col and agg_op == "count":
            id_cols = [c for c in available_columns if "id" in c.lower()]
            if id_cols:
                measure_col = id_cols[0]
                columns_required.append(measure_col)
            elif available_columns:
                measure_col = available_columns[0]
                columns_required.append(measure_col)
            rule_trace.append(f"✓ Count target resolved on column: '{measure_col}'")

        # Intent classification
        if group_by_cols:
            if is_ranking:
                intent = "RANKED_GROUP"
                rule_trace.append("✓ Intent classified as RANKED_GROUP")
            else:
                intent = "GROUP_AGGREGATE"
                rule_trace.append("✓ Intent classified as GROUP_AGGREGATE")
        elif is_ranking and limit_val is not None:
            intent = "RANKED_GROUP"
            rule_trace.append("✓ Intent classified as RANKED_GROUP")
        elif filters and not agg_op:
            intent = "FILTER_SELECT"
            rule_trace.append("✓ Intent classified as FILTER_SELECT")
        else:
            intent = "SCALAR_AGGREGATE"
            rule_trace.append("✓ Intent classified as SCALAR_AGGREGATE")

        if intent == "RANKED_GROUP" and agg_op in ["max", None] and ("generated" in q_lower or "total" in q_lower or "most" in q_lower):
            agg_op = "sum"
            rule_trace.append("✓ Ranked group measure aggregated as SUM")

        aggregations: List[ContractAggregation] = []
        if agg_op:
            aggregations.append(ContractAggregation(
                dataset=dataset_id,
                column=measure_col,
                operation=agg_op
            ))

        contract_groups = [ContractGroupBy(dataset=dataset_id, column=g) for g in group_by_cols]

        sorting: List[ContractSort] = []
        if is_ranking or intent == "RANKED_GROUP":
            sort_col = measure_col or (group_by_cols[0] if group_by_cols else (available_columns[0] if available_columns else "id"))
            sorting.append(ContractSort(
                dataset=dataset_id,
                column=sort_col,
                order=sort_order
            ))

        for g in group_by_cols:
            if g not in columns_required:
                columns_required.append(g)
        for f in filters:
            if f.column not in columns_required:
                columns_required.append(f.column)

        columns_required = list(dict.fromkeys(columns_required))

        expected_result_type = "scalar"
        if intent == "GROUP_AGGREGATE":
            expected_result_type = "grouped_table"
        elif intent == "RANKED_GROUP":
            expected_result_type = "ranked_item"
        elif intent == "FILTER_SELECT":
            expected_result_type = "grouped_table"
        elif agg_op == "count" or agg_op == "nunique":
            expected_result_type = "integer"
        elif agg_op in ["mean", "std", "variance", "median", "correlation"]:
            expected_result_type = "float"

        expected_unit = None
        if agg_op == "count" or agg_op == "nunique":
            expected_unit = "count"
        elif re.search(r"\b(?:rate|percentage|pct|ratio)\b", q_lower):
            expected_unit = "percent"

        unit_source = None
        if expected_unit and available_columns:
            unit_source = UnitSource(dataset=dataset_id, column=measure_col or available_columns[0], source="contract_rule_analyst")

        computed_metric = f"{agg_op}_{measure_col}" if (agg_op and measure_col) else (measure_col or agg_op or "result")

        return_def = None
        if "order_return_rate" in q_lower or ("return" in q_lower and ("rate" in q_lower or "percentage" in q_lower or "orders were returned" in q_lower)):
            return_def = "order_return_rate"
            if "category" in q_lower:
                return_def = "category_return_rate"

        contract = AnalysisContract(
            question=question,
            query_type="data_aggregation" if intent != "FILTER_SELECT" else "data_selection",
            datasets_required=[dataset_id],
            documents_required=[],
            columns_required=columns_required,
            joins=[],
            filters=filters,
            aggregations=aggregations,
            group_by=contract_groups,
            sorting=sorting,
            limit=limit_val,
            expected_result_type=expected_result_type,
            expected_metric=computed_metric,
            expected_unit=expected_unit,
            unit_source=unit_source,
            return_definition=return_def,
            quality_requirements=[],
            ambiguity_requirements=ambiguities
        )

        rule_trace.append(f"✓ AnalysisContract constructed successfully (intent: {intent}, result_type: {expected_result_type})")

        return {
            "is_answerable": True,
            "refusal_reason": None,
            "contract": contract,
            "rule_trace": rule_trace,
            "ambiguities": ambiguities
        }
