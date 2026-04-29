# brainstorm: 生成应用数据权限隔离 MVP

## Goal

记录产品决策并收敛范围：QuickApp 的定位是轻量快速生成内部小应用，不在当前阶段建设完整数据权限体系。generated app 数据能力应保持简单，避免把快速生成工具演变成重型项目开发平台。

## What I already know

* generated app 可以通过 `/api/generated/{app_id}/data/{collection}` 和 `/api/generated/{app_id}/data/{collection}/{record_id}` 持久化 JSON 数据。
* 当前 `backend/routers/app_data.py` 只检查 app 是否 active/editing/edit_failed 且有版本，不检查登录态、应用所有者、visibility 或 preview_token。
* 当前任何能猜到 active app_id 的请求都可以读写该 app 的 generated data。
* 项目已有 cookie 登录会话和 App 所有者概念：`services/auth_service.py:get_current_user()`。
* App 模型已有 `visibility` 和 `preview_token` 字段，但当前前端没有分享入口，grep 未发现 public/token 分享逻辑。
* `main.py` 的 `/generated/{app_id}/project/...` 生成文件访问同样只按 app 状态开放。
* 现有测试 `backend/tests/test_app_data.py` 覆盖 app/collection/record 隔离、状态限制、payload 限制，但没有用户权限隔离。

## Assumptions (temporary)

* 不建设完整 RBAC、成员授权、collection/record 级权限。
* 现有 app/collection/record 维度隔离和 payload 限制仍然保留。
* 如果后续做分享，再围绕分享 token 设计轻量边界，而不是先引入重权限模型。

## Open Questions

* 是否需要做一个极小的安全补丁：仅限制未 active 的应用不可读写，并保持当前 active 应用公开数据接口不变？

## Requirements (evolving)

* 不新增完整数据权限体系。
* 不新增 RBAC、应用成员、collection 权限配置或数据行级权限。
* 保持 generated app 内部调用数据 API 的方式简单。
* 保留现有 app/collection/record 隔离测试。
* 将“轻量优先，不做重权限体系”的产品判断记录清楚。

## Acceptance Criteria (evolving)

* [ ] 不产生完整权限系统实现任务。
* [ ] 不新增权限配置 UI 或复杂数据库模型。
* [ ] PRD 明确记录轻量化产品决策和未来触发条件。

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Out of Scope (explicit)

* 复杂 RBAC/按 collection 配置权限。
* 行级权限表达式。
* 管理后台权限配置 UI。
* 数据迁移/数据归属重写，除非实现中发现必须。

## Technical Notes

* 待检查：`backend/routers/app_data.py`、`backend/main.py` generated file serving、`backend/routers/apps.py` preview/share、`services/auth_service.py`、frontend sharing/preview components。
