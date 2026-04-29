# feature: 生成应用设备偏好选择

## Goal

在不增加用户发送摩擦的前提下，为生成/修改应用提供轻量设备偏好选择，让 LLM 根据手机端、电脑端或自适应目标生成更稳定的布局。

## What I already know

* 用户确认采用轻量切换控件，不做强制弹窗。
* 默认应为手机端优先，可选电脑端优先、自适应。
* 发送聊天时需要把选择传给后端，并注入生成/修改提示词。
* 当前后端生成提示词默认强制 mobile-first 与 375px 适配。
* 当前 chat 请求体只有 `message` 字段。

## Requirements

* 聊天输入区和首页 Hero 输入区提供轻量设备偏好切换。
* 默认值为手机端优先。
* 可选项：手机端、电脑端、自适应。
* 发送聊天时携带设备偏好到后端。
* 后端校验设备偏好并将对应布局要求注入生成/修改 prompt。
* 修改已有应用时也使用当前选择的设备偏好约束。
* 不使用强制弹窗，不阻塞用户发送。

## Acceptance Criteria

* [x] 用户可以在发送前切换手机端/电脑端/自适应。
* [x] 不选择时默认手机端优先。
* [x] chat 请求 payload 包含设备偏好。
* [x] 后端生成/修改 messages 中包含对应设备布局提示。
* [x] 非法设备偏好回落为手机端优先。
* [x] `npm --prefix frontend run build` passes。
* [x] 相关后端测试通过。

## Definition of Done

* 前端构建通过。
* 后端单测覆盖 prompt 注入或请求字段处理。
* 变更范围保持在设备偏好 UI、chat API 契约和 prompt 注入。

## Out of Scope

* 不给每个应用持久化设备偏好。
* 不增加数据库字段或迁移。
* 不做预览 iframe 的设备尺寸模拟器。
* 不做强制选择弹窗。

## Technical Approach

* 前端新增 `DevicePreference` union：`mobile | desktop | responsive`。
* `sendChat()` 增加可选 `devicePreference` 参数并写入 JSON body 的 `device_preference`。
* `ChatRequest` 增加 `device_preference` 字段，后端归一化非法值为 `mobile`。
* `app_service.handle_chat()`、`_run_html_generation()`、`_generate_with_limit()`、`_build_project_messages()` 传递设备偏好。
* 在 `_build_project_messages()` 中追加独立 system message，覆盖默认生成/修改 prompt 的布局目标。

## Technical Notes

* 已检查 `frontend/src/api/index.ts`：`sendChat()` 当前只提交 `{ message }`。
* 已检查 `frontend/src/components/ChatPanel.vue`：首页 composer 和聊天输入 toolbar 都可接入轻量控件。
* 已检查 `backend/routers/chat.py`：`ChatRequest` 当前只有 `message`。
* 已检查 `backend/services/app_service.py`：prompt 由 `_build_project_messages()` 组装。
* 已检查 `backend/services/ai_service.py`：基础生成/修改提示词仍要求 mobile-first，设备偏好需要额外 system prompt 明确目标布局。
