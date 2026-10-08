import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.models.analysis_contract import AnalysisContract
from backend.data.dataset_resolver import DatasetResolver, DatasetResolverError
from backend.data.column_resolver import ColumnResolver, ColumnResolverError
from backend.services.storage import storage_service

logger = logging.getLogger(__name__)

class ValidationResult(BaseModel):
    is_valid: bool
    refusal_reason: Optional[str] = None
    errors: List[str] = []

class ContractValidator:
    """Pre-execution gate that strictly validates contract completeness, schema compatibility, and structural correctness."""

    VALID_RESULT_TYPES = {
        "scalar", "integer", "float", "percentage", "ranked_item",
        "grouped_table", "comparison", "string", "boolean", "refusal"
    }

    VALID_AGGREGATIONS = {
        "sum", "mean", "median", "min", "max", "count", "nunique",
        "std", "variance", "correlation", "missing_values", "duplicate_analysis"
    }

    NUMERIC_ONLY_AGGREGATIONS = {
        "sum", "mean", "median", "std", "variance"
    }

    VALID_RETURN_DEFINITIONS = {
        "order_return_rate", "item_return_rate", "revenue_return_rate",
        "category_return_rate", "highest_return_rate_category"
    }

    VALID_UNITS = {
        "INR", "USD", "EUR", "percent", "%", "count", "unitless", "orders", "items", "customers", "days"
    }

    @classmethod
    def _find_dataset_for_col(cls, requested_ds: Optional[str], col_name: str, datasets_required: List[str]) -> str:
        if requested_ds:
            try:
                ColumnResolver.resolve_column(requested_ds, col_name)
                return requested_ds
            except ColumnResolverError:
                pass
        for ds_id in datasets_required:
            try:
                ColumnResolver.resolve_column(ds_id, col_name)
                return ds_id
            except ColumnResolverError:
                pass
        return requested_ds or datasets_required[0]

    @classmethod
    def validate_contract(cls, contract: AnalysisContract) -> ValidationResult:
        errors: List[str] = []

        # 1. Document retrieval query
        if contract.query_type == "document_retrieval":
            if not contract.documents_required:
                return ValidationResult(
                    is_valid=False,
                    refusal_reason="Document query has no documents_required specified",
                    errors=["Empty documents_required"]
                )
            return ValidationResult(is_valid=True)

        # 2. Check datasets required
        if not contract.datasets_required:
            return ValidationResult(
                is_valid=False,
                refusal_reason="Contract has no datasets_required specified",
                errors=["Empty datasets_required"]
            )

        # 3. Check each dataset exists via DatasetResolver
        resolved_dfs: Dict[str, pd.DataFrame] = {}
        for ds_id in contract.datasets_required:
            try:
                res_art = DatasetResolver.resolve_dataset(ds_id)
                df = storage_service.get_dataframe(res_art.dataset_id)
                if df is not None:
                    resolved_dfs[res_art.dataset_id] = df
            except DatasetResolverError as e:
                return ValidationResult(
                    is_valid=False,
                    refusal_reason=f"Dataset resolution failed: {e}",
                    errors=[str(e)]
                )

        # 4. Check each required column exists via ColumnResolver
        for col_spec in contract.columns_required:
            if "." in col_spec:
                ds_id, col_name = col_spec.split(".", 1)
                try:
                    ColumnResolver.resolve_column(ds_id, col_name)
                except ColumnResolverError as e:
                    errors.append(f"Column resolution failed: {e}")
            else:
                found = False
                for ds_id in contract.datasets_required:
                    try:
                        ColumnResolver.resolve_column(ds_id, col_spec)
                        found = True
                        break
                    except ColumnResolverError:
                        pass
                if not found:
                    errors.append(f"Required column '{col_spec}' does not exist in any required dataset {contract.datasets_required}")

        if errors:
            return ValidationResult(
                is_valid=False,
                refusal_reason=f"Column validation failed: {'; '.join(errors)}",
                errors=errors
            )

        # 5. Check joins reference real datasets & keys
        for join in contract.joins:
            try:
                left_d = cls._find_dataset_for_col(join.left_dataset, join.left_column, contract.datasets_required)
                right_d = cls._find_dataset_for_col(join.right_dataset, join.right_column, contract.datasets_required)
                ColumnResolver.resolve_column(left_d, join.left_column)
                ColumnResolver.resolve_column(right_d, join.right_column)
            except (DatasetResolverError, ColumnResolverError) as e:
                errors.append(f"Invalid join specification: {e}")

        # 6. Check filters reference real columns and are type compatible
        for flt in contract.filters:
            try:
                target_d = cls._find_dataset_for_col(flt.dataset, flt.column, contract.datasets_required)
                ColumnResolver.resolve_column(target_d, flt.column)
                
                # Check filter compatibility
                df = resolved_dfs.get(target_d)
                if df is not None and flt.column in df.columns:
                    col_dtype = df[flt.column].dtype
                    if flt.operator in [">", "<", ">=", "<="]:
                        if not pd.api.types.is_numeric_dtype(col_dtype) and not pd.api.types.is_datetime64_any_dtype(col_dtype):
                            # Try coercion test
                            converted = pd.to_numeric(df[flt.column], errors='coerce')
                            if converted.notna().sum() == 0:
                                errors.append(f"Inequality filter operator '{flt.operator}' incompatible with non-numeric column '{flt.column}' ({col_dtype})")
            except (DatasetResolverError, ColumnResolverError) as e:
                errors.append(f"Invalid filter column: {e}")

        # 7. Check aggregations reference real columns and are type compatible
        for agg in contract.aggregations:
            op_name = (agg.operation or "").lower()
            if op_name and op_name not in cls.VALID_AGGREGATIONS:
                errors.append(f"Unsupported aggregation operation: '{op_name}'")

            if agg.column:
                try:
                    target_d = cls._find_dataset_for_col(agg.dataset, agg.column, contract.datasets_required)
                    ColumnResolver.resolve_column(target_d, agg.column)

                    # Check numeric type compatibility
                    if op_name in cls.NUMERIC_ONLY_AGGREGATIONS:
                        df = resolved_dfs.get(target_d)
                        if df is not None and agg.column in df.columns:
                            col_dtype = df[agg.column].dtype
                            if not pd.api.types.is_numeric_dtype(col_dtype):
                                converted = pd.to_numeric(df[agg.column], errors='coerce')
                                if converted.notna().sum() == 0:
                                    errors.append(f"Numeric aggregation '{op_name}' is incompatible with non-numeric column '{agg.column}' of type '{col_dtype}'")
                except (DatasetResolverError, ColumnResolverError) as e:
                    errors.append(f"Invalid aggregation column: {e}")

        # 8. Check group_by columns exist
        for gb in contract.group_by:
            try:
                target_d = cls._find_dataset_for_col(gb.dataset, gb.column, contract.datasets_required)
                ColumnResolver.resolve_column(target_d, gb.column)
            except (DatasetResolverError, ColumnResolverError) as e:
                errors.append(f"Invalid group_by column: {e}")

        # 9. Check sorting columns exist
        for sort_spec in (contract.sorting or []):
            if sort_spec.column:
                try:
                    target_d = cls._find_dataset_for_col(sort_spec.dataset, sort_spec.column, contract.datasets_required)
                    ColumnResolver.resolve_column(target_d, sort_spec.column)
                except (DatasetResolverError, ColumnResolverError) as e:
                    errors.append(f"Invalid sort column: {e}")

        # 10. Check result type and unit validity (NO INR GUESSING)
        if contract.expected_result_type not in cls.VALID_RESULT_TYPES:
            errors.append(f"Unsupported result_type '{contract.expected_result_type}'")

        if contract.expected_unit and contract.expected_unit not in cls.VALID_UNITS:
            errors.append(f"Unsupported or unverified unit '{contract.expected_unit}'")

        # 11. Completeness requirements for return-rate queries
        if ("return rate" in contract.question.lower() or "return_rate" in (contract.expected_metric or "").lower()):
            if not contract.return_definition:
                return ValidationResult(
                    is_valid=False,
                    refusal_reason="Ambiguous return-rate query lacks an explicit return_definition in contract",
                    errors=["Missing return_definition"]
                )
            if contract.return_definition not in cls.VALID_RETURN_DEFINITIONS:
                errors.append(f"Unsupported return_definition '{contract.return_definition}'")

        if errors:
            return ValidationResult(
                is_valid=False,
                refusal_reason=f"Contract validation failed: {'; '.join(errors)}",
                errors=errors
            )

        return ValidationResult(is_valid=True)
