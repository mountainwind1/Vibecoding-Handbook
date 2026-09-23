#!/usr/bin/env python3
"""手册仓库自检：本地与 CI 跑同一套（手册自己的原则——根命令聚合，防"本地绿 CI 红"）。
用法：python3 scripts/check.py        退出码 0 = 全过
查：① skill 脚本自检 ② Markdown 代码围栏成对 ③ 相对链接不断 ④ SELFCHECK 段标与哨兵齐全
   ⑤ 模板只在 templates/（根目录不得再出现项目模板——它们会被当成本仓库的真指令加载）⑥ 自装 skill 指向 skills/ 源"""
import os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
fails = []
def fail(msg): fails.append(msg)
def tracked(): return [p for p in subprocess.run(["git", "ls-files", "-z"], capture_output=True).stdout.decode("utf-8").split("\0") if p]

# ① skill 脚本自检
for cmd in (["bash", "skills/prog/prog.sh", "--selftest"], [sys.executable, "skills/xreview/xreview.py", "--selftest"],
            [sys.executable, "skills/map/map.py", "--selftest"]):
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PROG_NO_GH="1"))
    if r.returncode != 0 or "selftest ok" not in r.stdout:
        out = (r.stdout + r.stderr).strip()
        lines = [l for l in out.split("\n") if "FAIL" in l] or out.split("\n")[-8:]      # 先给失败的断言，别只给输出的尾巴
        fail(f"自检失败：{' '.join(cmd)}\n    " + "\n    ".join(lines[:20]))

mds = [p for p in tracked() if p.endswith(".md") and os.path.isfile(p)]
for p in mds:
    text = open(p, encoding="utf-8").read()
    # ② 围栏成对
    if len(re.findall(r"^\s*```", text, flags=re.M)) % 2: fail(f"代码围栏不成对：{p}")
    # ③ 相对链接（跳过 http(s) / 锚点 / mailto，以及评审报告——那是外部模型的原文）
    if p.startswith("docs/reviews/"): continue
    body = re.sub(r"```.*?```", "", text, flags=re.S)                      # 代码块里的不算链接
    for m in re.finditer(r"(?<!\!)\[[^\]\n]*\]\(([^)\s]+)\)|<img[^>]+src=\"([^\"]+)\"|\!\[[^\]\n]*\]\(([^)\s]+)\)", body):
        target = next(g for g in m.groups() if g)
        if re.match(r"^(https?:|mailto:|#)", target): continue
        path = target.split("#")[0]; path = re.sub(r":\d+$", "", path)     # 去掉锚点与 file:line 后缀
        if not path or "{" in path: continue                                # 模板占位
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), path))): fail(f"断链：{p} → {target}")

# ④ SELFCHECK 段标与哨兵
sc = "templates/SELFCHECK.md" if os.path.exists("templates/SELFCHECK.md") else "SELFCHECK.md"
t = open(sc, encoding="utf-8").read()
for mark in [f"⟦M{i}⟧" for i in range(10)] + ["⟦VC-SELFCHECK-END⟧"]:
    if mark not in t: fail(f"{sc} 缺段标 {mark}")

# ⑤ 根目录不得有项目模板（AGENTS.md / CLAUDE.md / CHANGELOG.md 是本仓库自用的，不算）
for name in ["ENGINEERING.md", "PLAN.md", "PRD.md", "DECISIONS.md", "DESIGN.md", "SELFCHECK.md", "DEPLOY.md", "OPERATIONS.md", ".vibe"]:
    if os.path.exists(name): fail(f"根目录出现项目模板 `{name}`——模板只放 templates/")
for name in ["AGENTS.md", "CLAUDE.md"]:
    if os.path.exists(name) and "{" in open(name, encoding="utf-8").read().split("\n", 40)[-1] and "模板" in open(name, encoding="utf-8").readline():
        fail(f"根目录的 {name} 看起来还是模板")

# ⑥ 自装的 skill / agent 必须就是 skills/ 与 agents/ 源（符号链接），不许另存一份
for link, want in ((".claude/skills", "../skills"), (".claude/agents", "../agents"), (".agents/skills", "../skills")):
    if os.path.lexists(link) and not (os.path.islink(link) and os.readlink(link) == want): fail(f"{link} 应是指向 {want} 的符号链接")

if fails: print("check FAIL:\n  " + "\n  ".join(fails)); sys.exit(1)
print(f"check ok（{len(mds)} 个 Markdown 文件）")
