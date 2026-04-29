# Admin Configurable LLM Settings

## Goal

让管理员可以在 QuickDa 后台配置大模型连接信息，避免 `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 只能写死在 `.env` / `config.py` 中。配置保存后，新发起的命名、生成、编辑请求应使用后台配置；未配置时继续使用 `.env` 作为首次部署和本地开发 fallback。

## What I already know

* 当前 `backend/config.py` 的 `Settings` 强制读取 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
* `backend/services/ai_service.py` 通过传入的 `Settings` 读取 LLM base URL、model 和 API key。
* `backend/services/app_service.py` 在命名、生成、编辑时把 `settings` 传给 `ai_service`。
* 当前后台管理在 `frontend/src/components/EmployeeAdmin.vue`，已有“用户管理”和“风格管理”两个标签。
* 当前 admin API 在 `backend/routers/admin.py`，通过 `require_admin` 限制管理员访问。
* 当前数据库使用 SQLAlchemy model + Alembic migration，已有 `0001_initial_schema.py` 和 `0002_app_data_records.py`。

## Assumptions

* MVP 只支持一个全局默认 LLM 配置，不做多供应商路由或按用户/应用选择模型。
* API Key 需要可更新，但接口和前端不回传明文，只显示掩码状态。
* `.env` 配置保留为 fallback，避免新库/首次启动时没有数据库配置导致系统不可用。

## Open Questions

* None.

## Requirements

* 新增数据库表保存全局 LLM 配置。
* 管理员可查看当前配置摘要：base URL、model、是否已配置 API key、API key 掩码。
* 管理员可保存配置：base URL、model、API key。
* MVP 接受 API Key 明文存储在数据库中；但 GET 接口和前端展示不得返回明文，只显示掩码。
* 如果保存时 API key 留空，保留原 API key；如果首次配置且没有可用 API key，则返回中文错误。
* LLM 请求优先使用数据库配置；数据库没有完整配置时 fallback 到 `.env` 的 `settings`。
* 配置接口必须使用 `require_admin`。
* API 响应不得返回完整 API key。
* 前端后台新增“模型配置”标签，沿用现有后台管理视觉风格。
* 保存成功后，后续新生成/编辑/命名请求使用新配置；不要求影响已经进行中的 SSE 生成任务。

## Acceptance Criteria

* [ ] 管理员能在后台看到“模型配置”标签。
* [ ] 管理员能填写/修改 Base URL、模型名称、API Key 并保存。
* [ ] API Key 保存后只显示掩码或“已配置”，不在 GET 响应中返回明文。
* [ ] 未配置数据库模型设置时，现有 `.env` 配置继续可用。
* [ ] 配置保存后，新发起的 LLM 请求使用数据库配置。
* [ ] 非管理员无法访问模型配置接口。
* [ ] 后端测试覆盖 admin 权限、fallback、保存/读取掩码、LLM 调用使用 DB 配置。
* [ ] 前端 `npm --prefix frontend run build` 通过。
* [ ] 后端测试命令通过：`backend/.venv/Scripts/python -m unittest discover -s backend/tests -p "test_*.py" -v`。

## Definition of Done

* Backend model/migration/API/service/tests complete.
* Frontend admin UI/API types complete.
* Tests and frontend build pass.
* `.trellis/spec/` 更新 LLM 配置的可执行契约和安全边界。

## Technical Approach

1. 新增 ORM model 与 Alembic migration，例如 `LLMSetting` 或 `SystemSetting`。
2. 新增 service 负责读取有效 LLM 配置：优先 DB，缺失时 fallback 到 `settings`。
3. 调整 `ai_service` 或 `app_service` 调用路径，让命名、生成、编辑使用有效配置对象。
4. 在 `admin.py` 增加：
   * `GET /api/admin/llm-settings`
   * `PUT /api/admin/llm-settings`
5. 在 `frontend/src/api/index.ts` 增加类型和请求函数。
6. 在 `EmployeeAdmin.vue` 增加“模型配置”标签和表单。

## Decision (ADR-lite)

**Context**: `.env` 配置适合部署初始化，但不适合运营中切换模型、供应商或密钥。管理员后台已经承载用户和风格配置，模型配置放在同一后台入口符合当前产品结构。

**Decision**: MVP 做一个全局 LLM 配置，管理员通过后台更新；运行时优先读数据库配置，`.env` 作为 fallback；API Key 明文入库，但只允许后端运行时读取，管理 API 只返回掩码。

**Consequences**: 配置修改无需改文件或重启才能被新任务使用；实现简单直接。代价是数据库备份和访问权限需要按包含敏感密钥处理。

## Out of Scope

* 不做多供应商列表或模型路由策略。
* 不做按用户/应用选择不同模型。
* 不做用量价格配置和成本计费规则。
* 不做实时中断/切换正在进行的生成任务。
* 不做外部密钥管理系统集成。

## Technical Notes

* `backend/config.py` 当前 `LLM_*` 为必填；如果要支持纯后台配置，后续可放宽为可选，但 MVP 先保留 `.env` fallback。
* `backend/services/ai_service.py` 当前类型依赖 `Settings`，可通过引入轻量 dataclass/protocol 避免把 DB model 直接传给 HTTP 调用函数。
* `frontend/src/components/EmployeeAdmin.vue` 已有标签结构和错误状态，可直接新增第三个 tab。
* `frontend/src/api/index.ts` 是后台 API 类型和请求函数的集中位置。
