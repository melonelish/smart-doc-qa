import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import get_settings
from app.models.document import Document, DocumentStatus

settings = get_settings()

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
UPLOAD_DIR = _PROJECT_ROOT / "data" / "uploads"


class DocumentService:
    @staticmethod
    def save_uploaded_file(file: UploadFile) -> tuple[str, str, int]:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix.lower()
        stored_name = f"{file_id}{ext}"
        file_path = UPLOAD_DIR / stored_name
        content = file.file.read()
        file_path.write_bytes(content)
        return str(file_path.absolute()), ext, len(content)

    @staticmethod
    def create_document_record(
        db: Session,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
    ) -> Document:
        doc = Document(
            id=str(uuid.uuid4()),
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            status=DocumentStatus.UPLOADED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_document(db: Session, doc_id: str) -> Document | None:
        return db.query(Document).filter(Document.id == doc_id).first()

    @staticmethod
    def list_documents(
        db: Session, skip: int = 0, limit: int = 20
    ) -> list[Document]:
        return (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_document_status(
        db: Session,
        doc: Document,
        status: DocumentStatus,
        chunk_count: int = 0,
        error_message: str | None = None,
    ):
        doc.status = status
        doc.chunk_count = chunk_count
        doc.error_message = error_message
        doc.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(db: Session, doc: Document) -> bool:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
        db.delete(doc)
        db.commit()
        return True
