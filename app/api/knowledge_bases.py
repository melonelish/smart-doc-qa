"""Knowledge Base API Router."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.database import get_db
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])


class CreateKBRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class UpdateKBRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class AddDocsRequest(BaseModel):
    doc_ids: List[str] = Field(..., min_length=1)


@router.get("/")
async def list_knowledge_bases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    kbs = KnowledgeBaseService.list_all(db, skip, limit)
    result = []
    for kb in kbs:
        docs = KnowledgeBaseService.get_documents(db, kb.id)
        result.append({
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "document_count": len(docs),
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
        })
    return {"total": len(result), "items": result}


@router.post("/")
async def create_knowledge_base(req: CreateKBRequest, db: Session = Depends(get_db)):
    kb = KnowledgeBaseService.create(db, req.name, req.description)
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
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


@router.post("/{kb_id}/rebuild-index")
async def rebuild_kb_index(kb_id: str, db: Session = Depends(get_db)):
    try:
        store_dir = KnowledgeBaseService.rebuild_kb_index(db, kb_id)
        return {"message": "Index rebuilt successfully", "store_dir": store_dir}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))