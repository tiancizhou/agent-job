# fix: 历史聊天不展示生成代码

## Goal

修复重新进入应用或加载历史聊天时，LLM 生成的项目 JSON/代码内容被当作普通聊天消息展示的问题。历史聊天应展示用户可读的生成/修改结果摘要和状态，不展示大段代码或结构化生成产物。

## What I already know

* 用户反馈：聊天记录中会将历史生成的代码也展示出来。
* 当前生成能力依赖 LLM 返回项目 JSON/代码，不能影响后端生成和保存流程。
* 需要检查 `frontend/src/components/ChatPanel.vue` 的 `listConversations()` 加载/渲染逻辑。
* 需要检查后端 `Conversation` 保存逻辑，尤其是 `backend/services/app_service.py` 或 `backend/routers/chat.py`。
* 目标是轻量 bugfix：不做完整历史重构，不引入新的代码查看器。

## Requirements

* 历史聊天中不展示 LLM 返回的项目 JSON、文件内容或修改 JSON。
* 历史聊天仍展示用户发送的需求。
* 历史聊天中的助手消息应是用户可读摘要，例如“应用已生成或更新，可以在右侧预览。”或失败摘要。
* 不改变生成/修改能力，不影响 code_service 解析 LLM 原始输出。
* 对已有历史记录尽量兼容：如果数据库里已有代码内容，前端加载时也不能直接展示大段代码。

## Acceptance Criteria

* [ ] 重新进入应用后，历史消息不再出现 `{"files": ...}`、HTML/CSS/JS 大段代码或 `{"changes": ...}`。
* [ ] 用户历史需求仍正常展示。
* [ ] 新生成/修改完成后，当前会话和重新进入后的历史会话展示一致的用户可读摘要。
* [ ] 生成失败/修改失败仍能展示失败说明和错误详情。
* [ ] 前端 build 通过；如改后端，相关 backend tests 通过。

## Definition of Done

* Frontend build passes via `npm --prefix frontend run build`.
* If backend persistence behavior changes, add/update backend test where appropriate.
* No API or SSE contract breaking change unless explicitly justified.

## Out of Scope

* 完整聊天历史重构。
* 代码查看器、文件树或版本历史。
* 删除或迁移历史数据库记录。
* 改变 LLM 输出格式或 code_service 解析规则。

## Technical Approach

* 后端在 `app_service._generate_with_limit()` 保存 assistant `Conversation` 时，不再保存 LLM 原始 `reply_text`，改为保存用户可读摘要。
* `UsageRecord.reply_text` 仍保留原始输出用于用量/排查，`code_service` 也仍使用原始输出解析生成项目，不影响生成能力。
* 前端 `ChatPanel.vue` 加载历史 conversations 时，对所有 assistant 消息做兼容清洗；如果旧数据里已经存了 `files` / `changes` / HTML 代码，则展示摘要。
* 不改变 `/api/apps/{id}/conversations` 响应结构，也不新增数据库迁移。

## Technical Notes

* 已检查：`frontend/src/components/ChatPanel.vue` 历史消息 mapping。
* 已检查：`frontend/src/api/index.ts` Conversation 类型，无需改接口类型。
* 已检查：`backend/services/app_service.py` Conversation 保存，根因是 assistant conversation 保存了原始 `reply_text`。
* 已检查：`backend/routers/apps.py` conversations API，只按 app_id 返回历史记录，无需改路由签名。
