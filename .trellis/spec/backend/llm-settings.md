# LLM Settings Contract

> Runtime and API contract for administrator-configurable global LLM connection settings.

---

## Overview

QuickDa supports one global LLM configuration stored in the database. The database configuration is used for new app naming, generation, and edit requests when it is complete. The environment-backed `Settings` object remains the fallback for first deployment and local development.

---

## Data Model

- Table: `llm_settings`
- Single row ID: `global`
- Columns:
  - `base_url`: required provider base URL, trimmed before saving.
  - `model`: required model name, trimmed before saving.
  - `api_key`: nullable text, stored plaintext for the MVP.
  - `created_at`, `updated_at`: use the shared `DB_DATETIME` convention.

Alembic migrations must stay aligned with `/backend/models.py` and should not seed a default row because `.env` remains the fallback.

---

## Effective Configuration Resolution

Use `/backend/services/llm_config_service.py` to resolve LLM connection settings.

Resolution order:

1. Return the database row when `base_url`, `model`, and `api_key` are all non-empty after trimming.
2. Otherwise return the environment-backed `Settings` values.

Generation code that runs in the background must resolve this effective configuration inside its background database session, not from the original request-scoped session. New requests use the latest saved complete configuration; already-running SSE tasks are not required to switch.

Usage records must store the effective `model` and provider derived from the effective `base_url`, so usage reporting reflects the LLM configuration that actually handled the call.

---

## Admin API Contract

Routes live under `/api/admin` and must use `require_admin`:

- `GET /api/admin/llm-settings`
- `PUT /api/admin/llm-settings`

Response shape:

```json
{
  "base_url": "https://provider.example/v1",
  "model": "model-name",
  "api_key_configured": true,
  "api_key_masked": "sk-a****1234",
  "source": "database"
}
```

Security rules:

- Never return the plaintext API key in GET or PUT responses.
- Only return `api_key_configured` and `api_key_masked`.
- Do not log API key values.

Update rules:

- `base_url` and `model` are required and must be non-empty after trimming.
- A non-empty `api_key` replaces the stored key.
- An empty or omitted `api_key` preserves the existing stored key.
- On first save with no stored key, an empty or omitted `api_key` may use the fallback environment API key if one exists.
- On first save with no stored key and no fallback environment API key, return a Chinese `400` validation error.

---

## Frontend Contract

The admin UI has a “模型配置” tab in `/frontend/src/components/EmployeeAdmin.vue`.

Frontend requirements:

- Use API types from `/frontend/src/api/index.ts`.
- Display Base URL, model, source, and masked key/status only.
- Never bind or display a plaintext key returned from the server because the server must never return one.
- Treat the API key input as write-only; clear it after successful save.
- Disable saving while Base URL or model is empty or while a save is in progress.

---

## Scenario: Admin-Configurable LLM Settings

### 1. Scope / Trigger
- Trigger: Admin UI/API changes the runtime LLM provider settings used by app naming, generation, and edits.
- Applies to `models.LLMSetting`, `services/llm_config_service.py`, `routers/admin.py`, `services/app_service.py`, and `EmployeeAdmin.vue`.

### 2. Signatures
- `GET /api/admin/llm-settings -> LLMSettingsSummary`
- `PUT /api/admin/llm-settings {base_url: str, model: str, api_key?: str} -> LLMSettingsSummary`
- `llm_config_service.get_effective_llm_settings(db: Session, fallback: Settings) -> EffectiveLLMSettings`
- `llm_config_service.update_llm_settings(db: Session, body, fallback: Settings) -> LLMSetting`

### 3. Contracts
- `base_url` and `model` are required and trimmed.
- `api_key` is stored plaintext in `llm_settings.api_key` for this MVP.
- API responses never include plaintext `api_key`; use `api_key_configured` and `api_key_masked` only.
- New LLM work uses the complete database config first, then falls back to `.env` settings.
- Background generation resolves effective settings inside the background DB session.

### 4. Validation & Error Matrix
- Non-admin request -> existing auth/admin error.
- Empty `base_url` or `model` -> Chinese `400` validation error.
- Empty `api_key` with stored key -> preserve stored key.
- Empty `api_key` without stored key but with fallback key -> store/use fallback key.
- Empty `api_key` without stored key or fallback key -> Chinese `400` validation error.
- Incomplete DB row at runtime -> fallback `.env` settings.

### 5. Good/Base/Bad Cases
- Good: admin saves all three fields; subsequent generation records usage with the saved model/provider.
- Base: admin updates only model/base URL and leaves API key empty; existing key is preserved.
- Bad: API response includes the plaintext key or generation uses stale `.env` settings after a complete DB config exists.

### 6. Tests Required
- Admin route tests for permission enforcement.
- Save/read tests proving plaintext key is not returned and masked fields are returned.
- Update tests proving empty key preserves stored key and first-save fallback behavior.
- Service/generation tests proving effective DB settings are used for LLM calls and usage records.
- Frontend build proving admin UI/API types compile.

### 7. Wrong vs Correct
#### Wrong
```python
return {"api_key": setting.api_key}
```

#### Correct
```python
return {"api_key_configured": True, "api_key_masked": mask_api_key(setting.api_key)}
```

## Verification

For changes to this feature, run:

```bash
backend/.venv/Scripts/python -m unittest discover -s backend/tests -p "test_*.py" -v
npm --prefix frontend run build
```
