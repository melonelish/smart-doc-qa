from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.exceptions import (
    DocumentNotFoundError,
    FileTypeNotAllowedError,
    FileTooLargeError,
    ProcessingError,
)
from app.models.document import DocumentStatus
from app.services.document_service import DocumentService
from app.services.progress_ws import progress_tracker
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
        raise FileTypeNotAllowedError(ext, settings.allowed_extensions)

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise FileTooLargeError(
            len(content) / (1024 * 1024), settings.max_file_size_mb
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
        raise DocumentNotFoundError(doc_id)

    if doc.status == DocumentStatus.READY:
        return {"message": "文档已处理", "status": doc.status.value}

    DocumentService.update_document_status(db, doc, DocumentStatus.PROCESSING)

    try:
        progress_tracker.set(doc_id, "正在加载文档...", 10)
        chunks = load_and_split_document(doc.file_path)
        progress_tracker.set(doc_id, "文本分割完成", 40)

        qa = QAService()
        progress_tracker.set(doc_id, "正在创建向量库...", 60)
        qa.create_vector_store(chunks, doc.id)
        qa.extract_and_store_tables(doc.file_path, doc.id)
        progress_tracker.set(doc_id, "处理完成", 100)
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
        raise ProcessingError(str(e))


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


@router.get("/{doc_id}/content")
async def get_document_content(doc_id: str, db: Session = Depends(get_db)):
    """Return the raw file content for preview (text/plain, not JSON)."""
    from app.exceptions import DocumentNotFoundError
    doc = DocumentService.get_document(db, doc_id)
    if not doc:
        raise DocumentNotFoundError(doc_id)
    try:
        with open(doc.file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(doc.file_path, "r", encoding="gbk") as f:
                content = f.read()
        except Exception:
            raise HTTPException(status_code=415, detail="Unable to decode file content for preview")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found on disk")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=content)


@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str, db: Session = Depends(get_db)):
    """Return the raw uploaded file for inline preview (e.g. PDF)."""
    from fastapi.responses import FileResponse
    doc = DocumentService.get_document(db, doc_id)
    if not doc:
        raise DocumentNotFoundError(doc_id)
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    media_type = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(doc.file_type, "application/octet-stream")
    # NOTE: Do NOT pass filename= to FileResponse — Starlette's __call__
    # internally overwrites Content-Disposition to "attachment" when
    # filename is set, even if we already set it to "inline" via headers.
    return FileResponse(
        doc.file_path,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'},
    )


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
):
    doc = DocumentService.get_document(db, doc_id)
    if not doc:
        raise DocumentNotFoundError(doc_id)
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
        raise DocumentNotFoundError(doc_id)

    qa = QAService()
    qa.delete_vector_store(doc.id)
    DocumentService.delete_document(db, doc)

    return {"message": "文档已删除"}
