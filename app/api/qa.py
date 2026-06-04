import asyncio
import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.exceptions import VectorStoreNotFoundError, QAError
from app.models.document import ConversationRecord
from app.services.qa_service import QAService, conversation_memory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/qa", tags=["qa"])


def _save_turn(
    db: Session,
    doc_id: str,
    conv_id: str,
    role: str,
    content: str,
    sources: str | None = None,
):
    try:
        record = ConversationRecord(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            conversation_id=conv_id,
            role=role,
            content=content,
            sources=sources,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to save conversation turn: %s", e)


class QuestionRequest(BaseModel):
    document_id: str = Field(default="", description="文档ID（与kb_id二选一）")
    kb_id: str = Field(default="", description="知识库ID（与document_id二选一）")
    question: str = Field(
        ..., min_length=1, max_length=2000, description="问题内容"
    )
    conversation_id: str = Field(
        default="",
        description="对话ID，为空则开启新对话，传入已有ID则继续多轮对话",
    )
    top_k: int = Field(4, ge=1, le=20, description="检索文档块数量")
    use_hybrid: bool = Field(
        default=True,
        description="是否启用混合检索 (FAISS + BM25)",
    )
    use_rerank: bool = Field(
        default=True,
        description="是否启用 Cross-Encoder 重排序",
    )


class SourceChunk(BaseModel):
    chunk_index: int
    page: str = ""
    snippet: str


class SourceDetail(BaseModel):
    source: str
    chunks: list[SourceChunk]


class ToolLogEntry(BaseModel):
    tool: str
    args: dict
    result: str


class QuestionResponse(BaseModel):
    question: str
    conversation_id: str
    answer: str
    sources: list[str]
    source_details: list[SourceDetail]
    source_count: int
    retrieval_method: str
    tool_log: list[ToolLogEntry] = []


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):
    try:
        target_id = request.kb_id or request.document_id
        conv_id = request.conversation_id or str(uuid.uuid4())

        _save_turn(db, target_id, conv_id, "user", request.question)

        qa = QAService()
        if request.kb_id:
            result = qa.ask_question_by_kb(
                kb_id=request.kb_id,
                question=request.question,
                conversation_id=conv_id,
                top_k=request.top_k,
                use_hybrid=request.use_hybrid,
                use_rerank=request.use_rerank,
            )
        else:
            result = qa.ask_question(
                vector_store_name=request.document_id,
                question=request.question,
                conversation_id=conv_id,
                top_k=request.top_k,
                use_hybrid=request.use_hybrid,
                use_rerank=request.use_rerank,
            )

        _save_turn(
            db, target_id, result["conversation_id"],
            "assistant", result["answer"],
            sources=json.dumps(result.get("source_details", []), ensure_ascii=False),
        )
        return QuestionResponse(**result)
    except ValueError as e:
        raise VectorStoreNotFoundError(target_id)
    except RuntimeError as e:
        raise QAError(str(e))
    except Exception as e:
        raise QAError(str(e))


@router.post("/ask-stream")
async def ask_question_stream(request: QuestionRequest, db: Session = Depends(get_db)):
    try:
        target_id = request.kb_id or request.document_id
        conv_id = request.conversation_id or str(uuid.uuid4())

        _save_turn(db, target_id, conv_id, "user", request.question)

        qa = QAService()
        if request.kb_id:
            result = qa.ask_question_by_kb(
                kb_id=request.kb_id,
                question=request.question,
                conversation_id=conv_id,
                top_k=request.top_k,
                use_hybrid=request.use_hybrid,
                use_rerank=request.use_rerank,
            )
        else:
            result = qa.ask_question(
                vector_store_name=request.document_id,
                question=request.question,
                conversation_id=conv_id,
                top_k=request.top_k,
                use_hybrid=request.use_hybrid,
                use_rerank=request.use_rerank,
            )
    except ValueError as e:
        raise VectorStoreNotFoundError(request.document_id)
    except RuntimeError as e:
        raise QAError(str(e))

    _save_turn(
        db, target_id, result["conversation_id"],
        "assistant", result["answer"],
        sources=json.dumps(result.get("source_details", []), ensure_ascii=False),
    )

    async def sse_generator():
        conv_id = result.get("conversation_id", "")
        sources = result.get("sources", [])
        source_details = result.get("source_details", [])

        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id, 'sources': sources, 'source_details': source_details, 'retrieval_method': result.get('retrieval_method', ''), 'source_count': result.get('source_count', 0), 'tool_log': result.get('tool_log', [])}, ensure_ascii=False)}\n\n"

        answer = result.get("answer", "")
        for char in answer:
            yield f"data: {json.dumps({'type': 'token', 'text': char}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{doc_id}")
async def get_document_history(
    doc_id: str,
    conversation_id: str = "",
    limit: int = 50,
    db=Depends(get_db),
):
    query = db.query(ConversationRecord).filter(
        ConversationRecord.document_id == doc_id
    )
    if conversation_id:
        query = query.filter(
            ConversationRecord.conversation_id == conversation_id
        )
    records = (
        query
        .order_by(
            ConversationRecord.created_at.asc(),
            case(
                (ConversationRecord.role == "user", 0),
                else_=1,
            ).asc(),
        )
        .limit(limit)
        .all()
    )

    def _parse_sources(raw: str | None) -> list[str]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [
                    item["source"] if isinstance(item, dict) and "source" in item
                    else str(item)
                    for item in parsed
                ]
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    return {
        "document_id": doc_id,
        "count": len(records),
        "items": [
            {
                "id": r.id,
                "conversation_id": r.conversation_id,
                "role": r.role,
                "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                "sources": _parse_sources(r.sources),
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ],
    }


@router.get("/history")
async def list_conversations(
    limit: int = 20,
    db=Depends(get_db),
):
    from sqlalchemy import func
    records = (
        db.query(
            ConversationRecord.conversation_id,
            ConversationRecord.document_id,
            func.min(ConversationRecord.created_at).label("started_at"),
            func.count(ConversationRecord.id).label("message_count"),
        )
        .group_by(
            ConversationRecord.conversation_id,
            ConversationRecord.document_id,
        )
        .order_by(func.min(ConversationRecord.created_at).desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(records),
        "conversations": [
            {
                "conversation_id": r.conversation_id,
                "document_id": r.document_id,
                "started_at": r.started_at.isoformat(),
                "message_count": r.message_count,
            }
            for r in records
        ],
    }


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    conversation_memory.clear(conversation_id)
    deleted = (
        db.query(ConversationRecord)
        .filter(ConversationRecord.conversation_id == conversation_id)
        .delete()
    )
    db.commit()
    return {
        "message": f"对话 {conversation_id} 已清除",
        "deleted_records": deleted,
    }


@router.delete("/history/{record_id}")
async def delete_history_record(
    record_id: str,
    db: Session = Depends(get_db),
):
    record = (
        db.query(ConversationRecord)
        .filter(ConversationRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail=f"记录 {record_id} 不存在")
    db.delete(record)
    db.commit()
    return {"message": "历史记录已删除", "record_id": record_id}