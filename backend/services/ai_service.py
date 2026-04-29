from dataclasses import dataclass
from typing import AsyncIterator

import httpx


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
你是一个 Next.js 前端工程师。请生成一个可静态导出的 Next.js App Router + TypeScript 源项目。
你只能输出合法 JSON，不要输出解释，不要输出 markdown。不要输出纯 HTML/CSS/JS 项目结构。
JSON 格式如下：

{
  "files": [
    {"path": "package.json", "content": "完整文件内容"},
    {"path": "next.config.ts", "content": "完整文件内容"},
    {"path": "tsconfig.json", "content": "完整文件内容"},
    {"path": "next-env.d.ts", "content": "完整文件内容"},
    {"path": "app/layout.tsx", "content": "完整文件内容"},
    {"path": "app/page.tsx", "content": "完整文件内容"},
    {"path": "app/globals.css", "content": "完整文件内容"}
  ]
}

源项目要求：
- 必须包含 package.json、next.config.ts、tsconfig.json、next-env.d.ts、app/layout.tsx、app/page.tsx、app/globals.css
- package.json 的 build 脚本必须是 next build；依赖只使用 next、react、react-dom、typescript、@types/node、@types/react、@types/react-dom
- next.config.ts 必须启用 output: "export"，配置 images: { unoptimized: true }，并配置 assetPrefix: "./" 以便 /generated/{app_id}/project/index.html 下的 _next 静态资源使用同目录相对路径加载
- 使用 Next.js App Router 和 TypeScript；app/layout.tsx 必须输出 html/body 并导入 ./globals.css
- 禁止输出 index.html、css/style.css、js/app.js 这种纯静态旧结构
- 禁止 API routes、Route Handlers、Server Actions、Middleware、SSR、cookies()、headers()、getServerSideProps 或任何依赖请求上下文的功能
- 禁止 app/api/*、pages/api/*、middleware.ts、route.ts、route.tsx 等服务端运行时文件
- 交互逻辑必须在浏览器端执行；需要 useState/useEffect/事件处理时，对应组件必须使用 "use client"
- 页面必须使用 mobile-first 方式编写，默认样式先适配手机，再用 @media (min-width: 768px) 增强桌面端
- 页面在 375px 宽度下必须可读、可点、无横向滚动；不要使用固定大宽度、超宽表格或不可换行内容
- 表单、按钮、导航、卡片、表格都要适配移动端；表格在手机上改为卡片、横向滚动容器或可读的纵向布局
- 按钮、输入框、选择器等触控控件高度不小于 44px，并保留足够间距
- 图片、卡片、容器必须 max-width: 100%，布局宽度使用百分比、flex、grid、clamp、minmax 等响应式方式
- 如果应用需要保存用户新增、编辑或删除的数据，必须调用后端持久化接口，不要把 localStorage 作为主存储
- 持久化接口必须使用以 /api 开头的绝对路径：GET/POST /api/generated/{app_id}/data/{collection}，GET/PUT/DELETE /api/generated/{app_id}/data/{collection}/{record_id}
- 不要使用 ./api、api/generated 或 project/api 这类相对路径调用持久化接口
- POST/PUT 请求体必须是 {"data": {...}}，data 必须是对象；collection 使用英文、数字、下划线或短横线
- 客户端代码必须从当前页面路径解析 app_id，例如 /generated/{app_id}/project/index.html，不要硬编码 app_id
- 网络请求失败时在界面提示用户保存失败
- 只能输出 JSON
""".strip()

PROJECT_MODIFY_SYSTEM_PROMPT = """
你是一个 Next.js + TypeScript 项目修改器。你会收到当前源项目文件和用户修改需求。
你只能输出合法 JSON，不要输出解释，不要输出 markdown。
只返回需要修改的源文件。

JSON 格式如下：

{
  "changes": [
    {
      "path": "app/page.tsx",
      "content": "新的完整文件内容"
    }
  ]
}

要求：
- 当前项目是 Next.js App Router + TypeScript 静态导出源项目，不要改回 index.html、css/style.css、js/app.js 旧结构
- 每个 content 必须是完整文件内容
- 不要输出 diff
- 不要输出解释
- 保留 package.json、next.config.ts、tsconfig.json、next-env.d.ts、app/layout.tsx、app/page.tsx、app/globals.css 这些必要文件
- next.config.ts 必须继续启用 output: "export"，配置 images: { unoptimized: true }，并保留 assetPrefix: "./" 以便 /generated/{app_id}/project/index.html 下的 _next 静态资源使用同目录相对路径加载
- 禁止 API routes、Route Handlers、Server Actions、Middleware、SSR、cookies()、headers()、getServerSideProps 或任何依赖请求上下文的功能
- 禁止 app/api/*、pages/api/*、middleware.ts、route.ts、route.tsx 等服务端运行时文件
- 交互逻辑必须在浏览器端执行；需要 useState/useEffect/事件处理时，对应组件必须使用 "use client"
- 不要破坏现有移动端适配；CSS 要保持 mobile-first
- 修改后的页面在 375px 宽度下必须可读、可点、无横向滚动
- 按钮、输入框、选择器等触控控件高度不小于 44px
- 需要桌面增强时使用 @media (min-width: 768px)
- 如果应用需要保存用户新增、编辑或删除的数据，必须调用后端持久化接口，不要把 localStorage 作为主存储
- 持久化接口必须使用以 /api 开头的绝对路径：GET/POST /api/generated/{app_id}/data/{collection}，GET/PUT/DELETE /api/generated/{app_id}/data/{collection}/{record_id}
- 不要使用 ./api、api/generated 或 project/api 这类相对路径调用持久化接口
- POST/PUT 请求体必须是 {"data": {...}}，data 必须是对象；collection 使用英文、数字、下划线或短横线
- 客户端代码必须从当前页面路径解析 app_id，例如 /generated/{app_id}/project/index.html，不要硬编码 app_id
- 网络请求失败时在界面提示用户保存失败
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
    settings: object,
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


async def stream_chat(messages: list[dict], settings: object) -> AsyncIterator[str]:
    async for event in stream_chat_events(messages, settings):
        if event.content:
            yield event.content


async def non_streaming_chat_with_usage(messages: list[dict], settings: object) -> ChatResult:
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


async def non_streaming_chat(messages: list[dict], settings: object) -> str:
    return (await non_streaming_chat_with_usage(messages, settings)).content
