"""FastAPI Router for CaseLens AI Document Intelligence Platform."""
import os
import uuid
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import PlainTextResponse

from backend.caselens.models import (
    Workspace,
    WorkspaceCreate,
    DocumentMetadata,
    DocumentChunk,
    QuestionRequest,
    QuestionAnswerResponse,
    CaseAnalysisResponse,
    ContradictionResponse,
    DocumentComparisonResponse,
    MissingInfoAnalysisResponse,
    ReportExportResponse,
)
from backend.caselens.storage import caselens_storage
from backend.caselens.processor import DocumentProcessor, compute_sha256, sanitize_filename
from backend.caselens.retriever import caselens_retriever
from backend.caselens.qa_engine import caselens_qa_engine
from backend.caselens.case_analyzer import caselens_case_analyzer
from backend.caselens.contradiction_engine import caselens_contradiction_detector
from backend.caselens.comparison_engine import caselens_comparator
from backend.caselens.missing_info_engine import caselens_missing_analyzer
from backend.caselens.report_generator import caselens_report_generator
from backend.caselens.seed_data import load_seed_workspace, DEMO_WORKSPACE_ID

router = APIRouter(prefix="/caselens", tags=["CaseLens AI"])

# ==================== Health ====================
@router.get("/health")
def caselens_health():
    return {
        "status": "online",
        "service": "CaseLens AI Document Intelligence",
        "version": "1.0.0",
        "mode": "evidence_grounded_deterministic",
        "tagline": "Every claim has evidence. Every answer has a source."
    }

# ==================== Workspaces ====================
@router.get("/workspaces", response_model=List[Workspace])
def list_workspaces():
    ws_list = caselens_storage.list_workspaces()
    if not ws_list:
        # Auto-seed sample workspace if none exist
        load_seed_workspace()
        ws_list = caselens_storage.list_workspaces()
    return ws_list

@router.post("/workspaces", response_model=Workspace)
def create_workspace(payload: WorkspaceCreate):
    ws_id = f"ws-{uuid.uuid4().hex[:8]}"
    return caselens_storage.create_workspace(
        workspace_id=ws_id,
        name=payload.name,
        description=payload.description,
        is_demo=False
    )

@router.get("/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(workspace_id: str):
    ws = caselens_storage.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws

@router.delete("/workspaces/{workspace_id}")
def delete_workspace(workspace_id: str):
    success = caselens_storage.delete_workspace(workspace_id)
    return {"success": success, "message": f"Workspace {workspace_id} deleted."}

@router.post("/workspaces/demo/load", response_model=Workspace)
def load_demo_workspace():
    return load_seed_workspace()

@router.post("/workspaces/demo/reset")
def reset_demo_workspace():
    caselens_storage.delete_workspace(DEMO_WORKSPACE_ID)
    ws = load_seed_workspace()
    return {"success": True, "workspace": ws}

# ==================== Documents ====================
@router.get("/workspaces/{workspace_id}/documents", response_model=List[DocumentMetadata])
def list_documents(workspace_id: str):
    return caselens_storage.list_documents(workspace_id)

@router.post("/workspaces/{workspace_id}/documents/upload", response_model=DocumentMetadata)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...)
):
    ws = caselens_storage.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace does not exist.")

    raw_bytes = await file.read()
    filename = sanitize_filename(file.filename or "uploaded_document")
    valid, err_msg = DocumentProcessor.validate_file(filename, raw_bytes)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    doc_id = f"doc_{uuid.uuid4().hex[:10]}"
    ext = Path(filename).suffix.lower().replace(".", "")

    # Save to disk safely
    target_path = caselens_storage.documents_dir / f"{doc_id}_{filename}"
    with open(target_path, "wb") as f:
        f.write(raw_bytes)

    # Process & extract
    try:
        pages, meta = DocumentProcessor.extract_pages(target_path)
        chunks = DocumentProcessor.create_chunks(doc_id, filename, pages)
        status = "processed"
        error_msg = None
    except Exception as e:
        pages = []
        chunks = []
        status = "failed"
        error_msg = str(e)

    sha256 = compute_sha256(target_path)
    now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    doc_meta = DocumentMetadata(
        document_id=doc_id,
        workspace_id=workspace_id,
        filename=filename,
        file_type=ext,
        file_size_bytes=len(raw_bytes),
        content_hash=sha256,
        page_count=len(pages),
        chunk_count=len(chunks),
        created_at=now_ts,
        processing_status=status,
        error_message=error_msg,
        is_demo=False
    )

    caselens_storage.save_document(doc_meta, str(target_path), chunks)
    return doc_meta

@router.get("/documents/{document_id}", response_model=DocumentMetadata)
def get_document_details(document_id: str):
    doc = caselens_storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunk])
def get_document_chunks(document_id: str):
    chunks = caselens_storage.get_document_chunks(document_id)
    return chunks

@router.get("/documents/{document_id}/text")
def get_document_full_text(document_id: str):
    chunks = caselens_storage.get_document_chunks(document_id)
    if not chunks:
        raise HTTPException(status_code=404, detail="Document chunks not found.")
    full_text = "\n\n".join([f"--- Page {c.page_number} ---\n{c.text}" for c in chunks])
    return {"document_id": document_id, "text": full_text}

@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    success = caselens_storage.delete_document(document_id)
    return {"success": success, "message": f"Document {document_id} deleted."}

# ==================== Search & Q&A ====================
@router.get("/workspaces/{workspace_id}/search")
def search_documents(
    workspace_id: str,
    q: str = Query(..., min_length=2),
    top_k: int = 5
):
    chunks = caselens_storage.get_workspace_chunks(workspace_id)
    scored = caselens_retriever.retrieve(q, chunks, top_k=top_k, min_score=0.1)
    citations = caselens_retriever.build_citations(scored)
    return {
        "query": q,
        "total_results": len(citations),
        "results": [
            {
                "score": round(score, 3),
                "citation": cit.model_dump(),
                "snippet": snippet
            }
            for (chunk, score, snippet), cit in zip(scored, citations)
        ]
    }

@router.post("/qa/ask", response_model=QuestionAnswerResponse)
def ask_question(req: QuestionRequest):
    return caselens_qa_engine.answer_question(req)

@router.get("/workspaces/{workspace_id}/qa/history", response_model=List[QuestionAnswerResponse])
def get_qa_history(workspace_id: str):
    return caselens_storage.list_qa_runs(workspace_id)

# ==================== Case Analysis ====================
@router.post("/workspaces/{workspace_id}/analyze", response_model=CaseAnalysisResponse)
def analyze_case(workspace_id: str):
    return caselens_case_analyzer.analyze_workspace(workspace_id)

@router.get("/workspaces/{workspace_id}/analysis", response_model=CaseAnalysisResponse)
def get_case_analysis(workspace_id: str):
    analysis = caselens_storage.get_latest_case_analysis(workspace_id)
    if not analysis:
        analysis = caselens_case_analyzer.analyze_workspace(workspace_id)
    return analysis

# ==================== Contradiction Detection ====================
@router.post("/workspaces/{workspace_id}/contradictions", response_model=ContradictionResponse)
def scan_contradictions(workspace_id: str):
    return caselens_contradiction_detector.analyze_workspace(workspace_id)

@router.get("/workspaces/{workspace_id}/contradictions", response_model=ContradictionResponse)
def get_contradictions(workspace_id: str):
    res = caselens_storage.get_latest_contradictions(workspace_id)
    if not res:
        res = caselens_contradiction_detector.analyze_workspace(workspace_id)
    return res

# ==================== Missing Information ====================
@router.get("/workspaces/{workspace_id}/missing-info", response_model=MissingInfoAnalysisResponse)
def analyze_missing_information(
    workspace_id: str,
    template: str = Query("service_agreement", description="Template type: service_agreement, employment_agreement, commercial_lease, general_contract")
):
    return caselens_missing_analyzer.analyze(workspace_id, template_type=template)

# ==================== Document Comparison ====================
@router.get("/compare", response_model=DocumentComparisonResponse)
def compare_documents(
    doc_a: str = Query(..., description="Document ID A"),
    doc_b: str = Query(..., description="Document ID B")
):
    return caselens_comparator.compare_documents(doc_a, doc_b)

# ==================== Reports ====================
@router.post("/workspaces/{workspace_id}/reports", response_model=ReportExportResponse)
def create_report(
    workspace_id: str,
    title: Optional[str] = Form(None)
):
    return caselens_report_generator.generate_report(workspace_id, title)

@router.get("/workspaces/{workspace_id}/reports", response_model=List[ReportExportResponse])
def list_reports(workspace_id: str):
    return caselens_storage.list_reports(workspace_id)

@router.get("/reports/{report_id}", response_model=ReportExportResponse)
def get_report(report_id: str):
    rpt = caselens_storage.get_report(report_id)
    if not rpt:
        raise HTTPException(status_code=404, detail="Report not found.")
    return rpt

@router.get("/reports/{report_id}/download")
def download_report_markdown(report_id: str):
    rpt = caselens_storage.get_report(report_id)
    if not rpt:
        raise HTTPException(status_code=404, detail="Report not found.")
    return PlainTextResponse(
        content=rpt.markdown_content,
        headers={"Content-Disposition": f'attachment; filename="CaseLens_Report_{report_id}.md"'}
    )
