from backend.agents.analyst import DataAnalystAgent
from backend.agents.document_agent import DocumentAgent
from backend.codegen.generator import CodeGeneratorService
from backend.execution.sandbox import LocalIsolatedSandbox, DockerSandbox
from backend.rag.vector_store import global_vector_store
from backend.rag.embeddings import EmbeddingService
from backend.rag.retriever import DocumentRetriever
from backend.agents.orchestrator import AnalysisOrchestrator
from backend.config import settings

def get_orchestrator() -> AnalysisOrchestrator:
    analyst = DataAnalystAgent()
    code_service = CodeGeneratorService()

    if settings.SANDBOX_ENABLED:
        sandbox = DockerSandbox()
    else:
        sandbox = LocalIsolatedSandbox()

    emb_service = EmbeddingService(None)
    retriever = DocumentRetriever(global_vector_store, emb_service)
    doc_agent = DocumentAgent(retriever)

    return AnalysisOrchestrator(
        analyst=analyst,
        document_agent=doc_agent,
        code_generator=code_service,
        sandbox=sandbox
    )
