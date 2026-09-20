# CLAUDE.md · Vibecoding-Handbook 仓库自用（Claude Code 适配层）

共同规则在 AGENTS.md，用 import 机械加载：

@AGENTS.md

Claude Code 专属补充：

- 本仓库自装了手册的 skill（`.claude/skills` → `skills/`）：`/prog`、`/kof`、`/close`、`/xreview` 可用。但本仓库没有 PLAN.md（它不是按里程碑推进的应用项目），`/prog` 在这里没有可报的进度——要看某个真实项目的进度，到那个项目里跑。
- 需要带 key 的命令（`xreview` 调 DeepSeek / GLM）：如果当前会话启动早于所有者配置环境变量，用 `zsh -lic '…'` 在登录 shell 里跑，key 只存在于那个子进程里。
- `templates/CLAUDE.md` 是给项目用的模板，不是本文件的一部分。
