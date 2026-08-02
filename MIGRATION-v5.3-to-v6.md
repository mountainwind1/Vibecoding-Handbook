# v5.3 → v6 迁移指南

v5.3 把多 Agent 协作写进 PLAN.md；v6 把这些状态迁移到 `.vibe/`，让状态可被程序读取、检查和集成。

## 最小迁移

1. 新增 `.vibe/project.json`，写入默认分支、当前 milestone、topology、Integration Owner。
2. 为当前未完成任务各建一个 `.vibe/tasks/{task-id}.json`。
3. 把 PLAN.md 里的 Owner / Worktree / Writable Scope / Evidence 复制到 task JSON。
4. 新增 `.vibe/checks/default.json`，把四根命令和安全检查写成可执行条目。
5. 保留 PLAN.md 的人读叙事，不要把 PRD/PLAN 全部塞进 JSON。

## 迁移边界

- 历史已完成任务不必全部补 task JSON；从当前 milestone 开始即可。
- `.vibe/runtime/` 只放临时运行状态，不作为合并依据。
- CLI 可以先手写检查脚本；只要 JSON 结构稳定，就已经具备 v6 的核心收益。
