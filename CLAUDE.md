# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

QuickApp ("quick-da") is an enterprise internal tool where employees describe web apps via chat, an LLM generates multi-file static frontend projects (HTML/CSS/JS), and users can preview, iteratively edit, and share them. The UI is in Chinese.

## Development Commands

### Backend (Python / FastAPI)

```bash
cd backend
# Setup (creates .venv, installs deps, runs migrations)
./start.sh        # Linux/macOS
start.bat         # Windows

# Run dev server with auto-reload (Windows)
.venv\Scripts\uvicorn main:app --reload --port 8000

# Run all tests
cd backend && .venv/Scripts/python -m pytest tests/ -v

# Run a single test file
.venv/Scripts/python -m pytest tests/test_auth.py -v

# Run a single test
.venv/Scripts/python -m pytest tests/test_auth.py::TestAuth::test_register -v
```

### Frontend (Vue 3 / TypeScript / Vite)

```bash
cd frontend
npm install
npm run dev      # Dev server at localhost:5173, proxies /api /apps /generated to :8000
npm run build    # Builds to ../backend/static/ (served by FastAPI in production)
```

### Production Deploy

```bash
bash update-start.sh   # git pull → npm run build → start backend
```

## Architecture

### Data Flow: App Generation

1. User sends chat → `POST /api/apps/{id}/chat` (SSE endpoint in `routers/chat.py`)
2. `app_service.handle_chat()` orchestrates: if app is new, generates a Chinese name via non-streaming LLM call; then builds prompt messages and streams LLM response via SSE
3. LLM outputs JSON with `{"files": [{"path": ..., "content": ...}]}` (generation) or `{"changes": [...]}` (edit)
4. `code_service` parses JSON, saves files to `data/apps/{app_id}/project/`
5. Generated apps served at `/generated/{app_id}/project/index.html` with `Cache-Control: no-store`

### Concurrency Model

- Generation is gated by `asyncio.Semaphore` (configurable via `GENERATION_MAX_CONCURRENT`, default 10)
- `GenerationState` dataclass tracks per-app generation: chunks, subscriber queues, done status
- Multiple SSE subscribers can attach to the same in-progress generation via `asyncio.Queue`

### LLM Integration (`services/ai_service.py`)

- Uses OpenAI-compatible chat completions API via `httpx` async streaming
- Configurable provider via `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` in `.env`
- System prompts (`PROJECT_GENERATE_SYSTEM_PROMPT`, `PROJECT_MODIFY_SYSTEM_PROMPT`) instruct the LLM to output structured JSON only
- All generated apps must use mobile-first responsive design (375px minimum)

### Authentication (`services/auth_service.py`)

- Cookie-based sessions (`quickapp_session`, HTTP-only, 7-day expiry)
- Users are linked to `Employee` records; admin flag on `User` model controls access to management endpoints
- `get_current_user` dependency validates session, user existence, and employee active status

### File Safety (`services/code_service.py`)

- `is_safe_project_path()` validates paths: no traversal, absolute paths, or disallowed extensions
- `resolve_project_file()` resolves and verifies the target stays within the project directory
- Limits: max 20 project files, 10 change files per edit, 300KB per file

### Frontend-Backend Integration

- Vite dev server proxies `/api`, `/apps`, `/generated` to `http://localhost:8000`
- Production: frontend builds into `backend/static/`, served by FastAPI via `StaticFiles(html=True)`
- Frontend is a single-page Vue 3 app with no router; component switching managed by `App.vue`

### Database

- SQLAlchemy 2 ORM with Alembic migrations (2 versions)
- Default SQLite (`quickapp.db`), PostgreSQL supported via `DATABASE_URL`
- 8 models: Employee, User, SessionToken, Style, App, Conversation, UsageRecord, AppDataRecord
- `prepare_database.py` runs Alembic migrations on startup

### App Data Persistence

- Generated apps can call REST API to persist data: `GET/POST /api/generated/{app_id}/data/{collection}` and `GET/PUT/DELETE .../{collection}/{record_id}`
- The LLM system prompts instruct generated apps to use these endpoints instead of localStorage
- `AppDataRecord` model stores JSON payloads keyed by app_id + collection

## Key Configuration (`backend/config.py` + `.env`)

| Variable | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | required | API key for LLM provider |
| `LLM_BASE_URL` | required | OpenAI-compatible endpoint URL |
| `LLM_MODEL` | required | Model name |
| `SERVER_PORT` | 8000 | Backend port |
| `DATA_DIR` | `./data` | Where generated app files are stored |
| `DATABASE_URL` | `sqlite:///./quickapp.db` | Database connection |
| `GENERATION_MAX_CONCURRENT` | 10 | Max parallel LLM generation tasks |
