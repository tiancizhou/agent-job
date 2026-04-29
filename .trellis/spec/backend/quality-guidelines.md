# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

Backend code is small, direct FastAPI + SQLAlchemy code. Prefer readable functions, explicit validation, and tests for security-sensitive behavior over new abstractions.

Development commands from `/CLAUDE.md`:

```bash
cd backend && .venv/Scripts/python -m pytest tests/ -v
```

There is no separate backend lint/typecheck command configured in the repo at bootstrap time.

---

## Forbidden Patterns

- Do not bypass authentication dependencies for user-owned `/api` routes. Use `current_user: User = Depends(get_current_user)` or `Depends(require_admin)` as appropriate.
- Do not query or mutate user-owned apps without `App.user_id == current_user.id`, except public generated-app serving and generated-app data endpoints that intentionally use app status/version access rules.
- Do not write generated files from LLM output without `code_service` path validation. Preserve `is_safe_project_path()` and `resolve_project_file()` checks.
- Do not accept absolute paths, traversal paths, Windows drive paths, backslashes, unsupported extensions, too many files, or oversized files for generated projects.
- Do not allow generated Next.js projects to declare server/runtime paths (`app/api/*`, `pages/api/*`, middleware, route handlers) or unsafe `package.json` scripts/dependencies/version specifiers.
- Do not store generated app user data in local files or localStorage from backend code; persistence goes through `AppDataRecord` and `/api/generated/{app_id}/data/{collection}`.
- Do not add new dependencies or framework layers unless the feature clearly requires them.
- Do not commit secrets or `.env` values.

---

## Required Patterns

- Use `settings` from `/backend/config.py` for configurable values (`DATA_DIR`, `DATABASE_URL`, LLM settings, generation concurrency).
- Use `db: Session = Depends(get_db)` in request handlers and explicit `db.commit()`/`db.refresh()` after mutations.
- Keep response models on routes where existing routes use them (`response_model=AppResponse`, `list[EmployeeResponse]`, etc.).
- Preserve cookie-based auth behavior in `auth_service.py`: HTTP-only `quickapp_session`, 7-day expiry, active employee check.
- Preserve generated app cache busting/serving contract: generated project files are served under `/generated/{app_id}/project/...` with `Cache-Control: no-store`.
- For chat/generation, preserve SSE event names expected by the frontend: `message`, `progress`, and `result`.
- Keep LLM-generated project requirements in sync with tests and code: generation must include the fixed Next.js App Router + TypeScript MVP source files, build with static export enabled, use nested-preview-safe `_next` asset paths, and publish only built `out/` artifacts to `project/` for preview.

---

## Testing Requirements

- Add or update backend tests for auth/authorization changes, DB/migration changes, generated file safety, app data persistence, usage accounting, and token/LLM parsing.
- Tests are currently `unittest.TestCase` classes run by pytest. Follow existing style in `/backend/tests/test_auth.py`, `/backend/tests/test_code_service.py`, and `/backend/tests/test_app_data.py`.
- Tests that import the FastAPI app should set required LLM env vars and use temporary directories/databases, as in `load_app()` in `/backend/tests/test_auth.py`.
- Pure service helpers should be tested directly without starting the app when possible, as in `/backend/tests/test_code_service.py`.

---

## Code Review Checklist

Review backend changes for:

- Correct route placement and router registration in `/backend/main.py`.
- Correct auth dependency and ownership filters.
- Safe DB transaction boundaries and session lifecycle.
- Alembic migration included and aligned with `/backend/models.py` for schema changes.
- No sensitive data logged or returned.
- Generated file and generated app data limits preserved.
- SSE stream completion and app status transitions remain consistent on success/failure.
- Relevant tests added/updated and passing.

## Impact Radius Analysis

Before finishing a backend change, classify the impact radius and expand verification accordingly:

- L1: Local helper or implementation detail in one backend module. Verify the focused tests for that helper/module.
- L2: One API/service feature area. Verify route tests and the related service behavior, including expected `HTTPException` details.
- L3: Database model, migration, auth/session, generated file safety, or app data persistence. Verify migrations/tests and any frontend API types that mirror changed response shapes.
- L4: Cross-layer behavior touching backend API contracts plus frontend usage. Trace request/response/error flow through `/backend/routers/`, `/backend/services/`, `/frontend/src/api/index.ts`, and affected Vue components.
- L5: App-wide contracts such as authentication, generation/SSE, generated app serving, or production build/static serving. Run both backend tests and frontend build where feasible, and manually reason through deployment/runtime effects.

For this bootstrap-guidelines task itself, the intended impact radius is documentation/spec only. If code outside `.trellis/spec/` or `.trellis/tasks/00-bootstrap-guidelines/` changes, treat it as out of scope unless explicitly justified.

---

## Real Examples

- `/backend/routers/apps.py`: authenticated app CRUD with ownership filters.
- `/backend/services/auth_service.py`: session validation and admin dependency.
- `/backend/services/code_service.py`: generated file validation and safe path resolution.
- `/backend/tests/test_auth.py`: end-to-end auth and access-control tests with `TestClient`.
- `/backend/tests/test_code_service.py`: focused validation tests for LLM project file parsing.
