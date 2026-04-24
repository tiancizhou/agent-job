import asyncio
import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.orm import Session

from config import Settings
from database import SessionLocal
from models import App, Conversation, Style
from services import ai_service, code_service

SYSTEM_PROMPT = (
    "You are an expert frontend developer. When the user describes an application, "
    "generate a complete, self-contained HTML file that implements it. "
    "Always wrap your HTML in a ```html code block. "
    "Include all CSS and JavaScript inline. Make it visually polished. "
    "The page must include <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> "
    "and use responsive CSS (flexbox/grid, relative units, media queries) so it works well on mobile phones."
)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@dataclass
class GenerationState:
    chunks: list[str] = field(default_factory=list)
    queues: list[asyncio.Queue] = field(default_factory=list)
    done: bool = False
    status: str | None = None
    url: str | None = None
    task: asyncio.Task | None = None


_generation_states: dict[str, GenerationState] = {}


async def handle_chat(
    app: App,
    user_message: str,
    db: Session,
    settings: Settings,
) -> AsyncIterator[str]:
    state = _generation_states.get(app.id)
    if state and not state.done:
        async for chunk in _subscribe_generation(app.id, state):
            yield chunk
        return

    is_first = app.version == 0
    app.status = "creating" if is_first else "editing"
    app.progress = "正在分析需求..."
    db.commit()

    existing_user_message = (
        db.query(Conversation)
        .filter(Conversation.app_id == app.id, Conversation.role == "user")
        .order_by(Conversation.created_at.desc())
        .first()
    )
    if user_message and (not existing_user_message or existing_user_message.content != user_message):
        db.add(Conversation(
            id=str(uuid.uuid4()),
            app_id=app.id,
            role="user",
            content=user_message,
        ))
        db.commit()

    state = GenerationState()
    _generation_states[app.id] = state
    state.task = asyncio.create_task(_run_html_generation(app.id, user_message, settings, state))

    async for chunk in _subscribe_generation(app.id, state):
        yield chunk


async def _subscribe_generation(app_id: str, state: GenerationState) -> AsyncIterator[str]:
    for chunk in state.chunks:
        yield _sse("message", {"content": chunk})

    if state.done:
        yield _sse("result", {"url": state.url, "status": state.status})
        return

    queue: asyncio.Queue = asyncio.Queue()
    state.queues.append(queue)
    try:
        while True:
            event, data = await queue.get()
            yield _sse(event, data)
            if event == "result":
                return
    finally:
        if queue in state.queues:
            state.queues.remove(queue)


async def _publish(state: GenerationState, event: str, data: dict) -> None:
    for queue in list(state.queues):
        await queue.put((event, data))


async def _run_html_generation(
    app_id: str,
    user_message: str,
    settings: Settings,
    state: GenerationState,
) -> None:
    db = SessionLocal()
    try:
        app = db.query(App).filter(App.id == app_id).first()
        if not app:
            state.done = True
            state.status = "failed"
            state.url = None
            await _publish(state, "result", {"url": None, "status": "failed"})
            return

        is_first = app.version == 0
        if is_first:
            await _set_app_name(app, user_message, settings, db)

        prior_conversations = (
            db.query(Conversation)
            .filter(Conversation.app_id == app.id)
            .order_by(Conversation.created_at)
            .all()
        )

        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        style_prompt = _get_style_prompt(app, db)
        if style_prompt:
            messages.append({"role": "system", "content": style_prompt})
        if app.version > 0:
            html_path = Path(settings.DATA_DIR) / "apps" / app.id / "index.html"
            if html_path.exists():
                current_html = html_path.read_text(encoding="utf-8")
                messages.append({"role": "system", "content": f"Current HTML:\n{current_html}"})

        for conv in prior_conversations:
            messages.append({"role": conv.role, "content": conv.content})

        full_reply: list[str] = []
        async for chunk in ai_service.stream_chat(messages, settings):
            full_reply.append(chunk)
            state.chunks.append(chunk)
            await _publish(state, "message", {"content": chunk})

        reply_text = "".join(full_reply)
        html = code_service.extract_html(reply_text)

        if html:
            code_service.save_html(app.id, html, settings.DATA_DIR)
            app.status = "active"
            app.version = (app.version or 0) + 1
        else:
            app.status = "failed"

        app.progress = None
        db.add(Conversation(
            id=str(uuid.uuid4()),
            app_id=app.id,
            role="assistant",
            content=reply_text,
        ))
        db.commit()

    except Exception:
        app = db.query(App).filter(App.id == app_id).first()
        if app:
            app.status = "failed"
            app.progress = None
            db.commit()
    finally:
        app = db.query(App).filter(App.id == app_id).first()
        state.done = True
        state.status = app.status if app else "failed"
        state.url = f"/apps/{app_id}/" if app and app.status == "active" else None
        await _publish(state, "result", {"url": state.url, "status": state.status})
        db.close()


async def _set_app_name(app: App, user_message: str, settings: Settings, db: Session) -> None:
    naming_messages = [
        {
            "role": "user",
            "content": f"请根据用户需求生成一个简短中文应用名称，最多 8 个汉字，不要使用英文，不要加引号或解释：{user_message}",
        }
    ]
    try:
        app_name = await ai_service.non_streaming_chat(naming_messages, settings)
        clean_name = app_name.strip().strip('"').strip("'")
        app.name = clean_name if re.search(r"[\u4e00-\u9fff]", clean_name) else "新应用"
        db.commit()
        db.refresh(app)
    except Exception:
        pass


def _get_style_prompt(app: App, db: Session) -> str | None:
    if not app.style_id:
        return None
    style = db.query(Style).filter(Style.id == app.style_id, Style.is_active == True).first()
    return style.prompt if style else None
