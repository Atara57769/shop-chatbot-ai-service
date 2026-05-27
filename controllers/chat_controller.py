import logging
from fastapi import APIRouter, HTTPException
from models import ChatRequest
from dependencies import chat_service_impl

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/chat')
async def chat(req: ChatRequest):
    try:
        logger.info(f"Received chat request: {req.message}")
        # Convert Message Pydantic objects to dicts for the service layer
        history_list = [{"role": m.role, "content": m.content} for m in req.history]
        reply = chat_service_impl.process_chat_message(
            message=req.message,
            history=history_list
        )
        return {'reply': reply}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
