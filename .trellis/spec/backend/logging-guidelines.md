# Logging Guidelines

> How logging is done in this project.

---

## Overview

The current backend does not define an application logging wrapper and does not call `logging.getLogger(...)` in app modules. Runtime logging is mostly provided by Uvicorn/FastAPI, Alembic, and test output. When adding logs, keep them minimal and use Python's standard `logging` module rather than introducing a new logging dependency.

Because this product handles employee identifiers, session cookies, prompts, generated code, and LLM API keys, logs must avoid sensitive content by default.

---

## Log Levels

If new logging is necessary, use conventional Python levels:

- `debug`: local-only details that are useful while diagnosing parsing or branching. Avoid in normal production paths.
- `info`: major lifecycle events such as startup/migration success or a generation task reaching a terminal state, without prompt or code content.
- `warning`: recoverable unusual states, such as malformed upstream SSE chunks or non-critical provider metadata missing.
- `error`/`exception`: unexpected failures where the request/task cannot complete. Use `logger.exception(...)` only inside an `except` block and sanitize context.

Do not replace existing client-visible `HTTPException` handling with log-only behavior.

---

## Structured Logging

There is no structured logging format in the current repo. If adding logs, prefer stable key/value context in the message or `extra` fields while keeping values non-sensitive.

Acceptable context examples:

- `app_id`
- `user_id` only when needed for backend diagnostics; prefer internal UUID over employee number
- route/action name such as `generate`, `edit`, `name`
- final status such as `active`, `failed`, `edit_failed`
- token counts from `UsageRecord` if not tied to prompt text

---

## What to Log

Only add logs when they help operate or debug the system:

- Backend startup or database preparation failures.
- LLM provider request failures without request/response bodies.
- Generation task terminal status if diagnosing stuck apps.
- File parsing/safety failures as aggregate diagnostics, not with full generated file content.
- Migration failures in setup scripts.

---

## What NOT to Log

Do not log:

- `LLM_API_KEY`, full `LLM_BASE_URL` credentials, cookies, or `quickapp_session` values.
- Passwords or password hashes.
- Full employee names/numbers unless the endpoint already exposes them and the log is absolutely necessary.
- User prompts, conversation content, LLM replies, generated HTML/CSS/JS, or persisted app data payloads.
- Full request/response bodies for auth, chat, or generated app data endpoints.

---

## Current Examples and Gaps

- `/backend/services/ai_service.py` silently skips malformed streamed chunks; there is no warning log today.
- `/backend/services/app_service.py` catches broad generation exceptions and updates app state but does not log the exception. This is current behavior; if future work needs observability, add sanitized `logger.exception` there.
- `/backend/tests/` assert behavior through responses and DB state rather than log output.
