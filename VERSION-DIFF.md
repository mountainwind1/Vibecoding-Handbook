# 版本差异说明

## v5.2 · Single-Agent Solid

- 目标：单人 + Claude Code 长周期正式项目。
- 核心：文档规模化、Phase 模式、PRD 两层 JIT、子系统参考文档、支付检查单、UI 程序化断言、拍板门。
- 状态：稳定版，适合大多数单人项目。

## v5.3 · Multi-Agent Ready

- 目标：单人同时开多个 AI 会话 / worktree，或 Claude + Codex 混合开发。
- 核心：Agent Ownership、Task Claim/State、Worktree Isolation、Writable Scope、Integration Role/Gate、vendor-neutral adapter、Evidence Chain。
- 设计取舍：状态仍写在人读的 PLAN.md 中，保持低复杂度；不引入调度器。

## v6 · Multi-Agent Native

- 目标：多机、多 Agent 长期并行，任务状态可被机器读取和调度。
- 核心：`.vibe/tasks`、持久化项目状态、Agent runtime 与 project truth 分离、调度拓扑、contract owner/freeze、handoff packet、deterministic checks/CLI。
- 设计取舍：复杂度更高，适合需要真实并行和自动调度的项目。
