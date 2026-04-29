import os
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_BASE_URL"] = "https://example.test"
os.environ["LLM_MODEL"] = "test-model"

from services import ai_service


class AiServicePromptTestCase(unittest.TestCase):
    def test_parse_non_streaming_response_returns_content_and_usage(self):
        result = ai_service.parse_non_streaming_response({
            "choices": [{"message": {"content": "应用"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
        })

        self.assertEqual("应用", result.content)
        self.assertEqual(10, result.usage.prompt_tokens)
        self.assertEqual(3, result.usage.completion_tokens)
        self.assertEqual(13, result.usage.total_tokens)

    def test_parse_stream_chunk_returns_usage_without_content(self):
        content, usage = ai_service.parse_stream_chunk({
            "choices": [],
            "usage": {"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50},
        })

        self.assertIsNone(content)
        self.assertEqual(20, usage.prompt_tokens)
        self.assertEqual(30, usage.completion_tokens)
        self.assertEqual(50, usage.total_tokens)

    def test_project_generation_prompt_requires_next_static_export_output(self):
        prompt = ai_service.PROJECT_GENERATE_SYSTEM_PROMPT

        self.assertIn("Next.js", prompt)
        self.assertIn("TypeScript", prompt)
        self.assertIn("App Router", prompt)
        self.assertIn("package.json", prompt)
        self.assertIn("app/page.tsx", prompt)
        self.assertIn('output: "export"', prompt)
        self.assertIn("images: { unoptimized: true }", prompt)
        self.assertIn('assetPrefix: "./"', prompt)
        self.assertIn("/generated/{app_id}/project/index.html", prompt)
        self.assertIn("禁止输出 index.html", prompt)
        self.assertIn("API routes", prompt)
        self.assertIn("Server Actions", prompt)
        self.assertIn("mobile-first", prompt)
        self.assertIn("375px", prompt)
        self.assertIn("44px", prompt)
        self.assertIn("@media (min-width: 768px)", prompt)

    def test_project_modify_prompt_preserves_next_static_export_and_mobile_adaptation(self):
        prompt = ai_service.PROJECT_MODIFY_SYSTEM_PROMPT

        self.assertIn("Next.js", prompt)
        self.assertIn("TypeScript", prompt)
        self.assertIn('output: "export"', prompt)
        self.assertIn("images: { unoptimized: true }", prompt)
        self.assertIn('assetPrefix: "./"', prompt)
        self.assertIn("/generated/{app_id}/project/index.html", prompt)
        self.assertIn("不要改回 index.html", prompt)
        self.assertIn("Route Handlers", prompt)
        self.assertIn("mobile-first", prompt)
        self.assertIn("不要破坏", prompt)
        self.assertIn("44px", prompt)

    def test_project_prompts_require_absolute_persistence_api_paths(self):
        for prompt in [ai_service.PROJECT_GENERATE_SYSTEM_PROMPT, ai_service.PROJECT_MODIFY_SYSTEM_PROMPT]:
            self.assertIn("以 /api 开头的绝对路径", prompt)
            self.assertIn("/api/generated/{app_id}/data/{collection}", prompt)
            self.assertIn("不要使用 ./api", prompt)


if __name__ == "__main__":
    unittest.main()
