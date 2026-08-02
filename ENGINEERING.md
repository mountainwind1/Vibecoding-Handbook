# ENGINEERING.md · 工程规则（模板 · 配套工作手册 v5.3）

> 本文件只写与具体 AI 供应商无关的工程事实。Claude、Codex、IDE Agent 都按这里执行。

## 根命令

- Lint：`{lint}`
- Typecheck：`{typecheck}`
- Build：`{build}`
- Test：`{test}`
- CI 状态：`{gh pr checks / 平台等价命令}`

## Writable Scope

- 默认只允许修改 PLAN 任务声明的目录/文件。
- 共享文件默认受保护：契约、schema、迁移、锁文件、CI、设计 token、权限配置。
- 需要改共享文件时，任务必须升级为【单独+确认】，并由 Integration Owner 合并。

## Contract Owner / Freeze

- 跨层契约必须有 owner。
- 契约 freeze 后，前后端可并行；freeze 之后的破坏性变更必须重新开决策记录。
- 契约文件是单一真相，禁止在应用层复制一份相似 schema。

## Evidence Chain

每个可合并任务至少留下：

- 任务 ID 与 owner。
- branch / commit / PR。
- 改动范围。
- 本地命令结果。
- CI 结果。
- 关键人工或浏览器验证证据。
- 风险和遗留项。

证据链写回 PLAN.md 的 Evidence 字段；大型 Phase 可另建 `EVIDENCE.md`，PLAN 只留链接。

## Integration Gate

合并前检查：

- 任务状态为 review。
- 没有未解释的 Writable Scope 越界。
- 四根命令绿，CI 绿。
- 涉敏任务安全审计无高危。
- 数据迁移、契约、锁文件变更已由 owner 复核。
- CHANGELOG / DECISIONS / PRD / DESIGN 按需同步。

## Vendor-neutral Adapter

- Claude Code：`CLAUDE.md` 可以保留工具特定注意事项，但不能成为唯一项目真相。
- Codex：进入项目先读 `AGENTS.md` + `ENGINEERING.md` + 当前 PLAN 任务。
- 其他 Agent：若不支持自动读文件，启动提示词必须显式要求读取上述文件。
