# Next.js TypeScript Static Export MVP

## Goal

将 QuickDa 生成应用从纯 HTML/CSS/JS 输出标准化为 Next.js + TypeScript 源项目，同时保持当前轻量预览体验：后端对生成结果进行构建校验，成功后只把静态导出产物作为预览文件服务，不运行常驻 Next.js 服务。

## What I already know

* 用户已确认先做“Next.js 项目模板输出 + 构建校验 + 静态导出预览”的 MVP。
* 当前生成链路要求 LLM 返回 `{ "files": [...] }`，并保存到 `data/apps/{app_id}/project/`。
* 当前预览入口是 `/generated/{app_id}/project/index.html`，前端 iframe 已依赖这个静态入口。
* 当前 `code_service` 对新项目要求 `index.html`、`css/style.css`、`js/app.js`，文件上限 20 个、单文件 300KB。
* 当前保存逻辑已经支持临时目录 + 原子替换，失败时应保留上一个可用版本。
* Next.js 静态导出通过 `next build` 生成 `out/`，预览应服务 `out/` 内容而不是源文件目录。

## Requirements

* LLM 新建应用时输出 Next.js + TypeScript 源项目，而不是纯 HTML 项目。
* 生成 JSON 仍使用 `{ "files": [{ "path": string, "content": string }] }`，避免改动 SSE/前端聊天协议。
* MVP 使用 Next.js App Router + TypeScript 的固定最小模板：`package.json`、`next.config.ts`、`tsconfig.json`、`next-env.d.ts`、`app/layout.tsx`、`app/page.tsx`、`app/globals.css`。
* `next.config.ts` 必须启用静态导出：`output: "export"`，配置 `images.unoptimized = true`，并使用 `assetPrefix: "./"` 约束 `_next` 资源适配嵌套预览路径。
* 生成/修改后的项目必须避免 Next.js 运行时特性：API routes、Route Handlers、Server Actions、Middleware、SSR、依赖请求上下文的 cookies/headers。
* 交互逻辑必须在浏览器端执行；需要持久化时继续调用现有 `/api/generated/{app_id}/data/{collection}` 接口。
* 后端保存源文件到应用目录的源项目位置，并运行构建校验。
* 构建成功后，将静态导出 `out/` 产物发布到现有预览目录 `data/apps/{app_id}/project/`，保持 `/generated/{app_id}/project/index.html` 不变。
* 构建、解析、验证或导出失败时，设置 `failed` / `edit_failed`，返回中文错误；编辑失败必须保留上一个可用预览版本。
* 修改应用时，LLM 应读取并修改 Next.js 源项目文件，修改后重新构建并发布静态导出产物。
* 保留已有设备偏好和风格 prompt 注入能力，让它们约束 Next.js 页面布局和视觉风格。

## Acceptance Criteria

* [ ] 新建应用的系统 prompt 明确要求 Next.js + TypeScript 静态导出项目，并禁止纯 HTML 项目结构。
* [ ] `parse_project_json_or_raise()` 接受并校验 Next.js 必要源文件，拒绝缺失必要文件、不安全路径、不支持后缀和超限内容。
* [ ] `save_project()` / `save_changes()` 不直接发布未构建源文件；构建成功后预览目录包含 `index.html` 和 `_next/static/...` 等导出产物。
* [ ] 构建失败不会删除或覆盖上一个可用 `project/` 预览目录。
* [ ] `/generated/{app_id}/project/index.html` 继续可用于 iframe 预览，且 CSS/JS 从同一 `project/` 目录下加载，不要求前端协议改动。
* [ ] 后端测试覆盖：Next.js 必要文件校验、非法路径/后缀拒绝、构建失败保留旧预览、修改后重新构建发布。
* [ ] 前端 `npm --prefix frontend run build` 通过。
* [ ] 后端测试命令通过：`backend/.venv/Scripts/python -m unittest discover -s backend/tests -p "test_*.py" -v`。

## Definition of Done

* Tests added/updated for backend validation and build/publish behavior.
* Frontend build and backend tests pass.
* `.trellis/spec/` 更新跨层生成产物契约、构建失败行为和预览边界。
* 不引入常驻 Next.js 服务，不改变现有聊天 SSE 协议。

## Technical Approach

1. 将生成边界拆成两个目录概念：
   * `source/`：保存 LLM 生成的 Next.js + TypeScript 源项目。
   * `project/`：保存 `next build` 后的静态导出产物，继续作为预览目录。
2. 更新 `ai_service.PROJECT_GENERATE_SYSTEM_PROMPT` 和 `PROJECT_MODIFY_SYSTEM_PROMPT`，要求输出 Next.js 静态导出源文件、使用嵌套预览安全的 `_next` 资源路径配置，并禁止服务器运行时特性。
3. 扩展 `code_service`：
   * 支持 Next.js 源文件后缀和路径校验。
   * 校验必要源文件。
   * 原子保存源项目。
   * 调用构建步骤，必要时将导出产物中的根路径 `/_next/...` 资源引用改写为相对路径，再把 `out/` 原子发布到 `project/`。
4. `app_service._save_generation_result()` 仍返回 `/generated/{app_id}/project/index.html`，状态和错误处理沿用现有 `ProjectValidationError` 机制。
5. 修改读取当前项目文件逻辑，使编辑 prompt 读取源项目而不是静态导出产物。

## Decision (ADR-lite)

**Context**: QuickDa 希望生成结果更标准、可维护，但产品定位仍是轻量、即时预览。如果直接运行每个 Next.js 应用，会增加进程管理、端口、资源隔离和运维成本。

**Decision**: MVP 生成 Next.js + TypeScript 源项目，后端执行构建校验，并只发布静态导出产物到现有预览目录。

**Consequences**: 预览链路保持简单，前端改动最小；代价是后端需要 Node/npm 构建环境，生成项目必须避开服务端运行时能力，构建耗时会进入生成等待链路。

## Out of Scope

* 不运行 `next dev` / `next start`，不为每个生成应用启动 Node 服务。
* 不支持任意 npm 依赖安装；MVP 固定 Next/React/TypeScript 基础依赖。
* 不支持 Next API routes、Route Handlers、Server Actions、Middleware、SSR。
* 不新增版本历史 UI；编辑失败继续保留上一个可用版本即可。
* 不改变前端 iframe 预览入口和聊天 SSE payload。
* 不在本任务实现复杂构建沙箱或远程构建队列。

## Research References

* [`research/nextjs-static-export.md`](research/nextjs-static-export.md) — Next.js + TypeScript 静态导出的最小文件结构、构建输出和运行时禁用约束。

## Technical Notes

* `backend/services/ai_service.py` 当前 prompt 仍要求纯静态 HTML 项目，需要改成 Next.js + TypeScript。
* `backend/services/code_service.py` 当前要求 `index.html/css/style.css/js/app.js`，且允许后缀不足以覆盖 `.ts/.tsx` 和静态导出资源。
* `backend/services/app_service.py` 当前 `_save_generation_result()` 直接 `save_project()` 后返回 `/generated/{id}/project/index.html`，应改成保存源项目 + 构建发布。
* `backend/main.py` 的 `/generated/{app_id}/project/{file_path:path}` 可以继续服务静态导出文件，只要 `resolve_project_file()` 允许 `_next/static` 产物路径和后缀。
* `frontend/src/components/ChatPanel.vue` 的 `projectPreviewUrl()` 可保持不变。
