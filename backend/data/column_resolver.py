import re
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from backend.data.dataset_resolver import DatasetResolver, DatasetResolverError

logger = logging.getLogger(__name__)

class ColumnResolution(BaseModel):
    dataset_id: str
    requested_column: str
    resolved_column: str
    data_type: Optional[str] = None
    is_exact_match: bool

class ColumnResolverError(Exception):
    pass

class ColumnResolver:
    """
    Authoritative dynamic column resolver.
    Implements safe normalization (lowercase, trim, normalize spaces/underscores/hyphens/punctuation).
    Matches columns unambiguously.
    Refuses if ambiguous or absent.
    Zero fuzzy guessing.
    """

    @staticmethod
    def normalize_col(name: str) -> str:
        if not name:
            return ""
        n = name.lower().strip()
        n = re.sub(r"\([^)]*\)", "", n)
        n = re.sub(r"[^a-z0-9]", " ", n)
        return " ".join(n.split())

    @staticmethod
    def resolve_column(dataset_id: str, column_name: str, explicit_schema_mapping: Optional[Dict[str, str]] = None) -> ColumnResolution:
        if not dataset_id or not column_name:
            raise ColumnResolverError("Dataset ID and column name must both be specified")

        resolved_ds = DatasetResolver.resolve_dataset(dataset_id)
        cols = resolved_ds.columns

        # 1. Check explicit schema mapping first if provided
        if explicit_schema_mapping and column_name in explicit_schema_mapping:
            mapped_col = explicit_schema_mapping[column_name]
            if mapped_col in cols:
                return ColumnResolution(
                    dataset_id=resolved_ds.dataset_id,
                    requested_column=column_name,
                    resolved_column=mapped_col,
                    is_exact_match=False
                )

        # 2. Exact match check
        if column_name in cols:
            return ColumnResolution(
                dataset_id=resolved_ds.dataset_id,
                requested_column=column_name,
                resolved_column=column_name,
                is_exact_match=True
            )

        # 3. Case-insensitive exact match
        ci_matches = [c for c in cols if c.lower() == column_name.lower()]
        if len(ci_matches) == 1:
            return ColumnResolution(
                dataset_id=resolved_ds.dataset_id,
                requested_column=column_name,
                resolved_column=ci_matches[0],
                is_exact_match=False
            )
        elif len(ci_matches) > 1:
            raise ColumnResolverError(f"Ambiguous column '{column_name}' matches multiple columns: {ci_matches}")

        # 4. Safe normalization match (e.g. 'Revenue ($)' matches 'revenue')
        norm_req = ColumnResolver.normalize_col(column_name)
        norm_matches = []
        for c in cols:
            if ColumnResolver.normalize_col(c) == norm_req:
                norm_matches.append(c)

        if len(norm_matches) == 1:
            return ColumnResolution(
                dataset_id=resolved_ds.dataset_id,
                requested_column=column_name,
                resolved_column=norm_matches[0],
                is_exact_match=False
            )
        elif len(norm_matches) > 1:
            raise ColumnResolverError(f"Ambiguous column '{column_name}' matches multiple normalized columns: {norm_matches}")

        raise ColumnResolverError(
            f"Column '{column_name}' does not exist in dataset '{dataset_id}'. "
            f"Available columns: {cols}. Silent fuzzy column mapping is strictly prohibited."
        )

    @staticmethod
    def validate_columns_exist(dataset_id: str, column_names: List[str]) -> List[ColumnResolution]:
        results = []
        for col in column_names:
            res = ColumnResolver.resolve_column(dataset_id, col)
            results.append(res)
        return results
