from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.qa_service import QAService

router = APIRouter(prefix="/api/v1/qa", tags=["qa"])


class QuestionRequest(BaseModel):
    document_id: str = Field(..., description="文档ID")
    question: str = Field(..., min_length=1, max_length=2000, description="问题内容")
    top_k: int = Field(4, ge=1, le=20, description="检索相关文档块数量")


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    source_count: int


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    try:
        qa = QAService()
        result = qa.ask_question(
            vector_store_name=request.document_id,
            question=request.question,
            top_k=request.top_k,
        )
        return QuestionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答服务异常: {str(e)}")
