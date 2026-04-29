# brand: 通用用户定位与轻量有趣文案

## Goal

根据产品重新定位，去掉中天钢铁特定标识，弱化工号概念，并将首页/登录页标语从偏工作工具的表达优化为更面向 C 端用户的轻量、有趣、好玩的创作体验。

## What I already know

* 用户明确要求：去掉中天钢铁标识，弱化工号概念，用用户名代替。
* 用户进一步明确：面向 C 端用户时，轻量级、好玩、有趣才是吸引点，需优化“用一句话生成登记页、活动页、看板和日常小工具”等偏工作工具标语。
* 当前系统仍使用 `employee_no` 作为后端/API/数据库字段。
* 本任务应优先调整前端用户可见文案，不做账号模型/API/数据库字段重命名。
* 已发现主要可见位置：`LoginPanel.vue`、`EmployeeAdmin.vue`、`App.vue`。
* 后端存在中文错误 detail 使用“工号”，如不调整会在错误时暴露旧概念。

## Requirements

* 登录页去掉“中天钢铁内部工具”，改为更轻量有趣的 QuickDa 定位文案。
* 首页 Hero、登录 Hero、示例和输入提示弱化登记/看板/工作工具场景，突出轻量、好玩、有趣的小应用创作。
* 登录/注册表单把“工号”可见标签、提示、错误改为“用户名”。
* 顶部管理员入口和后台管理页把“工号管理/员工访问”改为“用户管理/用户访问”。
* 用户列表中仍可显示底层账号值，但标签用“用户名”。
* 尽量保留 `employee_no` API、类型、变量和后端字段兼容，不做破坏性重命名。

## Acceptance Criteria

* [x] 前端主要 UI 不再显示“中天钢铁”。
* [x] 首页/登录页标语突出轻量、有趣、好玩的小应用创作，不再使用偏工作工具的旧标语。
* [x] 前端主要 UI 不再以“工号”作为用户登录/管理概念，改为“用户名”。
* [x] 登录、注册、管理页仍可使用现有 5 位账号规则。
* [x] `npm --prefix frontend run build` passes。
* [x] 不修改数据库模型或 API payload 字段。

## Definition of Done

* 前端构建通过。
* 变更范围保持在文案/轻量错误提示，不做账号系统重构。

## Out of Scope

* 不重命名 `employee_no` 后端字段、API payload、数据库列或 TypeScript API 类型。
* 不改认证规则和默认账号格式。
* 不引入组织/租户/企业品牌配置。

## Technical Approach

* 只替换用户可见中文文案。
* 保留 `employeeNo` 变量、`employee_no` payload、`Employee` 类型和后端模型名称。
* 后端仅可调整用户可展示的中文错误 detail，不改接口结构。

## Technical Notes

* 已搜索前端：主要命中 `LoginPanel.vue`、`EmployeeAdmin.vue`、`App.vue`、`api/index.ts`。
* `api/index.ts` 的 `employee_no` 命中为跨层兼容字段，按 out-of-scope 保留。
* 后端 `routers/auth.py`、`routers/admin.py` 存在可展示中文错误文案，可轻量改为“用户名”。
