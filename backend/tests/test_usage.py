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


def load_database(tmpdir: str):
    old_cwd = os.getcwd()
    os.chdir(tmpdir)
    sys.path.insert(0, str(BACKEND_DIR))
    os.environ["LLM_API_KEY"] = "test-key"
    os.environ["LLM_BASE_URL"] = "https://example.test"
    os.environ["LLM_MODEL"] = "test-model"
    for name in list(sys.modules):
        if name in {"database", "models"}:
            sys.modules.pop(name, None)
    try:
        database = importlib.import_module("database")
        models = importlib.import_module("models")
        command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
        return database, models
    finally:
        os.chdir(old_cwd)


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


class UsageRecordTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database, self.models = load_database(self.tmp.name)

    def tearDown(self):
        self.database.engine.dispose()
        self.tmp.cleanup()

    def test_usage_record_can_store_token_consumption(self):
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Employee(employee_no="64021", name="用户一", status="active"))
            db.add(self.models.User(
                id="user-1",
                employee_no="64021",
                password_hash=self.models.hash_password("123456"),
                is_admin=False,
            ))
            db.commit()
            db.add(self.models.App(id="app-1", user_id="user-1", name="应用一", status="active", version=1))
            db.commit()
            record = self.models.UsageRecord(
                user_id="user-1",
                app_id="app-1",
                action="generate",
                provider="deepseek",
                model="deepseek-chat",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                is_estimated=True,
                status="success",
            )
            db.add(record)
            db.commit()

            saved = db.query(self.models.UsageRecord).filter(self.models.UsageRecord.user_id == "user-1").first()
            self.assertIsNotNone(saved)
            self.assertEqual("app-1", saved.app_id)
            self.assertEqual("generate", saved.action)
            self.assertEqual("deepseek", saved.provider)
            self.assertEqual("deepseek-chat", saved.model)
            self.assertEqual(0, float(saved.cost))
            self.assertEqual(100, saved.prompt_tokens)
            self.assertEqual(50, saved.completion_tokens)
            self.assertEqual(150, saved.total_tokens)
            self.assertTrue(saved.is_estimated)
            self.assertEqual("success", saved.status)
            self.assertIsNotNone(saved.created_at)
            self.assertIsNotNone(saved.updated_at)
        finally:
            db.close()


class UsageApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app, database, models = load_app(self.tmp.name)
        self.client = TestClient(app)
        self.database = database
        self.models = models

    def tearDown(self):
        self.database.engine.dispose()
        self.tmp.cleanup()

    def seed_users(self):
        db = self.database.SessionLocal()
        try:
            db.add(self.models.Employee(employee_no="64021", name="用户一", status="active"))
            db.add(self.models.Employee(employee_no="64022", name="用户二", status="active"))
            user_one = self.models.User(
                id="user-one",
                employee_no="64021",
                password_hash=self.models.hash_password("123456"),
                is_admin=False,
            )
            user_two = self.models.User(
                id="user-two",
                employee_no="64022",
                password_hash=self.models.hash_password("123456"),
                is_admin=False,
            )
            db.add(user_one)
            db.add(user_two)
            db.commit()
        finally:
            db.close()

    def login_user_one(self):
        response = self.client.post("/api/auth/login", json={"employee_no": "64021", "password": "123456"})
        self.assertEqual(200, response.status_code)

    def seed_usage_records(self):
        base_time = datetime(2026, 4, 25, 10, 0, 0)
        db = self.database.SessionLocal()
        try:
            db.add(self.models.App(id="app-one", user_id="user-one", name="报名页", status="active", version=1))
            db.add(self.models.UsageRecord(
                id="usage-old",
                user_id="user-one",
                app_id="app-one",
                action="generate",
                provider="deepseek",
                model="deepseek-chat",
                prompt_tokens=100,
                completion_tokens=40,
                total_tokens=140,
                is_estimated=False,
                status="success",
                created_at=base_time,
            ))
            db.add(self.models.UsageRecord(
                id="usage-new",
                user_id="user-one",
                app_id=None,
                action="edit",
                provider="deepseek",
                model="deepseek-chat",
                prompt_tokens=30,
                completion_tokens=20,
                total_tokens=50,
                is_estimated=True,
                status="failed",
                created_at=base_time + timedelta(minutes=5),
            ))
            db.add(self.models.UsageRecord(
                id="usage-other-user",
                user_id="user-two",
                app_id=None,
                action="generate",
                provider="deepseek",
                model="deepseek-chat",
                prompt_tokens=999,
                completion_tokens=999,
                total_tokens=1998,
                is_estimated=False,
                status="success",
                created_at=base_time + timedelta(minutes=10),
            ))
            db.commit()
        finally:
            db.close()

    def test_created_app_has_project_defaults(self):
        self.seed_users()
        self.login_user_one()

        response = self.client.post("/api/apps", json={})

        self.assertEqual(201, response.status_code)
        app = response.json()
        self.assertEqual("index.html", app["entry_path"])
        self.assertEqual("project", app["project_type"])
        self.assertEqual("private", app["visibility"])
        self.assertIsNone(app["preview_token"])

    def test_usage_endpoints_require_login(self):
        summary = self.client.get("/api/usage/summary")
        records = self.client.get("/api/usage/records")

        self.assertEqual(401, summary.status_code)
        self.assertEqual(401, records.status_code)

    def test_usage_summary_returns_zeroes_for_user_without_records(self):
        self.seed_users()
        self.login_user_one()

        response = self.client.get("/api/usage/summary")

        self.assertEqual(200, response.status_code)
        self.assertEqual({
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "record_count": 0,
            "estimated_record_count": 0,
            "successful_record_count": 0,
            "failed_record_count": 0,
            "first_record_at": None,
            "last_record_at": None,
        }, response.json())

    def test_usage_summary_aggregates_only_current_user_records(self):
        self.seed_users()
        self.seed_usage_records()
        self.login_user_one()

        response = self.client.get("/api/usage/summary")

        self.assertEqual(200, response.status_code)
        summary = response.json()
        self.assertEqual(130, summary["prompt_tokens"])
        self.assertEqual(60, summary["completion_tokens"])
        self.assertEqual(190, summary["total_tokens"])
        self.assertEqual(2, summary["record_count"])
        self.assertEqual(1, summary["estimated_record_count"])
        self.assertEqual(1, summary["successful_record_count"])
        self.assertEqual(1, summary["failed_record_count"])
        self.assertIsNotNone(summary["first_record_at"])
        self.assertIsNotNone(summary["last_record_at"])

    def test_usage_records_are_user_scoped_ordered_and_include_optional_app_name(self):
        self.seed_users()
        self.seed_usage_records()
        self.login_user_one()

        response = self.client.get("/api/usage/records")

        self.assertEqual(200, response.status_code)
        records = response.json()
        self.assertEqual(["usage-new", "usage-old"], [record["id"] for record in records])
        self.assertIsNone(records[0]["app_id"])
        self.assertIsNone(records[0]["app_name"])
        self.assertEqual("deepseek", records[0]["provider"])
        self.assertEqual(0, records[0]["cost"])
        self.assertIn("updated_at", records[0])
        self.assertEqual("报名页", records[1]["app_name"])
        self.assertNotIn("usage-other-user", [record["id"] for record in records])

    def test_usage_records_do_not_expose_other_users_app_name(self):
        self.seed_users()
        db = self.database.SessionLocal()
        try:
            db.add(self.models.App(id="app-two", user_id="user-two", name="他人应用", status="active", version=1))
            db.add(self.models.UsageRecord(
                id="usage-stale",
                user_id="user-one",
                app_id="app-two",
                action="generate",
                provider="deepseek",
                model="deepseek-chat",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                is_estimated=False,
                status="success",
                created_at=datetime(2026, 4, 25, 11, 0, 0),
            ))
            db.commit()
        finally:
            db.close()
        self.login_user_one()

        response = self.client.get("/api/usage/records")

        self.assertEqual(200, response.status_code)
        records = response.json()
        self.assertEqual("usage-stale", records[0]["id"])
        self.assertIsNone(records[0]["app_name"])

    def test_usage_records_support_limit_and_offset(self):
        self.seed_users()
        self.seed_usage_records()
        self.login_user_one()

        response = self.client.get("/api/usage/records?limit=1&offset=1")

        self.assertEqual(200, response.status_code)
        records = response.json()
        self.assertEqual(1, len(records))
        self.assertEqual("usage-old", records[0]["id"])


if __name__ == "__main__":
    unittest.main()
