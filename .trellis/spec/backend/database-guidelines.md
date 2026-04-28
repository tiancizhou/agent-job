# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

The backend uses SQLAlchemy 2-style ORM imports with classic `Column(...)` model definitions. The default database is SQLite (`sqlite:///./quickapp.db`), with PostgreSQL supported through `DATABASE_URL`.

Current DB conventions:

- Engine/session/Base live in `/backend/database.py`.
- ORM models live in `/backend/models.py`.
- Alembic migrations live in `/backend/alembic/versions/`.
- Request handlers receive `db: Session = Depends(get_db)` for request-scoped sessions.
- Background generation code that outlives a request opens its own `SessionLocal()` and closes it in `finally` (`/backend/services/app_service.py`).
- Timestamps use `now_utc()` and the shared `DB_DATETIME` type in `/backend/models.py`, with a SQLite-specific storage format that omits microseconds.

---

## Query Patterns

- Use `db.query(Model).filter(...).first()` for single-row lookups. Examples: `/backend/routers/auth.py` looks up `Employee` and `User`; `/backend/routers/apps.py` looks up apps by both `App.id` and `App.user_id`.
- Always enforce ownership in the query for user-owned resources. Example: `/backend/routers/apps.py` filters `App.id == app_id, App.user_id == current_user.id` for get/update/delete operations.
- Use `.order_by(...).all()` for ordered lists. Examples: apps by `App.updated_at.desc()`, conversations by `Conversation.created_at`, styles by `Style.sort_order.asc(), Style.created_at.desc()`.
- Use SQLAlchemy aggregate functions for summary endpoints. `/backend/routers/usage.py` uses `func.sum`, `func.count`, `case`, `func.min`, and `func.max` to build the usage summary.
- After creating or mutating ORM objects, call `db.commit()` and `db.refresh(obj)` before returning when the caller needs generated/default values. Examples: `create_app`, `create_employee`, `create_style`, `create_app_data_record`.
- Use bulk operations only where current code already does so for simple cascading state changes, such as deleting sessions when an employee is disabled or nulling style references before deleting a style.

---

## Transactions and Sessions

- Request handlers rely on explicit commits. There is no automatic unit-of-work wrapper around requests.
- Do not keep request-scoped sessions in long-running background tasks. `app_service._run_html_generation()` correctly creates a fresh `SessionLocal()` and closes it in `finally`.
- When deleting or updating dependent data, commit in the same handler once all related changes are made. Examples: `/backend/routers/admin.py` disables an employee and deletes sessions before one commit; `delete_style` nulls `App.style_id`, deletes the style, then commits.
- For generated app data updates, manually set `updated_at = now_utc()` when replacing the JSON payload (`/backend/routers/app_data.py`).

---

## Migrations

- Alembic is the source of schema changes. Add a new file under `/backend/alembic/versions/` instead of relying only on `Base.metadata.create_all()`.
- Migrations define explicit `revision`, `down_revision`, `upgrade()`, and `downgrade()` values, as in `0001_initial_schema.py` and `0002_app_data_records.py`.
- Keep migration column definitions aligned with `/backend/models.py`, especially `DB_DATETIME`, check constraints, foreign key `ondelete`, indexes, and nullable settings.
- Startup uses `/backend/prepare_database.py`/Alembic per project docs; tests run migrations in temporary directories before importing the app (`/backend/tests/test_auth.py`).

---

## Naming Conventions

- Table names are plural snake_case: `employees`, `users`, `sessions`, `styles`, `apps`, `conversations`, `usage_records`, `app_data_records`.
- Column names are snake_case: `employee_no`, `password_hash`, `is_admin`, `created_at`, `updated_at`, `preview_token`.
- String UUID primary keys use `String(36)` and `_uuid()` defaults unless an ID is explicitly assigned.
- Status-like columns are strings constrained with `CheckConstraint`; allowed values are also listed as module constants in `/backend/models.py` (`APP_STATUSES`, `USAGE_ACTIONS`, etc.).
- Index names use `ix_<table>_<columns>`: `ix_apps_user_updated`, `ix_conversations_app_created`, `ix_app_data_records_app_collection_created`.
- Check names use `ck_<table>_<column-or-purpose>`: `ck_apps_status`, `ck_usage_records_total_tokens`.

---

## Common Mistakes

- Do not query user-owned objects by ID only in authenticated routes; include the owner filter to avoid cross-user access.
- Do not add new DB columns only to `/backend/models.py`; add and test an Alembic migration too.
- Do not use raw JSON objects in `AppDataRecord.payload`; the current schema stores compact JSON as `Text` and validates size before writing.
- Do not bypass `get_db()` in request handlers unless you are intentionally outside a request lifecycle.
- Do not assume SQLite cascades are disabled; `/backend/database.py` enables `PRAGMA foreign_keys=ON` for SQLite connections.
