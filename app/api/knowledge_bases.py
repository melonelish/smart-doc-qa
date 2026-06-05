"""Knowledge Base API Router."""

import logging
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
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
from app.services.progress_ws import progress_tracker

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])
settings = get_settings()
logger = logging.getLogger(__name__)


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
    # Verify KB exists
    kb = KnowledgeBaseService.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Verify document exists and is in this KB
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    ok = KnowledgeBaseService.remove_document(db, kb_id, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Association not found")

    # Rebuild vector store without the removed document
    try:
        KnowledgeBaseService.rebuild_kb_index(db, kb_id)
    except ValueError:
        # No remaining readable documents — remove the vector store
        from app.services.qa_service import QAService
        QAService.delete_vector_store(f"kb_{kb_id}")
    return {"message": "Document removed from knowledge base"}


def _upload_to_kb_background(kb_id: str, doc_id: str, file_path: str, filename: str):
    """Background task: process document into KB vector store."""
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        doc = DocumentService.get_document(db, doc_id)
        if not doc:
            logger.warning("KB upload background: doc not found | doc_id=%s", doc_id)
            return

        DocumentService.update_document_status(db, doc, DocumentStatus.PROCESSING)
        progress_tracker.set(doc_id, "正在加载文档...", 10)

        chunks = load_and_split_document(file_path)
        if not chunks:
            raise ValueError("文档内容为空或无法提取文本")
        progress_tracker.set(doc_id, "文本分割完成", 40)

        for chunk in chunks:
            chunk.metadata["document_id"] = doc.id
            chunk.metadata["document_name"] = filename
        kb_store_name = f"kb_{kb_id}"
        qa = QAService()

        # Pre-warm embeddings so the model-loading delay is visible in UI.
        # On first call HuggingFaceEmbeddings loads the transformer from disk;
        # without progress feedback the frontend appears frozen at 40%.
        progress_tracker.set(doc_id, "正在加载 AI 模型...", 50)
        from app.services.qa_service import get_embeddings
        get_embeddings()
        progress_tracker.set(doc_id, "AI 模型加载完成", 55)

        progress_tracker.set(doc_id, "正在创建向量库...", 60)
        qa.create_vector_store(chunks, kb_store_name)
        qa.extract_and_store_tables(file_path, kb_store_name)
        # Update doc_ids.txt
        doc_ids_path = Path(settings.vector_store_path) / kb_store_name / "doc_ids.txt"
        existing_ids = set()
        if doc_ids_path.exists():
            existing_ids = set(doc_ids_path.read_text(encoding="utf-8").split(","))
        existing_ids.add(doc.id)
        doc_ids_path.write_text(",".join(sorted(existing_ids)), encoding="utf-8")
        DocumentService.update_document_status(
            db, doc, DocumentStatus.READY, chunk_count=len(chunks)
        )
        progress_tracker.set(doc_id, "处理完成", 100)
        logger.info("KB upload processed OK | kb_id=%s doc_id=%s chunks=%d",
                     kb_id, doc_id, len(chunks))
    except Exception as e:
        logger.error("KB upload processing failed | kb_id=%s doc_id=%s error=%s",
                      kb_id, doc_id, e)
        progress_tracker.set(doc_id, f"处理失败: {e}", 0)
        db.rollback()
        try:
            doc = DocumentService.get_document(db, doc_id)
            if doc:
                DocumentService.update_document_status(
                    db, doc, DocumentStatus.FAILED, error_message=str(e)
                )
        except Exception:
            pass
    finally:
        db.close()


@router.post("/{kb_id}/upload")
async def upload_to_kb(
    kb_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Upload a file directly into a knowledge base, then auto-process in background."""
    kb = KnowledgeBaseService.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File name required")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{ext}" not in settings.allowed_file_extensions:
        raise FileTypeNotAllowedError(ext, settings.allowed_extensions)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件，不允许上传")
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise FileTooLargeError(
            len(content) / (1024 * 1024), settings.max_file_size_mb
        )
    await file.seek(0)

    # Save file & create document record
    file_path_src, file_type, file_size = DocumentService.save_uploaded_file(file)
    # Move to kb-scoped path
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

    # Process in background
    background_tasks.add_task(
        _upload_to_kb_background, kb_id, doc.id, file_path, file.filename
    )
    logger.info("Document uploaded to KB | kb_id=%s doc_id=%s filename=%s",
                kb_id, doc.id, doc.filename)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "kb_id": kb_id,
        "kb_name": kb.name,
        "status": doc.status.value,
    }


@router.post("/{kb_id}/rebuild-index")
async def rebuild_kb_index(kb_id: str, db: Session = Depends(get_db)):
    try:
        store_dir = KnowledgeBaseService.rebuild_kb_index(db, kb_id)
        return {"message": "Index rebuilt successfully", "store_dir": store_dir}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))