# .vibe · 机器可读项目状态（实验 · 可选）

> **状态：实验，默认不启用。** 这一层设计于 v6，但截至 v7 没有任何真实项目用过它，配套 CLI 也只是设计草案。默认的协作方式是把任务状态写在 PLAN.md 里（手册「多 Agent 协作协议」）。要用它：把本目录复制到项目根，并在项目 `AGENTS.md` 的「运行模式声明」里显式声明启用、注明决策号。说明见手册附录 C。

`.vibe/` 保存 Agent 协作的 project truth。它不是模型记忆，也不是临时草稿；能影响调度、合并、证据和门禁的状态都应提交进 git。

## 目录

- `project.json`：项目级状态、拓扑、默认 gate、protected scopes。
- `tasks/*.json`：每个任务的机器状态。
- `checks/*.json`：deterministic checks 定义。
- `.schema/*.schema.json`：任务和项目状态 schema 草案。
- `runtime/`：本地 Agent runtime 占位，默认不把临时内容当项目真相。
