# AGENTS.md · Vibecoding-Handbook 仓库自用规则

> 这是**手册仓库自己**的工作规则（Codex 自动加载本文件；Claude Code 经 `CLAUDE.md` 里的 `@AGENTS.md` 加载）。
> 给项目用的模板在 `templates/`——那里的文件含 `{占位}`，是要被复制走的产物，**不是**给你的指令。

## 这个仓库是什么

一套面向 AI 编程 Agent 的正式项目工程方法：主手册（`Vibe-Coding-正式项目工作手册v*.md`）+ 项目模板（`templates/`）+ 可安装的 skill（`skills/`、`agents/`）。公开仓库，读者是别的项目。

| 路径 | 内容 | 注意 |
|---|---|---|
| `Vibe-Coding-正式项目工作手册v7.md` | 当前主手册 | v6 及更早的手册文件已冻结，不再改 |
| `templates/` | 项目模板（AGENTS / CLAUDE / ENGINEERING / PLAN / PRD / …，以及可选的 `.vibe/`） | 改模板 = 改所有下游项目将来的起点 |
| `skills/`、`agents/` | skill 与子代理的**唯一源**；`.claude/skills`、`.claude/agents`、`.agents/skills` 是指向它们的符号链接 | 不许另存一份 |
| `docs/reviews/` | xreview 的真实评审报告（案例） | 外部模型的原文，不改 |
| `scripts/check.py` | 本地与 CI 共用的自检 | 提交前必跑 |

## 硬规则

1. **不直接 push main**：分支 → PR → 合并；合并由仓库所有者来点（或明确下令）。
2. **提交前跑 `python3 scripts/check.py`**，全过才提交。它查：skill 脚本自检、Markdown 围栏成对、相对链接不断、SELFCHECK 段标齐全、根目录没有混进项目模板、自装 skill 是符号链接。
3. **不提交密钥**；`xreview` 用到的 key 只存在于所有者的环境变量里——不读、不打印、不写入任何文件。
4. **改结构化文档只增量编辑**：手册、模板、CHANGELOG 逐段改，不整文件重生成；批量替换用"断言恰好命中 1 次"的精确替换，不用盲正则。
5. **脚本类 skill 必须带自检，且自检要先证明它能失败**：改守卫逻辑时做变异验证（先确认原版绿；崩溃 / 语法错不算红）。

## 方法（这些教训都付过学费）

- **改上游前先看下游**：所有者的真实项目里装着这些 skill 和模板的实例，常常已经演化得比上游好。动 `kof` / `PLAN` / `CLAUDE.md` 这类会被实例化的东西之前，先只读对比下游的实际版本；新脚本先拿真实文件跑。修改别的仓库必须先得到所有者同意。
- **规则来自实证**：手册里的每条护栏都有出处（哪个项目、哪次事故）。没有在真实项目里验证过的机制，不进默认路径——`.vibe/` 就是反例（设计了、没人用过，v7 降为实验）。
- **同一类问题第三次出现，改结构不改文档**（护栏 12）。
- **工具事实以官方文档 + 实测为准**，不凭记忆、不信第三方文章；模型的自述不是证据。
- **输出默认精简**：给人看的状态 / 报告只留做决定要用的信息，细节放开关后面。

## 发版

CHANGELOG 的 `[Unreleased]` 定版 → README（中 / 英）最新版声明 → 在合并 commit 上打 annotated tag → GitHub release（标题沿用 `Vibe Coding Handbook vX · …`）。破坏性变更要有 `MIGRATION-*.md`。
