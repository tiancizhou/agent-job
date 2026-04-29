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

## Scenario: Generated Artifact Validation and Recovery

### 1. Scope / Trigger
- Trigger: Chat generation/editing changes the cross-layer SSE contract and writes LLM-produced files to disk.
- Applies to `services/code_service.py`, `services/app_service.py`, and frontend consumers of `/api/apps/{app_id}/chat`.

### 2. Signatures
- `code_service.parse_project_json_or_raise(text: str) -> list[dict[str, str]]`
- `code_service.parse_changes_json_or_raise(text: str) -> list[dict[str, str]]`
- `code_service.save_project(app_id: str, files: list[dict[str, str]], data_dir: str) -> Path`
- `code_service.save_changes(app_id: str, changes: list[dict[str, str]], data_dir: str) -> Path`
- SSE result payload: `{"url": string | null, "status": string, "error": string | null}`

### 3. Contracts
- Generate responses must contain `files`; edit responses must contain `changes`.
- Generated projects must include `index.html`, `css/style.css`, and `js/app.js`.
- `save_project()` and `save_changes()` must perform atomic replacement through temporary project directories.
- `edit_failed` means the previous usable project version is still available.
- `error` is user-facing Chinese text suitable for direct UI display.

### 4. Validation & Error Matrix
- Invalid JSON -> `ProjectValidationError` with a Chinese parse failure reason.
- Missing required generated files -> `ProjectValidationError` listing missing paths.
- Unsafe path / unsupported extension / traversal / Windows drive path -> `ProjectValidationError`.
- Too many files or oversized content -> `ProjectValidationError`.
- Edit without an existing project -> `ProjectValidationError` and `edit_failed` when the app already had a version.
- Unexpected generation exception -> terminal `failed` or `edit_failed` plus generic Chinese `error`.

### 5. Good/Base/Bad Cases
- Good: valid generated JSON writes to a temp directory and then replaces `/data/apps/{id}/project`.
- Base: valid edit copies the current project to temp, applies all changes, validates final project limits, then replaces the target.
- Bad: parsing fails or a later file is invalid; no existing project files are overwritten or removed.

### 6. Tests Required
- Unit tests for parse errors with `ProjectValidationError` details.
- Unit tests proving invalid `save_project()` input does not remove an existing project.
- Unit tests proving invalid `save_changes()` input does not partially write earlier changes.
- Unit tests proving the final edited project still respects total file-count and file-size limits.

### 7. Wrong vs Correct
#### Wrong
```python
shutil.rmtree(project_dir)
for file in files:
    write_file(file)
```

#### Correct
```python
write_project_files(temp_dir, files)
replace_project_dir(project_dir, temp_dir, backup_dir)
```

## Scenario: Chat Device Preference

### 1. Scope / Trigger
- Trigger: `/api/apps/{app_id}/chat` accepts a request field that changes generation/edit prompt constraints.
- Applies to `routers/chat.py` and `services/app_service.py` message construction.

### 2. Signatures
- `ChatRequest.device_preference: str = "mobile"`
- `app_service.normalize_device_preference(value: str | None) -> str`
- `_build_project_messages(..., device_preference: str | None = None) -> list[dict]`

### 3. Contracts
- Accepted values: `mobile`, `desktop`, `responsive`.
- Invalid or missing values normalize to `mobile`; do not reject the chat request.
- `_build_project_messages()` must append a device layout `system` message for both generation and modification prompts.

### 4. Validation & Error Matrix
- `None` / missing -> `mobile`.
- Unknown string -> `mobile`.
- Valid value -> corresponding layout target prompt.
- Existing in-progress generation subscription -> returns the existing stream; a new preference must not restart generation.

### 5. Good/Base/Bad Cases
- Good: desktop preference adds a system prompt requiring desktop-first wide-screen layout while preserving basic responsiveness.
- Base: omitted preference still adds the mobile-first target prompt.
- Bad: validating with HTTP 422/400 for unknown preference, increasing send friction.

### 6. Tests Required
- Unit/service test proving desktop and responsive prompts are included.
- Unit/service test proving invalid values fall back to the mobile prompt.
- Existing chat/generation tests must continue to pass with the default argument.

### 7. Wrong vs Correct
#### Wrong
```python
if body.device_preference not in VALID_DEVICE_PREFERENCES:
    raise HTTPException(status_code=400, detail="Invalid device")
```

#### Correct
```python
device_preference = normalize_device_preference(body.device_preference)
```

## Common Mistakes

- Do not let unsafe file path details leak to clients; convert to 404 like `serve_generated_project_file()`.
- Do not leave apps stuck in `creating`/`editing` after generation exceptions; set a terminal failure status and commit.
- Do not delete or partially overwrite an existing generated project before all LLM output has been validated and written successfully.
- Do not return plain strings for API errors; raise `HTTPException` for normal APIs or `ProjectValidationError` inside generated artifact parsing/saving.
- Do not add custom exception classes without also documenting and applying a consistent FastAPI handler.
- Do not swallow errors that are required for user feedback, except for explicitly non-critical best-effort work like app naming.
