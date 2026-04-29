# fix: ChatPanel 底部输入区完整显示

## Goal

修复聊天页底部输入框和发送按钮在视口底部被裁切、无法完整显示的问题，保持当前聊天 + 预览结构不变，只调整布局高度/overflow/padding。

## What I already know

* 用户截图显示桌面端聊天区底部 composer 被页面底部裁切，输入框和发送按钮只露出上半部分。
* 问题发生在 `ChatPanel.vue` 工作区内，右侧预览正常显示。
* 近期刚增加了预览 header guidance，但截图中的裁切更像主布局高度、聊天滚动区或输入区底部空间问题。
* 预计涉及 `frontend/src/components/ChatPanel.vue`，必要时检查 `frontend/src/App.vue` 外层布局高度。

## Requirements

* 桌面端聊天输入框和发送按钮必须完整显示。
* 聊天消息区域仍可滚动，输入区固定在聊天面板底部可见。
* 不改变交互结构，不新增按钮或导航。
* 保持移动端布局不退化。

## Acceptance Criteria

* [ ] 截图所示宽屏桌面布局下，底部输入框和发送按钮完整可见。
* [ ] 消息较多时只滚动消息区，不裁切输入区。
* [ ] 前端 build 通过。
* [ ] 不改后端 API 或聊天 SSE 逻辑。

## Definition of Done

* `npm --prefix frontend run build` passes.
* CSS 改动局限在布局可见性修复范围内。
* 如能本地打开页面，应人工检查桌面宽屏聊天页。

## Out of Scope

* 聊天 UI 重设计。
* 移动端导航改造。
* 消息气泡样式重做。
* 后端和 API 改动。

## Technical Approach

最小 CSS 修复：

* `ChatPanel.vue` 根容器补齐 `min-height: 0` 和 `overflow: hidden`，确保它作为 `App.vue` flex 子项时不把内容撑出视口。
* `chat-panel__workspace` 补齐 `box-sizing: border-box` 和 `overflow: hidden`，让 18px padding 计入可用高度，避免底部输入区被外层裁切。
* 保持消息滚动仍由 `chat-panel__messages` 承担，输入区留在面板底部。

## Technical Notes

* 已检查：`frontend/src/components/ChatPanel.vue` 的 workspace/conversation/messages/input-bar CSS。
* 已检查：`frontend/src/App.vue` 的 app shell/main 高度和 overflow。
* 根因判断：`chat-panel__workspace` 是 flex 子项且带 padding，但默认 content-box 会让实际高度超出父容器；外层 `overflow: hidden` 导致底部 composer 被裁切。
