# 修复 start.bat 闪退

## Goal

排查并修复 Windows 下运行 `backend/start.bat` 出错时窗口直接关闭的问题，使启动失败时用户能看到明确错误并按键退出；正常路径仍保持现有自动更新、构建、准备数据库、启动后端流程。

## What I already know

* 用户反馈现在启动 `start.bat` 时直接闪退。
* `backend/start.bat` 在 `git pull`、`npm run build`、创建虚拟环境、安装依赖、数据库准备失败时直接 `exit /b 1`。
* 双击 `.bat` 时，一旦脚本退出，窗口会立即关闭，用户看不到失败原因。

## Requirements

* 启动脚本失败时显示失败步骤和退出码。
* 双击运行失败时窗口保留，提示按任意键退出。
* 正常启动流程不改变：拉取代码、构建前端、准备后端环境、迁移数据库、启动 uvicorn。
* 不引入新的依赖或大规模重构。

## Acceptance Criteria

* [ ] `backend/start.bat` 中每个关键步骤失败时不再静默退出。
* [ ] 失败信息能指出是哪一步失败。
* [ ] 脚本语法适用于 Windows batch。
* [ ] 代码修改最小化。

## Definition of Done

* 脚本修改完成。
* 至少通过静态检查确认 batch 控制流合理。
* 如可行，用命令行方式验证失败路径不会直接关闭。

## Out of Scope

* 不改变后端服务架构。
* 不替换启动脚本为 PowerShell。
* 不调整 LLM、数据库、前端业务逻辑。

## Technical Notes

* 主要文件：`backend/start.bat`。
