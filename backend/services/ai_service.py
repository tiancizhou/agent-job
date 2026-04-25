from typing import AsyncIterator

import httpx

from config import Settings

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
- CSS 尽量写入 css/style.css
- JS 尽量写入 js/app.js
- 支持多页面
- 多页面之间使用相对路径跳转
- 所有资源路径必须是相对路径
- 页面必须适配移动端
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
- 只能输出 JSON
""".strip()


async def stream_chat(
    messages: list[dict],
    settings: Settings,
) -> AsyncIterator[str]:
    """
    Call an OpenAI-compatible chat completions endpoint with streaming.
    Yields each content delta string as it arrives.
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
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue


async def non_streaming_chat(messages: list[dict], settings: Settings) -> str:
    """
    Call the chat completions endpoint without streaming and return the full reply.
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
        return data["choices"][0]["message"]["content"]
