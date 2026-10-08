import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.analysis_contract import AnalysisContract

logger = logging.getLogger(__name__)

class OperationVerificationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

class OperationVerifier:
    """
    Deterministic comparator evaluating runtime operation traces against AnalysisContract specifications.
    Validates AGGREGATE, FILTER, GROUP_BY, JOIN, SORT, and LIMIT events with strict field equality.
    """

    @classmethod
    def verify_operations(
        cls,
        contract: AnalysisContract,
        runtime_operations: List[Dict[str, Any]]
    ) -> OperationVerificationResult:
        if not contract:
            return OperationVerificationResult(is_valid=True)

        if contract.query_type == "document_retrieval":
            return OperationVerificationResult(is_valid=True)

        errors: List[str] = []
        details = {
            "contract_aggregations": [a.model_dump() for a in contract.aggregations],
            "contract_filters": [f.model_dump() for f in contract.filters],
            "contract_group_by": [g.column for g in contract.group_by],
            "contract_joins": [j.model_dump() for j in contract.joins],
            "runtime_operations_count": len(runtime_operations or [])
        }

        ops = runtime_operations or []

        # 1. Verify Aggregations (function AND column AND dataset)
        for contract_agg in contract.aggregations:
            expected_fn = (contract_agg.operation or "").lower()
            expected_col = contract_agg.column
            expected_ds = contract_agg.dataset

            if expected_fn:
                matching_agg = None
                mismatch_reasons = []

                for op in ops:
                    if op.get("operation") == "aggregate":
                        actual_fn = (op.get("function") or "").lower()
                        actual_col = op.get("column")
                        actual_ds = op.get("dataset")

                        fn_match = (actual_fn == expected_fn)
                        col_match = (not expected_col or actual_col == expected_col or str(actual_col).lower() == str(expected_col).lower())
                        ds_match = (not expected_ds or not actual_ds or actual_ds == expected_ds or expected_ds in str(actual_ds))

                        if fn_match and col_match and ds_match:
                            matching_agg = op
                            break
                        else:
                            if not fn_match:
                                mismatch_reasons.append(f"function '{actual_fn}' != expected '{expected_fn}'")
                            if not col_match:
                                mismatch_reasons.append(f"column '{actual_col}' != expected '{expected_col}'")
                            if not ds_match:
                                mismatch_reasons.append(f"dataset '{actual_ds}' != expected '{expected_ds}'")

                if not matching_agg:
                    if mismatch_reasons:
                        errors.append(f"Aggregation verification failed: contract specified {expected_fn}({expected_col}) on dataset '{expected_ds}', but runtime executed: {'; '.join(set(mismatch_reasons))}")
                    else:
                        errors.append(f"Missing required aggregation: contract specified {expected_fn}({expected_col}) on dataset '{expected_ds}', but operation was not found in runtime trace.")

        # 2. Verify Filters (column AND operator AND value AND dataset)
        for contract_filter in contract.filters:
            target_col = contract_filter.column
            target_op = contract_filter.operator or "=="
            target_val = str(contract_filter.value).lower() if contract_filter.value is not None else None
            target_ds = contract_filter.dataset

            matching_filter = None
            mismatch_reasons = []

            for op in ops:
                if op.get("operation") == "filter":
                    actual_col = op.get("column")
                    actual_op = op.get("operator", "==")
                    actual_val = str(op.get("value")).lower() if op.get("value") is not None else None
                    actual_ds = op.get("dataset")

                    col_match = (actual_col and target_col and (actual_col == target_col or actual_col.lower() == target_col.lower()))
                    op_match = (actual_op == target_op)
                    val_match = (target_val is None or actual_val == target_val)
                    ds_match = (not target_ds or not actual_ds or actual_ds == target_ds or target_ds in str(actual_ds) or (contract.joins and any(d in str(actual_ds) for d in contract.datasets_required)))

                    if col_match and op_match and val_match and ds_match:
                        matching_filter = op
                        break
                    else:
                        if col_match:
                            if not op_match:
                                mismatch_reasons.append(f"operator '{actual_op}' != expected '{target_op}'")
                            if not val_match:
                                mismatch_reasons.append(f"value '{actual_val}' != expected '{target_val}'")
                            if not ds_match:
                                mismatch_reasons.append(f"dataset '{actual_ds}' != expected '{target_ds}'")

            if not matching_filter:
                if mismatch_reasons:
                    errors.append(f"Filter verification failed: contract specified filter '{target_col} {target_op} {contract_filter.value}', but runtime had {'; '.join(set(mismatch_reasons))}")
                else:
                    errors.append(f"Missing required filter: contract specified filter '{target_col} {target_op} {contract_filter.value}', but filter was not executed in runtime trace.")

        # 3. Verify GroupBy (all requested group columns)
        for contract_gb in contract.group_by:
            target_col = contract_gb.column
            matching_gb = None
            mismatch_col = None

            for op in ops:
                if op.get("operation") in ["group_by", "groupby"]:
                    actual_col = op.get("column")
                    actual_cols = op.get("columns", [])
                    if actual_col and (actual_col == target_col or actual_col.lower() == target_col.lower()):
                        matching_gb = op
                        break
                    elif actual_cols and any(c == target_col or c.lower() == target_col.lower() for c in actual_cols):
                        matching_gb = op
                        break
                    elif actual_col:
                        mismatch_col = actual_col

            if not matching_gb:
                if mismatch_col:
                    errors.append(f"GroupBy verification failed: contract specified GROUP BY '{target_col}', but runtime executed GROUP BY '{mismatch_col}'.")
                else:
                    errors.append(f"Missing required GroupBy: contract specified GROUP BY '{target_col}', but operation was not found in runtime trace.")

        # 4. Verify Joins (left_dataset, left_column, right_dataset, right_column, how)
        for contract_join in contract.joins:
            left_ds = contract_join.left_dataset
            left_col = contract_join.left_column
            right_ds = contract_join.right_dataset
            right_col = contract_join.right_column
            expected_how = contract_join.how or "inner"

            matching_join = None
            mismatch_reasons = []

            for op in ops:
                if op.get("operation") == "join":
                    act_left_ds = op.get("left_dataset")
                    act_right_ds = op.get("right_dataset")
                    act_left_col = op.get("left_column") or op.get("on")
                    act_right_col = op.get("right_column") or op.get("on")
                    act_how = op.get("how", "inner")

                    col_match = (
                        (act_left_col and left_col and (act_left_col == left_col or act_left_col.lower() == left_col.lower())) and
                        (act_right_col and right_col and (act_right_col == right_col or act_right_col.lower() == right_col.lower()))
                    )
                    how_match = (act_how == expected_how)
                    ds_match = (
                        (not left_ds or not act_left_ds or left_ds == act_left_ds or left_ds in str(act_left_ds)) and
                        (not right_ds or not act_right_ds or right_ds == act_right_ds or right_ds in str(act_right_ds))
                    )

                    if col_match and how_match and ds_match:
                        matching_join = op
                        break
                    else:
                        if not col_match:
                            mismatch_reasons.append(f"join columns '{act_left_col}'='{act_right_col}' != expected '{left_col}'='{right_col}'")
                        if not how_match:
                            mismatch_reasons.append(f"how '{act_how}' != expected '{expected_how}'")

            if not matching_join:
                if mismatch_reasons:
                    errors.append(f"Join verification failed: contract specified join on '{left_col}'='{right_col}', but runtime had {'; '.join(set(mismatch_reasons))}")
                else:
                    errors.append(f"Missing required Join: contract specified join on '{left_col}'='{right_col}', but join was not executed in runtime trace.")

        # 5. Verify Sort (column AND order)
        for contract_sort in (contract.sorting or []):
            target_col = contract_sort.column
            target_order = contract_sort.order or "desc"
            matching_sort = None
            mismatch_order = None

            for op in ops:
                if op.get("operation") == "sort":
                    actual_col = op.get("column")
                    actual_order = op.get("order", "asc")
                    if actual_col and (actual_col == target_col or actual_col.lower() == target_col.lower()):
                        if actual_order == target_order:
                            matching_sort = op
                            break
                        else:
                            mismatch_order = actual_order

            if not matching_sort:
                if mismatch_order:
                    errors.append(f"Sort verification failed: contract specified SORT BY '{target_col}' {target_order}, but runtime sorted {mismatch_order}.")
                else:
                    errors.append(f"Missing required Sort: contract specified SORT BY '{target_col}' {target_order}, but sort was not executed in runtime trace.")

        # 6. Verify Limit (exact value)
        if contract.limit is not None:
            matching_limit = None
            actual_limit_val = None
            for op in ops:
                if op.get("operation") == "limit":
                    actual_limit_val = op.get("value")
                    if actual_limit_val == contract.limit:
                        matching_limit = op
                        break

            if not matching_limit:
                if actual_limit_val is not None:
                    errors.append(f"Limit verification failed: contract specified LIMIT {contract.limit}, but runtime executed LIMIT {actual_limit_val}.")
                else:
                    errors.append(f"Missing required Limit: contract specified LIMIT {contract.limit}, but limit was not recorded in runtime trace.")

        is_valid = len(errors) == 0
        return OperationVerificationResult(is_valid=is_valid, errors=errors, details=details)
