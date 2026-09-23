# CHANGELOG · Vibe Coding 正式项目工作手册

> 手册仓库自己的版本史（只增不改，新条目在顶部）。给项目用的 CHANGELOG 模板在 [templates/CHANGELOG.md](templates/CHANGELOG.md)。

---

## [Unreleased]
### 新增（试验）
- **`map` skill · 项目地图**（试验中，不进默认路径）：进度块回答"做到第几个任务"，回答不了"在业务流程的哪一步、问题出在哪块、精力花在哪"。脚本从 PLAN.md + `ENGINEERING.md`「模块地图」（新增的可选一节：业务线 + 「模块 × 层 × 路径」表）+ git 现算，出一个自带页面（阶段 / 线路图 / 模块卡片 / 问题原文 / 投入热力图）；装了 [archify](https://github.com/tt-a1i/archify) 时同一份事实另画成交互架构图（布局由脚本按网格算好，不让 agent 手摆坐标；「你在这里 / 问题在哪 / 投入最多 / 跨仓库依赖」四个章节；节点可跳源码）。PLAN 读法与 `prog` 同口径，自检里交叉核对。`kof` 任务收尾静默刷新；`--publish` 执行项目自配的发布命令（托管不绑定任何一家 agent 工具），**发布后像匿名浏览器一样打开网址，能看到地图就失败**（页面有安全欠账原文）；推荐托管 = Cloudflare Workers 静态资源 + Cloudflare Access（按官方文档核实，未实测；GitHub Pages 从私有仓库发布照样公开，排除）。
- 两个真实项目只读试跑的发现：一个项目的运维控制台占全部代码与文档改动的 31%（单个里程碑 1.8 万行），产品本体查询 API 占 7%；另一个项目文档占 46%。这正是"设计得太细、浪费 token"能被看见的地方——地图把数字摆出来，值不值由用户判断。
### 更正（v7 发版后）
- **v7 发版说明里对首次真实试用的描述不完整，特此更正。** 原文写"排第二的'高危'成立，其余 4 条成立但严重度偏低"——这些发现本身属实，但漏了关键事实：**6 条里有 5 条是该项目自己的 A5 审计（`security-auditor` 子代理，有运行环境、做了实测）早已发现或评估过的**，其中排第二的"高危"就是一条已登记的欠账；只有 1 条低危可能是新的；排第一的"高危"是误报。根因：A5 报告与欠账清单属需授权内容、被 `xreview` 扣下，评审方看不到；而主控第一遍裁决时没有对照项目已有记录去重。
### 变更
- `xreview` SKILL.md：合并裁决的第一步改为"对照项目已有的欠账清单与审计报告去重"；使用场景改为"优先用在没有 A5 的命门 diff 上，或放在 A5 之前当初筛；已经跑过 A5 的里程碑再跑，边际收益低"。`close` 第 4 步、v7 手册 5.1 同步。

## [v7] - 2026-09-20
> **破坏性 · 结构调整。** 主题：**默认路径只留被真实项目验证过的机制**（Field-Proven）。三块：`.vibe/` 降为实验并翻转默认、`xreview` 异构模型复核门（外发限制机制化）、项目模板移入 `templates/` + 手册仓库自用规则与 CI。v6 手册冻结于 v6.2；升级见 `MIGRATION-v6-to-v7.md`。发版前 `xreview` 已在真实项目的一个涉敏里程碑上试用。
### 破坏性变更（结构调整）
- **`.vibe/` 机器状态层降为实验**：它设计于 v6，但没有任何真实项目用过，而"v6 模板 + v5.3 模式"跑完了 25+ 个里程碑——默认路径和被验证路径此前是反的。v7：多 Agent 协作协议（源自 v5.3，任务状态在人读的 PLAN.md）为默认；`.vibe/` 模板移到 `templates/.vibe/`，手册里整节移入**附录 C**（只移不删，99 行逐行一致），`VIBE-CLI.md` 标为设计草案。
- **运行模式声明的方向翻转**：默认（PLAN 人读状态、无 `.vibe/`）不再需要声明；偏离默认（替换基准视口、挂起硬规则、启用 `.vibe/`）才声明。模板 `AGENTS.md` / `CLAUDE.md` / `ENGINEERING.md` / `PLAN.md` / `SELFCHECK.md` 同步。
- **项目模板移入 `templates/`**：根目录不再有模板——它们曾被 Claude Code / Codex 当成本仓库的真指令加载（占位符 `{lint}`、"先读 `.vibe/project.json`"）。`CHANGELOG.md` 拆开：根目录 = 手册自己的版本史，`templates/CHANGELOG.md` = 项目模板。
- **新建 v7 手册**（`Vibe-Coding-正式项目工作手册v7.md`），v6 手册冻结于 v6.2。迁移见 `MIGRATION-v6-to-v7.md`。
### 新增（仓库与模板）
- 手册仓库自用的 `AGENTS.md` / `CLAUDE.md`（真规则，不再是模板）；自装 skill——`.claude/skills`、`.claude/agents`、`.agents/skills` 是指向 `skills/`、`agents/` 的符号链接，源只有一份。
- `scripts/check.py` + GitHub Actions：本地与 CI 同一条命令——skill 脚本自检、Markdown 围栏成对、相对链接不断、SELFCHECK 段标齐全、根目录不得混进项目模板、自装 skill 必须是符号链接。
- **新 CI 第一次运行就抓到一个真 bug**：`prog.sh` 的标题截断在 macOS（BWK awk，按字节）与 Linux（gawk 在 UTF-8 locale 下按字符）不一致——同一份 PLAN 在 Linux 上的输出长 3 倍，本地自检永远测不出。修法：awk 统一在 `LC_ALL=C` 下按字节处理。正是手册护栏 3"本地绿 ≠ CI 绿"的又一例，也是给一个文档仓库配 CI 值不值的答案。
- PLAN 任务行两种写法都认可：复选框，或表格 `| M3-T4 | 内容 | ⬜ / ✅ |`（真实项目里两种都在用；`prog` 自 v6.2 起两种都认）。
### 变更
- `SELFCHECK.md` → v7：R2.10 仅对启用 `.vibe/` 的项目适用；R5.* 去掉重复编号（门禁层 → R5.6，`.vibe` 状态门 → R5.7）。
- README（中 / 英）：版本表增 v7 行、协作模型图去掉 `.vibe`、快速开始改为从 `templates/` 复制并安装 skill、设计原则改为"实证优先 / 人读文档是真相 / 自动化必须确定"；`VERSION-DIFF.md` 增 v6.1 / v6.2 / v7。
### 新增（多 Agent：`xreview` 异构复核门）
- `skills/xreview`：把被评审的 diff 发给别家模型（Codex / DeepSeek / GLM）各出一份只读报告，主控合并裁决。`xreview.py` 只用标准库，带 `--dry-run` 与 `--selftest`。**外发规则机制化**：默认只发 diff；凭证文件永不外发 + gitleaks 扫内容（异常即拒发）；全局设计文档与名字涉及口令·权限的文件默认扣下，要发须 `--include-restricted --authorized … --authorized-for …`（授权点名接收方）；Codex 走权限档隔离且每次预检（正 / 负对照），DeepSeek / GLM 直连 HTTPS（域名白名单、不跟随重定向）；key 只从环境变量取。
- 手册阶段 5 新增 5.1「`xreview` 复核门与多 Agent 的分工原则」：按独立性划分 Agent（执行者 / 独立验证者 / 只读调研者）、主控 = Integration Owner、复核门位置与强度、裁决规则（多方同报优先、独报先复现）、外发限制是硬约束、按难度派工为试验路径。
- **发版前的真实项目试用**（一个涉敏里程碑的 diff，19 个文件约 71KB，只发 Codex，2 分钟）：6 条发现逐条核实——排第一的"高危"实测不成立、排第二的"高危"成立、其余 4 条成立但严重度偏低；需授权的 13 个文件被自动扣下。试用还确认了一个边界：仓库位于系统临时目录时 Codex 隔离预检会拒跑（正确行为，已写进 SKILL.md）。
- `prog.sh` 自检改用绝对路径调用自己（`bash prog.sh` 不带路径时原先会 command not found）。
- `ENGINEERING.md` 模板新增「外发限制」节；`close` 第 4 步可叠加 `xreview`；`kof` 的"找另一个模型讨论"指向 `xreview` 的外发规则；模型档映射表增「异构评审方」行。
- `docs/reviews/`：`xreview` 的头三轮真实运行都是审它自己——Codex（隔离环境）7 条、DeepSeek 两轮共 11 条、GLM 11 条，逐条先复现再修。多方同报：授权没绑定到具体文件、检查与打开之间的窗口、报告目录豁免过宽。GLM 独报的一条最狠：`str.splitlines` 认 `\x0c` 等非 git 行界，可伪造 diff 文件头让被扣下的 PRD 内容挂在别的文件名下发出去（复现成立）。解析 diff 文本这一处至此出了第 4 个绕过 → 按护栏 12 改结构：**不再解析 diff 文本**，文件清单取自 `git diff --name-status -z`、补丁按文件单取。另：Codex 进程清掉别家 key、预检加第二个负对照、git 输出严格 UTF-8、gitleaks 在评审包目录里跑、报告文件名校验、HTTP 改流式（GLM 长思考曾被断连）并各家并行。22 种实现变异均能让自检变红。

## [v6.2] - 2026-09-19
> 两个来源：① 对照 2026-09 的 Claude Code / Codex 修正过时事实；② 多个真实项目实跑的反馈（进度黑箱、不停点"下一步"）。发版前在 TideAnywhere 跑完一个完整里程碑（M12：立项 → `/kof a` → `close` 八步 → 0.14.0），期间的试用反馈已并入本版。
### 变更（批次 0 · 对照 2026-09 的 Claude Code / Codex 修正过时事实）
- 提示词末尾的 `ultrathink` 全部移除（该关键词在 Claude Code 已失效）；正文改用工具中立的"高 / 默认 / 低推理档位"。
- 分档表不再写死 Opus / Sonnet / Haiku：正文只写"旗舰 / 主力 / 轻量"，新增「模型档映射表」与「工具适配表」（Claude Code ↔ Codex CLI），模型换代只改这一处。
- 规则文件加载机制化：CLAUDE.md 模板用 `@AGENTS.md`、`@ENGINEERING.md` import 取代"请先读"；写明 Codex 自动加载 AGENTS.md 且合计默认上限 32 KiB（AGENTS.md 须保持精简）。
- `.claude/commands/` 统一改为 skill（跨工具格式：Claude Code `.claude/skills/`、Codex `.agents/skills/`）；内置评审命令更新为 `/code-review`、`/security-review`（Claude Code）与 `/review`（Codex）。
- 速查页"8 条护栏"更正为 12 条。
### 新增（批次 1 · 多项目实跑反馈：进度黑箱 / 不停点"下一步"）
- `skills/prog`：只读项目进度块——里程碑 n/m、下一个任务是否命门、积压的「待拍板 / 偏差」、git 与 CI 健康；`prog.sh` 由 PLAN + git + gh 现算（不新增状态文件、不经模型转述），带 `--selftest`，可不经 AI 直接跑。
- `prog` 试用反馈修正（TideAnywhere M12 首日）：**新增项目总体进度**（已收口里程碑 / 总数，含从 `已完成里程碑：M0–M11` 行解析已归档里程碑；当前里程碑的任务比例折入总体百分比）；**默认输出精简为三段**——进度 / 下一步 / 待处理，其余收进 `--full`（收口用）；`待拍板` 全文、`偏差` 精简模式只给一行；长标题截描述、保留【…】标注；下一步卡在 `待拍板` 时提示"卡在你这里"；标记行约定"只写一句话"。
- `skills/close`：里程碑收口验收门，0–7 步逐步出证据（待拍板清零与偏差裁决 → 四命令 → 重跑历史断言 → 旅程走查 + 能力可达性 → 独立 A5 → 文档同步与归档 → PR/CI 后停下 → 合并后核对）。
- `agents/security-auditor.md`：A5 的子代理定义，"禁止自审"从纪律变机制。
- `kof` 模式四 `/kof a` 自动循环 + 停止条件表 + loop 内 PR 流程，以及"遇到需要方案的问题 → 找另一个模型讨论"规程——**回填自 TideAnywhere 的实战版 kof**（M1 用到 M11）。
- 手册阶段 3 新增 3D「自动循环与进度块」；Evidence 标记约定 `待拍板：`（停）/ `偏差：`（不停，收口裁决）。
- skill 统一采用"流程 + 借口→反驳（取自实证）+ 危险信号 + 验证"骨架。
### 变更（批次 1）
- **人工检查点上移**：`/kof a` 显式开启自动循环，命中停止条件才停（不开时节奏照旧）；任务颗粒度从"约 30 分钟"改为"一个可独立回滚的 commit"；`/clear` 不再是任务间必经步骤；4.4 由"每项确认 diff"改为"逐项 commit、遇偏离才停"。不变：一任务一 commit、命门的人工确认门、禁止靠删/跳/弱化测试让检查变绿。
- `kof`：移除全部项目占位与「项目坑位」（违反手册自己的"skill 不放项目状态"）——根命令与红线读 ENGINEERING.md，命门 / 涉敏点 / 本机环境 / 悬案 / 易错点读 CLAUDE.md；可原样安装、随手册升级覆盖。
- `close` 第 4 步补口径（M12 试用暴露）：审计复测之后又改的代码同样要交回复测，直到"最后一次改动之后有一次复测"；当轮修掉的中低危至少由审计代理定点复验。
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
