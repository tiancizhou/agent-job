# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

Frontend quality is enforced mainly by TypeScript and the Vite production build. There is no ESLint, Prettier, or frontend test runner configured at bootstrap time.

Primary verification command:

```bash
cd frontend && npm run build
```

This runs `vue-tsc && vite build` and writes the production assets to `/backend/static/` per project configuration.

---

## Forbidden Patterns

- Do not add Vue Router for normal app navigation; the current app uses conditional rendering and `mobileView` state in `App.vue`.
- Do not add Pinia/Vuex or a server-state library for isolated state changes.
- Do not bypass `/frontend/src/api/index.ts` for backend calls unless implementing a special streaming/browser API pattern that belongs there afterward.
- Do not remove `credentials: "include"` from API calls; backend auth is cookie-based.
- Do not use relative API paths for generated app data in LLM-generated apps; prompts require `/api/generated/...` absolute paths.
- Do not replace the Chinese UI copy with English for end-user text.
- Do not introduce untyped emits, `any`, or broad type assertions to silence `vue-tsc`.
- Do not leave polling intervals running after streaming/generation ends.

---

## Required Patterns

- Use Vue 3 `<script setup lang="ts">` and Composition API for new components.
- Keep shared API response/request types and fetch functions in `/frontend/src/api/index.ts`.
- Use typed `defineProps` and `defineEmits` for component boundaries.
- Keep styles scoped to components and follow the existing BEM-like class naming.
- Preserve mobile responsiveness around the existing breakpoint (`@media (max-width: 768px)`) and `100dvh`/safe-area patterns where relevant.
- Preserve the chat SSE contract in `sendChat()` callbacks: chunk, progress, and result handling.
- Use visible error/loading states in Chinese when API calls can fail. Examples: `LoginPanel.vue`, `EmployeeAdmin.vue`, `UsagePanel.vue`, `ChatPanel.vue`.

---

## Testing and Verification Requirements

- Run `npm run build` from `/frontend` after frontend changes to catch TypeScript and Vue SFC errors.
- There are currently no unit/component tests configured. If adding a test framework, document it and add scripts; otherwise verify through build and manual flows.
- Manually check core flows affected by UI changes: login/register, app list selection/deletion, create app/chat streaming, preview iframe, admin employee/style management, usage panel.
- For generated preview changes, verify cache busting still works (`?t=` version/date parameter) and iframe sandbox remains appropriate.

---

## Code Review Checklist

Review frontend changes for:

- TypeScript strictness: no new `any`, nullable values handled, API types updated.
- Component boundaries: props/emits typed, no direct prop mutation.
- API behavior: `credentials: "include"`, `/api` base path, errors handled.
- State ownership: app-shell state remains in `App.vue`; component state remains local unless reused.
- Mobile UX: shell/sidebar/tabbar and chat/preview mobile modes still work.
- Accessibility basics: real buttons for actions, labels for inputs, iframe title, safe external links.
- Chinese user-facing copy and consistent status labels.
- Timers/SSE: pollers are started/stopped and streaming flags clear on success/failure.

## Impact Radius Analysis

Before finishing a frontend change, classify the impact radius and expand verification accordingly:

- L1: Styling or local UI-only change in one component. Verify scoped CSS, Chinese copy, and local interaction states.
- L2: Component logic or props/emits affecting parent-child communication. Verify typed props/emits and callers in `/frontend/src/App.vue` or sibling components.
- L3: API wrapper/type change or shared app-shell state. Verify `/frontend/src/api/index.ts`, affected components, and `vue-tsc` via `npm run build`.
- L4: Cross-layer change where frontend expectations depend on backend response/error/SSE contracts. Trace backend route/service output through the API wrapper into component state and UI error/loading behavior.
- L5: App-wide frontend contracts such as authentication flow, chat streaming, generated preview URLs, mobile shell navigation, or production build output. Run the frontend build and reason through affected manual flows.

For this bootstrap-guidelines task itself, the intended impact radius is documentation/spec only. If code outside `.trellis/spec/` or `.trellis/tasks/00-bootstrap-guidelines/` changes, treat it as out of scope unless explicitly justified.

---

## Real Examples

- `/frontend/src/api/index.ts`: typed API wrapper and SSE parser.
- `/frontend/src/App.vue`: top-level state ownership and mobile shell.
- `/frontend/src/components/ChatPanel.vue`: most important quality hotspot for streaming, polling cleanup, preview URLs, and generated-artifact normalization.
- `/frontend/src/components/EmployeeAdmin.vue`: admin form validation and local list updates.
- `/frontend/src/components/UsagePanel.vue`: loading/error/empty states for panel data.
