#!/usr/bin/env python3
"""close · 收口开销自测（第 0 步）：从 git + PLAN 现算本里程碑与上一里程碑的开销，只提示不拦。

数字：重型占比 / Evidence 中位字数 / 收口提交数与小时 / CI 重跑次数（--gh 才算）/ DECISIONS 体积 / 每会话自动读进的规则字数。
为什么：规则会衰减，数字不会——一个项目的 Evidence 中位从 1,510 字涨到 3,038 字没人发现；写了"效果待实测"的改动，要有机制自动回答。
头两次收口只看数，数稳了再升门禁。
用法：python3 overhead.py [--repo .] [--ms M14] [--gh] [--selftest]
"""
import argparse
import os
import re
import statistics
import subprocess
import sys

TASK_CB = re.compile(r"^- \[( |x|X)\] \*{0,2}([A-Za-z][-A-Za-z0-9.]*?-T[0-9A-Za-z]+)")
TASK_TB = re.compile(r"^\| *([A-Za-z][-A-Za-z0-9.]*?-T[0-9A-Za-z]+) *\|")
HEAD = re.compile(r"^## +(M[-A-Za-z0-9.]*)")
FIELD = re.compile(r"^\s*(- )?(状态|Owner|Worktree|Writable Scope|内容|依赖|完成定义)\s*[:：]")
EVID = re.compile(r"^\s*(- )?Evidence\s*[:：]\s*")
HEAVY = re.compile(r"【重型】|命门|【单独")
CLOSE_SUBJ = re.compile(r"收口|close|A5|xreview|走查|复测|复验|归档", re.I)


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else ""


def read(repo, name, at=None):
    if at:
        return git(repo, "show", f"{at}:{name}")
    p = os.path.join(repo, name)
    return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""


def parse_tasks(text):
    """复选框与表格两种任务行都认；Evidence 从「Evidence：」起到下一个字段行为止。"""
    lines = text.splitlines()
    tasks, i = [], 0
    while i < len(lines):
        m = TASK_CB.match(lines[i]) or TASK_TB.match(lines[i])
        if not m:
            i += 1
            continue
        if TASK_CB.match(lines[i]):
            done, tid = m.group(1) in "xX", m.group(2)
        else:
            done, tid = "✅" in lines[i], m.group(1)
        title = lines[i]
        j = i + 1
        block = []
        while j < len(lines) and not (TASK_CB.match(lines[j]) or TASK_TB.match(lines[j]) or lines[j].startswith("#")):
            block.append(lines[j])
            j += 1
        ev = ""
        for k, b in enumerate(block):
            if EVID.match(b):
                ev = EVID.sub("", b)
                for b2 in block[k + 1:]:
                    if FIELD.match(b2) or re.match(r"^\s*- \[", b2) or not b2.strip():
                        break
                    ev += b2.strip()
                break
        tasks.append(dict(id=tid, ms=tid.rsplit("-T", 1)[0], heavy=bool(HEAVY.search(title)),
                          ev=len(re.sub(r"\s", "", ev)), done=done))
        i = j
    return tasks


def milestones(text):
    out = []
    for l in text.splitlines():
        m = HEAD.match(l)
        if m:
            out.append((m.group(1), ("已收口" in l) or ("✅" in l)))
    return out


def pick(repo, ms_arg=None):
    """本里程碑：--ms，或 PLAN 声明的「当前里程碑：」，或 PLAN 里最后一个未收口的；上一里程碑：PLAN 里最后一个已收口的，PLAN 没有就取归档里最后一个。"""
    plan, arch = read(repo, "PLAN.md"), read(repo, "PLAN-ARCHIVE.md")
    tasks = parse_tasks(arch) + parse_tasks(plan)
    cur = ms_arg
    if not cur:
        m = re.search(r"当前里程碑[:：]\s*\**\s*(M[-A-Za-z0-9.]*)", plan)
        if m:
            cur = m.group(1)
    if not cur:
        # 没声明就取 PLAN 里最后一个未收口且有任务的里程碑——收口时它就是最新的；
        # 不取第一个：老里程碑常挂着一两条没勾的欠账
        for ms, closed in milestones(plan):
            if not closed and any(t["ms"] == ms for t in tasks):
                cur = ms
    in_plan = [ms for ms, c in milestones(plan) if c and ms != cur]
    in_arch = [ms for ms, c in milestones(arch) if ms != cur]
    prev = in_plan[-1] if in_plan else (in_arch[-1] if in_arch else None)
    return cur, prev, tasks


def phase(repo, ms):
    """按提交说明里的里程碑号归类：收口类（收口 / close / A5 / xreview / 走查 / 复测 / 归档）与任务类。"""
    tok = re.compile(r"(?<![A-Za-z0-9])" + re.escape(ms) + r"(?![0-9A-Za-z])")
    rec = {"close": dict(n=0, t0=None, t1=None, doc=0), "task": dict(n=0, t0=None, t1=None, doc=0)}
    last = None
    out = git(repo, "log", "--no-merges", "--format=%x1e%H%x1f%ct%x1f%s", "--numstat")
    for chunk in out.split("\x1e")[1:]:
        head, *rows = chunk.split("\n")
        sha, ct, subj = head.split("\x1f", 2)
        if not tok.search(subj):
            continue
        ct = int(ct)
        if last is None:
            last = sha                      # git log 从新到旧，第一个命中的就是该里程碑最后一次提交
        r = rec["close"] if CLOSE_SUBJ.search(subj) else rec["task"]
        r["n"] += 1
        r["t0"] = ct if r["t0"] is None else min(r["t0"], ct)
        r["t1"] = ct if r["t1"] is None else max(r["t1"], ct)
        for row in rows:
            f = row.split("\t")
            if len(f) == 3 and f[0] != "-" and f[2].endswith(".md"):
                r["doc"] += int(f[0]) + int(f[1])
    for r in rec.values():
        r["hours"] = (r["t1"] - r["t0"]) / 3600 if r["n"] > 1 else 0.0
    return rec, last


def reruns(repo, t0, t1):
    """CI 重跑次数：窗口内 attempt > 1 的 run 数。要 gh；拿不到就 None。"""
    try:
        r = subprocess.run(["gh", "run", "list", "--limit", "200", "--json", "attempt,createdAt"],
                           cwd=repo, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        import datetime
        import json
        n = 0
        for run in json.loads(r.stdout):
            ts = datetime.datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00")).timestamp()
            if run.get("attempt", 1) > 1 and (t0 is None or t0 - 86400 <= ts <= (t1 or ts) + 7 * 86400):
                n += 1
        return n
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def sizes(repo, at=None):
    claude = read(repo, "CLAUDE.md", at)
    auto = len(claude) + sum(len(read(repo, p, at)) for p in re.findall(r"^@(\S+)", claude, re.M))
    return len(read(repo, "DECISIONS.md", at)), auto


def numbers(repo, ms, tasks, use_gh):
    mine = [t for t in tasks if t["ms"] == ms]
    heavy = sum(t["heavy"] for t in mine)
    evs = [t["ev"] for t in mine if t["done"] and t["ev"] > 0]
    rec, last = phase(repo, ms)
    c = rec["close"]
    dec, auto = sizes(repo, last) if last else (None, None)
    return dict(heavy=(heavy, len(mine)), ev=(statistics.median(evs) if evs else None),
                close_n=c["n"], close_h=c["hours"], close_doc=c["doc"],
                rerun=(reruns(repo, c["t0"], c["t1"]) if use_gh else None), dec=dec, auto=auto)


def fmt(v, kind):
    if v is None:
        return "—"
    if kind == "ratio":
        a, b = v
        return f"{a}/{b}" + (f" {100 * a // b}%" if b else "")
    if kind == "k":
        return f"{v / 1000:.1f}K"
    if kind == "h":
        return f"{v:.1f}h"
    return f"{int(v):,}"


def arrow(prev, cur, kind):
    if prev is None or cur is None:
        return ""
    a = prev[0] / prev[1] if kind == "ratio" and prev[1] else (prev if kind != "ratio" else 0)
    b = cur[0] / cur[1] if kind == "ratio" and cur[1] else (cur if kind != "ratio" else 0)
    return "↑" if b > a else ("↓" if b < a else "→")


ROWS = [("重型占比", "heavy", "ratio", True), ("Evidence 中位字数", "ev", "n", True),
        ("收口提交数", "close_n", "n", True), ("收口跨度（小时）", "close_h", "h", True),
        ("收口改动的文档行", "close_doc", "n", True), ("CI 重跑次数", "rerun", "n", True),
        ("DECISIONS 体积", "dec", "k", True), ("每会话自动读进", "auto", "k", True)]


def render(cur, prev, ncur, nprev):
    lines = [f"收口开销（只提示不拦）  本里程碑 {cur} ｜ 上一里程碑 {prev or '无'}",
             f"{'指标':<18}{'上一':>10}{'本次':>10}  变化"]
    worse = []
    for label, key, kind, bad_up in ROWS:
        p = nprev.get(key) if nprev else None
        c = ncur.get(key)
        ar = arrow(p, c, kind)
        lines.append(f"{label:<18}{fmt(p, kind):>10}{fmt(c, kind):>10}  {ar}")
        if ar == "↑" and bad_up:
            worse.append(label)
    if worse:
        lines.append("⚠ 变差：" + "、".join(worse) + "。先量两次再定门禁；要么解释，要么下次收口压回去。")
    if ncur.get("rerun") is None:
        lines.append("（CI 重跑次数要 --gh 才算）")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ms", help="本里程碑编号，默认从 PLAN 取")
    ap.add_argument("--gh", action="store_true", help="用 gh 数 CI 重跑次数")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    cur, prev, tasks = pick(a.repo, a.ms)
    if not cur:
        print("找不到本里程碑：PLAN.md 里没有「当前里程碑：」，也没有带未勾任务的里程碑。")
        return 0
    print(render(cur, prev, numbers(a.repo, cur, tasks, a.gh), numbers(a.repo, prev, tasks, False) if prev else None))
    return 0


# ---------------------------------------------------------------- 自检

def selftest():
    import tempfile

    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)
            print("FAIL", msg)

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "-C", tmp, "init", "-q"], check=True)

        def w(name, text):
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(text)

        def commit(msg, ts):
            env = dict(os.environ, GIT_AUTHOR_DATE=f"@{ts} +0000", GIT_COMMITTER_DATE=f"@{ts} +0000",
                       GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            subprocess.run(["git", "-C", tmp, "add", "-A"], check=True, env=env)
            subprocess.run(["git", "-C", tmp, "commit", "-qm", msg], check=True, env=env)

        T = 1_700_000_000
        w("AGENTS.md", "x" * 100)
        w("CLAUDE.md", "@AGENTS.md\n" + "y" * 50)
        w("DECISIONS.md", "d" * 100)
        w("PLAN-ARCHIVE.md", "## M1 · 甲 ✅\n- [x] **M1-T1 · 做数据** —【重型】【单独+确认】（命门）\n  Evidence：" + "a" * 100 +
          "\n  内容：x\n- [x] **M1-T2 · 页面** —【常规】\n  Evidence：" + "b" * 300 + "\n")
        w("PLAN.md", "当前里程碑：M2\n已完成里程碑：M1\n## M2 · 乙\n- [x] **M2-T1 · a** —【常规】【可批量】\n  Evidence：" + "c" * 50 +
          "\n- [x] **M2-T2 · b** —【常规】（命门：改契约）\n  Evidence：" + "d" * 70 + "\n  依赖：T1\n- [ ] **M2-T3 · 收口验收门**\n")
        commit("M1-T1: 做数据", T)
        w("page.py", "p = 1\n")
        commit("M1-T2: 页面", T + 3600)
        w("DECISIONS.md", "d" * 300)
        commit("M1 收口：走查 + 归档", T + 7200)
        w("notes.md", "n\n" * 10)
        commit("M1 收口复测", T + 10800)
        w("a.py", "a = 1\n")
        commit("M2-T1: a", T + 20000)
        w("DECISIONS.md", "d" * 500)
        commit("M2-T2: b", T + 23600)

        cur, prev, tasks = pick(tmp)
        check((cur, prev) == ("M2", "M1"), f"本 / 上一里程碑应为 M2 / M1，得到 {cur} / {prev}")
        check(pick(tmp, "M1")[0] == "M1", "--ms 应覆盖 PLAN 声明")
        n1, n2 = numbers(tmp, "M1", tasks, False), numbers(tmp, "M2", tasks, False)
        check(n1["heavy"] == (1, 2) and n2["heavy"] == (1, 3), f"重型占比应为 1/2 与 1/3，得到 {n1['heavy']} {n2['heavy']}")
        check(n1["ev"] == 200 and n2["ev"] == 60, f"Evidence 中位应为 200 与 60（只算已勾且有 Evidence 的），得到 {n1['ev']} {n2['ev']}")
        check(n1["close_n"] == 2 and abs(n1["close_h"] - 1.0) < 1e-6, f"M1 收口应 2 次提交、跨 1.0 小时，得到 {n1['close_n']} {n1['close_h']}")
        check(n1["close_doc"] == 10 + 2, f"M1 收口改动文档行应为 12（notes 10 行 + DECISIONS 单行改写 1+1），得到 {n1['close_doc']}")
        check(n2["close_n"] == 0, "M2 还没收口，收口提交应为 0")
        check(n1["dec"] == 300 and n2["dec"] == 500, f"DECISIONS 体积应取各自最后一次提交时的值 300 / 500，得到 {n1['dec']} {n2['dec']}")
        check(n1["auto"] == 161 and n2["auto"] == 161, f"自动读进应为 CLAUDE 61 + 导入的 AGENTS 100 = 161，得到 {n1['auto']}")
        out = render("M2", "M1", n2, n1)
        check("Evidence 中位字数" in out and "       200        60  ↓" in out, "表格应显示 200 → 60 ↓")
        check("⚠ 变差：DECISIONS 体积" in out, "DECISIONS 300 → 500 应报变差")
        check("重型占比" not in out.split("⚠")[-1], "重型占比 50% → 33% 不该算变差")
        check("--gh 才算" in out, "没开 --gh 应提示")
        # 没有上一里程碑也能出表
        check("上一里程碑 无" in render("M2", None, n2, None), "没有上一里程碑时应显示「无」")
        # 表格写法任务也认
        tb = parse_tasks("## M3 · 丙\n| 任务 | 内容 | 状态 |\n|---|---|---|\n| M3-T1 | 做 A【重型】 | ✅ |\n| M3-T2 | 做 B | ⬜ |\n")
        check(len(tb) == 2 and tb[0]["heavy"] and tb[0]["done"] and not tb[1]["done"], "表格任务行应被解析")

    if fails:
        print(f"selftest FAILED: {len(fails)}")
        return 1
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
