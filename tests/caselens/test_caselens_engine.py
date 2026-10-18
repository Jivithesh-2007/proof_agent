"""Comprehensive test suite for CaseLens AI Document Intelligence Platform."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.caselens.models import QuestionRequest
from backend.caselens.storage import caselens_storage
from backend.caselens.processor import DocumentProcessor
from backend.caselens.qa_engine import caselens_qa_engine, INSUFFICIENT_EVIDENCE_REPLY
from backend.caselens.contradiction_engine import caselens_contradiction_detector
from backend.caselens.comparison_engine import caselens_comparator
from backend.caselens.missing_info_engine import caselens_missing_analyzer
from backend.caselens.report_generator import caselens_report_generator
from backend.caselens.seed_data import load_seed_workspace, DEMO_WORKSPACE_ID

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def demo_workspace():
    return load_seed_workspace()

# 1. Test Seed Data & Workspaces
def test_load_seed_workspace(demo_workspace):
    assert demo_workspace.id == DEMO_WORKSPACE_ID
    assert demo_workspace.is_demo is True
    assert demo_workspace.document_count >= 3

    docs = caselens_storage.list_documents(DEMO_WORKSPACE_ID)
    assert len(docs) >= 3
    filenames = [d.filename for d in docs]
    assert "01_Master_Services_Agreement_Acme_Apex.txt" in filenames
    assert "02_SLA_Amendment_Addendum_Apex.txt" in filenames

# 2. Test File Validation and Malformed Inputs
def test_processor_validation():
    # Valid TXT
    valid, _ = DocumentProcessor.validate_file("contract.txt", b"Valid legal terms")
    assert valid is True

    # Invalid extension
    valid, err = DocumentProcessor.validate_file("script.exe", b"binary content")
    assert valid is False
    assert "Unsupported file type" in err

    # Malformed PDF (lacks %PDF header)
    valid, err = DocumentProcessor.validate_file("fake.pdf", b"This is not a pdf file")
    assert valid is False
    assert "missing %PDF header" in err

# 3. Test Evidence-Grounded Q&A (Scenario 1: Supported Answer with real citations)
def test_qa_supported_answer(demo_workspace):
    req = QuestionRequest(
        workspace_id=DEMO_WORKSPACE_ID,
        question="What is the base retainer fee?",
        strict_evidence_only=True
    )
    resp = caselens_qa_engine.answer_question(req)

    assert resp.has_sufficient_evidence is True
    assert len(resp.citations) > 0
    assert "$150,000" in resp.answer or "$225,000" in resp.answer
    assert resp.verification.is_valid is True
    assert resp.verification.passage_match_verified is True
    assert resp.verification.claim_supported is True
    assert resp.verification.verification_status == "supported by source"

# 4. Test Evidence-Grounded Q&A (Scenario 2: Insufficient Evidence honest refusal)
def test_qa_insufficient_evidence(demo_workspace):
    req = QuestionRequest(
        workspace_id=DEMO_WORKSPACE_ID,
        question="What is the nuclear non-proliferation penalty clause?",
        strict_evidence_only=True
    )
    resp = caselens_qa_engine.answer_question(req)

    assert resp.has_sufficient_evidence is False
    assert resp.answer == INSUFFICIENT_EVIDENCE_REPLY
    assert len(resp.citations) == 0
    assert resp.verification.claim_supported is False
    assert resp.verification.verification_status == "unsupported"

# 5. Test Contradiction Detection (Scenario 3: Date conflict June 30, 2027 vs July 31, 2027)
def test_contradiction_detection(demo_workspace):
    resp = caselens_contradiction_detector.analyze_workspace(DEMO_WORKSPACE_ID)

    assert resp.total_contradictions > 0
    categories = [f.category for f in resp.findings]
    assert "Date Mismatch" in categories

    date_finding = next(f for f in resp.findings if f.category == "Date Mismatch")
    assert "2027" in date_finding.doc_a_passage
    assert "2027" in date_finding.doc_b_passage
    assert date_finding.doc_a_name != date_finding.doc_b_name
    assert date_finding.status == "Potential Contradiction"

# 6. Test Document Comparison (Scenario 4: Changed monetary amount and dates)
def test_document_comparison(demo_workspace):
    docs = caselens_storage.list_documents(DEMO_WORKSPACE_ID)
    doc_1 = next(d for d in docs if "01_Master" in d.filename)
    doc_2 = next(d for d in docs if "02_SLA" in d.filename)

    comp = caselens_comparator.compare_documents(doc_1.document_id, doc_2.document_id)

    assert comp.doc_a_id == doc_1.document_id
    assert comp.doc_b_id == doc_2.document_id
    assert comp.modified_clauses > 0
    # Difference should flag monetary amendment or date modification
    assert any("Monetary amendment" in d or "Date modification" in d or "modified" in d for d in comp.key_differences)

# 7. Test Missing Information Analysis (Scenario 5: Commercial Lease Missing Expected Clauses)
def test_missing_information_analysis(demo_workspace):
    resp = caselens_missing_analyzer.analyze(DEMO_WORKSPACE_ID, template_type="commercial_lease")

    assert resp.present_count > 0
    assert resp.missing_count > 0
    assert resp.disclaimer != ""
    # Omitted clauses should be marked missing
    missing_fields = [c.field_name for c in resp.checks if c.status == "missing"]
    assert len(missing_fields) > 0

# 8. Test Comprehensive Report Generation (Scenario 6)
def test_report_generation(demo_workspace):
    rpt = caselens_report_generator.generate_report(DEMO_WORKSPACE_ID, "Test Audit Report")

    assert rpt.report_id.startswith("RPT-")
    assert len(rpt.documents_analyzed) >= 3
    assert "# Test Audit Report" in rpt.markdown_content
    assert "Executive Summary" in rpt.markdown_content
    assert "Evidence Register" in rpt.markdown_content

# 9. Test API Endpoints
def test_caselens_api_routes(client, demo_workspace):
    # Health check
    res = client.get("/api/caselens/health")
    assert res.status_code == 200
    assert res.json()["service"] == "CaseLens AI Document Intelligence"

    # List workspaces
    res = client.get("/api/caselens/workspaces")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Documents listing
    res = client.get(f"/api/caselens/workspaces/{DEMO_WORKSPACE_ID}/documents")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 3

    # Document text preview
    doc_id = docs[0]["document_id"]
    res = client.get(f"/api/caselens/documents/{doc_id}/text")
    assert res.status_code == 200
    assert "text" in res.json()

    # Search endpoint
    res = client.get(f"/api/caselens/workspaces/{DEMO_WORKSPACE_ID}/search?q=retainer")
    assert res.status_code == 200
    assert res.json()["total_results"] > 0

    # Q&A endpoint
    res = client.post("/api/caselens/qa/ask", json={
        "workspace_id": DEMO_WORKSPACE_ID,
        "question": "What is the notice period for termination?",
        "strict_evidence_only": True
    })
    assert res.status_code == 200
    qa = res.json()
    assert "notice" in qa["answer"].lower()
    assert qa["verification"]["is_valid"] is True

    # Case Analysis endpoint
    res = client.get(f"/api/caselens/workspaces/{DEMO_WORKSPACE_ID}/analysis")
    assert res.status_code == 200
    assert "parties_and_entities" in res.json()

    # Contradictions endpoint
    res = client.get(f"/api/caselens/workspaces/{DEMO_WORKSPACE_ID}/contradictions")
    assert res.status_code == 200
    assert res.json()["total_contradictions"] > 0

    # Missing info endpoint
    res = client.get(f"/api/caselens/workspaces/{DEMO_WORKSPACE_ID}/missing-info?template=service_agreement")
    assert res.status_code == 200
    assert "checks" in res.json()

    # Reports endpoint
    res = client.get(f"/api/caselens/workspaces/{DEMO_WORKSPACE_ID}/reports")
    assert res.status_code == 200
    assert len(res.json()) > 0
