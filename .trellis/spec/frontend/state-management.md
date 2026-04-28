# State Management

> How state is managed in this project.

---

## Overview

The project uses local Vue Composition API state only. There is no Pinia, Vuex, router state, or server-state cache library. `App.vue` acts as the app shell and owner of cross-component state; child components own their local UI state.

State is intentionally simple and explicit: `ref`, `computed`, props, emits, and occasional `localStorage`.

---

## State Categories

### App-shell state

Owned by `/frontend/src/App.vue`:

- `currentUser`, `isCheckingAuth`
- `apps`, `selectedAppId`
- `styles`
- `usageSummary`, `isUsagePanelOpen`
- `showAdmin`
- `mobileView`

`App.vue` passes data down to `AppList`, `ChatPanel`, `EmployeeAdmin`, `LoginPanel`, and `UsagePanel`, then updates state from emitted events.

### Component-local UI state

Owned inside components:

- Login form mode/input/error/submitting and pointer animation state in `LoginPanel.vue`.
- Delete confirmation state in `AppList.vue`.
- Employee/style forms, editing state, and tab selection in `EmployeeAdmin.vue`.
- Usage records/loading/error in `UsagePanel.vue`.
- Chat messages, streaming IDs, progress map, preview URL, style picker, polling timers, and resume state in `ChatPanel.vue`.

### Persisted browser state

`App.vue` stores only the selected app ID in `window.localStorage` under `quickapp:selectedAppId`. Generated apps are instructed to use backend persistence APIs instead of localStorage for their own data.

### Server state

Server data is fetched manually through `/frontend/src/api/index.ts` and stored in refs/arrays. Mutations update local state directly or refetch the relevant list.

---

## When to Use Global State

There is no global store. Keep state in the nearest owner:

- If multiple top-level panels need the state, keep it in `App.vue` and pass it down.
- If only one component needs it, keep it local to that component.
- If it must survive page reloads and is small UI preference/state, use `localStorage` deliberately (current example: selected app ID).
- If it is authoritative business data, store it on the backend and refetch/update through the API module.

Do not add Pinia/Vuex for isolated features without a larger state-management need.

---

## Server State Synchronization

Current synchronization patterns:

- Initial auth/app/style/usage load happens in `App.vue` `onMounted` after `getCurrentUser()` succeeds.
- App creation/deletion updates `apps` locally and selected app state immediately.
- `onAppUpdated()` refetches apps and usage summary after generation completes.
- `ChatPanel.vue` fetches app details and conversations when `selectedAppId` changes.
- `ChatPanel.vue` starts interval polling for apps in `creating`/`editing` state and stops polling when the app leaves those states or the stream ends.
- Usage records are loaded when `UsagePanel` mounts and on manual refresh.

---

## Derived State

Use `computed` for derived UI values instead of duplicating refs:

- `LoginPanel.vue`: `canSubmit`, `loginStyle`.
- `EmployeeAdmin.vue`: `canAdd`, `activeCount`, `disabledCount`, `canAddStyle`.
- `ChatPanel.vue`: `previewUrl`, `previewTitle`, `previewDescription`, `currentStyleName`, `currentAppIsStreaming`, `streamProgress`.

---

## Common Mistakes

- Do not mutate shared app-shell state from child components directly; emit typed events and let `App.vue` update.
- Do not store server-authoritative data only in `localStorage`.
- Do not add a store library for a single component's state.
- Do not forget to clear timers/pollers in long-lived components. `ChatPanel.vue` maintains `statusPollers` and has explicit stop helpers.
- Do not let local arrays get stale after admin mutations; current pattern maps/replaces updated items or prepends created items.
