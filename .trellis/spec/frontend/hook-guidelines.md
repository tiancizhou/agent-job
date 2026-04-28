# Hook Guidelines

> How hooks/composables are used in this project.

---

## Overview

This is a Vue project, so the relevant pattern is Vue composables rather than React hooks. At bootstrap time there are no custom composable files such as `useAuth.ts` or `useApps.ts`; stateful logic lives directly in `App.vue` and components.

Do not introduce a composables layer for small changes. Add one only when the same stateful logic is genuinely reused by multiple components.

---

## Current Composition API Patterns

The project uses Vue Composition API primitives directly:

- `ref` for mutable state (`currentUser`, `apps`, `inputText`, `isSubmitting`).
- `computed` for derived state (`canSubmit`, `activeCount`, `previewUrl`, `currentAppIsStreaming`).
- `watch` for prop-driven loading in `ChatPanel.vue`.
- `onMounted` for initial API loads in `App.vue`, `EmployeeAdmin.vue`, and `UsagePanel.vue`.
- `onUnmounted` for cleanup in components that create timers/listeners (used in `ChatPanel.vue`).
- `nextTick` for DOM-dependent UI updates such as scrolling or textarea sizing in `ChatPanel.vue`.

---

## Data Fetching

There is no React Query/SWR/Vue Query. Data fetching is explicit async functions calling `/frontend/src/api/index.ts`:

- `App.vue` calls `getCurrentUser`, `listApps`, `listStyles`, `getUsageSummary`, `logout`, and `deleteApp`.
- `EmployeeAdmin.vue` calls admin employee/style APIs and updates local arrays after successful mutations.
- `UsagePanel.vue` calls `listUsageRecords` on mount and when the user clicks refresh.
- `ChatPanel.vue` calls `createApp`, `getApp`, `getAppPreview`, `listConversations`, `sendChat`, and `setAppStyle`.

Errors are generally caught near the call site and shown as Chinese UI messages or fallback state.

---

## When to Create a Composable

A new composable may be appropriate if all are true:

- The same stateful workflow is needed by at least two components.
- The logic is not just a single API call wrapper that belongs in `/frontend/src/api/index.ts`.
- The composable can expose typed refs/computed/functions without hiding important side effects.

If created, follow Vue naming conventions:

- Put it under `/frontend/src/composables/`.
- Name files and functions `useXxx.ts` / `useXxx()`.
- Keep returned state explicit, e.g. `{ records, isLoading, error, loadRecords }`.

This directory does not currently exist, so only add it when justified by reuse.

---

## Common Mistakes

- Do not create a `use*` composable just to move code out of a long component; bootstrap reality is component-local logic.
- Do not call composables conditionally if they are introduced; call at setup top level.
- Do not bypass the typed API module from composables; keep fetch details centralized in `/frontend/src/api/index.ts`.
- Do not create global mutable module state casually; prefer component refs unless state must survive component boundaries.

---

## Real Examples of Current Patterns

- `/frontend/src/App.vue`: top-level refs and async functions for auth/app/style/usage state.
- `/frontend/src/components/LoginPanel.vue`: local form refs plus `computed` validation.
- `/frontend/src/components/EmployeeAdmin.vue`: separate local state groups for employees and styles.
- `/frontend/src/components/ChatPanel.vue`: watcher-driven loading, timer cleanup, streaming state maps, and computed preview state.
