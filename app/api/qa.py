import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.exceptions import VectorStoreNotFoundError, QAError
from app.models.document import ConversationRecord
from app.services.qa_service import QAService, conversation_memory

router = APIRouter(prefix="/api/v1/qa", tags=["qa"])


import uuid
from datetime import datetime


def _save_conversation_turn(
    db: Session,
    doc_id: str,
    conv_id: str,
    role: str,
    content: str,
    sources: str | None = None,
):
    """Write a single conversation turn to DB (fire-and-forget)."""
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
    except Exception:
        db.rollback()  # non-fatal; don't block the user's answer


class QuestionRequest(BaseModel):
    document_id: str = Field(..., description="文档ID")
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


class QuestionResponse(BaseModel):
    question: str
    conversation_id: str
    answer: str
    sources: list[str]
    source_details: list[SourceDetail]
    source_count: int
    retrieval_method: str


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):
    try:
        qa = QAService()
        result = qa.ask_question(
            vector_store_name=request.document_id,
            question=request.question,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            use_hybrid=request.use_hybrid,
            use_rerank=request.use_rerank,
        )
        # Persist to DB
        _save_conversation_turn(
            db, request.document_id, result["conversation_id"],
            "user", request.question,
            sources=None,
        )
        _save_conversation_turn(
            db, request.document_id, result["conversation_id"],
            "assistant", result["answer"],
            sources=json.dumps(result.get("source_details", []), ensure_ascii=False),
        )
        return QuestionResponse(**result)
    except ValueError as e:
        raise VectorStoreNotFoundError(request.document_id)
    except RuntimeError as e:
        raise QAError(str(e))
    except Exception as e:
        raise QAError(str(e))


@router.post("/ask-stream")
async def ask_question_stream(request: QuestionRequest):
    """SSE 流式问答 —— 答案逐字返回，消除长回答等待焦虑。"""
    try:
        qa = QAService()
        result = qa.ask_question(
            vector_store_name=request.document_id,
            question=request.question,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            use_hybrid=request.use_hybrid,
            use_rerank=request.use_rerank,
        )
    except ValueError as e:
        raise VectorStoreNotFoundError(request.document_id)
    except RuntimeError as e:
        raise QAError(str(e))

    async def sse_generator():
        """Server-Sent Events generator."""
        # 1) Send metadata header
        conv_id = result.get("conversation_id", "")
        sources = result.get("sources", [])
        source_details = result.get("source_details", [])

        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id, 'sources': sources, 'source_details': source_details, 'retrieval_method': result.get('retrieval_method', ''), 'source_count': result.get('source_count', 0)}, ensure_ascii=False)}\n\n"

        # 2) Stream answer text character-by-character
        answer = result.get("answer", "")
        for char in answer:
            yield f"data: {json.dumps({'type': 'token', 'text': char}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)  # small delay for visual effect

        # 3) Done
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
    """获取指定文档的问答历史（支持按对话ID过滤）。"""
    from app.models.document import ConversationRecord
    query = db.query(ConversationRecord).filter(
        ConversationRecord.document_id == doc_id
    )
    if conversation_id:
        query = query.filter(
            ConversationRecord.conversation_id == conversation_id
        )
    records = (
        query
        .order_by(ConversationRecord.created_at.asc())
        .limit(limit)
        .all()
    )
    return {
        "document_id": doc_id,
        "count": len(records),
        "items": [
            {
                "id": r.id,
                "conversation_id": r.conversation_id,
                "role": r.role,
                "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                "sources": r.sources,
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
    """列出所有对话会话（按去重 conversation_id）。"""
    from sqlalchemy import func
    from app.models.document import ConversationRecord
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
async def clear_conversation(conversation_id: str):
    """清除指定对话的历史记录"""
    conversation_memory.clear(conversation_id)
    return {"message": f"对话 {conversation_id} 已清除"}
