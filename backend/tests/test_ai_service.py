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
    def test_project_generation_prompt_requires_mobile_first_output(self):
        prompt = ai_service.PROJECT_GENERATE_SYSTEM_PROMPT

        self.assertIn("viewport", prompt)
        self.assertIn("width=device-width", prompt)
        self.assertIn("mobile-first", prompt)
        self.assertIn("375px", prompt)
        self.assertIn("44px", prompt)
        self.assertIn("@media (min-width: 768px)", prompt)

    def test_project_modify_prompt_preserves_mobile_adaptation(self):
        prompt = ai_service.PROJECT_MODIFY_SYSTEM_PROMPT

        self.assertIn("viewport", prompt)
        self.assertIn("mobile-first", prompt)
        self.assertIn("不要破坏", prompt)
        self.assertIn("44px", prompt)


if __name__ == "__main__":
    unittest.main()
