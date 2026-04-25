from dataclasses import dataclass
from typing import AsyncIterator

import httpx

from config import Settings


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatResult:
    content: str
    usage: TokenUsage | None = None


@dataclass
class StreamChatEvent:
    content: str | None = None
    usage: TokenUsage | None = None


PROJECT_GENERATE_SYSTEM_PROMPT = """
你是一个前端工程师。请生成一个多文件纯静态前端项目。
你只能输出合法 JSON，不要输出解释，不要输出 markdown。
JSON 格式如下：

{
  "files": [
    {
      "path": "index.html",
      "content": "完整文件内容"
    },
    {
      "path": "css/style.css",
      "content": "完整文件内容"
    },
    {
      "path": "js/app.js",
      "content": "完整文件内容"
    }
  ]
}

要求：
- 必须包含 index.html
- index.html 必须包含 <meta name="viewport" content="width=device-width, initial-scale=1.0">
- CSS 尽量写入 css/style.css
- JS 尽量写入 js/app.js
- 支持多页面
- 多页面之间使用相对路径跳转
- 所有资源路径必须是相对路径
- 页面必须使用 mobile-first 方式编写，默认样式先适配手机，再用 @media (min-width: 768px) 增强桌面端
- 页面在 375px 宽度下必须可读、可点、无横向滚动；不要使用固定大宽度、超宽表格或不可换行内容
- 表单、按钮、导航、卡片、表格都要适配移动端；表格在手机上改为卡片、横向滚动容器或可读的纵向布局
- 按钮、输入框、选择器等触控控件高度不小于 44px，并保留足够间距
- 图片、卡片、容器必须 max-width: 100%，布局宽度使用百分比、flex、grid、clamp、minmax 等响应式方式
- 只能输出 JSON
""".strip()

PROJECT_MODIFY_SYSTEM_PROMPT = """
你是一个前端项目修改器。你会收到当前项目文件和用户修改需求。
你只能输出合法 JSON，不要输出解释，不要输出 markdown。
只返回需要修改的文件。

JSON 格式如下：

{
  "changes": [
    {
      "path": "css/style.css",
      "content": "新的完整文件内容"
    }
  ]
}

要求：
- 只包含需要修改的文件
- 每个 content 必须是完整文件内容
- 不要输出 diff
- 不要输出解释
- 不要破坏现有移动端适配；如果修改 index.html，要保留 viewport；如果修改 CSS，要保持 mobile-first
- 修改后的页面在 375px 宽度下必须可读、可点、无横向滚动
- 按钮、输入框、选择器等触控控件高度不小于 44px
- 需要桌面增强时使用 @media (min-width: 768px)
- 只能输出 JSON
""".strip()


def parse_usage(data: dict) -> TokenUsage | None:
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return None
    return TokenUsage(
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
    )


def parse_stream_chunk(chunk: dict) -> tuple[str | None, TokenUsage | None]:
    usage = parse_usage(chunk)
    choices = chunk.get("choices") or []
    content = None
    if choices:
        delta = choices[0].get("delta", {})
        content = delta.get("content")
    return content, usage


def parse_non_streaming_response(data: dict) -> ChatResult:
    return ChatResult(
        content=data["choices"][0]["message"]["content"],
        usage=parse_usage(data),
    )


async def stream_chat_events(
    messages: list[dict],
    settings: Settings,
) -> AsyncIterator[StreamChatEvent]:
    """
    Call an OpenAI-compatible chat completions endpoint with streaming.
    Yields content events and a usage event when the provider returns one.
    """
    url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    import json
                    chunk = json.loads(data)
                    content, usage = parse_stream_chunk(chunk)
                    if content:
                        yield StreamChatEvent(content=content)
                    if usage:
                        yield StreamChatEvent(usage=usage)
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue


async def stream_chat(messages: list[dict], settings: Settings) -> AsyncIterator[str]:
    async for event in stream_chat_events(messages, settings):
        if event.content:
            yield event.content


async def non_streaming_chat_with_usage(messages: list[dict], settings: Settings) -> ChatResult:
    """
    Call the chat completions endpoint without streaming and return the full reply with usage when available.
    """
    url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return parse_non_streaming_response(data)


async def non_streaming_chat(messages: list[dict], settings: Settings) -> str:
    return (await non_streaming_chat_with_usage(messages, settings)).content
