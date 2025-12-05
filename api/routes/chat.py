"""Chat endpoints."""

from fastapi import APIRouter, HTTPException
import logging

from src.schemas.chat import ChatRequest, ChatResponse, ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process chat request.

    Args:
        request: ChatRequest with message and context

    Returns:
        ChatResponse with reply and metadata
    """
    try:
        if not request.message or not request.message.strip():
            raise ValueError("Message cannot be empty")

        logger.info(f"Processing chat request: {request.message[:100]}...")

        response = ChatResponse(
            message=request.message,
            reply="Processing your request...",
            session_id=request.session_id,
            confidence=0.85,
            source="chat",
            requires_clarification=False
        )

        logger.info(f"Chat response generated")
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat: {str(e)}"
        )


@router.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a session."""
    try:
        return {
            "session_id": session_id,
            "messages": [],
            "created_at": None
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.delete("/conversation/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation session."""
    try:
        return {
            "status": "success",
            "message": f"Session {session_id} deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )
