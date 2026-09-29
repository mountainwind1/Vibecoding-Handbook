#!/usr/bin/env python3
"""kof · SessionStart hook：/clear 或上下文被压缩之后，把"落点 + 交接 + 上一段会话里用户说过的话"注入上下文。

只读，不写任何文件。只在来源是 clear / compact 时输出，其它来源（startup / resume / fork）静默退出。
用法：
  Claude Code hook（stdin 是 hook 的 JSON，含 source / cwd / transcript_path）：
      python3 "$CLAUDE_PROJECT_DIR/.claude/skills/kof/session-start.py"
  没装 hook，清完手动跑：
      python3 .claude/skills/kof/session-start.py --source clear --previous
      （--previous = 跳过最新那份记录——就是当前这个刚 clear 出来的会话）
  自检：--selftest
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re
import subprocess
import sys

SOURCES = ("clear", "compact")
NOISE = ("<task-notification>", "<local-command-stdout>", "<command-name>", "<command-message>",
         "<local-command-caveat>", "<ide_")
SYSTEM_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
UNCHECKED = re.compile(r"^\s*- \[ \]")


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace")
        return r.stdout.strip() if r.returncode == 0 else ""
    except OSError:
        return ""


def locate(repo):
    """落点：分支与脏文件、最近提交、stash、PLAN 第一个未完成任务、最新交接行。不是 git 仓库就返回空。"""
    top = git(repo, "rev-parse", "--show-toplevel")
    if not top:
        return []
    out = []
    status = git(repo, "status", "-sb").splitlines()
    dirty = len(status) - 1
    out.append(f"[落点] {status[0] if status else '?'} · 未提交 {dirty} 个文件")
    log = git(repo, "log", "--oneline", "-3").replace("\n", " ｜ ")
    if log:
        out.append(f"[提交] {log}")
    stash = git(repo, "stash", "list").splitlines()
    if stash:
        out.append(f"[stash] {len(stash)} 条——新会话默认看不见，先决定是恢复还是丢")
    plan = os.path.join(top, "PLAN.md")
    if os.path.exists(plan):
        with open(plan, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        todo = [f"L{i} {l.strip()[:120]}" for i, l in enumerate(lines, 1) if UNCHECKED.match(l)][:3]
        out.append("[PLAN] 未完成：" + (" ｜ ".join(todo) if todo else "无（里程碑全勾，走立项流程）"))
        handoff = [f"L{i} {l.strip()[:200]}" for i, l in enumerate(lines, 1) if "交接：" in l]
        if handoff:
            out.append("[交接] " + handoff[-1])
    return out


def project_dir(repo):
    """没有 hook 给的 transcript_path 时，按 Claude Code 的目录编码规则推。"""
    return os.path.join(os.path.expanduser("~"), ".claude", "projects",
                        re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(repo)))


def pick_transcript(directory, source, current=None, previous=False):
    """clear：最近一份不是当前会话的记录；compact：当前会话自己的记录（压缩前的消息都还在里面）。"""
    if source == "compact" and current and os.path.exists(current):
        return current
    files = sorted(glob.glob(os.path.join(directory, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if current:
        cur = os.path.realpath(current)
        files = [f for f in files if os.path.realpath(f) != cur]
    if previous and files:
        files = files[1:]
    return files[0] if files else None


def clean(text):
    text = SYSTEM_REMINDER.sub("", text).strip()
    if not text or text.startswith(NOISE):
        return ""
    return re.sub(r"\s+", " ", text)


def user_messages(path, n=30, width=200):
    """只取用户自己敲的话：不要工具结果、不要子代理、不要元消息、不要压缩摘要、不要命令回显。"""
    keep = collections.deque(maxlen=n)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "user" or e.get("isMeta") or e.get("isCompactSummary") or e.get("isSidechain"):
                continue
            content = (e.get("message") or {}).get("content")
            if isinstance(content, list):
                content = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
            if not isinstance(content, str):
                continue
            text = clean(content)
            if not text:
                continue
            if len(text) > width:
                text = text[: width - 1] + "…"
            keep.append((stamp(e.get("timestamp")), text))
    return list(keep)


def stamp(ts):
    try:
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        return t.strftime("%m-%d %H:%M")
    except (AttributeError, ValueError):
        return "--:--"


def render(source, located, msgs, src_file, n):
    head = ("kof · 上下文已清（/clear）。按 kof 模式二【重载阶段】走：读规则 → 对照下面的落点与交接 → 补漏检查 → 再动手。"
            if source == "clear" else
            "kof · 上下文刚被压缩，摘要可能丢细节。把摘要当线索不当事实：按 kof 模式二【重载阶段】2–4 步重读 PLAN / DECISIONS 并补漏，再继续。")
    lines = [head, *located]
    if msgs:
        lines.append(f"[上一段会话里用户说过的话 · 最近 {len(msgs)} 条（上限 {n}），逐条对照是否已落盘；来源 {os.path.basename(src_file)}]")
        lines += [f"  {i}. {t} {m}" for i, (t, m) in enumerate(msgs, 1)]
    elif src_file:
        lines.append(f"[上一段会话记录 {os.path.basename(src_file)} 里没有可用的用户消息]")
    else:
        lines.append("[没找到上一段会话的记录]")
    return "\n".join(lines)


def read_hook_input():
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except ValueError:
        return {}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="clear / compact；不给就读 hook 输入")
    ap.add_argument("--repo", help="仓库目录，默认 hook 的 cwd 或当前目录")
    ap.add_argument("--transcripts", help="会话记录目录，默认 hook 的 transcript_path 所在目录")
    ap.add_argument("--previous", action="store_true", help="手动模式：跳过最新一份记录（当前会话）")
    ap.add_argument("-n", type=int, default=30, help="最多带回多少条用户消息")
    ap.add_argument("--width", type=int, default=200, help="每条截多长")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    hook = {} if args.source else read_hook_input()
    source = args.source or hook.get("source")
    if source not in SOURCES:
        return 0
    repo = args.repo or hook.get("cwd") or os.getcwd()
    current = hook.get("transcript_path")
    directory = args.transcripts or (os.path.dirname(current) if current else project_dir(repo))
    src_file = pick_transcript(directory, source, current, args.previous) if os.path.isdir(directory) else None
    msgs = user_messages(src_file, args.n, args.width) if src_file else []
    print(render(source, locate(repo), msgs, src_file, args.n))
    return 0


# ---------------------------------------------------------------- 自检

def selftest():
    import tempfile
    import time

    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)
            print("FAIL", msg)

    def entry(text, **extra):
        e = {"type": "user", "timestamp": "2026-09-29T03:00:00.000Z",
             "message": {"role": "user", "content": text}}
        e.update(extra)
        return json.dumps(e, ensure_ascii=False)

    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        os.makedirs(repo)
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
        with open(os.path.join(repo, "PLAN.md"), "w", encoding="utf-8") as fh:
            fh.write("# PLAN\n- [x] **M1-T1 · 做完的**\n  Evidence：好\n"
                     "- [ ] **M1-T2 · 没做完的**\n  Evidence：交接：recon 到 api.py:40，试过方案 A 失败\n"
                     "- [ ] **M1-T3 · 后面的**\n")
        subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "PLAN.md"], check=True)
        subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], check=True)
        with open(os.path.join(repo, "dirty.txt"), "w") as fh:
            fh.write("x")

        tdir = os.path.join(tmp, "transcripts")
        os.makedirs(tdir)
        old = os.path.join(tdir, "old.jsonl")
        noise_result = json.dumps({"type": "user", "timestamp": "2026-09-29T03:00:00Z", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": "工具结果不该出现"}]}})
        rows = [
            entry("第一句会被条数上限挤掉"),
            entry("第二句留着凑数"),
            entry("不装 tidepre"),
            entry("<system-reminder>提醒正文不该出现</system-reminder>\n不动提交历史"),
            entry("<task-notification>后台任务通知不该出现</task-notification>"),
            entry("<local-command-stdout>命令回显不该出现</local-command-stdout>"),
            entry("元消息不该出现", isMeta=True),
            entry("压缩摘要不该出现", isCompactSummary=True),
            entry("子代理消息不该出现", isSidechain=True),
            noise_result,
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "AI 的回复不该出现"}}),
            json.dumps({"type": "user", "timestamp": "2026-09-29T03:01:00Z", "message": {"role": "user", "content": [
                {"type": "text", "text": "文本块形式的用户消息"}]}}),
            "这行不是 JSON",
            entry("长" * 500),
        ]
        with open(old, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        time.sleep(0.05)
        cur = os.path.join(tdir, "current.jsonl")
        with open(cur, "w", encoding="utf-8") as fh:
            fh.write(entry("/kof c") + "\n")
        os.utime(cur, None)

        # clear：取 old（排除当前），条数上限 5 → 第一句被挤掉
        picked = pick_transcript(tdir, "clear", current=cur)
        check(picked == old, f"clear 应选上一份记录，选了 {picked}")
        msgs = user_messages(old, n=5, width=50)
        texts = [m for _, m in msgs]
        check(len(msgs) == 5, f"条数上限 5，得到 {len(msgs)}")
        check("不装 tidepre" in texts, "用户原话应保留")
        check("不动提交历史" in texts, "system-reminder 应剥掉、正文保留")
        check("文本块形式的用户消息" in texts, "text 块形式的消息应保留")
        check(not any("第一句" in t for t in texts), "超出条数上限的最早消息应被挤掉")
        for bad in ("工具结果", "提醒正文", "后台任务通知", "命令回显", "元消息", "压缩摘要", "子代理", "AI 的回复"):
            check(not any(bad in t for t in texts), f"噪音「{bad}」不该出现")
        check(all(len(t) <= 50 for t in texts) and any(t.endswith("…") for t in texts), "每条应截到宽度并加省略号")

        # compact：读当前会话自己的记录
        check(pick_transcript(tdir, "compact", current=cur) == cur, "compact 应读当前会话的记录")
        # 手动模式 --previous：跳过最新一份
        check(pick_transcript(tdir, "clear", previous=True) == old, "--previous 应跳过最新一份")

        located = locate(repo)
        joined = "\n".join(located)
        check("未提交 1 个文件" in joined, f"应数出 1 个未提交文件：{joined}")
        check("M1-T2" in joined and "M1-T3" in joined and "M1-T1" not in joined, "PLAN 只列未完成任务")
        check("交接：recon 到 api.py:40" in joined, "应带出最新交接行")
        check(locate(tmp) == [], "非 git 目录应返回空落点")

        out = render("clear", located, msgs, old, 5)
        check(out.startswith("kof · 上下文已清") and "old.jsonl" in out and "  1. " in out, "clear 输出格式")
        check(render("compact", [], [], cur, 5).startswith("kof · 上下文刚被压缩") and "没有可用的用户消息" in render("compact", [], [], cur, 5), "compact 输出格式")

        # 主入口：非 clear/compact 静默；hook 输入走通
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["--source", "startup", "--repo", repo])
        check(buf.getvalue() == "", "startup 来源应静默")
        buf = io.StringIO()
        sys_stdin, sys.stdin = sys.stdin, io.StringIO(json.dumps({"source": "clear", "cwd": repo, "transcript_path": cur}))
        try:
            with contextlib.redirect_stdout(buf):
                main([])
        finally:
            sys.stdin = sys_stdin
        check("不装 tidepre" in buf.getvalue() and "M1-T2" in buf.getvalue(), "hook 输入应走通整条链")

    if fails:
        print(f"selftest FAILED: {len(fails)}")
        return 1
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
