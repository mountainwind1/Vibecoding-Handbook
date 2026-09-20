# v6.x → v7 迁移指南

v7 是结构调整：**默认路径只留被真实项目验证过的机制**。对已经在跑的项目，迁移量取决于你有没有真的用 `.vibe/`。

## 先判断你是哪一种

| 你的项目 | 迁移量 |
|---|---|
| 用 v6 模板，但在 `AGENTS.md` 声明了"v5.3 模式 / 不使用 `.vibe/`"（绝大多数） | 很小：删掉那句降级声明即可——它现在就是默认 |
| 真的在用 `.vibe/tasks/*.json` | 可以继续用：把"降级声明"换成"启用 `.vibe/`（实验）"的声明，注明决策号 |
| 只读手册、自己没装模板 | 无 |

## 步骤

1. **运行模式声明的方向翻转了。** v6：不用 `.vibe/` 要声明降级。v7：默认就是"任务状态在 PLAN.md、不用 `.vibe/`"，**不需要声明**；偏离默认才声明（替换布局基准视口、挂起某条硬规则、启用 `.vibe/`）。
   - 项目 `AGENTS.md`：删掉"运行在 v5.3 模式 / 不使用 `.vibe/`"那句；其他偏离（视口、i18n 挂起…）照旧保留。
   - 项目 `CLAUDE.md` 启动顺序：删掉"再读 `.vibe/project.json` …"那一步；冲突裁决改为"以 AGENTS.md 为准"。
   - 项目 `PLAN.md` 头部：删掉"机器可执行状态以 `.vibe/tasks/*.json` 为准"。
2. **SELFCHECK.md 换成 v7 版**（`templates/SELFCHECK.md`）：R2.10 改为仅对启用 `.vibe/` 的项目适用；R5.* 去掉了重复编号（门禁层 → R5.6，`.vibe` 状态门 → R5.7）。引用过旧编号的地方同步一下。
3. **装 / 升级 skill**：把 `skills/` 下的目录原样复制到项目的 `.claude/skills/`（Codex：`.agents/skills/`），`agents/security-auditor.md` 复制到 `.claude/agents/`。v7 新增 `xreview`；`kof` / `prog` / `close` 自 v6.2 起不存放项目状态，直接覆盖即可。
   - 旧版 `kof`（v6.1 及更早）里写着项目状态的：先迁进项目的 `CLAUDE.md`「本机环境与常设悬案」「易错点」与 `ENGINEERING.md`，再覆盖。
4. **要用 `xreview` 的项目**：在 `ENGINEERING.md` 加「外发限制」节（见模板），写清本项目追加的禁区与常设授权；key 放在自己的环境变量里（`DEEPSEEK_API_KEY` / `GLM_API_KEY`），不进仓库。
5. **模板路径**：手册仓库里模板从根目录移到了 `templates/`。只影响你以后从哪里复制模板，不影响已有项目。

## 不需要做的

- 不需要重建 PLAN / PRD / DECISIONS。
- 不需要删除已有的 `.vibe/` 目录——想留就在 `AGENTS.md` 声明启用；不想留就删，并确认 `CLAUDE.md` / `PLAN.md` 里不再提它。
- v6 手册文件冻结于 v6.2，仍可阅读；tag `v6.2` 保留了当时的全部模板。
