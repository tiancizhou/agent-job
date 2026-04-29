# Backend Development Guidelines

> Best practices for backend development in this project.

---

## Overview

These guidelines document the current backend conventions for QuickApp's FastAPI + SQLAlchemy application under `/backend`. They are based on the checked-in code and `/CLAUDE.md` project instructions.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Populated |
| [Database Guidelines](./database-guidelines.md) | ORM patterns, queries, migrations | Populated |
| [Error Handling](./error-handling.md) | Error types, handling strategies | Populated |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Populated |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | Populated |
| [LLM Settings Contract](./llm-settings.md) | Admin-configurable LLM connection contract | Populated |

---

## Quality Check

For backend changes, read the guideline files relevant to the touched area and always include [Quality Guidelines](./quality-guidelines.md). In particular, verify:

- Router/service placement follows [Directory Structure](./directory-structure.md).
- ORM/session/migration changes follow [Database Guidelines](./database-guidelines.md).
- API errors and SSE failure handling follow [Error Handling](./error-handling.md).
- Logs, if added, follow [Logging Guidelines](./logging-guidelines.md) and do not expose secrets, prompts, generated code, or session data.
- The backend verification command from [Quality Guidelines](./quality-guidelines.md) passes when backend behavior changed.

---

**Language**: All documentation should be written in **English**.
