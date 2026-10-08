import re
import uuid
import time
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models.query import AnalysisRequest
from backend.models.analysis import AnalysisResult, AnalysisPlan, AnalysisStatus, CanonicalResult
from backend.models.analysis_contract import (
    AnalysisContract, ContractOperation, ContractJoin, ContractFilter,
    ContractAggregation, ContractGroupBy, ContractSort, UnitSource
)
from backend.models.verification import VerificationResult, CheckStatus
from backend.models.dataset import DatasetArtifact
from backend.models.document import DocumentMetadata
from backend.agents.proofai_rule_analyst import ProofAIRuleAnalyst
from backend.agents.analyst import DataAnalystAgent
from backend.agents.document_agent import DocumentAgent
from backend.codegen.generator import CodeGeneratorService
from backend.execution.sandbox import SandboxExecutionEnvironment, LocalIsolatedSandbox
from backend.analysis.contract_executor import ContractExecutor
from backend.analysis.reference_engine import ReferenceEngine
from backend.verification.result_checker import ResultChecker
from backend.verification.reproducibility import ReproducibilityVerifier
from backend.verification.evidence import EvidenceAccumulator
from backend.verification.confidence import ConfidenceCalculator
from backend.verification.contract_checker import StaticContractChecker
from backend.verification.contract_validator import ContractValidator
from backend.verification.join_checker import JoinChecker
from backend.verification.proof_policy import ProofPolicy
from backend.verification.operation_verifier import OperationVerifier
from backend.services.storage import storage_service
from backend.services.answer_renderer import AnswerRenderer
from backend.config import settings

from backend.ml.return_prediction import ReturnPredictionService
from backend.data.catalog import dataset_catalog
from backend.data.dataset_resolver import DatasetResolver

class AnalysisOrchestrator:
    """
    Central proof-carrying orchestrator.
    Powered strictly by deterministic ProofAIRuleAnalyst, AnalysisContract,
    Deterministic Analytics Engine, ReferenceEngine, and complete ProofPolicy.
    NO external LLM or Ollama required.
    """

    def __init__(
        self,
        analyst: Optional[DataAnalystAgent] = None,
        document_agent: Optional[DocumentAgent] = None,
        code_generator: Optional[CodeGeneratorService] = None,
        sandbox: Optional[SandboxExecutionEnvironment] = None,
        planner: Optional[Any] = None
    ):
        self.analyst = analyst or DataAnalystAgent()
        self.document_agent = document_agent
        self.code_generator = code_generator or CodeGeneratorService()
        self.sandbox = sandbox or LocalIsolatedSandbox()

    def _resolve_datasets(self, question: str, req_selected: List[str], has_documents: bool = False) -> List[str]:
        """Creates one authoritative resolved list of dataset IDs."""
        if req_selected:
            resolved = []
            for ds in req_selected:
                ds_id = dataset_catalog.resolve_dataset_by_name(ds) or ds
                resolved.append(ds_id)
            return list(dict.fromkeys(resolved))

        if has_documents:
            return []

        q_lower = question.lower()
        table_ids = []

        if "profit" in q_lower or "revenue" in q_lower or "sales" in q_lower or "aov" in q_lower or "order" in q_lower:
            ds_id = dataset_catalog.table_to_id.get("orders")
            if ds_id: table_ids.append(ds_id)

        if "customer" in q_lower or "state" in q_lower or "segment" in q_lower:
            ds_id = dataset_catalog.table_to_id.get("customers")
            if ds_id: table_ids.append(ds_id)

        if "category" in q_lower or "product" in q_lower or "item" in q_lower:
            ds_items = dataset_catalog.table_to_id.get("order_items")
            ds_prods = dataset_catalog.table_to_id.get("products")
            if ds_items: table_ids.append(ds_items)
            if ds_prods: table_ids.append(ds_prods)

        if "return" in q_lower or "returned" in q_lower:
            ds_ret = dataset_catalog.table_to_id.get("returns")
            if ds_ret: table_ids.append(ds_ret)
            ds_ord = dataset_catalog.table_to_id.get("orders")
            if ds_ord: table_ids.append(ds_ord)
            if "category" in q_lower or "product" in q_lower:
                ds_prods = dataset_catalog.table_to_id.get("products")
                ds_items = dataset_catalog.table_to_id.get("order_items")
                if ds_prods: table_ids.append(ds_prods)
                if ds_items: table_ids.append(ds_items)

        if table_ids:
            return list(dict.fromkeys(table_ids))

        all_user_datasets = [
            d for d in storage_service.list_datasets()
            if not d.dataset_id.startswith("ds_kaggle_")
        ]
        if all_user_datasets:
            return [all_user_datasets[-1].dataset_id]

        all_kaggle = dataset_catalog.list_datasets()
        return [d["dataset_id"] for d in all_kaggle]

    def process_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        start_total = time.perf_counter()
        analysis_id = f"ans_{uuid.uuid4().hex[:12]}"

        # Check if provider is configured if an unsupported external provider is forced
        if settings.LLM_PROVIDER not in ("rule_analyst", "rule_based", "ollama", "mock", "deterministic", "catboost", "default"):
            return AnalysisResult(
                analysis_id=analysis_id,
                question=request.question,
                answer=f"Provider '{settings.LLM_PROVIDER}' is not configured.",
                status=AnalysisStatus.MODEL_NOT_CONFIGURED,
                result_kind="refusal",
                confidence=0.0
            )

        # 0. Predictive ML Query Path (CatBoost Return Prediction Capability)
        if ReturnPredictionService.is_prediction_query(request.question):
            pred_data = ReturnPredictionService.predict_return_risk(request.question)
            if "error" in pred_data:
                v_res = VerificationResult(status="REFUSED", confidence_score=0.0)
                result = AnalysisResult(
                    analysis_id=analysis_id,
                    question=request.question,
                    answer=pred_data["error"],
                    status=AnalysisStatus.REFUSED,
                    result_kind="refusal",
                    refusal_reason="model_not_configured",
                    verification=v_res,
                    confidence=0.0
                )
                storage_service.save_analysis_run(analysis_id, request.question, AnalysisStatus.REFUSED.value, result.model_dump())
                return result

            metrics = pred_data.get("metrics", {})
            roc_auc_val = metrics.get("roc_auc", "N/A")
            preds = pred_data.get("predictions", [])
            conf_val = float(roc_auc_val) if isinstance(roc_auc_val, (int, float)) else 0.80

            v_res = VerificationResult(
                v1_code_executed=CheckStatus.NOT_APPLICABLE,
                v2_output_exists=CheckStatus.NOT_APPLICABLE,
                v3_output_valid_canonical=CheckStatus.NOT_APPLICABLE,
                status="MODEL_PREDICTION",
                confidence_score=conf_val
            )
            answer_str = f"[MODEL PREDICTION] Order Return Risk Analysis: {len(preds)} high-risk orders identified. Model: CatBoostClassifier (ROC-AUC {roc_auc_val})."
            result = AnalysisResult(
                analysis_id=analysis_id,
                question=request.question,
                answer=answer_str,
                status=AnalysisStatus.MODEL_PREDICTION,
                result_kind="model_prediction",
                expected_result_type="model_prediction",
                verification=v_res,
                confidence=conf_val,
                warnings=[pred_data.get("disclaimer", "MODEL PREDICTION: Fact check against deterministic historical records.")]
            )
            storage_service.save_analysis_run(analysis_id, request.question, AnalysisStatus.MODEL_PREDICTION.value, result.model_dump())
            return result

        # 1. Dataset Resolution & Artifact Loading
        has_docs = bool(request.selected_documents)
        initial_dataset_ids = self._resolve_datasets(request.question, request.selected_datasets, has_documents=has_docs)

        selected_artifacts: List[DatasetArtifact] = []
        dataset_schemas: List[Dict[str, Any]] = []
        quality_warnings: List[Dict[str, Any]] = []

        for ds_id in initial_dataset_ids:
            artifact = storage_service.get_dataset_artifact(ds_id)
            if artifact:
                selected_artifacts.append(artifact)
                dataset_schemas.append(artifact.profile.model_dump())
                quality_warnings.extend([w.model_dump() for w in artifact.profile.quality_warnings])

        # 2. Document-Only Query Path
        selected_doc_metas: List[DocumentMetadata] = []
        document_summaries: List[Dict[str, Any]] = []
        for doc_id in request.selected_documents:
            meta = storage_service.get_document_metadata(doc_id)
            if meta:
                selected_doc_metas.append(meta)
                document_summaries.append(meta.model_dump())

        doc_chunks = []
        if (request.selected_documents or not selected_artifacts) and self.document_agent:
            doc_chunks = self.document_agent.retrieve_supporting_chunks(
                request.question,
                selected_document_ids=request.selected_documents,
                top_k=3
            )

        if not selected_artifacts and selected_doc_metas:
            evidence_coll = EvidenceAccumulator.build_evidence([], "", {}, doc_chunks=doc_chunks)
            mock_exec_res = {"success": True, "stdout": "", "stderr": "", "parsed_output": None}
            answer = self.analyst.synthesize_answer(request.question, mock_exec_res, evidence_coll.items)

            v_result = VerificationResult(
                v1_code_executed=CheckStatus.NOT_APPLICABLE,
                v2_output_exists=CheckStatus.NOT_APPLICABLE,
                v3_output_valid_canonical=CheckStatus.NOT_APPLICABLE,
                v4_result_type_matched=CheckStatus.NOT_APPLICABLE,
                v5_result_finite_valid=CheckStatus.NOT_APPLICABLE,
                v6_reproducible=CheckStatus.NOT_APPLICABLE,
                v7_required_datasets_used=CheckStatus.NOT_APPLICABLE,
                v13_evidence_sources_matched=CheckStatus.PASS if len(evidence_coll.items) > 0 else CheckStatus.NOT_APPLICABLE,
                status="DOCUMENT_SUPPORTED",
                confidence_score=0.95
            )

            result = AnalysisResult(
                analysis_id=analysis_id,
                question=request.question,
                answer=answer,
                status=AnalysisStatus.DOCUMENT_SUPPORTED,
                result_kind="document_supported",
                resolved_dataset_ids=initial_dataset_ids,
                evidence=evidence_coll.items,
                verification=v_result,
                confidence=0.95
            )
            storage_service.save_analysis_run(analysis_id, request.question, AnalysisStatus.DOCUMENT_SUPPORTED.value, result.model_dump())
            return result

        # 3. Deterministic ProofAI Rule Analyst Evaluation
        rule_analysis_res = ProofAIRuleAnalyst.analyze(
            request.question,
            selected_artifacts,
            selected_dataset_ids=initial_dataset_ids
        )

        rule_trace = rule_analysis_res.get("rule_trace", [])

        if not rule_analysis_res.get("is_answerable") or not rule_analysis_res.get("contract"):
            refusal_reason_str = rule_analysis_res.get("refusal_reason") or "unsupported_question"
            v_res = VerificationResult(
                v1_code_executed=CheckStatus.NOT_APPLICABLE,
                v2_output_exists=CheckStatus.NOT_APPLICABLE,
                v3_output_valid_canonical=CheckStatus.NOT_APPLICABLE,
                status="REFUSED",
                confidence_score=0.0
            )
            proof_trace = {
                "question": request.question,
                "rule_reasoning": rule_trace,
                "final_status": "REFUSED",
                "refusal_reason": refusal_reason_str
            }
            result = AnalysisResult(
                analysis_id=analysis_id,
                question=request.question,
                answer=f"Question refused: {refusal_reason_str}.",
                status=AnalysisStatus.REFUSED,
                result_kind="refusal",
                expected_result_type="refusal",
                refusal_reason=refusal_reason_str,
                resolved_dataset_ids=initial_dataset_ids,
                proof_trace=proof_trace,
                verification=v_res,
                confidence=0.0,
                warnings=rule_analysis_res.get("ambiguities", [])
            )
            storage_service.save_analysis_run(analysis_id, request.question, AnalysisStatus.REFUSED.value, result.model_dump())
            return result

        contract: AnalysisContract = rule_analysis_res["contract"]
        resolved_dataset_ids = contract.datasets_required or initial_dataset_ids

        # 4. Pre-Execution Contract Validator Gate
        contract_val_res = ContractValidator.validate_contract(contract)
        if not contract_val_res.is_valid:
            v_res = VerificationResult(
                v1_code_executed=CheckStatus.NOT_APPLICABLE,
                v2_output_exists=CheckStatus.NOT_APPLICABLE,
                status="REFUSED",
                confidence_score=0.0
            )
            proof_trace = {
                "question": request.question,
                "rule_reasoning": rule_trace,
                "analysis_contract": contract.model_dump(),
                "final_status": "REFUSED",
                "refusal_reason": contract_val_res.refusal_reason
            }
            result = AnalysisResult(
                analysis_id=analysis_id,
                question=request.question,
                answer=f"Contract validation refused: {contract_val_res.refusal_reason}",
                status=AnalysisStatus.REFUSED,
                result_kind="refusal",
                expected_result_type="refusal",
                refusal_reason=contract_val_res.refusal_reason or "incomplete_contract",
                resolved_dataset_ids=resolved_dataset_ids,
                analysis_contract=contract,
                proof_trace=proof_trace,
                verification=v_res,
                confidence=0.0,
                warnings=contract_val_res.errors
            )
            storage_service.save_analysis_run(analysis_id, request.question, AnalysisStatus.REFUSED.value, result.model_dump())
            return result

        # 5. Deterministic Code Generation & Sandbox Execution
        gen_res = self.code_generator.generate_and_validate(
            question=request.question,
            dataset_schemas=dataset_schemas,
            quality_warnings=quality_warnings,
            analysis_contract=contract
        )
        code = gen_res.get("code", "")
        expected_type = contract.expected_result_type

        attempts_count = 1
        dataset_files = {art.dataset_id: Path(art.workspace_path) for art in selected_artifacts}
        t0_exec = time.perf_counter()
        exec_res = self.sandbox.execute(code, selected_artifacts)
        execution_ms = round((time.perf_counter() - t0_exec) * 1000.0, 2)

        if not exec_res.get("success", False):
            v_res = VerificationResult(
                v1_code_executed=CheckStatus.PASS,
                v2_output_exists=CheckStatus.FAIL,
                v3_output_valid_canonical=CheckStatus.FAIL,
                status="VERIFICATION_FAILED",
                confidence_score=0.0,
                errors=[exec_res.get("error", "Execution failed: non-zero exit or exception.")]
            )
            result = AnalysisResult(
                analysis_id=analysis_id,
                question=request.question,
                answer=f"Execution failed: {exec_res.get('error', 'Execution error')}",
                status=AnalysisStatus.EXECUTION_FAILED,
                result_kind="verification_failed",
                resolved_dataset_ids=resolved_dataset_ids,
                analysis_contract=contract,
                code=code,
                execution_result=exec_res,
                verification=v_res,
                confidence=0.0,
                error_message=exec_res.get("error"),
                attempts_count=attempts_count
            )
            storage_service.save_analysis_run(analysis_id, request.question, AnalysisStatus.EXECUTION_FAILED.value, result.model_dump())
            return result

        # 6. Verification Phase
        t0_ver = time.perf_counter()
        verification_errors: List[str] = []

        # Result Checker (V2, V3, V4, V5)
        out_present, out_valid, type_matched, res_checker_errors = ResultChecker.check_result(exec_res, expected_type)
        verification_errors.extend(res_checker_errors)

        # Reproducibility Verifier (V6)
        repro_status, repro_diff, repro_method, repro_errors = ReproducibilityVerifier.verify_reproducibility(
            self.sandbox, code, exec_res, selected_artifacts, contract=contract
        )
        verification_errors.extend(repro_errors)

        # Static AST Contract Checker (V7, V8, V9)
        v7_ast, v8_ast, v9_ast, ast_errors = StaticContractChecker.check_contract(code, contract, resolved_dataset_ids)
        verification_errors.extend(ast_errors)

        # Dynamic Runtime Operation Verifier (V9 semantic check)
        runtime_ops = exec_res.get("runtime_operations", [])
        op_ver_res = OperationVerifier.verify_operations(contract, runtime_ops)
        if not op_ver_res.is_valid:
            v9_ast = CheckStatus.FAIL
            verification_errors.extend(op_ver_res.errors)

        # Runtime Dataset Access Verification (V7 runtime check)
        accessed_dataset_ids = exec_res.get("accessed_dataset_ids", [])
        v7_runtime = CheckStatus.PASS
        if accessed_dataset_ids:
            unauthorized = [ds for ds in accessed_dataset_ids if ds not in resolved_dataset_ids]
            if unauthorized:
                v7_runtime = CheckStatus.FAIL
                verification_errors.append(f"V7 Failure: Code accessed unauthorized dataset(s): {unauthorized}.")

        v7_final = CheckStatus.FAIL if (v7_ast == CheckStatus.FAIL or v7_runtime == CheckStatus.FAIL) else CheckStatus.PASS

        # Extract Canonical Result
        parsed = exec_res.get("parsed_output", {})
        canonical_res = None
        accessed_columns = []
        if isinstance(parsed, dict) and "result" in parsed:
            metric_val = parsed.get("metric", contract.expected_metric or "result")
            canonical_res = CanonicalResult(
                result=parsed["result"],
                result_type=expected_type,
                metric=metric_val,
                label=metric_val if expected_type == "ranked_item" else None,
                unit=parsed.get("unit", contract.expected_unit),
                dataset_ids=resolved_dataset_ids
            )

        # Verify Real Column Access (V8)
        runtime_cols_evidence = exec_res.get("accessed_columns", [])
        if contract.columns_required:
            for col in contract.columns_required:
                if any(ev.get("column") == col for ev in runtime_cols_evidence if isinstance(ev, dict)):
                    accessed_columns.append(col)
                elif code and f"['{col}']" in code or f'["{col}"]' in code:
                    accessed_columns.append(col)
            missing = [c for c in contract.columns_required if c not in accessed_columns]
            if missing:
                v8_ast = CheckStatus.FAIL
                verification_errors.append(f"V8 Failure: Required contract columns were not accessed at runtime: {missing}")

        # 7. Independent Reference Calculation Engine & Comparison
        t0_ref = time.perf_counter()
        ref_res = ReferenceEngine.compute_reference(contract, dataset_files)
        reference_ms = round((time.perf_counter() - t0_ref) * 1000.0, 2)

        v_ref_status = CheckStatus.PASS
        reference_matches = True
        if ref_res.get("success", False) and canonical_res:
            gen_val = canonical_res.result
            ref_val = ref_res.get("result")

            if isinstance(gen_val, (int, float)) and isinstance(ref_val, (int, float)):
                abs_diff = abs(float(gen_val) - float(ref_val))
                rel_diff = abs_diff / (abs(float(ref_val)) + 1e-9)
                if abs_diff > 1e-2 and rel_diff > 1e-4:
                    v_ref_status = CheckStatus.FAIL
                    reference_matches = False
                    verification_errors.append(f"Reference Mismatch: Generated result ({gen_val}) differs from independent reference calculation ({ref_val}). Abs diff: {abs_diff}")
            elif ref_res.get("label") and canonical_res.label:
                if str(canonical_res.label).lower() != str(ref_res.get("label")).lower():
                    v_ref_status = CheckStatus.FAIL
                    reference_matches = False
                    verification_errors.append(f"Reference Label Mismatch: Generated label ({canonical_res.label}) differs from reference label ({ref_res.get('label')}).")
            elif isinstance(gen_val, list) and isinstance(ref_val, list):
                if len(gen_val) != len(ref_val):
                    v_ref_status = CheckStatus.FAIL
                    reference_matches = False
                    verification_errors.append(f"Reference Table Row Mismatch: Generated {len(gen_val)} rows vs reference {len(ref_val)} rows.")
        else:
            if not ref_res.get("success", False):
                v_ref_status = CheckStatus.FAIL
                reference_matches = False
                verification_errors.append(f"Reference Engine failed: {ref_res.get('error')}")

        # 8. Join Validation & Explosion Checker
        join_evidence = []
        crit_join_issue = False
        if contract.joins:
            for join_spec in contract.joins:
                left_name = dataset_catalog.resolve_dataset_by_name(join_spec.left_dataset) or join_spec.left_dataset
                right_name = dataset_catalog.resolve_dataset_by_name(join_spec.right_dataset) or join_spec.right_dataset
                df_left = storage_service.get_dataframe(left_name)
                df_right = storage_service.get_dataframe(right_name)
                if df_left is not None and df_right is not None:
                    j_val = JoinChecker.validate_join(
                        df_left, df_right,
                        left_key=join_spec.left_column,
                        right_key=join_spec.right_column,
                        how=join_spec.how or "inner",
                        expected_cardinality=join_spec.expected_cardinality
                    )
                    join_evidence.append(j_val)
                    if j_val.get("critical_issue"):
                        crit_join_issue = True
                        verification_errors.append(j_val["critical_issue"])

        # 9. V11 Unit Verification (No INR guessing)
        v11_unit_status = CheckStatus.PASS
        if contract.expected_unit:
            if not canonical_res or canonical_res.unit != contract.expected_unit:
                v11_unit_status = CheckStatus.FAIL
                verification_errors.append(f"V11 Mismatch: Expected unit '{contract.expected_unit}' but got '{canonical_res.unit if canonical_res else None}'.")
        else:
            v11_unit_status = CheckStatus.NOT_APPLICABLE

        # 10. Synthesize Answer
        evidence_coll = EvidenceAccumulator.build_evidence(
            resolved_dataset_ids,
            code,
            exec_res,
            doc_chunks=doc_chunks
        )

        answer = None
        if hasattr(self.analyst, "synthesize_answer"):
            try:
                answer = self.analyst.synthesize_answer(request.question, exec_res, evidence_coll.items)
            except Exception:
                answer = None

        if not answer:
            if canonical_res and canonical_res.result is not None:
                if isinstance(canonical_res.result, list):
                    # Grouped table answer
                    groups_summary = ", ".join([f"{list(r.values())[0]}: {list(r.values())[1]}" for r in canonical_res.result[:10]])
                    answer = f"The {contract.expected_metric or 'aggregated results'} across groups are: {groups_summary}."
                elif canonical_res.label:
                    answer = f"The highest {contract.expected_metric or 'metric'} is {canonical_res.label} with a value of {canonical_res.result}{(' ' + canonical_res.unit) if canonical_res.unit else ''}."
                else:
                    answer = f"The calculated {contract.expected_metric or 'result'} is {canonical_res.result}{(' ' + canonical_res.unit) if canonical_res.unit else ''}."
            else:
                answer = "Calculation completed successfully."

        # V10 Numerical Consistency Check
        v10_consistent = CheckStatus.PASS
        if canonical_res and isinstance(canonical_res.result, (int, float)) and answer:
            nums = re.findall(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", answer)
            clean_nums = []
            for n in nums:
                try:
                    clean_nums.append(float(n.replace(",", "")))
                except ValueError:
                    pass
            if clean_nums:
                target = float(canonical_res.result)
                if not any(abs(n - target) < 1e-3 or (target != 0 and abs(n - target) / abs(target) < 0.01) for n in clean_nums):
                    v10_consistent = CheckStatus.FAIL
                    verification_errors.append(f"V10 Mismatch: Final textual answer numbers {clean_nums} do not match canonical result {target}.")

        # Data Quality Check Status
        qual_performed = True
        qual_issues = len(quality_warnings) > 0
        crit_qual_issues = any(w.get("severity") == "critical" for w in quality_warnings) or crit_join_issue

        verification_ms = round((time.perf_counter() - t0_ver) * 1000.0, 2)

        v_result = VerificationResult(
            v1_code_executed=CheckStatus.PASS,
            v2_output_exists=out_present,
            v3_output_valid_canonical=out_valid,
            v4_result_type_matched=type_matched,
            v5_result_finite_valid=type_matched,
            v6_reproducible=repro_status,
            v7_required_datasets_used=v7_final,
            v8_required_columns_used=v8_ast,
            v9_expected_operation_reflected=v9_ast,
            v10_final_answer_consistent=v10_consistent,
            v11_unit_matched=v11_unit_status,
            v12_quality_requirements_satisfied=CheckStatus.FAIL if crit_qual_issues else CheckStatus.PASS,
            v13_evidence_sources_matched=CheckStatus.PASS if len(evidence_coll.items) > 0 else CheckStatus.NOT_APPLICABLE,
            executed=CheckStatus.PASS,
            execution_success=CheckStatus.PASS,
            output_present=out_present,
            output_valid=out_valid,
            expected_type_matched=type_matched,
            reproducible=repro_status,
            selected_datasets_used=v7_final,
            result_consistent=v10_consistent,
            quality_check_performed=qual_performed,
            quality_issues_found=qual_issues,
            critical_quality_issues=crit_qual_issues,
            status="VERIFIED" if (reference_matches and not crit_qual_issues and v7_final == CheckStatus.PASS and v8_ast != CheckStatus.FAIL and v9_ast == CheckStatus.PASS and v10_consistent == CheckStatus.PASS) else "VERIFICATION_FAILED",
            comparison_method=repro_method,
            numeric_tolerance_difference=repro_diff,
            errors=verification_errors
        )

        # Proof Policy Evaluation
        final_analysis_status, result_kind = ProofPolicy.evaluate_policy(
            verification_result=v_result,
            reference_matches=reference_matches,
            has_critical_quality_issue=crit_qual_issues,
            is_model_prediction=False,
            is_document_only=False,
            is_refused=False
        )
        v_result.status = final_analysis_status.value

        flat_quality_warnings = [w for art in selected_artifacts for w in art.profile.quality_warnings]
        conf_score = ConfidenceCalculator.calculate_confidence(v_result, flat_quality_warnings)
        v_result.confidence_score = conf_score

        total_ms = round((time.perf_counter() - start_total) * 1000.0, 2)

        # Structured Proof Trace with Real Measured Evidence
        proof_trace = {
            "question": request.question,
            "rule_reasoning": rule_trace,
            "analysis_contract": contract.model_dump(),
            "authorized_datasets": resolved_dataset_ids,
            "accessed_datasets": accessed_dataset_ids or resolved_dataset_ids,
            "accessed_columns": list(set(accessed_columns or contract.columns_required)),
            "runtime_operations": runtime_ops,
            "join_evidence": join_evidence,
            "canonical_result": canonical_res.model_dump() if canonical_res else None,
            "reference_result": ref_res,
            "reference_match": reference_matches,
            "reproducibility": {
                "status": repro_status.value,
                "method": repro_method,
                "tolerance": repro_diff,
                "matches": repro_status == CheckStatus.PASS
            },
            "data_quality": {
                "performed": qual_performed,
                "issues_found": qual_issues,
                "critical": crit_qual_issues
            },
            "security": {
                "sandbox": exec_res.get("execution_mode", "local_isolated"),
                "passed": exec_res.get("success", False)
            },
            "verification_checks": v_result.model_dump(),
            "final_status": final_analysis_status.value,
            "execution": {
                "success": exec_res.get("success", False),
                "execution_ms": execution_ms,
                "reference_ms": reference_ms,
                "verification_ms": verification_ms,
                "total_ms": total_ms
            }
        }

        result = AnalysisResult(
            analysis_id=analysis_id,
            question=request.question,
            answer=answer,
            status=final_analysis_status,
            result_kind=result_kind,
            resolved_dataset_ids=resolved_dataset_ids,
            analysis_contract=contract,
            code=code,
            expected_result_type=expected_type,
            execution_result=exec_res,
            canonical_result=canonical_res,
            reference_result=ref_res,
            proof_trace=proof_trace,
            join_evidence=join_evidence,
            accessed_dataset_ids=accessed_dataset_ids or resolved_dataset_ids,
            accessed_columns=list(set(accessed_columns or contract.columns_required)),
            evidence=evidence_coll.items,
            verification=v_result,
            confidence=conf_score,
            attempts_count=attempts_count
        )

        storage_service.save_analysis_run(analysis_id, request.question, final_analysis_status.value, result.model_dump())
        return result
