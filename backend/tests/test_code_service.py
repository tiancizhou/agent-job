import json
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from services import code_service


class ProjectCodeServiceTestCase(unittest.TestCase):
    def test_parse_project_json_accepts_fenced_json(self):
        payload = {
            "files": [
                {"path": "index.html", "content": "<html></html>"},
                {"path": "css/style.css", "content": "body { margin: 0; }"},
                {"path": "js/app.js", "content": "console.log('ok')"},
            ]
        }

        files = code_service.parse_project_json(f"```json\n{json.dumps(payload)}\n```")

        self.assertEqual(payload["files"], files)

    def test_parse_project_json_accepts_raw_json(self):
        payload = {
            "files": [
                {"path": "index.html", "content": "<html></html>"},
                {"path": "css/style.css", "content": "body { margin: 0; }"},
                {"path": "js/app.js", "content": "console.log('ok')"},
            ]
        }

        files = code_service.parse_project_json(json.dumps(payload))

        self.assertEqual(payload["files"], files)

    def test_parse_project_json_rejects_single_html_project(self):
        payload = {"files": [{"path": "index.html", "content": "<html></html>"}]}

        self.assertIsNone(code_service.parse_project_json(json.dumps(payload)))

    def test_parse_project_json_rejects_missing_index(self):
        payload = {"files": [{"path": "pages/home.html", "content": "<html></html>"}]}

        self.assertIsNone(code_service.parse_project_json(json.dumps(payload)))
        with self.assertRaisesRegex(code_service.ProjectValidationError, "缺少必要文件"):
            code_service.parse_project_json_or_raise(json.dumps(payload))

    def test_parse_project_json_rejects_invalid_json_with_detail(self):
        with self.assertRaisesRegex(code_service.ProjectValidationError, "不是有效 JSON"):
            code_service.parse_project_json_or_raise("not json")

    def test_parse_project_json_rejects_unsafe_paths(self):
        unsafe_paths = [
            "../secret.txt",
            "..\\secret.txt",
            "/tmp/index.html",
            "C:\\tmp\\index.html",
            "backend.py",
        ]
        for path in unsafe_paths:
            with self.subTest(path=path):
                payload = {
                    "files": [
                        {"path": "index.html", "content": "<html></html>"},
                        {"path": path, "content": "bad"},
                    ]
                }
                self.assertIsNone(code_service.parse_project_json(json.dumps(payload)))

    def test_parse_project_json_rejects_limits(self):
        too_many = {
            "files": [
                {"path": "index.html", "content": "<html></html>"},
                *[
                    {"path": f"pages/{i}.html", "content": "<html></html>"}
                    for i in range(code_service.MAX_PROJECT_FILES)
                ],
            ]
        }
        oversized = {
            "files": [
                {"path": "index.html", "content": "x" * (code_service.MAX_FILE_BYTES + 1)},
            ]
        }

        self.assertIsNone(code_service.parse_project_json(json.dumps(too_many)))
        self.assertIsNone(code_service.parse_project_json(json.dumps(oversized)))

    def test_parse_changes_json_accepts_changes_without_index(self):
        payload = {"changes": [{"path": "css/style.css", "content": "body { color: red; }"}]}

        changes = code_service.parse_changes_json(json.dumps(payload))

        self.assertEqual(payload["changes"], changes)

    def test_save_project_read_project_and_save_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = [
                {"path": "index.html", "content": "<html><link rel='stylesheet' href='css/style.css'></html>"},
                {"path": "css/style.css", "content": "body { color: black; }"},
                {"path": "js/app.js", "content": "console.log('old')"},
            ]

            project_dir = code_service.save_project("app-1", files, tmpdir)

            self.assertEqual(Path(tmpdir) / "apps" / "app-1" / "project", project_dir)
            self.assertEqual("body { color: black; }", (project_dir / "css" / "style.css").read_text(encoding="utf-8"))
            self.assertEqual(sorted(files, key=lambda item: item["path"]), code_service.read_project_files("app-1", tmpdir))

            changes = [
                {"path": "css/style.css", "content": "body { color: blue; }"},
            ]
            code_service.save_changes("app-1", changes, tmpdir)

            self.assertEqual("body { color: blue; }", (project_dir / "css" / "style.css").read_text(encoding="utf-8"))
            self.assertEqual("console.log('old')", (project_dir / "js" / "app.js").read_text(encoding="utf-8"))

    def test_save_project_rejects_invalid_entries_without_removing_existing_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_files = [
                {"path": "index.html", "content": "<html>old</html>"},
                {"path": "css/style.css", "content": "body { color: black; }"},
                {"path": "js/app.js", "content": "console.log('old')"},
            ]
            project_dir = code_service.save_project("app-1", original_files, tmpdir)

            with self.assertRaises(code_service.ProjectValidationError):
                code_service.save_project("app-1", [{"path": "../bad.txt", "content": "bad"}], tmpdir)

            self.assertEqual("<html>old</html>", (project_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual("body { color: black; }", (project_dir / "css" / "style.css").read_text(encoding="utf-8"))

    def test_save_changes_rejects_invalid_entries_without_partial_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_files = [
                {"path": "index.html", "content": "<html>old</html>"},
                {"path": "css/style.css", "content": "body { color: black; }"},
                {"path": "js/app.js", "content": "console.log('old')"},
            ]
            project_dir = code_service.save_project("app-1", original_files, tmpdir)

            with self.assertRaises(code_service.ProjectValidationError):
                code_service.save_changes("app-1", [
                    {"path": "css/style.css", "content": "body { color: blue; }"},
                    {"path": "../bad.txt", "content": "bad"},
                ], tmpdir)

            self.assertEqual("body { color: black; }", (project_dir / "css" / "style.css").read_text(encoding="utf-8"))
            self.assertEqual("console.log('old')", (project_dir / "js" / "app.js").read_text(encoding="utf-8"))

    def test_save_changes_rejects_final_project_file_count_over_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_files = [
                {"path": "index.html", "content": "<html>old</html>"},
                {"path": "css/style.css", "content": "body { color: black; }"},
                {"path": "js/app.js", "content": "console.log('old')"},
                *[
                    {"path": f"existing/{i}.html", "content": "<html></html>"}
                    for i in range(9)
                ],
            ]
            project_dir = code_service.save_project("app-1", original_files, tmpdir)
            changes = [
                {"path": f"pages/{i}.html", "content": "<html></html>"}
                for i in range(code_service.MAX_CHANGE_FILES)
            ]

            with self.assertRaisesRegex(code_service.ProjectValidationError, "文件数量超过上限"):
                code_service.save_changes("app-1", changes, tmpdir)

            self.assertEqual("body { color: black; }", (project_dir / "css" / "style.css").read_text(encoding="utf-8"))
            self.assertFalse((project_dir / "pages" / "0.html").exists())


if __name__ == "__main__":
    unittest.main()
