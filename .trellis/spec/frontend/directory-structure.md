# Directory Structure

> How frontend code is organized in this project.

---

## Overview

The frontend is a small Vue 3 + TypeScript + Vite single-page app. There is no Vue Router, no Pinia/Vuex store, and no feature-folder architecture. `App.vue` owns top-level screen switching and passes state/events to components.

The UI is in Chinese. Production builds are written to `/backend/static/` and served by FastAPI; Vite dev proxies `/api`, `/apps`, and `/generated` to the backend.

---

## Directory Layout

```text
/frontend
├── package.json             # scripts: dev, build, preview
├── vite.config.ts           # build output and backend proxy settings
├── tsconfig.json            # strict TypeScript
└── src
    ├── main.ts              # createApp(App).mount("#app")
    ├── App.vue              # top-level authenticated app shell and state
    ├── api/
    │   └── index.ts         # typed fetch wrapper and API functions
    └── components/
        ├── AppList.vue
        ├── ChatPanel.vue
        ├── EmployeeAdmin.vue
        ├── LoginPanel.vue
        ├── MessageBubble.vue
        └── UsagePanel.vue
```

---

## Module Organization

- Put reusable UI sections in `/frontend/src/components/` as single-file Vue components.
- Keep top-level application state and layout in `/frontend/src/App.vue`: current user, selected app, app list, styles, usage summary, admin panel toggle, and mobile tab selection.
- Keep all backend API calls and exported response interfaces in `/frontend/src/api/index.ts`.
- Keep component-local helper interfaces inside the component when they are not shared. Example: `Message` and `ResumeStreamState` in `/frontend/src/components/ChatPanel.vue`.
- Do not add routing files for normal screen switching; current navigation is conditional rendering in `App.vue` and component state.
- There is no assets directory at bootstrap time. Inline SVG and CSS gradients are currently used instead of imported image assets.

---

## Naming Conventions

- Vue component files use PascalCase: `LoginPanel.vue`, `ChatPanel.vue`, `UsagePanel.vue`.
- API functions use lower camelCase verbs: `getCurrentUser`, `listApps`, `createApp`, `sendChat`, `listUsageRecords`.
- TypeScript interfaces exported from the API module use PascalCase matching backend resources: `App`, `Style`, `CurrentUser`, `UsageRecord`.
- Component CSS classes use BEM-like names scoped to the component prefix: `app-list__item--active`, `chat-panel__style-card--selected`, `usage-panel__stat`.
- Event names in Vue emits are kebab-case strings when consumed in templates: `app-created`, `app-updated`, `new-app`.

---

## Examples

- `/frontend/src/App.vue` shows the app-shell pattern: conditional login/admin/chat rendering, prop passing, event handlers, and `localStorage` for selected app ID.
- `/frontend/src/api/index.ts` is the single place for backend contracts and fetch/SSE parsing.
- `/frontend/src/components/AppList.vue` is a concise presentational/list component with typed props and emits.
- `/frontend/src/components/ChatPanel.vue` is the example for complex stateful UI: streaming chat, polling, preview iframe, style picker, and mobile preview/chat modes.
