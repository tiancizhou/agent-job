# fix: QD favicon 图标

## Goal

修复浏览器标签页仍显示默认图标的问题，让网页 favicon 与 QuickDa / QD 品牌一致。

## What I already know

* 用户截图显示浏览器标签页图标仍是默认图标。
* 产品命名已确定为 QuickDa，简称 QD，中文名快搭。
* 当前 `frontend/index.html` 已设置标题 `QuickDa 快搭`，但没有 favicon link。
* 当前前端没有 `frontend/public/` 图标资源。

## Requirements

* 新增一个可由 Vite 直接复制的 QD SVG favicon。
* 在 `frontend/index.html` 中引用该 favicon。
* 图标风格与已接入的 QD 内联 SVG Logo 保持一致。
* 不引入图片外链或额外构建工具。

## Acceptance Criteria

* [x] 浏览器标签页使用 QD favicon，不再显示默认图标。
* [x] `frontend/index.html` 包含 favicon 声明。
* [x] `npm --prefix frontend run build` passes。
* [x] 变更范围仅限 favicon 和任务记录。

## Definition of Done

* 前端构建通过。
* favicon 资源在构建产物中可用。

## Out of Scope

* 不重新设计整体 logo。
* 不修改登录页、侧边栏等已有品牌 UI。
* 不修改后端、API、数据库或内部兼容标识。

## Technical Approach

* 创建 `frontend/public/favicon.svg`，复用蓝橙渐变圆角方块和 QD 字母风格。
* 在 `frontend/index.html` 增加 `<link rel="icon" type="image/svg+xml" href="/favicon.svg" />`。

## Technical Notes

* 已检查 `frontend/index.html`，当前没有 favicon link。
* 已检查前端图标资源，当前无 `frontend/public/` 下的 favicon/svg/png/ico。
