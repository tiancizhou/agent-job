# brainstorm: 应用版本历史与回退 MVP

## Goal

记录产品决策：暂不实现应用版本历史。现有生成产物原子保存已经能保证修改失败时保留上一个可用项目，当前阶段不额外维护可浏览/可回退的版本链。

## What I already know

* 上一任务已实现生成/修改保存的原子替换，失败时保留旧项目。
* `App.version` 当前是单个递增整数，用于预览缓存刷新和状态判断。
* 现有数据库没有应用版本历史表；当前 Alembic 最新版本是 `0002_app_data_records`。
* `app_service._generate_with_limit()` 在生成/修改成功后递增 `app.version`，失败不递增。
* `code_service.save_project()` 和 `save_changes()` 当前只维护 `data/apps/{app_id}/project/` 当前版本目录。
* `GET /api/apps/{app_id}/preview` 当前只返回当前项目预览 URL。
* 前端 `ChatPanel.vue` 当前只展示实时预览，没有版本历史入口。
* 用户希望下一步实现应用版本历史与回退 MVP。

## Assumptions (temporary)

* MVP 优先支持成功版本的保存、列表展示和回退，不做复杂 diff。
* 版本快照应复用现有项目文件结构，而不是只存数据库元数据。
* 回退本质上应把选中的历史版本恢复为当前 `project`，并递增当前应用版本。

## Open Questions

* 无。当前决策是取消该功能，不进入实现。

## Requirements (evolving)

* 不新增应用版本历史表。
* 不新增版本列表、历史预览、手动回退 UI。
* 保留现有失败回退语义：修改失败时不覆盖当前可用项目。

## Acceptance Criteria (evolving)

* [ ] 不产生代码实现任务。
* [ ] 不新增数据库迁移或前端版本历史入口。
* [ ] 决策记录清楚说明为什么暂不做版本历史。

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Out of Scope (explicit)

* 版本 diff/对比 UI。
* 多人协作冲突解决。
* 自动命名版本或用户手动填写版本说明。
* 清理策略/版本数量上限，除非实现中发现必须限制。

## Technical Notes

* 待检查：`backend/models.py`、Alembic migrations、`backend/services/code_service.py`、`backend/services/app_service.py`、`backend/routers/apps.py`、`frontend/src/api/index.ts`、`frontend/src/components/ChatPanel.vue`。
