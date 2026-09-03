# ENGINEERING.md · 工程规则（模板 · 配套工作手册 v6）

> 本文件只写与具体 AI 供应商无关的工程事实。Claude、Codex、IDE Agent 都按这里执行。

## 根命令

> 一律经聚合器（Makefile / just / npm scripts）暴露，**本地、CI、部署三处跑同一套目标**——这是防"本地绿 CI 红"的结构性手段，不是纪律手段。

- Lint：`{lint}`
- Typecheck：`{typecheck}`
- Build：`{build}`
- Test：`{test}`
- 开发环境：`{dev}`
- 数据迁移：`{db-upgrade} / {db-downgrade}`
- 契约类型生成：`{api-types}`
- CI 状态：`{gh pr checks / 平台等价命令}`

## Writable Scope

- 默认只允许修改 PLAN 任务声明的目录/文件。
- 共享文件默认受保护：契约、schema、迁移、锁文件、CI、设计 token、权限配置。
- 生成文件（如 `types.gen.*`）**禁止手改**，唯一合法修改方式是重新运行生成命令；CI 以「重跑生成 + `git diff --exit-code`」闸住漂移——"禁止手改"管的是别写错，这条闸管的是**别忘了写**。
- 需要改共享文件时，任务必须升级为【单独+确认】，并由 Integration Owner 合并。

## Contract Owner / Freeze

- 跨层契约必须有 owner（通常指定到泳道，如后端）。
- 每个里程碑开工先定稿该切片契约再冻结——冻结是两泳道并行的起跑线。
- 契约 freeze 后，前后端可并行；freeze 之后的破坏性变更必须重新开决策记录，且**必须重跑生成并与 schema 变更同一 commit 提交**（生成物滞后一个 commit，两端就各自为真）。
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

v6 项目必须额外满足：

- `.vibe/tasks/{task-id}.json` 状态迁移合法。
- changed files 全部落在 `writable_scope`，或 protected scope approval 已记录。
- task JSON 的 checks 与 evidence 覆盖本次合并。
- contract freeze 状态允许合并。

## 数据与运行约定（{项目按需填写}）

> 业务红线的工程表达——那些"违反了不会立刻报错、但事后代价巨大"的约定，写成一条条可判定的禁令，条条注出处（D××）。

- {示例：坐标恒用 longitude/latitude 全拼，序列化时经度在前；展示层转换只在组件内做，数据层恒定}
- {示例：业务主表只软删除，`DELETE FROM {核心表}` 属禁止操作}
- {示例：历史/审计表 append-only，禁止 UPDATE；原始来源数据不可覆盖}
- {示例：密钥只在 `.env`；`Read(.env)` 已在 permissions 对 AI 拒读}

## Vendor-neutral Adapter

- Claude Code：`CLAUDE.md` 可以保留工具特定注意事项，但不能成为唯一项目真相。
- Codex：进入项目先读 `AGENTS.md` + `ENGINEERING.md` + 当前 PLAN 任务。
- 其他 Agent：若不支持自动读文件，启动提示词必须显式要求读取上述文件。
