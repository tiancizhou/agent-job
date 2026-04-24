from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import App, User
from services import app_service
from services.auth_service import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = ""


@router.post("/apps/{app_id}/chat")
async def chat(
    app_id: str,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(App).filter(App.id == app_id, App.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    async def event_stream():
        async for event in app_service.handle_chat(
            app=app,
            user_message=body.message,
            db=db,
            settings=settings,
        ):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")
