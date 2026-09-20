#!/usr/bin/env python3
"""xreview · 异构模型复核门：把一份评审包发给若干个"别家"模型，各出一份只读报告。

设计约束（来自用户的外发限制，机制化而不是靠自觉）：
  1. 默认只发被评审的 diff；多发任何文件都要 --authorized "<授权记录>"。
  2. 密钥 / 凭证类路径出现在评审包里 → 直接拒发（没有授权开关）；发出前再扫一遍内容（gitleaks，缺了用正则兜底）。
  3. 全局设计文档（PRD / DESIGN / DECISIONS / doc(s)/ …）默认从 diff 里**自动扣下**并列出；
     要发须 --include-design + --authorized。
  4. 评审方不得拥有仓库访问权：Codex 在只含评审包的目录里、用权限档隔离跑，且每次先做零成本预检；
     DeepSeek / GLM 直连 HTTP API（没有代理外壳 = 没有读文件的能力）。
  5. key 只从环境变量取，本脚本不打印、不落盘；缺 key 的评审方跳过并说明。

只用标准库。用法见 --help；自检：xreview.py --selftest
"""
import argparse, datetime, fnmatch, hashlib, json, os, re, shutil, subprocess, sys, tempfile, urllib.request

# ---- 路径分类 ---------------------------------------------------------------
SECRET_GLOBS = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.keystore", "*.jks", "id_rsa*", "id_ed25519*",
                "*secret*", "*credential*", "*password*", "*passwd*", ".npmrc", ".pypirc", ".netrc", "auth.json",
                "settings.local.json", "*.tfstate", "*.tfstate.*", "*.kdbx"]
SECRET_OK = [".env.example", ".env.sample", ".env.template"]
DESIGN_GLOBS = ["PRD*.md", "DESIGN*.md", "DECISIONS*.md", "doc/*", "docs/*", "*设计*", "*架构*", "*design*.md", "*architecture*.md"]
DESIGN_OK = ["docs/reviews/*", "doc/reviews/*"]

def _match(path, globs):
    base = os.path.basename(path)
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(base, g) for g in globs)

def classify(path, extra_withhold=()):
    """→ 'secret' | 'design' | 'ok'"""
    if _match(path, SECRET_GLOBS) and not _match(path, SECRET_OK):
        return "secret"
    if (_match(path, DESIGN_GLOBS) or _match(path, list(extra_withhold))) and not _match(path, DESIGN_OK):
        return "design"
    return "ok"

# ---- 评审包 -----------------------------------------------------------------
def split_diff(text):
    """git diff 文本 → [(path, hunk_text)]"""
    parts, cur, path = [], [], None
    for line in text.splitlines(keepends=True):
        m = re.match(r'^diff --git "?a/(.*?)"? "?b/(.*?)"?\s*$', line)
        if line.startswith("diff --git") and (not m or "\\" in m.group(2)):
            # 解析不了路径（多半是 git 把非 ASCII 文件名写成了八进制转义）→ 无法分类 → 失败即关
            sys.exit(f"拒发：无法解析 diff 头里的路径：{line.strip()[:120]}（用 `git -c core.quotepath=false diff` 生成）")
        if m:
            if path is not None: parts.append((path, "".join(cur)))
            path, cur = m.group(2), [line]
        elif path is not None:
            cur.append(line)
    if path is not None: parts.append((path, "".join(cur)))
    return parts

def build_payload(diff_text, includes, include_design, authorized, extra_withhold=(), excludes=()):
    """→ (payload_text, included_paths, withheld_paths)；违规直接 SystemExit。"""
    included, withheld, chunks = [], [], []
    for path, hunk in split_diff(diff_text):
        if _match(path, list(excludes)): continue
        kind = classify(path, extra_withhold)
        if kind == "secret":
            sys.exit(f"拒发：评审包含密钥/凭证类路径 `{path}`。这类内容没有授权开关——用 --exclude 去掉它再来。")
        if kind == "design" and not include_design:
            withheld.append(path); continue
        if kind == "design" and not authorized:
            sys.exit(f"拒发：`{path}` 属全局设计文档，发给第三方需要用户授权——先问用户，再带 --authorized \"<授权记录>\"。")
        included.append(path); chunks.append(hunk)
    for f in includes:
        kind = classify(f, extra_withhold)
        if kind == "secret":
            sys.exit(f"拒发：`{f}` 属密钥/凭证类路径，没有授权开关。")
        if not authorized:
            sys.exit(f"拒发：额外附带文件 `{f}` 需要用户授权——先问用户，再带 --authorized \"<授权记录>\"。")
        with open(f, encoding="utf-8", errors="replace") as fh:
            chunks.append(f"\n=== 附带文件：{f} ===\n{fh.read()}\n")
        included.append(f)
    return "".join(chunks), included, withheld

SECRET_RES = [r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"\bsk-[A-Za-z0-9_\-]{20,}", r"\bghp_[A-Za-z0-9]{30,}",
              r"\bxox[abps]-[A-Za-z0-9\-]{10,}", r"(?i)(pass(word|wd)?|secret|token|api[_-]?key)\w*\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"]

def scan_secrets(payload_dir, use_gitleaks=True):
    """发现疑似密钥 → SystemExit。不回显密钥本身。"""
    if use_gitleaks and shutil.which("gitleaks"):
        r = subprocess.run(["gitleaks", "dir", payload_dir, "--no-banner", "--redact", "--exit-code", "1"],
                           capture_output=True, text=True)
        if r.returncode == 1:
            rules = sorted(set(re.findall(r"RuleID:\s*(\S+)", r.stdout + r.stderr)))
            sys.exit(f"拒发：gitleaks 在评审包里扫到疑似密钥（规则：{', '.join(rules) or '见 gitleaks 输出'}）。先清掉再来。")
        if r.returncode == 0: return "gitleaks"
    for name in os.listdir(payload_dir):
        text = open(os.path.join(payload_dir, name), encoding="utf-8", errors="replace").read()
        for i, line in enumerate(text.splitlines(), 1):
            for rx in SECRET_RES:
                if re.search(rx, line):
                    sys.exit(f"拒发：评审包第 {i} 行疑似密钥（正则兜底扫描）。先清掉再来。")
    return "regex"

# ---- 评审方 -----------------------------------------------------------------
PROMPT = """你是独立的代码评审方，来自另一家模型厂商——你的价值在于盲区与实现方不同。你看不到仓库，只有下面这份评审包。
只出报告：不要整文件重写，不要夸奖。
重点找"能通过测试与 CI、却会在生产出事"的问题：竞态 / TOCTOU、默认值站在宽松侧的守卫（fail-open）、信任边界错误、
注入与转义、被破坏的不变量、错误的重试与幂等、遗漏的状态分支、"通过了但没测到真正失败形态"的测试。
每条发现以一行起头：`[高|中|低] 路径:行号 — 问题`，随后一两句写触发条件与建议修法。
你没有运行环境：所有发现都是「读码推断」；拿不准就写明拿不准，不要编造文件名或行号。
没有发现就写"未发现问题"。最后单列一段「未覆盖面」：这份评审包没给你看、但你认为值得看的地方。
{focus}"""

CODEX_PROFILE = ['-c', 'default_permissions="xreview"',
                 '-c', 'permissions.xreview.filesystem={":minimal"="read", ":workspace_roots"={"."="read"}}']

def codex_isolation_ok(payload_dir, probe):
    """零成本预检（不调模型）：权限档下，仓库里的探针文件必须读不到。权限档是 beta，schema 变了这里会先红。"""
    cmd = ["codex", "sandbox", *CODEX_PROFILE, "--", "sh", "-c",
           f"head -c 1 '{probe}' >/dev/null 2>&1 && echo READABLE || echo BLOCKED"]
    r = subprocess.run(cmd, cwd=payload_dir, capture_output=True, text=True, timeout=60)
    return r.stdout.strip().endswith("BLOCKED")

def review_codex(payload_dir, prompt, probe, timeout=900):
    if not shutil.which("codex"): return None, "未安装 codex CLI，跳过"
    if not codex_isolation_ok(payload_dir, probe):
        return None, "隔离预检失败：权限档下仍读得到仓库文件——拒跑（Codex 的权限档是 beta，先查其配置写法是否变了）"
    out = os.path.join(payload_dir, "codex_out.md")
    cmd = ["codex", "exec", "-C", payload_dir, "--skip-git-repo-check", "--ephemeral", "--color", "never",
           *CODEX_PROFILE, "-o", out, prompt + "\n评审包在当前目录的 payload.diff，只读它。"]
    r = subprocess.run(cmd, cwd=payload_dir, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not os.path.exists(out):
        return None, f"codex exec 失败（exit {r.returncode}）：{(r.stderr or r.stdout)[-300:]}"
    text = open(out, encoding="utf-8").read(); os.remove(out)
    return text, "codex（CLI 默认模型）"

HTTP_VENDORS = {
    "deepseek": dict(url="https://api.deepseek.com/chat/completions", keys=["DEEPSEEK_API_KEY"], model="deepseek-chat"),
    "glm": dict(url="https://open.bigmodel.cn/api/paas/v4/chat/completions", keys=["GLM_API_KEY", "ZHIPUAI_API_KEY"], model="glm-4.6"),
}

def review_http(vendor, prompt, payload_text, timeout=600):
    cfg = HTTP_VENDORS[vendor]; up = vendor.upper()
    key = next((os.environ[k] for k in cfg["keys"] if os.environ.get(k)), None)
    if not key: return None, f"环境变量 {' / '.join(cfg['keys'])} 未设置，跳过（key 只从环境变量取）"
    url = os.environ.get(f"XREVIEW_{up}_URL", cfg["url"]); model = os.environ.get(f"XREVIEW_{up}_MODEL", cfg["model"])
    body = json.dumps({"model": model, "stream": False, "messages": [
        {"role": "user", "content": f"{prompt}\n=== 评审包开始 ===\n{payload_text}\n=== 评审包结束 ==="}]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"], f"{vendor}（{model}）"
    except Exception as e:                       # 不回显请求头 / key
        return None, f"{vendor} 调用失败：{type(e).__name__}: {str(e)[:200]}"

# ---- 主流程 -----------------------------------------------------------------
def run(args):
    if args.payload:
        kind = classify(args.payload, args.withhold)
        if kind == "secret": sys.exit(f"拒发：`{args.payload}` 属密钥/凭证类路径，没有授权开关。")
        if not args.authorized:
            sys.exit(f"拒发：整份文件 `{args.payload}` 发给第三方需要用户授权——先问用户，再带 --authorized \"<授权记录>\"。")
        payload = open(args.payload, encoding="utf-8", errors="replace").read(); included, withheld = [args.payload], []
    else:
        r = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--no-color", f"{args.base}...HEAD"], capture_output=True, text=True)
        if r.returncode != 0: sys.exit(f"git diff 失败：{r.stderr.strip()}")
        payload, included, withheld = build_payload(r.stdout, args.include, args.include_design, args.authorized, args.withhold, args.exclude)
    if not payload.strip(): sys.exit("评审包为空（diff 为空，或全部被扣下 / 排除）。")
    size = len(payload.encode())
    if size > args.max_bytes: sys.exit(f"评审包 {size} 字节，超过上限 {args.max_bytes}：缩小 --base 范围或用 --exclude。")

    root = os.path.expanduser("~/.cache/xreview"); os.makedirs(root, mode=0o700, exist_ok=True)
    pdir = tempfile.mkdtemp(prefix="run-", dir=root)
    try:
        with open(os.path.join(pdir, "payload.diff"), "w", encoding="utf-8") as fh: fh.write(payload)
        scanner = scan_secrets(pdir)
        sha = hashlib.sha256(payload.encode()).hexdigest()[:16]
        print(f"评审包   {size} 字节 · sha256 {sha} · 密钥扫描：{scanner} 通过")
        print(f"包含     {len(included)} 个文件：{', '.join(included[:12])}{' …' if len(included) > 12 else ''}")
        if withheld: print(f"已扣下   {len(withheld)} 个全局设计文档（未发出）：{', '.join(withheld)}")
        if args.authorized: print(f"授权记录 {args.authorized}")
        if args.dry_run: print("dry-run：到此为止，什么都没发。"); return 0

        prompt = PROMPT.format(focus=(f"本次请重点看：{args.focus}" if args.focus else ""))
        probe = args.probe or next((os.path.abspath(p) for p in subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.splitlines() if os.path.isfile(p)), None)
        os.makedirs(args.out, exist_ok=True); date = datetime.date.today().strftime("%Y%m%d"); done = 0
        for rv in args.reviewers.split(","):
            rv = rv.strip()
            if rv == "codex": text, info = review_codex(pdir, prompt, probe)
            elif rv in HTTP_VENDORS: text, info = review_http(rv, prompt, payload)
            else: text, info = None, "未知评审方"
            if text is None: print(f"跳过     {rv}：{info}"); continue
            path = os.path.join(args.out, f"{args.task}_{rv}_{date}.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f"# xreview · {args.task} · {info}\n\n- 日期：{date}\n- 评审包：{size} 字节，sha256 {sha}\n- 包含：{', '.join(included)}\n"
                         f"- 已扣下（未发出）：{', '.join(withheld) or '无'}\n- 授权记录：{args.authorized or '无（只发了代码 diff）'}\n"
                         f"- 性质：读码推断，未经实测——采信前先复现\n\n---\n\n{text}\n")
            print(f"完成     {rv} → {path}"); done += 1
        print(f"共 {done} 份报告。下一步由主控模型合并裁决：多方同报 = 大概率真问题；只有一方报 = 先复现再动。")
        return 0 if done else 2
    finally:
        shutil.rmtree(pdir, ignore_errors=True)

def selftest():
    import http.server, threading
    fails = []
    def check(name, cond):
        if not cond: fails.append(name)
    def must_exit(name, fn, needle):
        try: fn(); fails.append(name + "（没有拒发）")
        except SystemExit as e: check(name + "（提示语）", needle in str(e))
    # 路径分类
    for p, want in [(".env", "secret"), ("deploy/.env.production", "secret"), (".env.example", "ok"), ("certs/server.pem", "secret"),
                    ("src/app/credentials.py", "secret"), ("PRD.md", "design"), ("doc/05_系统设计.md", "design"),
                    ("docs/reviews/M3_codex.md", "ok"), ("DECISIONS-ARCHIVE.md", "design"), ("src/api/routes.py", "ok"), ("PLAN.md", "ok")]:
        check(f"classify {p}", classify(p) == want)
    check("classify 项目追加的扣下规则", classify("spec/内部口径.md", ["spec/*"]) == "design")
    # 评审包：设计文档默认扣下、密钥路径拒发、授权与排除
    d = lambda p: f"diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n@@ -1 +1 @@\n-old {p}\n+new {p}\n"
    diff = d("src/a.py") + d("PRD.md") + d("tests/test_a.py")
    text, inc, wh = build_payload(diff, [], False, None)
    check("设计文档默认扣下", inc == ["src/a.py", "tests/test_a.py"] and wh == ["PRD.md"] and "new PRD.md" not in text and "new src/a.py" in text)
    # 中文文件名：原样路径要能分类；八进制转义的路径无法分类 → 拒发（否则设计文档会混在上一个文件的 hunk 里溜出去）
    text, inc, wh = build_payload(d("src/a.py") + d("doc/05_系统设计.md") + d("src/数据.py"), [], False, None)
    check("中文设计文档被扣下", wh == ["doc/05_系统设计.md"] and inc == ["src/a.py", "src/数据.py"] and "系统设计" not in text)
    quoted = d("src/a.py") + 'diff --git "a/\\347\\263\\273\\347\\273\\237.md" "b/\\347\\263\\273\\347\\273\\237.md"\n+机密设计\n'
    must_exit("八进制转义路径", lambda: build_payload(quoted, [], False, None), "无法解析")
    must_exit("--include-design 无授权", lambda: build_payload(diff, [], True, None), "需要用户授权")
    text, inc, wh = build_payload(diff, [], True, "用户 2026-09-20 同意：PRD 给 codex")
    check("授权后设计文档进包", "PRD.md" in inc and "new PRD.md" in text)
    must_exit("密钥路径拒发", lambda: build_payload(diff + d(".env"), [], True, "有授权也不行"), "没有授权开关")
    text, inc, wh = build_payload(diff + d(".env"), [], False, None, excludes=[".env"])
    check("--exclude 去掉密钥路径后可发", ".env" not in inc and "new .env" not in text)
    # --include 附带文件：无授权拒发；密钥路径有授权也拒发；有授权才进包
    inc_dir = tempfile.mkdtemp(); note = os.path.join(inc_dir, "note.md"); envf = os.path.join(inc_dir, ".env")
    open(note, "w", encoding="utf-8").write("附带说明-MARK"); open(envf, "w").write("X=1")
    try:
        must_exit("--include 无授权", lambda: build_payload(diff, [note], False, None), "需要用户授权")
        must_exit("--include 密钥路径", lambda: build_payload(diff, [envf], False, "有授权也不行"), "没有授权开关")
        text, inc, wh = build_payload(diff, [note], False, "用户同意附带 note.md")
        check("--include 授权后进包", note in inc and "附带说明-MARK" in text)
    finally: shutil.rmtree(inc_dir, ignore_errors=True)
    # 内容扫描（强制走正则兜底，不依赖本机有没有 gitleaks）
    tmp = tempfile.mkdtemp()
    try:
        open(os.path.join(tmp, "payload.diff"), "w").write('+db_password = "hunter2hunter2"\n')
        must_exit("正则兜底扫到密钥", lambda: scan_secrets(tmp, use_gitleaks=False), "疑似密钥")
        open(os.path.join(tmp, "payload.diff"), "w").write("+x = compute(a, b)\n")
        check("干净评审包放行", scan_secrets(tmp, use_gitleaks=False) == "regex")
    finally: shutil.rmtree(tmp, ignore_errors=True)
    # HTTP 评审方：本地假服务器核对请求形态；缺 key 跳过
    seen = {}
    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            seen["auth"] = self.headers.get("Authorization"); seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = json.dumps({"choices": [{"message": {"content": "[中] src/a.py:1 — 假发现"}}]}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(out)
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    saved = {k: os.environ.pop(k, None) for k in ["DEEPSEEK_API_KEY", "XREVIEW_DEEPSEEK_URL", "XREVIEW_DEEPSEEK_MODEL", "GLM_API_KEY", "ZHIPUAI_API_KEY"]}
    try:
        t, info = review_http("glm", "P", "payload"); check("缺 key 跳过", t is None and "未设置" in info)
        os.environ.update(DEEPSEEK_API_KEY="test-key-not-real", XREVIEW_DEEPSEEK_URL=f"http://127.0.0.1:{srv.server_port}/chat/completions", XREVIEW_DEEPSEEK_MODEL="m-test")
        t, info = review_http("deepseek", "提示词", "PAYLOAD-BODY")
        check("HTTP 返回解析", t == "[中] src/a.py:1 — 假发现" and "m-test" in info)
        check("HTTP 请求形态", seen.get("auth") == "Bearer test-key-not-real" and seen["body"]["model"] == "m-test" and "PAYLOAD-BODY" in seen["body"]["messages"][0]["content"])
        check("报告信息不含 key", "test-key-not-real" not in info)
    finally:
        srv.shutdown()
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None: os.environ[k] = v
    if fails: print("selftest FAIL:\n  " + "\n  ".join(fails)); return 1
    print("selftest ok"); return 0

def main():
    ap = argparse.ArgumentParser(description="xreview · 异构模型复核门（只读报告；默认只发 diff；密钥拒发；设计文档须授权）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--base", default="main", help="评审 `git diff BASE...HEAD`（默认 main）")
    ap.add_argument("--payload", help="改为评审整份文件（如 PRD.md）——必须带 --authorized")
    ap.add_argument("--task", default="review", help="任务号，用于报告文件名（如 M3-T4）")
    ap.add_argument("--reviewers", default="codex,deepseek,glm")
    ap.add_argument("--focus", help="请评审方重点看的方面（一句话）")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="从 diff 里去掉匹配的文件（可重复）")
    ap.add_argument("--withhold", action="append", default=[], metavar="GLOB", help="项目追加的\"需授权才外发\"路径（可重复）")
    ap.add_argument("--include-design", action="store_true", help="把 diff 里的全局设计文档也发出去（须 --authorized）")
    ap.add_argument("--include", action="append", default=[], metavar="FILE", help="额外附带文件（须 --authorized）")
    ap.add_argument("--authorized", metavar="记录", help="用户授权记录：谁、何时、同意把什么发给谁")
    ap.add_argument("--out", default="docs/reviews"); ap.add_argument("--max-bytes", type=int, default=400_000)
    ap.add_argument("--probe", help="Codex 隔离预检用的仓库内文件（默认取 git ls-files 第一个）")
    ap.add_argument("--dry-run", action="store_true", help="只显示会发什么，不发")
    args = ap.parse_args()
    sys.exit(selftest() if args.selftest else run(args))

if __name__ == "__main__":
    main()
