# Component Guidelines

> How components are built in this project.

---

## Overview

Components are Vue 3 single-file components using `<script setup lang="ts">` and scoped CSS. The current codebase favors direct Composition API state/functions inside each component over abstracted composables or class-style components.

Most UI text is Chinese. Components communicate upward with typed `defineEmits` and receive data through typed `defineProps`.

---

## Component Structure

Use the existing SFC order:

1. `<template>`
2. `<script setup lang="ts">`
3. `<style scoped>`

Examples: `/frontend/src/components/AppList.vue`, `/frontend/src/components/LoginPanel.vue`, `/frontend/src/components/UsagePanel.vue`.

Within `<script setup>`:

- Import Vue APIs first, then local components, then API functions/types.
- Define props and emits near the top.
- Declare refs/computed state before lifecycle hooks and functions.
- Keep helper functions in the same component when only used there.

---

## Props and Emits Conventions

- Use type-literal `defineProps` for component props:

```ts
defineProps<{
  apps: App[]
  selectedAppId: string | null
}>()
```

- Use `withDefaults` when a prop has a default, as in `ChatPanel.vue` for `mobileView`.
- Use typed tuple emits:

```ts
const emit = defineEmits<{
  select: [id: string]
  delete: [id: string]
  "new-app": []
}>()
```

- Template event names are kebab-case (`@app-created`, `@new-app`), matching the string keys in `defineEmits`.
- Use `type` imports for API interfaces: `import { ..., type App, type Style } from "../api/index"`.

---

## Styling Patterns

- Use `<style scoped>` in components. There is no global CSS framework or Tailwind setup.
- Use BEM-like class names with a component prefix: `login-card__header`, `app-list__badge--active`, `chat-panel__workspace--collapsed`.
- Current visual style uses CSS gradients, rounded cards, subtle shadows, `backdrop-filter`, CSS variables for pointer-driven effects, and responsive `@media (max-width: 768px)` rules.
- Keep mobile behavior in component CSS when it belongs to that component. Example: `App.vue` controls mobile shell/sidebar/tabbar; `ChatPanel.vue` controls mobile chat/preview panes.
- Buttons usually include `type="button"` unless they submit a form. Forms use `@submit.prevent`.

---

## Accessibility

Current accessibility is practical but not framework-enforced. Preserve existing patterns and improve locally when touching UI:

- Use semantic elements where present: `form`, `button`, `section`, `header`, `nav`, `article`, `time`.
- Use real buttons for actions, not clickable divs when adding new controls.
- Add `type="button"` to non-submit buttons.
- Preserve labels on form inputs; examples are in `LoginPanel.vue` and `EmployeeAdmin.vue`.
- Keep iframe titles and safe link attributes. `ChatPanel.vue` uses `title="应用预览"` and preview links use `target="_blank" rel="noopener noreferrer"`.
- Existing code uses some clickable cards/divs (for example app selection in `AppList.vue`). Document this as current reality; prefer buttons for new interactive list controls where feasible.

---

## Common Mistakes

- Do not introduce Options API or class components; match `<script setup lang="ts">` Composition API.
- Do not add global CSS for component-specific styles unless changing the app-wide design system.
- Do not mutate props directly; emit events and let the parent update state.
- Do not duplicate backend API types in components when they already exist in `/frontend/src/api/index.ts`.
- Do not replace Chinese UI strings with English in user-facing components.

---

## Real Examples

- `/frontend/src/components/AppList.vue`: simple typed props/emits, local delete confirmation state, BEM scoped CSS.
- `/frontend/src/components/LoginPanel.vue`: form validation with `computed`, submit state, emitted authenticated user, pointer-driven CSS variables.
- `/frontend/src/components/UsagePanel.vue`: modal-style panel, `@click.self` backdrop close, server data loaded on mount.
- `/frontend/src/components/ChatPanel.vue`: complex component with typed props/defaults, typed emits, local interfaces, watchers, streaming callbacks, and preview iframe.
