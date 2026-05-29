from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.qa_service import QAService, conversation_memory

router = APIRouter(prefix="/api/v1/qa", tags=["qa"])


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
async def ask_question(request: QuestionRequest):
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
        return QuestionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答服务异常: {str(e)}")


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """清除指定对话的历史记录"""
    conversation_memory.clear(conversation_id)
    return {"message": f"对话 {conversation_id} 已清除"}
