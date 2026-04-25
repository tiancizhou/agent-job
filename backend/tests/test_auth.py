import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]


def load_app(tmpdir: str):
    old_cwd = os.getcwd()
    os.chdir(tmpdir)
    sys.path.insert(0, str(BACKEND_DIR))
    os.environ["LLM_API_KEY"] = "test-key"
    os.environ["LLM_BASE_URL"] = "https://example.test"
    os.environ["LLM_MODEL"] = "test-model"
    os.environ["DATA_DIR"] = str(Path(tmpdir) / "data")

    for name in list(sys.modules):
        if name in {"main", "database", "models", "config"} or name.startswith("routers") or name.startswith("services"):
            sys.modules.pop(name, None)

    try:
        main = importlib.import_module("main")
        return main.app, importlib.import_module("database"), importlib.import_module("models")
    finally:
        os.chdir(old_cwd)


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app, database, models = load_app(self.tmp.name)
        self.client = TestClient(app)
        self.database = database
        self.models = models

    def tearDown(self):
        self.database.engine.dispose()
        self.tmp.cleanup()

    def test_apps_require_login(self):
        response = self.client.get("/api/apps")
        self.assertEqual(401, response.status_code)

    def test_unknown_employee_cannot_set_password(self):
        response = self.client.post(
            "/api/auth/register",
            json={"employee_no": "64004", "password": "123456"},
        )
        self.assertEqual(403, response.status_code)

    def test_admin_can_create_employee_after_login(self):
        db = self.database.SessionLocal()
        try:
            employee = self.models.Employee(employee_no="64003", name="管理员", status="active")
            admin = self.models.User(employee_no="64003", password_hash=self.models.hash_password("123456"), is_admin=True)
            db.add(employee)
            db.add(admin)
            db.commit()
        finally:
            db.close()

        login = self.client.post(
            "/api/auth/login",
            json={"employee_no": "64003", "password": "123456"},
        )
        self.assertEqual(200, login.status_code)

        created = self.client.post(
            "/api/admin/employees",
            json={"employee_no": "64004", "name": "测试用户"},
        )
        self.assertEqual(201, created.status_code)
        self.assertEqual("64004", created.json()["employee_no"])

    def create_two_users_and_one_app(self):
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Employee(employee_no="64003", name="用户一", status="active"))
            db.add(self.models.Employee(employee_no="64004", name="用户二", status="active"))
            db.add(self.models.User(employee_no="64003", password_hash=self.models.hash_password("123456"), is_admin=False))
            db.add(self.models.User(employee_no="64004", password_hash=self.models.hash_password("123456"), is_admin=False))
            db.commit()
        finally:
            db.close()

        self.client.post("/api/auth/login", json={"employee_no": "64003", "password": "123456"})
        app_response = self.client.post("/api/apps")
        self.assertEqual(201, app_response.status_code)
        app_id = app_response.json()["id"]
        db = self.database.SessionLocal()
        try:
            app = db.query(self.models.App).filter(self.models.App.id == app_id).first()
            app.status = "active"
            db.commit()
        finally:
            db.close()
        self.client.post("/api/auth/logout")
        return app_id

    def test_user_only_sees_own_apps(self):
        app_id = self.create_two_users_and_one_app()

        self.client.post("/api/auth/login", json={"employee_no": "64004", "password": "123456"})
        apps = self.client.get("/api/apps")
        self.assertEqual([], apps.json())
        other_app = self.client.get(f"/api/apps/{app_id}")
        self.assertEqual(404, other_app.status_code)

    def test_generated_app_page_is_public_after_generation(self):
        app_id = self.create_two_users_and_one_app()
        html_dir = Path(self.tmp.name) / "data" / "apps" / app_id
        html_dir.mkdir(parents=True)
        (html_dir / "index.html").write_text("<html>owned</html>", encoding="utf-8")

        anonymous = self.client.get(f"/apps/{app_id}/")
        self.assertEqual(200, anonymous.status_code)
        self.assertIn("owned", anonymous.text)

        self.client.post("/api/auth/login", json={"employee_no": "64004", "password": "123456"})
        other_user = self.client.get(f"/apps/{app_id}/")
        self.assertEqual(200, other_user.status_code)
        self.assertIn("owned", other_user.text)

    def test_generated_project_files_are_public_after_generation(self):
        app_id = self.create_two_users_and_one_app()
        project_dir = Path(self.tmp.name) / "data" / "apps" / app_id / "project"
        project_dir.mkdir(parents=True)
        (project_dir / "index.html").write_text("<html><link rel='stylesheet' href='css/style.css'></html>", encoding="utf-8")
        (project_dir / "css").mkdir()
        (project_dir / "css" / "style.css").write_text("body { color: red; }", encoding="utf-8")

        anonymous_index = self.client.get(f"/generated/{app_id}/project/index.html")
        self.assertEqual(200, anonymous_index.status_code)
        self.assertIn("stylesheet", anonymous_index.text)

        anonymous_css = self.client.get(f"/generated/{app_id}/project/css/style.css")
        self.assertEqual(200, anonymous_css.status_code)
        self.assertEqual("no-store", anonymous_css.headers["cache-control"])
        self.assertEqual("body { color: red; }", anonymous_css.text)

        self.client.post("/api/auth/login", json={"employee_no": "64004", "password": "123456"})
        other_user = self.client.get(f"/generated/{app_id}/project/index.html")
        self.assertEqual(200, other_user.status_code)
        self.assertIn("stylesheet", other_user.text)

        traversal = self.client.get(f"/generated/{app_id}/project/../index.html")
        self.assertEqual(404, traversal.status_code)

    def test_generated_project_files_remain_accessible_while_editing_or_edit_failed(self):
        app_id = self.create_two_users_and_one_app()
        project_dir = Path(self.tmp.name) / "data" / "apps" / app_id / "project"
        project_dir.mkdir(parents=True)
        (project_dir / "index.html").write_text("<html>last good</html>", encoding="utf-8")

        self.client.post("/api/auth/login", json={"employee_no": "64003", "password": "123456"})
        db = self.database.SessionLocal()
        try:
            app = db.query(self.models.App).filter(self.models.App.id == app_id).first()
            app.version = 1
            app.status = "editing"
            db.commit()
        finally:
            db.close()

        editing_response = self.client.get(f"/generated/{app_id}/project/index.html")
        self.assertEqual(200, editing_response.status_code)
        self.assertIn("last good", editing_response.text)

        db = self.database.SessionLocal()
        try:
            app = db.query(self.models.App).filter(self.models.App.id == app_id).first()
            app.status = "edit_failed"
            db.commit()
        finally:
            db.close()

        failed_edit_response = self.client.get(f"/generated/{app_id}/project/index.html")
        self.assertEqual(200, failed_edit_response.status_code)
        self.assertIn("last good", failed_edit_response.text)

    def test_user_can_delete_own_app_with_conversations_and_files(self):
        app_id = self.create_two_users_and_one_app()
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Conversation(
                id="delete-conversation-1",
                app_id=app_id,
                role="user",
                content="删除测试",
            ))
            db.commit()
        finally:
            db.close()

        html_dir = Path(self.tmp.name) / "data" / "apps" / app_id
        html_dir.mkdir(parents=True)
        (html_dir / "index.html").write_text("<html>delete me</html>", encoding="utf-8")

        self.client.post("/api/auth/login", json={"employee_no": "64003", "password": "123456"})
        response = self.client.delete(f"/api/apps/{app_id}")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"ok": True}, response.json())

        db = self.database.SessionLocal()
        try:
            self.assertIsNone(db.query(self.models.App).filter(self.models.App.id == app_id).first())
            self.assertEqual(0, db.query(self.models.Conversation).filter(self.models.Conversation.app_id == app_id).count())
        finally:
            db.close()
        self.assertFalse(html_dir.exists())

    def test_user_cannot_delete_other_users_app(self):
        app_id = self.create_two_users_and_one_app()

        self.client.post("/api/auth/login", json={"employee_no": "64004", "password": "123456"})
        response = self.client.delete(f"/api/apps/{app_id}")
        self.assertEqual(404, response.status_code)

        db = self.database.SessionLocal()
        try:
            self.assertIsNotNone(db.query(self.models.App).filter(self.models.App.id == app_id).first())
        finally:
            db.close()

    def test_background_generation_saves_project_files(self):
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Employee(employee_no="64014", name="项目测试", status="active"))
            db.add(self.models.User(
                employee_no="64014",
                password_hash=self.models.hash_password("123456"),
                is_admin=False,
            ))
            db.commit()
        finally:
            db.close()

        self.client.post("/api/auth/login", json={"employee_no": "64014", "password": "123456"})
        create_resp = self.client.post("/api/apps")
        self.assertEqual(201, create_resp.status_code)
        app_id = create_resp.json()["id"]

        import asyncio
        from unittest.mock import patch
        from config import Settings
        from services import ai_service, app_service

        project_reply = '{"files":[{"path":"index.html","content":"<html><link rel=\\"stylesheet\\" href=\\"css/style.css\\"></html>"},{"path":"css/style.css","content":"body { color: green; }"}]}'

        async def stream_project(messages, settings):
            yield project_reply

        db_gen = self.database.SessionLocal()
        try:
            app = db_gen.query(self.models.App).filter(self.models.App.id == app_id).first()
            with patch.object(ai_service, "stream_chat", stream_project):
                with patch.object(ai_service, "non_streaming_chat", return_value="项目"):
                    events = []
                    async def _run():
                        async for event in app_service.handle_chat(app, "生成多页面项目", db_gen, Settings()):
                            events.append(event)
                    asyncio.run(_run())
        finally:
            db_gen.close()

        project_dir = Path(self.tmp.name) / "data" / "apps" / app_id / "project"
        self.assertEqual("body { color: green; }", (project_dir / "css" / "style.css").read_text(encoding="utf-8"))
        self.assertTrue(any(f"/generated/{app_id}/project/index.html" in event for event in events))

    def test_background_generation_finishes_after_disconnect(self):
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Employee(employee_no="64013", name="后台测试", status="active"))
            db.add(self.models.User(
                employee_no="64013",
                password_hash=self.models.hash_password("123456"),
                is_admin=False,
            ))
            db.commit()
        finally:
            db.close()

        self.client.post("/api/auth/login", json={"employee_no": "64013", "password": "123456"})
        create_resp = self.client.post("/api/apps")
        self.assertEqual(201, create_resp.status_code)
        app_id = create_resp.json()["id"]

        import asyncio
        import threading
        from unittest.mock import patch
        from services import ai_service

        html_body = "```html\n<!DOCTYPE html><html><body>Hello</body></html>\n```"

        async def slow_stream(messages, settings):
            for word in html_body.split():
                yield word + " "
            yield "\n"

        generation_done = threading.Event()

        def run_generation():
            async def _run():
                from database import SessionLocal as SL
                from models import App as AppModel
                from config import Settings
                from services import app_service
                db_gen = SL()
                try:
                    app = db_gen.query(AppModel).filter(AppModel.id == app_id).first()
                    with patch.object(ai_service, "stream_chat", slow_stream):
                        with patch.object(ai_service, "non_streaming_chat", return_value="测试"):
                            async for _ in app_service.handle_chat(app, "生成测试页", db_gen, Settings()):
                                pass
                finally:
                    db_gen.close()
                    generation_done.set()

            loop = asyncio.new_event_loop()
            loop.run_until_complete(_run())
            loop.close()

        t = threading.Thread(target=run_generation, daemon=True)
        t.start()
        generation_done.wait(timeout=10)
        t.join(timeout=5)

        db = self.database.SessionLocal()
        try:
            app = db.query(self.models.App).filter(self.models.App.id == app_id).first()
            self.assertEqual("active", app.status)
            self.assertIsNone(app.progress)
            self.assertEqual(1, app.version)

            conv_count = db.query(self.models.Conversation).filter(self.models.Conversation.app_id == app_id).count()
            self.assertGreaterEqual(conv_count, 2)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
