# Error Handling

> How errors are handled in this project.

---

## Overview

The backend primarily uses FastAPI `HTTPException` for expected API errors and lets FastAPI produce the standard JSON response. There are no custom API error classes or global exception handlers in the current codebase.

Expected errors should be returned close to where validation/authorization fails. Unexpected errors are usually caught only around external or long-running generation work so the app can update generation status and keep the SSE stream well-formed.

---

## Error Types

- Expected client/auth/resource errors use `fastapi.HTTPException` with `status_code` and `detail`.
  - 400 for invalid input such as inactive/missing style or bad collection name.
  - 401 for unauthenticated or expired sessions.
  - 403 for active authentication but missing permission or unopened employee number.
  - 404 for missing apps/files/records, including unsafe generated file paths.
  - 409 for duplicate registration/employee numbers.
  - 413 for oversized generated app data payloads.
- Pydantic `BaseModel` request classes provide basic body shape validation.
- Service/file validation functions may raise `ValueError` for internal unsafe states; route code translates those to `HTTPException` when exposed over HTTP. Example: `main.py` catches `ValueError` from `code_service.resolve_project_file()` and returns 404.

---

## Error Handling Patterns

- Validate existence and authorization before performing mutations. Examples: `/backend/routers/apps.py` returns 404 when an app does not belong to the current user; `/backend/services/auth_service.py` returns 401 when a session is missing, expired, or tied to a disabled employee.
- Use Chinese `detail` strings for user-facing auth/admin validation messages where the existing UI displays them (`工号未开通`, `账号已注册`, `风格不存在`). Some internal/resource details remain English (`App not found`, `Not authenticated`); match the nearby route's existing language.
- For generated app file serving, hide unsafe paths and inaccessible apps as 404 rather than exposing path validation details. See `/backend/main.py`.
- For generated app data, keep validation helper functions small and explicit: `validate_collection()` raises 400, `encode_payload()` raises 413, `get_record()` raises 404 in `/backend/routers/app_data.py`.
- For LLM/generation failures, catch broad `Exception` in `/backend/services/app_service.py`, set `App.status` to `failed` or `edit_failed`, clear `progress`, record failed usage when possible, commit, and publish a final SSE `result` event.
- For optional non-critical work, failures may be swallowed. Example: `_set_app_name()` ignores naming failures so generation can continue.

---

## API Error Responses

FastAPI's default error response shape is used:

```json
{"detail": "App not found"}
```

Do not introduce a different envelope for one endpoint unless the whole API is being changed. Successful mutation/delete responses commonly return `{"ok": true}` (logout, delete app data, delete style) or a Pydantic response model.

SSE chat endpoints are different: `/backend/services/app_service.py` sends events formatted as:

```text
event: message
data: {"content":"..."}

```

and always attempts to finish with:

```text
event: result
data: {"url": null, "status": "failed"}

```

---

## Common Mistakes

- Do not let unsafe file path details leak to clients; convert to 404 like `serve_generated_project_file()`.
- Do not leave apps stuck in `creating`/`editing` after generation exceptions; set a terminal failure status and commit.
- Do not return plain strings for API errors; raise `HTTPException`.
- Do not add custom exception classes without also documenting and applying a consistent FastAPI handler.
- Do not swallow errors that are required for user feedback, except for explicitly non-critical best-effort work like app naming.
