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
from models import App, Conversation, Style, UsageRecord
from services import ai_service, code_service, token_service

LEGACY_HTML_SYSTEM_PROMPT = (
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
    error: str | None = None
    task: asyncio.Task | None = None


_generation_states: dict[str, GenerationState] = {}
_generation_semaphore: asyncio.Semaphore | None = None
_generation_semaphore_limit: int | None = None


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
        yield _sse("result", {"url": state.url, "status": state.status, "error": state.error})
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
    messages: list[dict] = []
    full_reply: list[str] = []
    stream_usage: ai_service.TokenUsage | None = None
    action = "generate"
    try:
        app = db.query(App).filter(App.id == app_id).first()
        if not app:
            state.done = True
            state.status = "failed"
            state.url = None
            state.error = "应用不存在，请刷新后重试。"
            await _publish(state, "result", {"url": None, "status": "failed", "error": state.error})
            return

        semaphore = _get_generation_semaphore(settings.GENERATION_MAX_CONCURRENT)
        if semaphore.locked():
            app.status = "failed" if (app.version or 0) == 0 else "edit_failed"
            app.progress = None
            state.status = "busy"
            state.error = "当前生成任务较多，请稍后再试。"
            db.commit()
            await _publish(state, "message", {"content": state.error})
            return

        async with semaphore:
            await _generate_with_limit(app, user_message, settings, state, db)
            return

    except Exception:
        app = db.query(App).filter(App.id == app_id).first()
        if app:
            if messages:
                _record_usage(
                    db=db,
                    app=app,
                    action=action,
                    messages=messages,
                    reply_text="".join(full_reply),
                    settings=settings,
                    usage=stream_usage,
                    status="failed",
                )
            app.status = "failed" if (app.version or 0) == 0 else "edit_failed"
            app.progress = None
            state.error = "生成过程中发生错误，请稍后重试。"
            db.commit()
    finally:
        app = db.query(App).filter(App.id == app_id).first()
        state.done = True
        state.status = state.status or (app.status if app else "failed")
        state.url = _active_app_url(app_id, settings) if app and app.status in {"active", "edit_failed"} and (app.version or 0) > 0 else None
        await _publish(state, "result", {"url": state.url, "status": state.status, "error": state.error})
        db.close()


def _get_generation_semaphore(limit: int) -> asyncio.Semaphore:
    global _generation_semaphore, _generation_semaphore_limit
    normalized_limit = max(0, limit)
    if _generation_semaphore is None or _generation_semaphore_limit != normalized_limit:
        _generation_semaphore = asyncio.Semaphore(normalized_limit)
        _generation_semaphore_limit = normalized_limit
    return _generation_semaphore


async def _generate_with_limit(
    app: App,
    user_message: str,
    settings: Settings,
    state: GenerationState,
    db: Session,
) -> None:
    messages: list[dict] = []
    full_reply: list[str] = []
    stream_usage: ai_service.TokenUsage | None = None
    action = "generate"
    app_id = app.id
    try:
        is_first = app.version == 0
        action = "generate" if is_first else "edit"
        if is_first:
            await _set_app_name(app, user_message, settings, db)

        prior_conversations = (
            db.query(Conversation)
            .filter(Conversation.app_id == app.id)
            .order_by(Conversation.created_at)
            .all()
        )

        messages = _build_project_messages(app, user_message, prior_conversations, settings, db)

        async for event in ai_service.stream_chat_events(messages, settings):
            if event.content:
                full_reply.append(event.content)
                state.chunks.append(event.content)
                await _publish(state, "message", {"content": event.content})
            if event.usage:
                stream_usage = event.usage

        reply_text = "".join(full_reply)
        await _publish(state, "progress", {"content": "正在解析项目文件..."})
        try:
            saved_url = _save_generation_result(app, reply_text, is_first, settings)
        except code_service.ProjectValidationError as exc:
            saved_url = None
            state.error = str(exc)

        if saved_url:
            app.status = "active"
            state.error = None
            app.version = (app.version or 0) + 1
            usage_status = "success"
        else:
            app.status = "failed" if is_first else "edit_failed"
            if not state.error:
                state.error = "模型返回的项目格式无法解析，请调整需求后重试。"
            usage_status = "failed"

        _record_usage(
            db=db,
            app=app,
            action=action,
            messages=messages,
            reply_text=reply_text,
            settings=settings,
            usage=stream_usage,
            status=usage_status,
        )
        app.progress = None
        db.add(Conversation(
            id=str(uuid.uuid4()),
            app_id=app.id,
            role="assistant",
            content=_assistant_conversation_summary(app.status, state.error),
        ))
        db.commit()

    except Exception:
        app = db.query(App).filter(App.id == app_id).first()
        if app:
            if messages:
                _record_usage(
                    db=db,
                    app=app,
                    action=action,
                    messages=messages,
                    reply_text="".join(full_reply),
                    settings=settings,
                    usage=stream_usage,
                    status="failed",
                )
            app.status = "failed" if (app.version or 0) == 0 else "edit_failed"
            app.progress = None
            state.error = "生成过程中发生错误，请稍后重试。"
            db.commit()


def _build_project_messages(
    app: App,
    user_message: str,
    prior_conversations: list[Conversation],
    settings: Settings,
    db: Session,
) -> list[dict]:
    if app.version == 0:
        messages: list[dict] = [{"role": "system", "content": ai_service.PROJECT_GENERATE_SYSTEM_PROMPT}]
    else:
        messages = [{"role": "system", "content": ai_service.PROJECT_MODIFY_SYSTEM_PROMPT}]
        project_files = code_service.read_project_files(app.id, settings.DATA_DIR)
        if project_files:
            messages.append({"role": "system", "content": f"当前项目文件：\n{json.dumps(project_files, ensure_ascii=False)}"})
        else:
            html_path = Path(settings.DATA_DIR) / "apps" / app.id / "index.html"
            if html_path.exists():
                current_html = html_path.read_text(encoding="utf-8")
                messages = [{"role": "system", "content": LEGACY_HTML_SYSTEM_PROMPT}]
                messages.append({"role": "system", "content": f"Current HTML:\n{current_html}"})

    style_prompt = _get_style_prompt(app, db)
    if style_prompt:
        messages.append({"role": "system", "content": style_prompt})

    for conv in prior_conversations:
        messages.append({"role": conv.role, "content": conv.content})
    if user_message and (not messages or messages[-1].get("content") != user_message):
        messages.append({"role": "user", "content": user_message})
    return messages


def _assistant_conversation_summary(status: str, error: str | None = None) -> str:
    if status == "active":
        return "应用已生成或更新，可以在右侧预览。"
    if status == "edit_failed":
        return error or "应用修改失败，已保留上一个可用版本。"
    if status == "failed":
        return error or "应用生成失败，请调整需求后重试。"
    return "应用生成已结束。"


def _save_generation_result(app: App, reply_text: str, is_first: bool, settings: Settings) -> str | None:
    if is_first:
        files = code_service.parse_project_json_or_raise(reply_text)
        code_service.save_project(app.id, files, settings.DATA_DIR)
        app.entry_path = "index.html"
        app.project_type = "project"
        return f"/generated/{app.id}/project/index.html"

    changes = code_service.parse_changes_json_or_raise(reply_text)
    code_service.save_changes(app.id, changes, settings.DATA_DIR)
    app.entry_path = "index.html"
    app.project_type = "project"
    return f"/generated/{app.id}/project/index.html"


def _active_app_url(app_id: str, settings: Settings) -> str:
    project_index = code_service.project_dir_for(app_id, settings.DATA_DIR) / "index.html"
    if project_index.exists():
        return f"/generated/{app_id}/project/index.html"
    return f"/apps/{app_id}/"


async def _set_app_name(app: App, user_message: str, settings: Settings, db: Session) -> None:
    naming_messages = [
        {
            "role": "user",
            "content": f"请根据用户需求生成一个简短中文应用名称，最多 8 个汉字，不要使用英文，不要加引号或解释：{user_message}",
        }
    ]
    try:
        result = await ai_service.non_streaming_chat_with_usage(naming_messages, settings)
        clean_name = result.content.strip().strip('"').strip("'")
        app.name = clean_name if re.search(r"[\u4e00-\u9fff]", clean_name) else "新应用"
        _record_usage(db, app, "name", naming_messages, result.content, settings, result.usage, "success")
        db.commit()
        db.refresh(app)
    except Exception:
        pass


def _provider_from_base_url(base_url: str) -> str:
    lowered = base_url.lower()
    if "deepseek" in lowered:
        return "deepseek"
    if "openai" in lowered:
        return "openai"
    return "unknown"


def _record_usage(
    db: Session,
    app: App,
    action: str,
    messages: list[dict],
    reply_text: str,
    settings: Settings,
    usage: ai_service.TokenUsage | None,
    status: str,
) -> None:
    if usage:
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens or prompt_tokens + completion_tokens
        is_estimated = False
    else:
        prompt_tokens = token_service.estimate_messages_tokens(messages)
        completion_tokens = token_service.estimate_text_tokens(reply_text)
        total_tokens = prompt_tokens + completion_tokens
        is_estimated = True
    db.add(UsageRecord(
        id=str(uuid.uuid4()),
        user_id=app.user_id,
        app_id=app.id,
        action=action,
        provider=_provider_from_base_url(settings.LLM_BASE_URL),
        model=settings.LLM_MODEL,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost=0,
        is_estimated=is_estimated,
        status=status,
    ))


def _get_style_prompt(app: App, db: Session) -> str | None:
    if not app.style_id:
        return None
    style = db.query(Style).filter(Style.id == app.style_id, Style.is_active == True).first()
    return style.prompt if style else None
