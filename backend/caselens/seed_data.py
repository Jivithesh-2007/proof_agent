"""Seed data and curated demonstration scenarios for CaseLens AI."""
import hashlib
from pathlib import Path
from backend.caselens.models import (
    Workspace,
    DocumentMetadata,
    QuestionRequest,
)
from backend.caselens.storage import caselens_storage
from backend.caselens.processor import DocumentProcessor
from backend.caselens.qa_engine import caselens_qa_engine
from backend.caselens.case_analyzer import caselens_case_analyzer
from backend.caselens.contradiction_engine import caselens_contradiction_detector
from backend.caselens.report_generator import caselens_report_generator

DEMO_WORKSPACE_ID = "demo-caselens-meridian"
DEMO_WORKSPACE_NAME = "Project Meridian: Commercial & SLA Review"
DEMO_WORKSPACE_DESC = "Fictional corporate case benchmarking multi-document contradiction detection, obligation extraction, and evidence-grounded Q&A."

DOC_1_TEXT = """MASTER SERVICES AGREEMENT
BETWEEN: Acme Corporation ("Client") and Apex Logistics Inc. ("Vendor")
EFFECTIVE DATE: January 15, 2024

SECTION 1: RECITALS & SCOPE OF SERVICES
1.1 Engagement: Vendor agrees to provide enterprise supply chain management and automated logistics dispatch services as detailed in Exhibit A.
1.2 Standard of Performance: Vendor shall perform all services with highest commercial diligence and maintain minimum SLA availability of 99.9% across all server endpoints.

SECTION 2: TERM AND EXPIRATION
2.1 Term: This Agreement shall commence on the Effective Date and shall expire on 30 June 2027 unless terminated earlier in accordance with Section 8.
2.2 Renewal: Upon mutual written consent, the parties may renew this Agreement for successive one (1) year intervals.

SECTION 3: COMPENSATION AND PAYMENT SCHEDULE
3.1 Base Retainer Fee: Acme Corp shall pay Apex Logistics an annual base retainer fee of $150,000 USD payable quarterly in advance.
3.2 Invoicing: Invoices shall be transmitted electronically and are payable within net thirty (30) days of receipt.

SECTION 4: CONFIDENTIALITY & NON-DISCLOSURE
4.1 Proprietary Information: Each party agrees to safeguard all confidential disclosures and proprietary technical data for a period of five (5) years following termination.

SECTION 5: INDEMNIFICATION & LIABILITY
5.1 Indemnification: Vendor agrees to defend and indemnify Client against third-party claims arising from gross negligence or willful misconduct.
5.2 Limitation of Liability: Total aggregate liability under this agreement shall not exceed total fees paid in the preceding twelve (12) months.

SECTION 6: TERMINATION FOR CONVENIENCE
6.1 Notice Period: Either party may terminate this Agreement without cause upon sixty (60) days prior written notice to the other party.
6.2 Material Breach: In the event of material default, the non-breaching party may terminate immediately if cure is not effected within fifteen (15) days.

SECTION 7: GOVERNING LAW & JURISDICTION
7.1 Jurisdiction: This Agreement shall be governed by the laws of the State of Delaware, without giving effect to conflict of laws principles.
"""

DOC_2_TEXT = """FIRST AMENDMENT AND SLA ADDENDUM
TO MASTER SERVICES AGREEMENT
BETWEEN: Acme Corporation ("Client") and Apex Logistics Inc. ("Vendor")
EFFECTIVE DATE: March 10, 2025

RECITALS:
WHEREAS, the parties entered into a Master Services Agreement dated January 15, 2024;
WHEREAS, the parties desire to expand high-throughput fulfillment hubs and update fee structures;

NOW, THEREFORE, the parties agree as follows:

ARTICLE 1: AMENDMENT TO TERM
1.1 Revised Expiration Date: Section 2.1 of the Master Agreement is hereby amended. The agreement expires on 31 July 2027 to align with international fiscal calendar requirements.

ARTICLE 2: REVISED COMPENSATION SCHEDULE
2.1 Adjusted Annual Fee: Due to expanded multi-region hosting and automated inventory nodes, the annual base retainer fee is adjusted to $225,000 USD payable quarterly.
2.2 Penalty Offsets: Apex Logistics agrees to credit 5% of monthly fees for each 0.1% SLA degradation below 99.9%.

ARTICLE 3: REVISED TERMINATION NOTICE
3.1 Expedited Notice Period: Section 6.1 of the Master Agreement is revised such that termination without cause requires thirty (30) days prior written notice rather than sixty days.

ARTICLE 4: GOVERNING JURISDICTION
4.1 Applicable Law: This Addendum and disputes arising hereunder shall be governed by the laws of the State of New York.
"""

DOC_3_TEXT = """COMMERCIAL WAREHOUSE LEASE AGREEMENT
DEMISED PREMISES: Facility 4B, Harbor Industrial Park, 400 Harbor Blvd
LANDLORD: Harbor Industrial Properties LLC
TENANT: Apex Logistics Inc.
COMMENCEMENT DATE: September 1, 2023

ARTICLE 1: PREMISES & PERMITTED USE
1.1 Premises: Landlord leases to Tenant warehouse suite comprising approximately 25,000 square feet.
1.2 Permitted Use: Tenant shall use the Premises strictly for dry-goods distribution, logistics sorting, and associated administrative offices.

ARTICLE 2: RENT AND SECURITY DEPOSIT
2.1 Monthly Base Rent: Tenant shall pay Landlord base rent of $18,500 per month on the first day of each calendar month.
2.2 Security Deposit: Tenant has deposited $37,000 as a security deposit for performance of all lease obligations.

ARTICLE 3: MAINTENANCE AND REPAIRS
3.1 Tenant Maintenance: Tenant shall maintain the interior warehouse spaces, loading docks, and HVAC filters in clean condition.
3.2 Landlord Structural Obligations: Landlord shall keep the roof, foundation, and exterior structural walls in good order.

ARTICLE 4: ALTERATIONS
4.1 Prior Consent: Tenant shall not make structural alterations without Landlord's prior written approval.
"""

def load_seed_workspace() -> Workspace:
    """
    Initializes or resets the curated sample workspace with all 6 demonstration scenarios.
    """
    # 1. Create Workspace
    ws = caselens_storage.create_workspace(
        workspace_id=DEMO_WORKSPACE_ID,
        name=DEMO_WORKSPACE_NAME,
        description=DEMO_WORKSPACE_DESC,
        is_demo=True,
    )

    # 2. Ingest Sample Documents
    sample_docs = [
        ("01_Master_Services_Agreement_Acme_Apex.txt", DOC_1_TEXT, "txt"),
        ("02_SLA_Amendment_Addendum_Apex.txt", DOC_2_TEXT, "txt"),
        ("03_Apex_Commercial_Warehouse_Lease.txt", DOC_3_TEXT, "txt"),
    ]

    for filename, text, ext in sample_docs:
        doc_id = f"demo_{Path(filename).stem}"
        file_path = caselens_storage.documents_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        pages, _ = DocumentProcessor.extract_pages(file_path)
        chunks = DocumentProcessor.create_chunks(doc_id, filename, pages, chunk_size=500, overlap=80)

        meta = DocumentMetadata(
            document_id=doc_id,
            workspace_id=DEMO_WORKSPACE_ID,
            filename=filename,
            file_type=ext,
            file_size_bytes=len(text.encode("utf-8")),
            content_hash=sha256,
            page_count=len(pages),
            chunk_count=len(chunks),
            created_at=ws.created_at,
            processing_status="processed",
            is_demo=True,
        )
        caselens_storage.save_document(meta, str(file_path), chunks)

    # 3. Seed Q&A Scenarios (Scenario 1 & 2)
    # Scenario 1: Supported answer
    caselens_qa_engine.answer_question(QuestionRequest(
        workspace_id=DEMO_WORKSPACE_ID,
        question="What is the base retainer fee and SLA availability obligation?",
        strict_evidence_only=True
    ))

    # Scenario 2: Unsupported answer (Zero evidence hallucination refusal)
    caselens_qa_engine.answer_question(QuestionRequest(
        workspace_id=DEMO_WORKSPACE_ID,
        question="What are the specific penalties and tariffs for quantum computing export violations?",
        strict_evidence_only=True
    ))

    # 4. Seed Structured Case Analysis
    caselens_case_analyzer.analyze_workspace(DEMO_WORKSPACE_ID)

    # 5. Seed Contradiction Analysis (Scenario 3: Date conflict June 30, 2027 vs July 31, 2027)
    caselens_contradiction_detector.analyze_workspace(DEMO_WORKSPACE_ID)

    # 6. Seed Comprehensive Report (Scenario 6)
    caselens_report_generator.generate_report(DEMO_WORKSPACE_ID, "Project Meridian — Legal Intelligence Audit Report")

    return caselens_storage.get_workspace(DEMO_WORKSPACE_ID) # type: ignore
