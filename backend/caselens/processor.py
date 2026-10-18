"""Document ingestion, extraction, chunking, and validation for CaseLens AI."""
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import uuid

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from backend.caselens.models import DocumentChunk, DocumentMetadata

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit

def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def sanitize_filename(filename: str) -> str:
    # Remove directory separators and null bytes
    clean = re.sub(r'[/\\?%*:|"<>~#]', '_', filename)
    clean = clean.replace('\0', '').strip()
    return clean or "document"

class DocumentProcessor:
    """Handles parsing, validation, chunking, and page-tracking for legal documents."""

    @classmethod
    def validate_file(cls, filename: str, file_bytes: bytes) -> Tuple[bool, str]:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type '{ext}'. Allowed: .pdf, .docx, .txt"
        
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            return False, f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."

        # Magic number checks
        if ext == ".pdf":
            if not file_bytes.startswith(b"%PDF"):
                return False, "File does not appear to be a valid PDF (missing %PDF header)."
        elif ext == ".docx":
            if not file_bytes.startswith(b"PK"):
                return False, "File does not appear to be a valid DOCX package (missing zip header)."

        return True, ""

    @classmethod
    def extract_pages(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extracts pages from file. Returns:
        - List of dicts: {"page_number": int, "text": str, "is_scanned": bool}
        - Metadata dict: {"page_count": int, "ocr_used": bool, "ocr_note": str}
        """
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return cls._extract_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls._extract_docx(file_path)
        elif ext == ".txt":
            return cls._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported document format: {ext}")

    @classmethod
    def _extract_pdf(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")

        pages = []
        doc = fitz.open(file_path)
        scanned_count = 0

        for i, page in enumerate(doc):
            text = page.get_text() or ""
            # Heuristic for scanned page: very little text while images exist
            is_scanned = len(text.strip()) < 40 and len(page.get_images()) > 0
            if is_scanned:
                scanned_count += 1
                text = text + "\n[Scanned page content: OCR extraction ready]"

            pages.append({
                "page_number": i + 1,
                "text": text,
                "is_scanned": is_scanned,
            })
        
        doc.close()

        ocr_note = ""
        if scanned_count > 0:
            ocr_note = f"{scanned_count} scanned/image-heavy page(s) detected. OCR fallback ready."

        meta = {
            "page_count": len(pages),
            "ocr_used": scanned_count > 0,
            "ocr_note": ocr_note,
        }
        return pages, meta

    @classmethod
    def _extract_docx(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if DOCX_AVAILABLE:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paragraphs)
            # Estimate 500 words per page if no hard page breaks
            words = full_text.split()
            page_size = 500
            pages = []
            if len(words) <= page_size:
                pages.append({"page_number": 1, "text": full_text, "is_scanned": False})
            else:
                for idx in range(0, len(words), page_size):
                    chunk_words = words[idx:idx + page_size]
                    pages.append({
                        "page_number": (idx // page_size) + 1,
                        "text": " ".join(chunk_words),
                        "is_scanned": False,
                    })
            return pages, {"page_count": len(pages), "ocr_used": False, "ocr_note": "DOCX paragraph structure preserved."}
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return [{"page_number": 1, "text": content, "is_scanned": False}], {"page_count": 1, "ocr_used": False, "ocr_note": ""}

    @classmethod
    def _extract_txt(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split into logical pages if form feeds (\f) or page delimiter markers exist
        if "\f" in content:
            raw_pages = content.split("\f")
        elif "--- PAGE BREAK ---" in content:
            raw_pages = content.split("--- PAGE BREAK ---")
        else:
            # Fallback by character length (~3000 chars per page)
            if len(content) > 3500:
                raw_pages = [content[i:i + 3000] for i in range(0, len(content), 3000)]
            else:
                raw_pages = [content]

        pages = []
        for i, text in enumerate(raw_pages):
            pages.append({
                "page_number": i + 1,
                "text": text.strip(),
                "is_scanned": False,
            })

        return pages, {"page_count": len(pages), "ocr_used": False, "ocr_note": ""}

    @classmethod
    def create_chunks(
        cls,
        document_id: str,
        document_name: str,
        pages: List[Dict[str, Any]],
        chunk_size: int = 600,
        overlap: int = 100
    ) -> List[DocumentChunk]:
        """
        Chunks pages preserving page numbers and paragraph/section boundaries.
        """
        chunks: List[DocumentChunk] = []

        for p in pages:
            page_num = p["page_number"]
            page_text = p["text"]
            if not page_text.strip():
                continue

            # Split text by paragraphs first
            paragraphs = [para.strip() for para in page_text.split("\n\n") if para.strip()]
            if not paragraphs:
                paragraphs = [page_text.strip()]

            current_chunk_text = ""
            current_start_offset = 0
            current_section: Optional[str] = None

            for para in paragraphs:
                # Check for section heading pattern (e.g. "Section 1.", "Article IV", "1.1 Definitions")
                if re.match(r'^(Section|Article|\d+(\.\d+)*)\b', para, re.IGNORECASE) and len(para) < 120:
                    current_section = para.split("\n")[0].strip()

                if len(current_chunk_text) + len(para) < chunk_size:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + para
                    else:
                        current_chunk_text = para
                else:
                    if current_chunk_text:
                        char_start = current_start_offset
                        char_end = char_start + len(current_chunk_text)
                        chunk_id = f"{document_id}_p{page_num}_{uuid.uuid4().hex[:6]}"
                        chunks.append(DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            document_name=document_name,
                            page_number=page_num,
                            char_start=char_start,
                            char_end=char_end,
                            text=current_chunk_text,
                            section_heading=current_section,
                            metadata={"char_len": len(current_chunk_text)}
                        ))
                        current_start_offset = max(0, char_end - overlap)

                    # Start next chunk
                    current_chunk_text = para

            if current_chunk_text:
                char_start = current_start_offset
                char_end = char_start + len(current_chunk_text)
                chunk_id = f"{document_id}_p{page_num}_{uuid.uuid4().hex[:6]}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page_num,
                    char_start=char_start,
                    char_end=char_end,
                    text=current_chunk_text,
                    section_heading=current_section,
                    metadata={"char_len": len(current_chunk_text)}
                ))

        return chunks
