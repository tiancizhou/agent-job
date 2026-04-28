# Frontend Development Guidelines

> Best practices for frontend development in this project.

---

## Overview

These guidelines document the current frontend conventions for QuickApp's Vue 3 + TypeScript + Vite application under `/frontend`. They are based on the checked-in code and `/CLAUDE.md` project instructions.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Populated |
| [Component Guidelines](./component-guidelines.md) | Component patterns, props, composition | Populated |
| [Hook Guidelines](./hook-guidelines.md) | Custom hooks, data fetching patterns | Populated |
| [State Management](./state-management.md) | Local state, global state, server state | Populated |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Populated |
| [Type Safety](./type-safety.md) | Type patterns, validation | Populated |

---

## Quality Check

For frontend changes, read the guideline files relevant to the touched area and always include [Quality Guidelines](./quality-guidelines.md) and [Type Safety](./type-safety.md). In particular, verify:

- Files and API boundaries follow [Directory Structure](./directory-structure.md).
- Components use the Vue SFC patterns in [Component Guidelines](./component-guidelines.md).
- Reusable state is not prematurely moved into composables; see [Hook Guidelines](./hook-guidelines.md) and [State Management](./state-management.md).
- Types remain strict and shared API shapes stay centralized in `/frontend/src/api/index.ts`.
- The frontend verification command from [Quality Guidelines](./quality-guidelines.md) passes when frontend behavior changed.

---

**Language**: All documentation should be written in **English**.
