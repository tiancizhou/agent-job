import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from services import token_service


class TokenServiceTestCase(unittest.TestCase):
    def test_estimate_text_tokens_counts_chinese_and_english_text(self):
        self.assertEqual(0, token_service.estimate_text_tokens(""))
        self.assertGreaterEqual(token_service.estimate_text_tokens("生成登记页"), 5)
        self.assertGreaterEqual(token_service.estimate_text_tokens("hello world"), 3)

    def test_estimate_messages_tokens_includes_roles_and_content(self):
        messages = [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "hello world"},
        ]

        self.assertGreaterEqual(token_service.estimate_messages_tokens(messages), 8)


if __name__ == "__main__":
    unittest.main()
