# AGENTS.md · 多 Agent 协作入口（模板 · 配套工作手册 v7）

> Claude / Codex / 其他编程 Agent 进入项目时先读本文件，再读 ENGINEERING.md、PRD.md、PLAN.md。Claude Code 项目仍可保留 CLAUDE.md，但跨工具规则以本文件为准。
> 加载方式：Codex 自动加载本文件（从仓库根到当前目录逐级拼接，**合计默认上限 32 KiB**，超出部分读不到——本文件保持精简，细节下沉 ENGINEERING.md）；Claude Code 只自动读 CLAUDE.md，由其中的 `@AGENTS.md` import 带入。

## 运行模式声明（先于一切规则）

{示例：布局断言基准视口为 1280px 桌面优先（见 D6）；i18n 条款已挂起（见 D××）。没有偏离默认之处就写"无"。}

> **默认模式不需要声明**：任务状态写在 PLAN.md（人读），不使用 `.vibe/`——这是被真实项目（25+ 个里程碑）验证过的路径。需要在此**显式声明并注明决策号**的是**偏离默认的地方**：替换布局基准视口、挂起某条硬规则、启用实验性的 `.vibe/` 机器状态层（手册附录 C）等。显式声明比每个会话口头解释便宜，也比默默不遵守诚实。未声明的豁免一律视为违规。

## 项目真相源

- 产品真相：PRD.md
- 当前任务与任务状态真相：PLAN.md
- （仅声明启用了实验性 `.vibe/` 的项目）机器任务状态：.vibe/tasks/*.json、.vibe/project.json
- 工程规则：ENGINEERING.md
- 决策历史：DECISIONS.md
- 视觉真相：DESIGN.md
- 版本历史：CHANGELOG.md
- 会话自查协议：SELFCHECK.md（配合上方模式声明的不适用注记）
- 部署真相：DEPLOY.md（有生产环境后）
- 运维真相：OPERATIONS.md（有生产环境后）

## Agent Ownership

- Product Owner：{人类 owner，负责拍板 PRD / 范围 / 取舍}
- Integration Owner：{人类或指定 Agent，只负责集成、冲突、门禁，不承接普通功能任务}
- Task Owner：每个任务只能有一个当前 owner；多人或多 Agent 并行时，必须先 claim 再动手。
- 单人项目三者可兼任，但检查时分开问：我现在是在实现，还是在集成？

## Task Claim / State

PLAN.md 中每个任务增加一行：

```text
状态：todo / claimed / in_progress / blocked / review / integrated
Owner：{agent-id / 人名}
Worktree：{路径或分支名}
Writable Scope：{允许改的目录/文件}
Evidence：{PR / commit / checks / screenshot / log}
```

任务状态以 PLAN.md 为准。任务行两种写法都可以、同一份 PLAN 只用一种：复选框，或表格 `| M3-T4 | 内容 | ⬜ / ✅ |`。（启用了实验性 `.vibe/` 的项目：机器状态以 `.vibe/tasks/{task-id}.json` 为准；与 PLAN 冲突时先停下，由 Integration Owner 修正。）

认领规则：

- claim 前先拉取最新 main，并确认任务仍是 todo。
- 把状态改为 claimed，填 Owner / Worktree / Writable Scope，单独提交或随任务首个提交提交。
- 只写 Writable Scope；确需越界时先停下，在 PLAN.md 任务下追加 Scope Change 说明。
- blocked 必须写明阻塞条件、已尝试证据、需要谁拍板。

## Worktree Isolation

- 每个并行 Agent 使用独立分支或 worktree。
- 分支命名：`agent/{agent-id}/{task-id}-{slug}`。
- 禁止两个 Agent 同时写同一文件，除非 Integration Owner 安排顺序合并。
- 共享契约文件、schema、迁移、锁文件、设计 token、**生成文件（types.gen 类，只能经生成命令再生）**、**CI 配置**属高冲突区，默认只能由一个 owner 修改。

## Integration Role / Gate

Integration Owner 的职责：

- 审查所有越界改动和共享契约改动。
- 合并前确认任务状态、证据链、测试、CI、冲突解决记录完整。
- 维护 integration 分支或 PR 队列。
- 合并后把任务状态改为 integrated，并在 PLAN / CHANGELOG 留痕。

合并门禁：

- Writable Scope 无越界，或越界已获确认。
- 四根命令绿：`{lint}` / `{typecheck}` / `{build}` / `{test}`。
- 涉敏任务安全审计无高危。
- 前端任务有布局断言或截图证据。
- PR / commit / checks / 关键证据已写入 Evidence。

## Handoff Packet

Agent 结束任务或被打断时必须留下：

```text
Task：
Owner：
Branch/Worktree：
Changed Scope：
Current State：
What changed：
Evidence：
Known risks：
Next step：
```

默认写进 PLAN 对应任务的 Evidence。（启用了实验性 `.vibe/` 的项目：同时写入对应 task JSON 的 `handoff` 字段。）

## Skills 迁移建议

- 高频角色提示词先沉淀为 `docs/skills/{skill-name}.md` 或工具原生 skill/command。
- Skill 只放稳定流程，不放项目临时状态；临时状态仍写 PLAN / DECISIONS。
- Skill 是跨工具格式（目录 + `SKILL.md`）：Claude Code 装在 `.claude/skills/`，Codex 装在 `.agents/skills/`；源文件只维护一份，禁止各改各的。跨工具共用的**规则**仍写在 AGENTS.md / ENGINEERING.md，skill 只放流程。
