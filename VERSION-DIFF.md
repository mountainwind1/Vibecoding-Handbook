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

## v6.1 / v6.2 · v6 手册内的增补

- v6.1：真实项目（25 个里程碑）复盘回填——护栏 10–12、A5 强化、A9 / A10、DEPLOY / OPERATIONS 模板、"v6 模板 + v5.3 模式"合法化。
- v6.2：过时工具事实修正（`ultrathink`、写死的模型名、`@AGENTS.md` import、commands → skill）；`prog` 进度块、`close` 收口门、`security-auditor` 子代理、`/kof a` 自动循环。v6 手册冻结于此。

## v7 · Field-Proven

- 目标：默认路径只留被真实项目验证过的机制。
- 核心：多 Agent 协作协议（源自 v5.3）为默认，任务状态在人读的 PLAN.md；`xreview` 异构模型复核门，外发限制机制化；流程以可安装的 skill 交付（`kof` / `prog` / `close` / `xreview`）；项目模板移入 `templates/`。
- 设计取舍：`.vibe/` 机器状态层降为**实验**（附录 C）——它设计于 v6，但没有真实项目用过；同期 Claude Code 与 Codex 都原生有了子代理、worktree 隔离与长程执行。运行模式声明的方向随之翻转：默认不需要声明，偏离默认（含启用 `.vibe/`）才声明。
- 破坏性：模板路径变了、声明方向变了。升级见 `MIGRATION-v6-to-v7.md`。
