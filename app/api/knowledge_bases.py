"""Knowledge Base API Router."""

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.config import get_settings
from app.db.database import get_db
from app.exceptions import (
    DocumentNotFoundError,
    FileTypeNotAllowedError,
    FileTooLargeError,
    ProcessingError,
)
from app.models.document import DocumentStatus
from app.services.document_service import DocumentService, UPLOAD_DIR
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.qa_service import QAService, load_and_split_document

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])
settings = get_settings()


class CreateKBRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    domain: str = Field(default="enterprise", max_length=50)


class UpdateKBRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class AddDocsRequest(BaseModel):
    doc_ids: List[str] = Field(..., min_length=1)


@router.get("/")
async def list_knowledge_bases(skip: int = 0, limit: int = 50, domain: Optional[str] = None, db: Session = Depends(get_db)):
    kbs = KnowledgeBaseService.list_all(db, skip, limit, domain=domain)
    result = []
    for kb in kbs:
        docs = KnowledgeBaseService.get_documents(db, kb.id)
        result.append({
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "domain": kb.domain,
            "document_count": len(docs),
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
        })
    return {"total": len(result), "items": result}


@router.post("/")
async def create_knowledge_base(req: CreateKBRequest, db: Session = Depends(get_db)):
    kb = KnowledgeBaseService.create(db, req.name, req.description, domain=req.domain)
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "domain": kb.domain,
        "document_count": 0,
        "created_at": kb.created_at.isoformat(),
        "updated_at": kb.updated_at.isoformat(),
    }


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: str, db: Session = Depends(get_db)):
    kb = KnowledgeBaseService.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    docs = KnowledgeBaseService.get_documents(db, kb.id)
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "document_count": len(docs),
        "documents": [
            {
                "id": d.id, "filename": d.filename,
                "file_type": d.file_type, "file_size": d.file_size,
                "status": d.status.value, "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
        "created_at": kb.created_at.isoformat(),
        "updated_at": kb.updated_at.isoformat(),
    }


@router.put("/{kb_id}")
async def update_knowledge_base(kb_id: str, req: UpdateKBRequest, db: Session = Depends(get_db)):
    kb = KnowledgeBaseService.update(db, kb_id, req.name, req.description)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"id": kb.id, "name": kb.name, "description": kb.description}


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str, db: Session = Depends(get_db)):
    ok = KnowledgeBaseService.delete(db, kb_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "Knowledge base deleted"}


@router.get("/{kb_id}/documents")
async def list_kb_documents(kb_id: str, db: Session = Depends(get_db)):
    """List documents in a knowledge base."""
    kb = KnowledgeBaseService.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    docs = KnowledgeBaseService.get_documents(db, kb_id)
    return {
        "total": len(docs),
        "items": [
            {
                "id": d.id, "filename": d.filename,
                "file_type": d.file_type, "file_size": d.file_size,
                "status": d.status.value, "chunk_count": d.chunk_count,
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
    }


@router.post("/{kb_id}/documents")
async def add_documents_to_kb(kb_id: str, req: AddDocsRequest, db: Session = Depends(get_db)):
    result = KnowledgeBaseService.add_documents_batch(db, kb_id, req.doc_ids)
    if result["added"] + result["skipped"] == 0:
        raise HTTPException(status_code=404, detail="Knowledge base or documents not found")
    try:
        KnowledgeBaseService.rebuild_kb_index(db, kb_id)
    except ValueError:
        pass
    added = result["added"]
    skipped = result["skipped"]
    return {
        "message": f"Added {added} document(s), {skipped} already present",
        "added": added,
        "skipped": skipped,
    }


@router.delete("/{kb_id}/documents/{doc_id}")
async def remove_document_from_kb(kb_id: str, doc_id: str, db: Session = Depends(get_db)):
    ok = KnowledgeBaseService.remove_document(db, kb_id, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Association not found")
    return {"message": "Document removed from knowledge base"}


@router.post("/{kb_id}/upload")
async def upload_to_kb(kb_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a file directly into a knowledge base, then auto-process."""
    kb = KnowledgeBaseService.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File name required")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{ext}" not in settings.allowed_file_extensions:
        raise FileTypeNotAllowedError(ext, settings.allowed_extensions)

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise FileTooLargeError(
            len(content) / (1024 * 1024), settings.max_file_size_mb
        )
    await file.seek(0)

    # Save file & create document record
    file_path_src, file_type, file_size = DocumentService.save_uploaded_file(file)
    # Move to kb-scoped path so it isn't dangling if KB is deleted
    kb_dir = UPLOAD_DIR / "kb" / kb_id
    kb_dir.mkdir(parents=True, exist_ok=True)
    dest = kb_dir / file.filename
    os.replace(file_path_src, dest)
    file_path = str(dest)

    doc = DocumentService.create_document_record(
        db, file.filename, file_path, file_type, file_size
    )

    # Add to KB
    result = KnowledgeBaseService.add_documents_batch(db, kb_id, [doc.id])
    if result["added"] == 0:
        raise HTTPException(status_code=400, detail="Failed to add document to KB")

    # Auto-process
    DocumentService.update_document_status(db, doc, DocumentStatus.PROCESSING)
    try:
        chunks = load_and_split_document(file_path)
        # Set doc metadata on each chunk for cross-doc traceability
        for chunk in chunks:
            chunk.metadata["document_id"] = doc.id
            chunk.metadata["document_name"] = doc.filename
        kb_store_name = f"kb_{kb_id}"
        qa = QAService()
        qa.create_vector_store(chunks, kb_store_name)
        # Update doc_ids.txt for tracking
        doc_ids_path = Path(settings.vector_store_path) / kb_store_name / "doc_ids.txt"
        existing_ids = set()
        if doc_ids_path.exists():
            existing_ids = set(doc_ids_path.read_text(encoding="utf-8").split(","))
        existing_ids.add(doc.id)
        doc_ids_path.write_text(",".join(sorted(existing_ids)), encoding="utf-8")
        DocumentService.update_document_status(
            db, doc, DocumentStatus.READY, chunk_count=len(chunks)
        )
    except Exception as e:
        DocumentService.update_document_status(
            db, doc, DocumentStatus.FAILED, error_message=str(e)
        )
        raise ProcessingError(str(e))

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "kb_id": kb_id,
        "kb_name": kb.name,
        "chunk_count": len(chunks),
        "status": "ready",
    }


@router.post("/{kb_id}/rebuild-index")
async def rebuild_kb_index(kb_id: str, db: Session = Depends(get_db)):
    try:
        store_dir = KnowledgeBaseService.rebuild_kb_index(db, kb_id)
        return {"message": "Index rebuilt successfully", "store_dir": store_dir}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))