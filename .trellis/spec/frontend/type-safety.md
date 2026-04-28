# Type Safety

> Type safety patterns in this project.

---

## Overview

The frontend uses TypeScript in strict mode (`"strict": true` in `/frontend/tsconfig.json`) with Vue 3 SFCs. The build command runs `vue-tsc` before Vite:

```bash
cd frontend && npm run build
```

Types are mostly hand-written interfaces in `/frontend/src/api/index.ts`, mirroring backend Pydantic/ORM response shapes.

---

## Type Organization

- Shared backend API shapes are exported from `/frontend/src/api/index.ts`: `App`, `Style`, `Conversation`, `CurrentUser`, `Employee`, `UsageSummary`, `UsageRecord`.
- API functions return `Promise<T>` through the generic `request<T>()` helper.
- Components import API types using `type` imports where possible:

```ts
import { listUsageRecords, type UsageRecord, type UsageSummary } from "../api/index"
```

- Component-only interfaces stay local to the component. Example: `Message` and `ResumeStreamState` in `/frontend/src/components/ChatPanel.vue`.
- Prop and emit types are declared inline with `defineProps` and `defineEmits`; no separate props interfaces unless reuse justifies them.

---

## API Type Patterns

- Use string literal unions for known enum-like fields:
  - `App.status`: `"creating" | "editing" | "active" | "failed" | "edit_failed"`
  - `App.project_type`: `"html" | "project"`
  - `App.visibility`: `"private" | "public" | "token"`
  - `Employee.status`: `"active" | "disabled"`
- Allow `null`/optional for backend nullable fields: `style_id?: string | null`, `progress?: string | null`, `preview_token?: string | null`.
- Some server values intentionally permit future strings while preserving known values, as in `UsageRecord.action: "name" | "generate" | "edit" | string`.
- Keep API paths centralized in `api/index.ts` with `const BASE = "/api"` and `credentials: "include"` for cookie auth.

---

## Validation

There is no runtime schema validation library (no Zod/Yup/io-ts). Validation is handled by:

- Backend Pydantic/SQLAlchemy constraints for API data.
- Component-level simple checks for UI forms, such as `LoginPanel.vue` and `EmployeeAdmin.vue` using `/^\d{5}$/` for employee number and non-empty names/prompts.
- Fetch error handling based on HTTP status (`request<T>` throws `new Error(`${res.status}`)`).
- SSE parsing in `sendChat()` catches malformed JSON and ignores it.

Do not add a validation library unless the feature requires substantial client-side schema validation.

---

## Common Patterns

- Type DOM refs explicitly: `ref<HTMLTextAreaElement | null>(null)`, `ref<HTMLElement | null>(null)` in `ChatPanel.vue`.
- Type constrained UI refs with literal unions: `ref<"login" | "register">("login")`, `ref<"apps" | "chat" | "preview">("chat")`.
- Use non-null assertion sparingly after a guard has established the value, as in `const appId = currentAppId.value!` inside `sendMessage()` after app creation/selection logic.
- Use `Record<string, T>` for ID-keyed maps such as `messageCache`, `streamProgressByAppId`, `statusPollers`, and `resumeStreams`.

---

## Forbidden Patterns

- Avoid `any`; use explicit interfaces or `unknown` plus narrowing if necessary.
- Do not duplicate API interfaces in components; update `/frontend/src/api/index.ts` when backend response shapes change.
- Do not ignore nullable fields from backend responses; handle `null` explicitly in UI.
- Do not type events/emits as untyped strings when adding new emits; use the tuple `defineEmits` style used in current components.
- Do not bypass `vue-tsc` errors by weakening `tsconfig` strictness.
