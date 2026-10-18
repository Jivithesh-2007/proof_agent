"""Missing Information Analysis Engine for CaseLens AI."""
import re
from typing import List, Dict, Any
from backend.caselens.models import (
    MissingInfoAnalysisResponse,
    MissingFieldCheck,
    DocumentChunk,
)
from backend.caselens.storage import caselens_storage

TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "service_agreement": [
        {"field": "Parties & Recitals", "category": "Identification", "importance": "critical", "keywords": ["agreement between", "party of the first part", "hereinafter referred to as", "client", "vendor"]},
        {"field": "Scope of Services", "category": "Obligations", "importance": "critical", "keywords": ["scope of work", "services to be provided", "deliverables", "statement of work"]},
        {"field": "Compensation & Payment Terms", "category": "Financial", "importance": "critical", "keywords": ["compensation", "fee", "payment terms", "invoicing", "net 30", "hourly rate"]},
        {"field": "Term and Termination Notice", "category": "Term", "importance": "critical", "keywords": ["term of agreement", "termination", "written notice", "expiration", "without cause"]},
        {"field": "Confidentiality & Non-Disclosure", "category": "Protection", "importance": "standard", "keywords": ["confidential information", "non-disclosure", "proprietary information"]},
        {"field": "Indemnification & Hold Harmless", "category": "Liability", "importance": "critical", "keywords": ["indemnify", "hold harmless", "defend and indemnify", "indemnification"]},
        {"field": "Limitation of Liability & Cap", "category": "Liability", "importance": "standard", "keywords": ["limitation of liability", "consequential damages", "aggregate liability", "cap"]},
        {"field": "Intellectual Property Ownership", "category": "IP", "importance": "critical", "keywords": ["work made for hire", "intellectual property", "ownership of deliverables", "all rights, title"]},
        {"field": "Governing Law & Dispute Resolution", "category": "Jurisdiction", "importance": "standard", "keywords": ["governing law", "jurisdiction", "arbitration", "courts of"]},
        {"field": "Force Majeure Event Clause", "category": "Risk", "importance": "optional", "keywords": ["force majeure", "acts of god", "unforeseeable circumstances"]},
        {"field": "Data Privacy & Security Protocols", "category": "Compliance", "importance": "standard", "keywords": ["data privacy", "gdpr", "personally identifiable information", "security measures"]},
    ],
    "employment_agreement": [
        {"field": "Job Title & Reporting Hierarchy", "category": "Role", "importance": "critical", "keywords": ["job title", "duties", "reporting to", "position"]},
        {"field": "Base Salary & Bonus Structure", "category": "Compensation", "importance": "critical", "keywords": ["base salary", "annual salary", "bonus", "equity", "stock options"]},
        {"field": "At-Will Employment Clause", "category": "Status", "importance": "critical", "keywords": ["at-will", "terminate at any time", "with or without cause"]},
        {"field": "Restrictive Covenants & Non-Compete", "category": "Protection", "importance": "standard", "keywords": ["non-compete", "non-solicitation", "restrictive covenants"]},
        {"field": "Proprietary Information Assignment", "category": "IP", "importance": "critical", "keywords": ["invention assignment", "proprietary information", "intellectual property"]},
        {"field": "Severance & Separation Package", "category": "Termination", "importance": "optional", "keywords": ["severance", "separation pay", "release of claims"]},
        {"field": "Governing Law & Forum", "category": "Jurisdiction", "importance": "standard", "keywords": ["governing law", "jurisdiction", "arbitration"]},
    ],
    "commercial_lease": [
        {"field": "Demised Premises Description", "category": "Premises", "importance": "critical", "keywords": ["demised premises", "suite", "square feet", "property description"]},
        {"field": "Lease Term & Commencement Date", "category": "Term", "importance": "critical", "keywords": ["commencement date", "expiration date", "initial term", "lease term"]},
        {"field": "Base Rent & Escalation Schedule", "category": "Financial", "importance": "critical", "keywords": ["base rent", "monthly rent", "annual escalation", "cpi adjustment"]},
        {"field": "Security Deposit & Letter of Credit", "category": "Financial", "importance": "standard", "keywords": ["security deposit", "letter of credit", "deposit amount"]},
        {"field": "Permitted Use of Premises", "category": "Operational", "importance": "standard", "keywords": ["permitted use", "exclusive use", "general office"]},
        {"field": "Maintenance & Repair Obligations", "category": "Maintenance", "importance": "critical", "keywords": ["maintenance", "repairs", "hvac", "common area maintenance", "cam"]},
        {"field": "Subletting and Assignment Rights", "category": "Transfer", "importance": "standard", "keywords": ["sublet", "assignment", "landlord consent"]},
        {"field": "Insurance Requirements & Indemnity", "category": "Insurance", "importance": "critical", "keywords": ["commercial general liability", "certificate of insurance", "indemnification"]},
        {"field": "Casualty & Condemnation Clauses", "category": "Risk", "importance": "standard", "keywords": ["casualty", "condemnation", "damage and destruction", "eminent domain"]},
    ],
    "general_contract": [
        {"field": "Identified Parties", "category": "Identification", "importance": "critical", "keywords": ["between", "parties", "client", "contractor"]},
        {"field": "Core Subject Matter & Deliverables", "category": "Obligations", "importance": "critical", "keywords": ["services", "goods", "deliverables", "specifications"]},
        {"field": "Consideration & Price", "category": "Financial", "importance": "critical", "keywords": ["price", "fee", "consideration", "payment"]},
        {"field": "Duration & Term", "category": "Term", "importance": "critical", "keywords": ["term", "duration", "expiration", "effective date"]},
        {"field": "Remedies & Breach Stipulations", "category": "Legal", "importance": "standard", "keywords": ["breach", "default", "remedies", "cure period"]},
        {"field": "Governing Law", "category": "Jurisdiction", "importance": "standard", "keywords": ["governing law", "jurisdiction", "venue"]},
        {"field": "Signatures & Execution Block", "category": "Execution", "importance": "critical", "keywords": ["in witness whereof", "authorized representative", "signed", "signatures"]},
    ]
}

class MissingInfoAnalyzer:
    """Evaluates documents against contract checklists and reports completeness."""

    def analyze(self, workspace_id: str, template_type: str = "service_agreement") -> MissingInfoAnalysisResponse:
        chunks = caselens_storage.get_workspace_chunks(workspace_id)
        full_text = "\n\n".join(c.text.lower() for c in chunks)

        template_items = TEMPLATES.get(template_type, TEMPLATES["service_agreement"])
        checks: List[MissingFieldCheck] = []

        present_cnt = 0
        missing_cnt = 0
        ambiguous_cnt = 0

        for item in template_items:
            found_snippet = None
            kw_hits = 0
            for kw in item["keywords"]:
                pos = full_text.find(kw)
                if pos != -1:
                    kw_hits += 1
                    if not found_snippet:
                        # Extract excerpt
                        start = max(0, pos - 20)
                        end = min(len(full_text), pos + 120)
                        found_snippet = full_text[start:end].strip()

            if kw_hits >= 2:
                status = "present"
                present_cnt += 1
                note = f"Identified standard phrasing matching {kw_hits} keywords in document corpus."
            elif kw_hits == 1:
                status = "ambiguous"
                ambiguous_cnt += 1
                note = "Partial mention found, but standard comprehensive clauses appear incomplete or abbreviated."
            else:
                status = "missing"
                missing_cnt += 1
                note = f"Expected {item['importance']} clause was not located in evaluated documents."

            checks.append(MissingFieldCheck(
                field_name=item["field"],
                category=item["category"],
                expected_importance=item["importance"],
                status=status,
                found_evidence=found_snippet,
                review_note=note
            ))

        return MissingInfoAnalysisResponse(
            workspace_id=workspace_id,
            template_type=template_type,
            present_count=present_cnt,
            missing_count=missing_cnt,
            ambiguous_count=ambiguous_cnt,
            checks=checks,
            disclaimer="Missing information reflects a template comparison observation and does not constitute formal legal invalidity."
        )

caselens_missing_analyzer = MissingInfoAnalyzer()
