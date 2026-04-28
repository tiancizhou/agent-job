# Directory Structure

> How backend code is organized in this project.

---

## Overview

The backend is a flat FastAPI application under `/backend`, not a packaged `src/` layout. Modules use direct imports such as `from database import get_db` and `from services import app_service` because the app is run from the backend directory.

Keep new backend code in the existing layers:

- `/backend/main.py` wires the FastAPI app, middleware, routers, generated-file serving, and frontend static serving.
- `/backend/routers/` contains HTTP endpoint modules. Routes are grouped by product area (`auth.py`, `apps.py`, `chat.py`, `admin.py`, `app_data.py`, `styles.py`, `usage.py`).
- `/backend/services/` contains reusable business/integration logic that is not tied to one request handler (`app_service.py`, `ai_service.py`, `auth_service.py`, `code_service.py`, `token_service.py`).
- `/backend/models.py` contains both SQLAlchemy ORM models and Pydantic response/request models.
- `/backend/database.py` owns engine/session/Base setup and the `get_db()` dependency.
- `/backend/config.py` owns Pydantic settings loaded from `.env`.
- `/backend/alembic/versions/` contains migrations.
- `/backend/tests/` contains Python `unittest`/pytest-compatible tests.

---

## Directory Layout

```text
/backend
├── main.py                  # FastAPI app composition and static/generated file routes
├── config.py                # pydantic-settings configuration
├── database.py              # SQLAlchemy engine/session/Base/get_db
├── models.py                # ORM models plus Pydantic API schemas
├── prepare_database.py      # startup migration/bootstrap helper
├── routers/                 # APIRouter endpoint modules
│   ├── auth.py
│   ├── apps.py
│   ├── chat.py
│   ├── admin.py
│   ├── app_data.py
│   ├── styles.py
│   └── usage.py
├── services/                # business logic and external integrations
│   ├── app_service.py
│   ├── ai_service.py
│   ├── auth_service.py
│   ├── code_service.py
│   └── token_service.py
├── alembic/versions/        # schema migrations
└── tests/                   # backend tests
```

---

## Module Organization

- Put new HTTP endpoints in a focused module under `/backend/routers/` and register the router in `/backend/main.py` with `app.include_router(..., prefix="/api")` unless the route intentionally lives outside `/api` (examples: generated app file serving in `main.py`).
- Keep request handlers thin: validate request/user ownership, call services for orchestration, perform simple DB reads/writes, then return ORM/Pydantic responses. Examples: `/backend/routers/chat.py` delegates streaming work to `app_service.handle_chat()`, and `/backend/routers/apps.py` delegates generated-project path logic to `code_service`.
- Put cross-route helpers in `/backend/services/`. Examples: authentication dependencies in `/backend/services/auth_service.py`, LLM calls in `/backend/services/ai_service.py`, and generated file parsing/safety in `/backend/services/code_service.py`.
- Keep DB models and API schemas in `/backend/models.py` to match the current codebase. Do not introduce a separate `schemas/` package unless doing a larger refactor.
- For generated files, preserve the existing storage convention: `settings.DATA_DIR/apps/{app_id}/project/` for multi-file generated projects, accessed through `code_service.project_dir_for()` and `code_service.resolve_project_file()`.

---

## Naming Conventions

- Router files use lowercase snake_case names matching the resource area: `app_data.py`, `usage.py`.
- Service files use lowercase snake_case with `_service` suffix when they are feature services: `app_service.py`, `auth_service.py`, `ai_service.py`, `code_service.py`.
- FastAPI route functions use action-oriented snake_case names: `list_apps`, `create_app`, `get_usage_summary`, `list_app_data_records`.
- Internal helper functions use a leading underscore when private to a module: `_sse`, `_publish`, `_record_usage`, `_can_serve_generated_files`.
- API paths are plural nouns where applicable (`/apps`, `/admin/employees`, `/usage/records`) and generated app persistence endpoints are under `/generated/{app_id}/data/{collection}`.

---

## Examples

- `/backend/routers/apps.py` is the main example for CRUD-style authenticated routes: dependency-injected `current_user`, `db: Session`, ownership filters, `HTTPException`, commit/refresh, and Pydantic response models.
- `/backend/routers/app_data.py` is the example for endpoint-local validation helpers (`validate_collection`, `encode_payload`) and manual response object construction (`record_response`).
- `/backend/services/app_service.py` is the example for longer orchestration: SSE formatting, generation state, async LLM streaming, DB updates, and usage recording.
- `/backend/services/code_service.py` is the example for file-system safety helpers and pure functions with focused tests in `/backend/tests/test_code_service.py`.
