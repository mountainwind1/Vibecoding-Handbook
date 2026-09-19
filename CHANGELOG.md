# CHANGELOG.md · 版本日志（模板 · 配套工作手册 v6）

> 只增不改，新条目加在顶部。PRD 是"当前真相"，历史变更全在这里。
> 版本号 ↔ 里程碑映射：MVP 期每合并一个里程碑记一条 `0.{n}.0`（M0=0.1.0、M1=0.2.0…，由收口验收门任务追加）；
> 正式上线 = `1.0.0`；上线后跟改动半径走（手册阶段 4.6）：微调 1.0.x / 常规改动 1.x.0 / 不兼容重大升级才 x.0.0。
> **轻量模式**：条目由收口验收门顺手写、最少一行"新用户现在能完成什么"；不为版本号单独开决策——里程碑编号就是事实上的版本。

---

## [Unreleased]
- {进行中、尚未发版的变更}
### 变更（v6.2 批次 0 · 对照 2026-09 的 Claude Code / Codex 修正过时事实）
- 提示词末尾的 `ultrathink` 全部移除（该关键词在 Claude Code 已失效）；正文改用工具中立的"高 / 默认 / 低推理档位"。
- 分档表不再写死 Opus / Sonnet / Haiku：正文只写"旗舰 / 主力 / 轻量"，新增「模型档映射表」与「工具适配表」（Claude Code ↔ Codex CLI），模型换代只改这一处。
- 规则文件加载机制化：CLAUDE.md 模板用 `@AGENTS.md`、`@ENGINEERING.md` import 取代"请先读"；写明 Codex 自动加载 AGENTS.md 且合计默认上限 32 KiB（AGENTS.md 须保持精简）。
- `.claude/commands/` 统一改为 skill（跨工具格式：Claude Code `.claude/skills/`、Codex `.agents/skills/`）；内置评审命令更新为 `/code-review`、`/security-review`（Claude Code）与 `/review`（Codex）。
- 速查页"8 条护栏"更正为 12 条。
### 新增（v6.2 批次 1 · 多项目实跑反馈：进度黑箱 / 不停点"下一步"）
- `skills/prog`：只读项目进度块——里程碑 n/m、下一个任务是否命门、积压的「待拍板 / 偏差」、git 与 CI 健康；`prog.sh` 由 PLAN + git + gh 现算（不新增状态文件、不经模型转述），带 `--selftest`，可不经 AI 直接跑。
- `prog` 试用反馈修正（TideAnywhere M12 首日）：`待拍板` / `偏差` 全文输出不再截断；长标题截描述、保留【…】标注；下一个任务卡在 `待拍板` 时提示"卡在你这里"而不是"做完会停"。
- `skills/close`：里程碑收口验收门，0–7 步逐步出证据（待拍板清零与偏差裁决 → 四命令 → 重跑历史断言 → 旅程走查 + 能力可达性 → 独立 A5 → 文档同步与归档 → PR/CI 后停下 → 合并后核对）。
- `agents/security-auditor.md`：A5 的子代理定义，"禁止自审"从纪律变机制。
- `kof` 模式四 `/kof a` 自动循环 + 停止条件表 + loop 内 PR 流程，以及"遇到需要方案的问题 → 找另一个模型讨论"规程——**回填自 TideAnywhere 的实战版 kof**（M1 用到 M11）。
- 手册阶段 3 新增 3D「自动循环与进度块」；Evidence 标记约定 `待拍板：`（停）/ `偏差：`（不停，收口裁决）。
- skill 统一采用"流程 + 借口→反驳（取自实证）+ 危险信号 + 验证"骨架。
### 变更（v6.2 批次 1）
- **人工检查点上移**：`/kof a` 显式开启自动循环，命中停止条件才停（不开时节奏照旧）；任务颗粒度从"约 30 分钟"改为"一个可独立回滚的 commit"；`/clear` 不再是任务间必经步骤；4.4 由"每项确认 diff"改为"逐项 commit、遇偏离才停"。不变：一任务一 commit、命门的人工确认门、禁止靠删/跳/弱化测试让检查变绿。
- `kof`：移除全部项目占位与「项目坑位」（违反手册自己的"skill 不放项目状态"）——根命令与红线读 ENGINEERING.md，命门 / 涉敏点 / 本机环境 / 悬案 / 易错点读 CLAUDE.md；可原样安装、随手册升级覆盖。
- CLAUDE.md 模板：TIER1 各条补"为什么"；TIER2 同步新节奏；新增「本机环境与常设悬案」节。
- SELFCHECK：由"每个会话开场强制自查"改为按需执行（接手/审计、收口前、用户点名）；R2.1 / R3.3 / P3.G1 / P3.5.G1 / M7 同步。

## [v6.1] - 2026-09-03
### 新增（TidePoint 实战复盘回填：25 个里程碑 / 93 条决策 / 186 个 PR / 8 轮 A5）
- 手册护栏 10–12：静默失败（验结果不验调用）、假绿治理（记过绿收口重验）、教训复发 ≥2 次改代码不改文档。
- 附录 A9 生产数据批量操作检查单（dry-run 全量 / 两段式 + expected_count / 判据同源 / 快照封条 / 定标先行）。
- 附录 A10 外部服务与数据集接入检查单（错误语义三分 / 权威实测当裁判 / 链路先定性 / LLM 规则层为主）。
- 新模板 `DEPLOY.md`（"配错不报错"防线清单 + 回滚演练）与 `OPERATIONS.md`（界面上看不出来的行为）。
- `examples/case-tidepoint.md`：案例复盘全文（数字、A5 战绩表、金句集、回填清单）。
### 变更
- A5 安全审计强化：四类高危模式提词（fail-open 守卫 / TOCTOU / 特权绕过 / 未认证资源耗尽）、修复后复验整条攻击链、报告三段式、中低危处置判据。
- A7 扩充：permissions 实战样例（含 `Read(.env)` 拒读）、CI 门禁五件套（契约漂移闸门 / 并发锁 / 依赖审计双班制等）、self-hosted runner 三纪律。
- B3 布局断言修订：双断言必须一起跑（scrollWidth 单跑是假绿）、登录真实角色量、基准视口跟产品形态走（375 不是通用常量）。
- 新增「运行模式声明」机制：v6 模板可显式降级 v5.3（AGENTS.md 声明 + SELFCHECK M0 豁免规则），未声明的豁免视为违规。
- 硬规则元规则：要么生效、要么显式改判（i18n 单语言挂起判例进 CLAUDE.md TIER1 / SELFCHECK R1.5）。
- ENGINEERING.md：根命令聚合原则（本地/CI/部署同一套）、生成物"重跑生成 + diff --exit-code"闸门、契约变更与生成物同 commit、新增「数据与运行约定」节。
- skills/kof：占位里程碑定位、坑位晋升机制、四条通用环境坑示例、里程碑完成分支补 A5 提醒。

## [v6] - 2026-08-02
### 新增
- Multi-Agent Native 状态层：`.vibe/project.json`、`.vibe/tasks/*.json`、checks、runtime、schema 草案。
- 新增 `VIBE-CLI.md`，定义 claim/start/block/evidence/handoff/gate/integrate 等 deterministic CLI。
- 新增 v6 主手册章节：project truth 与 agent runtime 分离、调度拓扑、contract owner/freeze、handoff packet、integration/merge gate。
- 新增 `MIGRATION-v5.3-to-v6.md` 和 `examples/v6/` 示例。
### 变更
- `AGENTS.md` / `ENGINEERING.md` / `PLAN.md` 升级为 v6 表述，PLAN 保留人读叙事，机器状态迁移到 `.vibe/tasks`。
### 兼容性
- v5.3 的人读 claim/scope/evidence 仍可保留；v6 以 `.vibe/` 为机器真相。

## [v5.3] - 2026-08-02
### 新增
- Multi-Agent Ready 适配层：Agent Ownership、Task Claim/State、Worktree Isolation、Writable Scope、Integration Role/Gate、Evidence Chain。
- 新增 `AGENTS.md` 通用 Agent 入口与 `ENGINEERING.md` vendor-neutral 工程规则。
- 新增 `MIGRATION-v5.2-to-v5.3.md`、`VERSION-DIFF.md` 和 `examples/` 示例。
### 变更
- `CLAUDE.md` 从唯一项目宪法调整为 Claude Code 适配层，跨工具规则上移到 AGENTS.md / ENGINEERING.md。
- `PLAN.md` 任务模板新增状态、Owner、Worktree、Writable Scope、Evidence 字段。
### 兼容性
- v5.2 单人工作流保持可用；v5.3 的多 Agent 字段可按需启用。

## [{x.y.z}] - {YYYY-MM-DD}
### 需求变更
- {改了什么需求；对应 PRD 哪一节被更新}
### 新增
- {新功能/新里程碑交付；如 "M1：新用户可与 AI 对局并看到输赢"}
### 修复
- {bug 修复}
### 受影响模块
- {包/目录}
### 技术要点
- {关键实现/迁移/依赖变化；重大决策指向 D××}

## [0.1.0] - {YYYY-MM-DD}
### 新增
- M0 工程地基：{仓库/CI/脚手架}
