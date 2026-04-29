# 生成产物校验和失败恢复

## Goal

提升 LLM 生成/修改应用时的稳定性：在保存文件前校验结构化输出和项目文件约束，在失败时给用户明确反馈，并避免半成品覆盖已有可用版本。

## Requirements

* 校验 LLM 输出 JSON 顶层结构。
* 校验生成文件与修改变更格式。
* 保存前校验路径安全、文件数量、文件大小、入口文件。
* 解析或写入失败时返回明确错误状态和通用中文失败详情。
* 失败恢复采用原子保存：先完整校验并写入临时位置，成功后再替换目标项目；失败时保留旧项目。
* 修改保存也必须避免部分写入：先基于当前项目构建临时完整项目，变更全部成功后再替换。
* 前端直接展示后端返回的通用失败详情，不维护错误码映射。
* 不新增显式重试按钮；用户继续在聊天框发送或调整需求即可再次触发生成/修改。

## Acceptance Criteria

* [ ] 非 JSON 或不符合结构的 LLM 输出不会写入项目目录。
* [ ] 生成结果缺少入口文件时失败并给出明确错误。
* [ ] 修改结果中非法路径、非法内容或缺少现有项目时不会部分写入。
* [ ] 已有可用项目在失败生成/修改后仍可访问。
* [ ] SSE `result` 事件包含失败详情，前端失败面板能展示该详情。
* [ ] 后端测试覆盖主要失败场景和原子保存行为。

## Definition of Done

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Technical Approach

* 在 `backend/services/code_service.py` 中把解析失败从 `None` 升级为可区分的校验错误，保留调用层能显示的中文原因。
* 将 `save_project()` 改为原子保存：验证全部文件，写入同级临时目录，完成后替换目标 `project` 目录，失败则清理临时目录并保留旧目录。
* 将 `save_changes()` 改为基于当前项目目录复制到临时目录、应用全部变更、验证入口文件仍存在，再替换目标目录。
* 在 `backend/services/app_service.py` 中捕获校验/保存失败原因，通过 SSE `result` data 返回 `error` 字段，并设置 `failed` 或 `edit_failed`。
* 在前端 SSE 处理和 `MessageBubble.vue` 中透传并展示 `error` 文案；没有 error 时保留现有通用文案。

## Decision (ADR-lite)

**Context**: 当前链路已有基础约束，但保存时可能先删除或逐个覆盖现有文件，且失败反馈不够明确。

**Decision**: 本 MVP 采用“原子保存 + 通用中文失败详情”，不做显式重试按钮、错误码映射或完整版本历史。

**Consequences**: 实现范围较小，能直接提升稳定性和用户反馈；未来如需版本历史，可在成功保存点之上扩展快照/回滚能力。

## Out of Scope

* 完整应用版本历史、版本对比、版本回滚 UI。
* 显式重试按钮或自动重试策略。
* 前端错误码到文案的独立映射体系。
* 多租户/细粒度数据权限改造。
* 生成质量评分或自动修复 LLM 输出。

## Technical Notes

* `backend/services/code_service.py` 已有路径安全、文件数量、文件大小、入口文件等基础约束。
* `parse_project_json()` 当前要求生成结果包含 `index.html`、`css/style.css`、`js/app.js`。
* `save_project()` 当前在写入前会删除现有 project 目录，生成失败或写入中断可能破坏上一个可用版本。
* `save_changes()` 当前直接逐个覆盖文件，修改失败可能留下部分变更。
* `backend/services/app_service.py` 当前只返回 `failed/edit_failed/busy/active` 等状态，缺少可展示的具体失败原因。
* 前端已有失败展示面板和文案归一化逻辑，但 SSE `result` 事件目前没有承载错误详情。
