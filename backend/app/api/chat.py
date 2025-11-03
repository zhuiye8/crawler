"""Chat API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.rag_service import chat_with_rag

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat endpoint with RAG (无需认证)

    - Retrieves relevant article chunks
    - Generates answer using GPT-4
    - Returns answer with sources

    完全开放访问，无需任何认证
    """
    try:
        result = await chat_with_rag(
            db=db,
            question=request.question,
            user_id="anonymous",
            conversation_id=request.conversation_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
