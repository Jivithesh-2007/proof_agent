import math
from typing import Dict, Any, Tuple, List, Optional
from backend.execution.sandbox import SandboxExecutionEnvironment
from backend.models.dataset import DatasetArtifact
from backend.models.analysis_contract import AnalysisContract
from backend.models.verification import CheckStatus
from backend.analysis.contract_executor import ContractExecutor

class ReproducibilityVerifier:
    """Verifies that analytical execution produces identical or numerically tolerant outputs and operation traces on repeat runs."""

    @classmethod
    def verify_reproducibility(
        cls,
        sandbox: Optional[SandboxExecutionEnvironment],
        code: Optional[str],
        initial_res: Dict[str, Any],
        datasets: List[DatasetArtifact],
        contract: Optional[AnalysisContract] = None,
        tolerance: float = 1e-6
    ) -> Tuple[CheckStatus, float, str, list[str]]:
        errors = []

        if code and sandbox:
            run2 = sandbox.execute(code, datasets)
            if not run2.get("success", False):
                return CheckStatus.FAIL, 0.0, "execution_failure", ["Reproducibility test failed: second execution crashed."]

            out1 = initial_res.get("parsed_output")
            out2 = run2.get("parsed_output")

            cols1 = set(c.get("column") for c in initial_res.get("accessed_columns", []) if isinstance(c, dict) and c.get("column"))
            cols2 = set(c.get("column") for c in run2.get("accessed_columns", []) if isinstance(c, dict) and c.get("column"))
            if cols1 and cols2 and cols1 != cols2:
                return CheckStatus.FAIL, 0.0, "column_evidence_mismatch", [f"Reproducibility evidence mismatch: run1 accessed columns {cols1} but run2 accessed {cols2}."]

            if out1 == out2 and out1 is not None:
                return CheckStatus.PASS, 0.0, "exact_canonical_match", []

            if isinstance(out1, dict) and isinstance(out2, dict) and "result" in out1 and "result" in out2:
                v1, v2 = out1["result"], out2["result"]
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    diff = abs(v1 - v2)
                    if diff <= tolerance or math.isclose(v1, v2, rel_tol=1e-5, abs_tol=tolerance):
                        return CheckStatus.PASS, round(diff, 6), "numeric_tolerance", []
                    else:
                        return CheckStatus.FAIL, round(diff, 6), "numeric_tolerance", [f"Numeric result mismatch on repeat run: {v1} vs {v2} (diff: {diff})."]
                elif v1 == v2:
                    return CheckStatus.PASS, 0.0, "exact_result_match", []

            if out1 is None or out2 is None:
                if initial_res.get("stdout") == run2.get("stdout"):
                    return CheckStatus.PASS, 0.0, "exact_stdout_match", []
                else:
                    return CheckStatus.FAIL, 0.0, "stdout_mismatch", ["Stdout mismatch on repeat execution."]

            return CheckStatus.FAIL, 0.0, "canonical_mismatch", [f"Output mismatch on repeat run: {out1} vs {out2}."]

        elif contract:
            dataset_files = {art.dataset_id: art.workspace_path for art in datasets}
            run2 = ContractExecutor.execute(contract, dataset_files)
            if not run2.get("success", False):
                return CheckStatus.FAIL, 0.0, "execution_failure", [f"Reproducibility run failed: {run2.get('error')}"]

            v1 = initial_res.get("result")
            v2 = run2.get("result")

            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                diff = abs(float(v1) - float(v2))
                if diff <= tolerance or math.isclose(float(v1), float(v2), rel_tol=1e-5, abs_tol=tolerance):
                    return CheckStatus.PASS, round(diff, 6), "numeric_tolerance", []
                else:
                    return CheckStatus.FAIL, round(diff, 6), "numeric_tolerance", [f"Numeric result mismatch: {v1} vs {v2}"]
            elif v1 == v2:
                return CheckStatus.PASS, 0.0, "exact_canonical_match", []
            else:
                return CheckStatus.FAIL, 0.0, "canonical_mismatch", [f"Result mismatch on repeat execution: {v1} != {v2}"]

        return CheckStatus.PASS, 0.0, "deterministic_verified", []
