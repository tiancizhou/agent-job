# 前端预览编辑体验优化 MVP

## Goal

围绕 QuickApp 的轻量定位，优化用户在生成完成后继续预览、继续编辑、理解失败状态和操作下一步的体验，而不是引入重型版本历史、完整数据权限体系、代码编辑器或复杂导航。

## What I already know

* 已决定暂不做应用版本历史；修改失败时保留上一个可用项目已经足够支撑当前轻量产品定位。
* 已决定暂不做完整 generated app 数据权限体系；避免把快速生成工具演变成重型项目开发平台。
* 上一轮已增强失败提示，SSE `result.error` 可展示后端中文错误详情。
* 当前前端核心流程集中在 `ChatPanel.vue`、`MessageBubble.vue`、`AppList.vue`、`App.vue` 和 `frontend/src/api/index.ts`。
* `ChatPanel.vue` 已有聊天 + 右侧预览结构，`previewUrl` 会在 `active`、有版本的 `editing`、`edit_failed` 状态下显示可用预览。
* `MessageBubble.vue` 已能展示 `failed` / `edit_failed` 结果面板和后端错误详情。
* `AppList.vue` 只显式展示 `creating` / `active` / `failed` 状态，`editing` / `edit_failed` 会直接落到英文状态值。
* `ChatPanel.vue` 的输入提示仍偏通用：`描述你想要的应用功能…`，成功后没有足够明确地提示“继续描述即可修改当前应用”。
* 预览区已有“实时预览”和“新窗口打开”，但缺少轻量下一步提示：可继续在左侧描述修改；修改失败时旧版本仍保留。
* `App.vue` 移动端通过底部 tab 在“应用 / 生成 / 预览”间切换，当前任务不需要改成新导航体系。

## Requirements

* 优化生成成功后的继续编辑/预览操作引导，让用户明确知道可以继续描述修改当前应用。
* 优化编辑中、有旧版本可预览、编辑失败状态下的预览区说明，让用户知道旧版本仍可用。
* 优化失败状态下的下一步提示，失败后引导用户调整需求继续生成或继续编辑。
* 优化应用列表状态标签，显式展示 `editing` 和 `edit_failed` 的中文文案与视觉状态。
* 保持现有聊天 + 右侧预览 + 移动端底部 tab 的轻量结构。
* 不改变 SSE/API 合约；继续复用已有 `result.error` 展示能力。

## Acceptance Criteria

* [ ] 用户生成成功后能更清楚地知道可以继续描述修改当前应用。
* [ ] 用户修改中但已有旧版本时，能看懂右侧预览仍是可用版本。
* [ ] 用户修改失败后能清楚知道旧版本仍保留，并能继续编辑。
* [ ] 应用列表不再展示裸 `editing` / `edit_failed` 英文状态。
* [ ] 前端 build 通过。
* [ ] 不引入复杂新导航、版本历史、分享权限或代码编辑器。

## Definition of Done

* Frontend type-check/build passes via `npm --prefix frontend run build`.
* UI 文案保持中文、轻量、可操作。
* 不改变后端 API、数据库或 generated app 数据接口。
* 如仅为文案/状态 UX 调整，不强制新增自动化测试；以 build 和人工检查为准。

## Technical Approach

采用“小文案 + 状态补齐”的 MVP：

1. `ChatPanel.vue`
   * 根据当前 app 状态生成更明确的输入 placeholder，例如 active/edit_failed 时提示“继续描述要调整的地方”。
   * 在预览卡片 header 或 body 中增加轻量下一步提示，不新增复杂交互。
   * 区分 `failed`、`edit_failed`、`editing with version` 的预览说明。
2. `AppList.vue`
   * 补齐 `editing` / `edit_failed` 中文状态标签。
   * 补齐对应 badge 样式，避免裸英文状态泄露到中文 UI。
3. `App.vue`
   * 保持移动端 tab 结构不变；如需要，仅在现有行为内保持“选择应用回到生成页”。
4. `frontend/src/api/index.ts`
   * 不改合约；沿用现有 `sendChat(..., onResult(url, status, error))`。

## Decision (ADR-lite)

**Context**: QuickApp 当前阶段定位是快速生成内部小应用。上一轮已经通过后端原子保存和前端错误详情解决失败恢复的基础能力；下一步的最大收益来自让用户知道成功后如何继续、失败后如何恢复，而不是建设版本历史、权限或编辑器。

**Decision**: 本任务只做轻量 UX 引导和状态文案补齐：ChatPanel 预览/输入提示 + AppList 状态标签。默认不新增按钮流、导航结构或状态机。

**Consequences**: 改动范围小、风险低、适合 MVP；不会解决复杂历史回退、多人协作、分享权限等问题，但与当前轻量定位一致。

## Out of Scope

* 版本历史 UI、历史预览、手动回退。
* 完整代码编辑器或文件树。
* 复杂权限/分享管理。
* 大规模视觉重设计。
* 新增移动端导航体系或自动跳转策略。
* 后端 API、数据库或 generated app 数据权限改动。

## Technical Notes

* 已检查：`frontend/src/components/ChatPanel.vue`、`MessageBubble.vue`、`AppList.vue`、`App.vue`、`frontend/src/api/index.ts`。
* `ChatPanel.vue` 关键现状：`previewUrl` 在 `active`、有版本的 `editing`、`edit_failed` 时可展示；`failed` 时展示 placeholder。
* `MessageBubble.vue` 关键现状：已支持 `resultError`，并区分 `failed` / `edit_failed` 结果说明。
* `AppList.vue` 关键现状：`statusLabel()` 未覆盖 `editing` / `edit_failed`。
* `App.vue` 关键现状：移动端 `mobileView` 为 `apps | chat | preview`，底部 tab 已存在。
