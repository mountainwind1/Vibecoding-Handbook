# v5.2 → v5.3 迁移指南

v5.3 的目标不是把单人流程改复杂，而是让现有 v5.2 项目在需要时能安全接入多个 AI 会话、多个 worktree、Claude/Codex 混合开发。

## 最小升级

1. 保留现有 v5.2 文件，不重写 PRD / PLAN / DECISIONS。
2. 新增 `AGENTS.md` 和 `ENGINEERING.md`。
3. 把 `CLAUDE.md` 中跨工具通用的规则移到 `AGENTS.md` / `ENGINEERING.md`，Claude 专属说明留在 `CLAUDE.md`。
4. 在 PLAN.md 任务模板里增加：状态、Owner、Worktree、Writable Scope、Evidence。
5. 指定一个 Integration Owner；哪怕只有你一个人，也把"实现者"和"集成者"两个角色分开检查。

## 不建议一次性迁移的内容

- 不需要把历史任务补成机器状态。
- 不需要给每个旧 commit 补 evidence。
- 不需要强制每个任务都开 worktree；只有并行时才启用。
- 不需要废弃 CLAUDE.md；v5.3 只是把它降级为 Claude 适配层。

## 升级后第一条规则

多个 Agent 同时工作前，先让每个 Agent 在 PLAN.md 里 claim 自己的任务，并写清 Writable Scope。没有 claim 的任务，不允许动手。
