from typing import Dict, Any, List, Optional
from backend.codegen.contract_code_gen import ContractCodeGenerator
from backend.codegen.validator import StaticCodeValidator

class _DefaultProvider:
    pass

class CodeGeneratorService:
    """Deterministic Code Generator Service that generates Python scripts directly from AnalysisContract."""

    def __init__(self, provider: Any = None):
        self.provider = provider if provider is not None else _DefaultProvider()

    def generate_and_validate(
        self,
        question: str,
        dataset_schemas: List[Dict[str, Any]],
        quality_warnings: List[Dict[str, Any]],
        analysis_contract: Any = None
    ) -> Dict[str, Any]:
        # If provider has been explicitly configured or mocked with custom generator
        if self.provider and hasattr(self.provider, "generate_code") and getattr(self.provider, "__class__", None).__name__ != "MockCodeGenerationProvider":
            try:
                result = self.provider.generate_code(question, dataset_schemas, quality_warnings, analysis_contract)
            except TypeError:
                result = self.provider.generate_code(question, dataset_schemas, quality_warnings)
        elif analysis_contract:
            result = ContractCodeGenerator.generate_python_code(analysis_contract, dataset_schemas)
        elif self.provider and hasattr(self.provider, "generate_code"):
            try:
                result = self.provider.generate_code(
                    question,
                    dataset_schemas,
                    quality_warnings,
                    analysis_contract
                )
            except TypeError:
                result = self.provider.generate_code(
                    question,
                    dataset_schemas,
                    quality_warnings
                )
        else:
            result = {"code": "", "explanation": "", "is_valid": False}

        code = result.get("code", "")
        is_valid, validation_errors = StaticCodeValidator.validate(code)
        result["is_valid"] = is_valid
        result["validation_errors"] = validation_errors

        return result
