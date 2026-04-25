import importlib
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
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
        database = importlib.import_module("database")
        models = importlib.import_module("models")
        command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
        return main.app, database, models
    finally:
        os.chdir(old_cwd)


class GeneratedAppDataApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app, database, models = load_app(self.tmp.name)
        self.client = TestClient(app)
        self.database = database
        self.models = models
        self.seed_users_and_apps()

    def tearDown(self):
        self.database.engine.dispose()
        self.tmp.cleanup()

    def seed_users_and_apps(self):
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Employee(employee_no="64021", name="用户一", status="active"))
            db.add(self.models.User(
                id="user-one",
                employee_no="64021",
                password_hash=self.models.hash_password("123456"),
                is_admin=False,
            ))
            db.commit()
            db.add(self.models.App(id="app-active", user_id="user-one", name="可用应用", status="active", version=1))
            db.add(self.models.App(id="app-editing", user_id="user-one", name="编辑中应用", status="editing", version=1))
            db.add(self.models.App(id="app-edit-failed", user_id="user-one", name="编辑失败应用", status="edit_failed", version=1))
            db.add(self.models.App(id="app-creating", user_id="user-one", name="创建中应用", status="creating", version=0))
            db.add(self.models.App(id="app-failed", user_id="user-one", name="失败应用", status="failed", version=0))
            db.add(self.models.App(id="app-other", user_id="user-one", name="另一个应用", status="active", version=1))
            db.commit()
        finally:
            db.close()

    def test_active_app_can_create_read_update_and_delete_collection_records(self):
        create_response = self.client.post(
            "/api/generated/app-active/data/todos",
            json={"data": {"title": "买咖啡", "done": False}},
        )

        self.assertEqual(201, create_response.status_code)
        created = create_response.json()
        self.assertEqual("app-active", created["app_id"])
        self.assertEqual("todos", created["collection"])
        self.assertEqual({"title": "买咖啡", "done": False}, created["data"])

        detail_response = self.client.get(f"/api/generated/app-active/data/todos/{created['id']}")
        self.assertEqual(200, detail_response.status_code)
        self.assertEqual(created["id"], detail_response.json()["id"])

        update_response = self.client.put(
            f"/api/generated/app-active/data/todos/{created['id']}",
            json={"data": {"title": "买咖啡", "done": True}},
        )
        self.assertEqual(200, update_response.status_code)
        self.assertEqual({"title": "买咖啡", "done": True}, update_response.json()["data"])

        list_response = self.client.get("/api/generated/app-active/data/todos")
        self.assertEqual(200, list_response.status_code)
        self.assertEqual([created["id"]], [record["id"] for record in list_response.json()])

        delete_response = self.client.delete(f"/api/generated/app-active/data/todos/{created['id']}")
        self.assertEqual(200, delete_response.status_code)
        self.assertEqual({"ok": True}, delete_response.json())

        missing_response = self.client.get(f"/api/generated/app-active/data/todos/{created['id']}")
        self.assertEqual(404, missing_response.status_code)

    def test_editing_and_edit_failed_apps_with_existing_versions_can_access_data(self):
        editing_response = self.client.post("/api/generated/app-editing/data/notes", json={"data": {"text": "编辑中"}})
        edit_failed_response = self.client.post("/api/generated/app-edit-failed/data/notes", json={"data": {"text": "编辑失败"}})

        self.assertEqual(201, editing_response.status_code)
        self.assertEqual(201, edit_failed_response.status_code)

    def test_inactive_or_missing_apps_cannot_access_data(self):
        for app_id in ["app-creating", "app-failed", "missing-app"]:
            response = self.client.get(f"/api/generated/{app_id}/data/todos")
            self.assertEqual(404, response.status_code)

    def test_records_are_isolated_by_app_and_collection(self):
        app_record = self.client.post("/api/generated/app-active/data/todos", json={"data": {"title": "本应用"}}).json()
        self.client.post("/api/generated/app-other/data/todos", json={"data": {"title": "其他应用"}})
        self.client.post("/api/generated/app-active/data/notes", json={"data": {"title": "其他集合"}})

        list_response = self.client.get("/api/generated/app-active/data/todos")
        self.assertEqual(200, list_response.status_code)
        self.assertEqual([app_record["id"]], [record["id"] for record in list_response.json()])

        cross_app_response = self.client.get(f"/api/generated/app-other/data/todos/{app_record['id']}")
        cross_collection_response = self.client.get(f"/api/generated/app-active/data/notes/{app_record['id']}")
        self.assertEqual(404, cross_app_response.status_code)
        self.assertEqual(404, cross_collection_response.status_code)

    def test_collection_name_must_be_safe(self):
        for collection in ["../todos", "todo/list", "中文", "has space"]:
            response = self.client.get(f"/api/generated/app-active/data/{collection}")
            self.assertIn(response.status_code, {400, 404, 422})

    def test_payload_must_be_json_object(self):
        for payload in [["todo"], "todo", 123]:
            response = self.client.post("/api/generated/app-active/data/todos", json={"data": payload})
            self.assertEqual(422, response.status_code)

    def test_payload_size_is_limited_and_not_saved(self):
        response = self.client.post(
            "/api/generated/app-active/data/todos",
            json={"data": {"text": "x" * (65 * 1024)}},
        )

        self.assertIn(response.status_code, {400, 413})
        db = self.database.SessionLocal()
        try:
            self.assertEqual(0, db.query(self.models.AppDataRecord).count())
        finally:
            db.close()

    def test_list_supports_limit_offset_and_created_desc_order(self):
        base_time = datetime(2026, 4, 25, 10, 0, 0)
        db = self.database.SessionLocal()
        try:
            for index in range(3):
                db.add(self.models.AppDataRecord(
                    id=f"record-{index}",
                    app_id="app-active",
                    collection="todos",
                    payload=f'{{"index": {index}}}',
                    created_at=base_time + timedelta(minutes=index),
                ))
            db.commit()
        finally:
            db.close()

        response = self.client.get("/api/generated/app-active/data/todos?limit=1&offset=1")

        self.assertEqual(200, response.status_code)
        records = response.json()
        self.assertEqual(1, len(records))
        self.assertEqual("record-1", records[0]["id"])
        self.assertEqual({"index": 1}, records[0]["data"])

    def test_deleting_app_cascades_app_data_records(self):
        self.client.post("/api/generated/app-active/data/todos", json={"data": {"title": "待删除"}})
        db = self.database.SessionLocal()
        try:
            self.assertEqual(1, db.query(self.models.AppDataRecord).filter(self.models.AppDataRecord.app_id == "app-active").count())
            app = db.query(self.models.App).filter(self.models.App.id == "app-active").first()
            db.delete(app)
            db.commit()
            self.assertEqual(0, db.query(self.models.AppDataRecord).filter(self.models.AppDataRecord.app_id == "app-active").count())
        finally:
            db.close()

    def test_update_and_delete_missing_records_return_404(self):
        update_response = self.client.put(
            "/api/generated/app-active/data/todos/missing-record",
            json={"data": {"title": "不存在"}},
        )
        delete_response = self.client.delete("/api/generated/app-active/data/todos/missing-record")

        self.assertEqual(404, update_response.status_code)
        self.assertEqual(404, delete_response.status_code)


if __name__ == "__main__":
    unittest.main()
