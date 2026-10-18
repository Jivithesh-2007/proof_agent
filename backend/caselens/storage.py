"""CaseLens persistence and database management with SQLite."""
import sqlite3
import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from backend.config import settings
from backend.caselens.models import (
    Workspace,
    DocumentMetadata,
    DocumentChunk,
    QuestionAnswerResponse,
    CaseAnalysisResponse,
    ContradictionResponse,
    DocumentComparisonResponse,
    ReportExportResponse,
)

class CaseLensStorage:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.STORAGE_DIR / "caselens.sqlite3")
        self.documents_dir = settings.STORAGE_DIR / "caselens_documents"
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Workspaces
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_documents (
                    document_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    processing_status TEXT NOT NULL,
                    error_message TEXT,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    storage_path TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES cl_workspaces(id) ON DELETE CASCADE
                )
            """)

            # Chunks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    char_start INTEGER NOT NULL DEFAULT 0,
                    char_end INTEGER NOT NULL DEFAULT 0,
                    text TEXT NOT NULL,
                    section_heading TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(document_id) REFERENCES cl_documents(document_id) ON DELETE CASCADE
                )
            """)

            # Q&A Runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_qa_runs (
                    query_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES cl_workspaces(id) ON DELETE CASCADE
                )
            """)

            # Case Analyses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_case_analyses (
                    analysis_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES cl_workspaces(id) ON DELETE CASCADE
                )
            """)

            # Contradictions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_contradictions (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES cl_workspaces(id) ON DELETE CASCADE
                )
            """)

            # Reports
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cl_reports (
                    report_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES cl_workspaces(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

    # ==================== Workspace Operations ====================
    def create_workspace(self, workspace_id: str, name: str, description: Optional[str] = None, is_demo: bool = False, created_at: Optional[str] = None) -> Workspace:
        import datetime
        ts = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO cl_workspaces (id, name, description, is_demo, created_at) VALUES (?, ?, ?, ?, ?)",
                (workspace_id, name, description, 1 if is_demo else 0, ts)
            )
            conn.commit()
        return self.get_workspace(workspace_id) # type: ignore

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cl_workspaces WHERE id = ?", (workspace_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            # Count docs & analyses
            cursor.execute("SELECT COUNT(*) as cnt FROM cl_documents WHERE workspace_id = ?", (workspace_id,))
            doc_cnt = cursor.fetchone()["cnt"]
            cursor.execute("SELECT COUNT(*) as cnt FROM cl_qa_runs WHERE workspace_id = ?", (workspace_id,))
            analysis_cnt = cursor.fetchone()["cnt"]

            return Workspace(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                is_demo=bool(row["is_demo"]),
                created_at=row["created_at"],
                document_count=doc_cnt,
                analysis_count=analysis_cnt,
            )

    def list_workspaces(self) -> List[Workspace]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cl_workspaces ORDER BY created_at DESC")
            rows = cursor.fetchall()
            workspaces = []
            for r in rows:
                ws = self.get_workspace(r["id"])
                if ws:
                    workspaces.append(ws)
            return workspaces

    def delete_workspace(self, workspace_id: str) -> bool:
        docs = self.list_documents(workspace_id)
        for doc in docs:
            self.delete_document(doc.document_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cl_qa_runs WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM cl_case_analyses WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM cl_contradictions WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM cl_reports WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM cl_workspaces WHERE id = ?", (workspace_id,))
            conn.commit()
        return True

    # ==================== Document Operations ====================
    def save_document(
        self,
        metadata: DocumentMetadata,
        storage_path: str,
        chunks: List[DocumentChunk]
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cl_documents 
                (document_id, workspace_id, filename, file_type, file_size_bytes, content_hash, page_count, chunk_count, created_at, processing_status, error_message, is_demo, storage_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.document_id,
                metadata.workspace_id,
                metadata.filename,
                metadata.file_type,
                metadata.file_size_bytes,
                metadata.content_hash,
                metadata.page_count,
                len(chunks),
                metadata.created_at,
                metadata.processing_status,
                metadata.error_message,
                1 if metadata.is_demo else 0,
                storage_path,
            ))

            # Delete old chunks if any
            cursor.execute("DELETE FROM cl_chunks WHERE document_id = ?", (metadata.document_id,))
            
            # Insert chunks
            for ch in chunks:
                cursor.execute("""
                    INSERT INTO cl_chunks
                    (chunk_id, document_id, workspace_id, document_name, page_number, char_start, char_end, text, section_heading, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ch.chunk_id,
                    ch.document_id,
                    metadata.workspace_id,
                    ch.document_name,
                    ch.page_number,
                    ch.char_start,
                    ch.char_end,
                    ch.text,
                    ch.section_heading,
                    json.dumps(ch.metadata),
                ))

            conn.commit()

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cl_documents WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentMetadata(
                document_id=row["document_id"],
                workspace_id=row["workspace_id"],
                filename=row["filename"],
                file_type=row["file_type"],
                file_size_bytes=row["file_size_bytes"],
                content_hash=row["content_hash"],
                page_count=row["page_count"],
                chunk_count=row["chunk_count"],
                created_at=row["created_at"],
                processing_status=row["processing_status"],
                error_message=row["error_message"],
                is_demo=bool(row["is_demo"]),
            )

    def list_documents(self, workspace_id: Optional[str] = None) -> List[DocumentMetadata]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("SELECT * FROM cl_documents WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            else:
                cursor.execute("SELECT * FROM cl_documents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                DocumentMetadata(
                    document_id=r["document_id"],
                    workspace_id=r["workspace_id"],
                    filename=r["filename"],
                    file_type=r["file_type"],
                    file_size_bytes=r["file_size_bytes"],
                    content_hash=r["content_hash"],
                    page_count=r["page_count"],
                    chunk_count=r["chunk_count"],
                    created_at=r["created_at"],
                    processing_status=r["processing_status"],
                    error_message=r["error_message"],
                    is_demo=bool(r["is_demo"]),
                )
                for r in rows
            ]

    def get_document_storage_path(self, document_id: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT storage_path FROM cl_documents WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            return row["storage_path"] if row else None

    def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cl_chunks WHERE document_id = ? ORDER BY page_number ASC, char_start ASC", (document_id,))
            rows = cursor.fetchall()
            return [
                DocumentChunk(
                    chunk_id=r["chunk_id"],
                    document_id=r["document_id"],
                    document_name=r["document_name"],
                    page_number=r["page_number"],
                    char_start=r["char_start"],
                    char_end=r["char_end"],
                    text=r["text"],
                    section_heading=r["section_heading"],
                    metadata=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def get_workspace_chunks(self, workspace_id: str, document_ids: Optional[List[str]] = None) -> List[DocumentChunk]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if document_ids:
                placeholders = ",".join(["?"] * len(document_ids))
                cursor.execute(
                    f"SELECT * FROM cl_chunks WHERE workspace_id = ? AND document_id IN ({placeholders}) ORDER BY page_number ASC",
                    (workspace_id, *document_ids)
                )
            else:
                cursor.execute(
                    "SELECT * FROM cl_chunks WHERE workspace_id = ? ORDER BY page_number ASC",
                    (workspace_id,)
                )
            rows = cursor.fetchall()
            return [
                DocumentChunk(
                    chunk_id=r["chunk_id"],
                    document_id=r["document_id"],
                    document_name=r["document_name"],
                    page_number=r["page_number"],
                    char_start=r["char_start"],
                    char_end=r["char_end"],
                    text=r["text"],
                    section_heading=r["section_heading"],
                    metadata=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def delete_document(self, document_id: str) -> bool:
        # Remove physical file if present
        path_str = self.get_document_storage_path(document_id)
        if path_str:
            p = Path(path_str)
            if p.exists() and p.is_file():
                try:
                    p.unlink()
                except Exception:
                    pass

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cl_chunks WHERE document_id = ?", (document_id,))
            cursor.execute("DELETE FROM cl_documents WHERE document_id = ?", (document_id,))
            conn.commit()
        return True

    # ==================== Q&A Persistence ====================
    def save_qa_run(self, run: QuestionAnswerResponse):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cl_qa_runs (query_id, workspace_id, question, answer, response_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run.query_id,
                run.searched_document_ids[0] if run.searched_document_ids else "default",
                run.question,
                run.answer,
                run.model_dump_json(),
                run.created_at,
            ))
            conn.commit()

    def list_qa_runs(self, workspace_id: Optional[str] = None) -> List[QuestionAnswerResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("SELECT response_json FROM cl_qa_runs WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            else:
                cursor.execute("SELECT response_json FROM cl_qa_runs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            runs = []
            for r in rows:
                try:
                    runs.append(QuestionAnswerResponse.model_validate_json(r["response_json"]))
                except Exception:
                    pass
            return runs

    # ==================== Case Analysis Persistence ====================
    def save_case_analysis(self, analysis: CaseAnalysisResponse):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cl_case_analyses (analysis_id, workspace_id, analysis_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                analysis.analysis_id,
                analysis.workspace_id,
                analysis.model_dump_json(),
                analysis.created_at,
            ))
            conn.commit()

    def get_latest_case_analysis(self, workspace_id: str) -> Optional[CaseAnalysisResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT analysis_json FROM cl_case_analyses WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1",
                (workspace_id,)
            )
            row = cursor.fetchone()
            if row:
                return CaseAnalysisResponse.model_validate_json(row["analysis_json"])
            return None

    # ==================== Contradiction Persistence ====================
    def save_contradictions(self, response: ContradictionResponse):
        import datetime
        import uuid
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cl_contradictions (id, workspace_id, response_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:8],
                response.workspace_id,
                response.model_dump_json(),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ))
            conn.commit()

    def get_latest_contradictions(self, workspace_id: str) -> Optional[ContradictionResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response_json FROM cl_contradictions WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1",
                (workspace_id,)
            )
            row = cursor.fetchone()
            if row:
                return ContradictionResponse.model_validate_json(row["response_json"])
            return None

    # ==================== Report Persistence ====================
    def save_report(self, report: ReportExportResponse):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cl_reports (report_id, workspace_id, title, report_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                report.report_id,
                report.workspace_id,
                report.title,
                report.model_dump_json(),
                report.created_at,
            ))
            conn.commit()

    def list_reports(self, workspace_id: Optional[str] = None) -> List[ReportExportResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("SELECT report_json FROM cl_reports WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            else:
                cursor.execute("SELECT report_json FROM cl_reports ORDER BY created_at DESC")
            rows = cursor.fetchall()
            reports = []
            for r in rows:
                try:
                    reports.append(ReportExportResponse.model_validate_json(r["report_json"]))
                except Exception:
                    pass
            return reports

    def get_report(self, report_id: str) -> Optional[ReportExportResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT report_json FROM cl_reports WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()
            if row:
                return ReportExportResponse.model_validate_json(row["report_json"])
            return None

caselens_storage = CaseLensStorage()
