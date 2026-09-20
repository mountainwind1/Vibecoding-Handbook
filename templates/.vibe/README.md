# .vibe · v6 机器可读项目状态

`.vibe/` 保存 Agent 协作的 project truth。它不是模型记忆，也不是临时草稿；能影响调度、合并、证据和门禁的状态都应提交进 git。

## 目录

- `project.json`：项目级状态、拓扑、默认 gate、protected scopes。
- `tasks/*.json`：每个任务的机器状态。
- `checks/*.json`：deterministic checks 定义。
- `.schema/*.schema.json`：任务和项目状态 schema 草案。
- `runtime/`：本地 Agent runtime 占位，默认不把临时内容当项目真相。
