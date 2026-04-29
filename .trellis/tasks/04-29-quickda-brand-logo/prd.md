# brand: QuickDa 命名与 QD Logo

## Goal

根据产品命名决策，将系统可见品牌从 QuickApp 更新为 QuickDa / QD / 快搭，并生成一个可直接在前端使用的 QD Logo，提升产品一致性。

## What I already know

* 用户已明确：应用英文名 QuickDa，简称 QD，中文名 快搭。
* 当前项目历史上使用 QuickApp 作为产品名，前端可见文案中可能仍有 QuickApp。
* 本任务应优先处理用户可见 UI 和页面标题，不做大规模代码包名/仓库名/数据库字段重命名。
* Logo 可以用内联 SVG 或前端组件/样式直接接入，避免新增复杂资源流水线。
* Windows 环境使用 `python` 命令。

## Requirements

* 将主要前端可见品牌文案更新为 QuickDa / QD / 快搭。
* 生成并接入一个可直接使用的 QD Logo。
* 登录页、侧边栏、首页 Hero、必要页面标题等用户入口应体现新品牌。
* 不改变 API、数据库模型、包名或仓库名。
* 不做大规模视觉重设计，只做轻量品牌替换和 logo 接入。

## Acceptance Criteria

* [x] 前端主要 UI 不再显示 QuickApp 品牌名，改为 QuickDa / QD / 快搭。
* [x] 侧边栏或主入口展示 QD Logo。
* [x] 页面标题/浏览器 title 使用 QuickDa 或快搭。
* [x] 前端 build 通过。
* [x] 不引入图片外链或需要额外构建工具的资产。

## Definition of Done

* `npm --prefix frontend run build` passes.
* Logo 在前端可见位置直接渲染。
* 变更范围保持在品牌文案和 logo UI，不做无关重构。

## Out of Scope

* 仓库名、包名、数据库字段、API path 重命名。
* 完整品牌手册或多套 logo 规范。
* 后端内部类名/注释的全面替换。
* 大规模 UI 重设计。

## Technical Approach

* 使用内联 SVG 作为 QD Logo，不新增图片文件或构建工具。
* 在 `AppList.vue` 侧边栏展示小号 QD Logo + QuickDa + 快搭/QD 副标题。
* 在 `LoginPanel.vue` 登录 Hero 展示大号 QD Logo + QuickDa，并将入口按钮/标题更新为 QuickDa。
* 将前端主要可见 QuickApp 文案替换为 QuickDa 或快搭。
* 保留 `quickapp:selectedAppId` localStorage key、`quickapp_session` cookie、`quickapp.db` 等内部兼容标识，不做破坏性重命名。

## Technical Notes

* 已检查：`frontend/src/components/AppList.vue`、`LoginPanel.vue`、`ChatPanel.vue`、`MessageBubble.vue`、`EmployeeAdmin.vue`、`frontend/index.html`。
* 已搜索前端用户可见 `QuickApp` 文案，当前前端已无 `QuickApp` 匹配。
* 已检查后端 `QuickApp/quickapp` 命中主要是 cookie、DB 文件名和测试 user-agent，按 out-of-scope 保留。
