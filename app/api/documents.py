from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.models.document import DocumentStatus
from app.services.document_service import DocumentService
from app.services.qa_service import QAService, load_and_split_document

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{ext}" not in settings.allowed_file_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，允许的类型: {settings.allowed_extensions}",
        )

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.max_file_size_mb}MB)",
        )

    await file.seek(0)

    file_path, file_type, file_size = DocumentService.save_uploaded_file(file)
    doc = DocumentService.create_document_record(
        db, file.filename, file_path, file_type, file_size
    )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status.value,
        "created_at": doc.created_at.isoformat(),
    }


@router.post("/{doc_id}/process")
async def process_document(
    doc_id: str,
    db: Session = Depends(get_db),
):
    doc = DocumentService.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.status == DocumentStatus.READY:
        return {"message": "文档已处理", "status": doc.status.value}

    DocumentService.update_document_status(db, doc, DocumentStatus.PROCESSING)

    try:
        qa = QAService()
        chunks = load_and_split_document(doc.file_path)
        qa.create_vector_store(chunks, doc.id)
        DocumentService.update_document_status(
            db, doc, DocumentStatus.READY, chunk_count=len(chunks)
        )
        return {
            "message": "文档处理完成",
            "status": DocumentStatus.READY.value,
            "chunk_count": len(chunks),
        }
    except Exception as e:
        DocumentService.update_document_status(
            db, doc, DocumentStatus.FAILED, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    docs = DocumentService.list_documents(db, skip, limit)
    return {
        "total": len(docs),
        "items": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status.value,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
    }


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
):
    doc = DocumentService.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
):
    doc = DocumentService.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    qa = QAService()
    qa.delete_vector_store(doc.id)
    DocumentService.delete_document(db, doc)

    return {"message": "文档已删除"}
