# ENGINEERING.md · 工程规则（模板 · 配套工作手册 v7）

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

启用了实验性 `.vibe/` 的项目（手册附录 C，须在 AGENTS.md 声明）额外满足：

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

## 模块地图（`map` skill 读这里；可选）

> 项目地图的骨架。业务线照 PRD 的用户旅程 / 架构蓝图排（一行一条，箭头 = 流程顺序，没进业务线的模块算「横切」）；路径表把文件归到「模块 × 层」，自上而下**首条命中为准**，`*` 可跨目录。层 = 页面 / 接口 / 数据 / 逻辑 / 测试 / 外部（跨仓库，放对接文档）/ 关键词（问题描述里会出现的别称）。没有这一节，`map` 按目录分组。
> 云端（可选）：加一行 `发布：<命令>`（`{dir}` = 产物目录），`map --publish` 时执行；发布后自动检查"不登录能不能打开"。页面含安全欠账原文，只发到有访问控制的地方——推荐做法见 `map` skill 的「云端」一节。

{业务线}：{模块A} → {模块B} → {模块C}

| 模块 | 层 | 路径 |
|---|---|---|
| {模块A} | 页面 | {如 frontend/src/pages/*} |
| {模块A} | 接口 | {如 backend/app/api/*} |
| {模块A} | 数据 | {如 backend/app/models/*, alembic/*} |
| {模块A} | 逻辑 | {如 backend/app/services/*} |
| {模块A} | 测试 | {如 tests/test_a*} |
| {跨仓库模块} | 外部 | {对接文档路径} |
| {模块A} | 关键词 | {别称} |

## 外发限制（什么能发给第三方模型；`xreview` 与"找另一个模型讨论"都受它约束）

- 默认只发被评审的代码 diff。凭证文件（`.env*` / 私钥 / `auth.json` …）永不外发。
- 全局设计文档、名字涉及口令·权限的文件：默认扣下；要发必须**先问用户**，授权要点名接收方（`--authorized` + `--authorized-for`）。
- 本项目追加的禁区（调用 `xreview` 时逐条 `--withhold`）：{如 `data/**`、`deploy/**`、`*客户*`}
- 常设授权（可选，须记 DECISIONS）：{如 D××：PRD 可发给 Codex；不发给其他厂商}

## Vendor-neutral Adapter

- Claude Code：`CLAUDE.md` 可以保留工具特定注意事项，但不能成为唯一项目真相；共同规则用 `@AGENTS.md`、`@ENGINEERING.md` import 加载，不靠"请先读"。
- Codex：自动加载 `AGENTS.md`（合计默认上限 32 KiB，保持精简）；本文件与当前 PLAN 任务由 AGENTS.md 指到、按需读取。
- 其他 Agent：若不支持自动读文件，启动提示词必须显式要求读取上述文件。
