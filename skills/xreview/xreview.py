#!/usr/bin/env python3
"""xreview · 异构模型复核门：把一份评审包发给若干个"别家"模型，各出一份只读报告。

设计约束（来自用户的外发限制，机制化而不是靠自觉）：
  1. 默认只发被评审的 diff；多发任何文件都要 --authorized "<授权记录>"。
  2. 凭证文件（.env / 私钥 / auth.json …）出现在评审包里 → 直接拒发，没有授权开关；
     发出前再扫一遍内容（gitleaks；运行异常即拒发，未安装才退到正则弱扫描）。
  3. 需授权内容——全局设计文档（PRD / DESIGN / DECISIONS / doc(s)/ …）与名字涉及口令·权限的文件——
     默认从 diff 里**自动扣下**并列出；要发须 --include-restricted + --authorized + --authorized-for（点名接收方）。
  4. 评审方不得拥有仓库访问权：Codex 在只含评审包的目录里、用权限档隔离跑，且每次先做零成本预检；
     DeepSeek / GLM 直连 HTTP API（没有代理外壳 = 没有读文件的能力）。
  5. key 只从环境变量取，本脚本不打印、不落盘；缺 key 的评审方跳过并说明。

只用标准库。用法见 --help；自检：xreview.py --selftest
"""
import argparse, datetime, fnmatch, hashlib, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request

# ---- 路径分类 ---------------------------------------------------------------
# 两档：① 真正的凭证文件——永不外发，没有授权开关；② 需授权才外发——默认扣下
SECRET_GLOBS = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.keystore", "*.jks", "id_rsa*", "id_ed25519*",
                ".npmrc", ".pypirc", ".netrc", "auth.json", "settings.local.json", "*.tfstate", "*.tfstate.*", "*.kdbx"]
SECRET_OK = [".env.example", ".env.sample", ".env.template"]
RESTRICTED_GLOBS = ["PRD*.md", "DESIGN*.md", "DECISIONS*.md", "doc/*", "docs/*", "*设计*", "*架构*", "*design*.md", "*architecture*.md",  # 全局设计文档
                    "*secret*", "*credential*", "*password*", "*passwd*", "*permission*", "*rbac*", "*密码*", "*密钥*", "*权限*"]           # 名字涉及口令 / 权限的文件
RESTRICTED_OK = ["docs/reviews/*", "doc/reviews/*"]

def _hits(path, globs):
    """大小写不敏感（macOS 文件系统本来就不分）；整条路径、每一级目录名、文件名都拿去匹配。"""
    p = path.replace("\\", "/").casefold(); parts = [x for x in p.split("/") if x]
    return [g for g in globs if fnmatch.fnmatchcase(p, g.casefold()) or any(fnmatch.fnmatchcase(x, g.casefold()) for x in parts)]

def _match(path, globs):
    return bool(_hits(path, globs))

def classify(path, extra_withhold=()):
    """→ 'secret'（永不外发）| 'restricted'（需用户授权，默认扣下）| 'ok'"""
    hits = _hits(path, SECRET_GLOBS)
    if _match(os.path.basename(path), SECRET_OK):          # .env.example 只豁免 .env* 规则，盖不掉别的命中（如 secret/ 目录）
        hits = [g for g in hits if not g.startswith(".env")]
    if hits:
        return "secret"
    if (_match(path, RESTRICTED_GLOBS) or _match(path, list(extra_withhold))) and not _match(path, RESTRICTED_OK):
        return "restricted"
    return "ok"

def classify_file(f, extra_withhold=()):
    """磁盘上的文件：拒绝符号链接（名字正常、指向 .env 的那种），并按真实路径再分类一次。"""
    if os.path.islink(f): sys.exit(f"拒发：`{f}` 是符号链接——不跟随。把真正要发的文件路径写出来。")
    if not os.path.isfile(f): sys.exit(f"拒发：`{f}` 不是普通文件。")
    rank = {"ok": 0, "restricted": 1, "secret": 2}
    return max(classify(f, extra_withhold), classify(os.path.realpath(f), extra_withhold), key=rank.get)

# ---- 评审包 -----------------------------------------------------------------
def split_diff(text):
    """git diff 文本 → [(new_path, hunk_text, old_path)]"""
    parts, cur, path, old = [], [], None, None
    for line in text.splitlines(keepends=True):
        m = re.match(r'^diff --git "?a/(.*?)"? "?b/(.*?)"?\s*$', line)
        if line.startswith("diff --git") and (not m or "\\" in m.group(2)):
            # 解析不了路径（多半是 git 把非 ASCII 文件名写成了八进制转义）→ 无法分类 → 失败即关
            sys.exit(f"拒发：无法解析 diff 头里的路径：{line.strip()[:120]}（用 `git -c core.quotepath=false diff` 生成）")
        if m:
            if path is not None: parts.append((path, "".join(cur), old))
            old, path, cur = m.group(1), m.group(2), [line]
        elif path is not None:
            cur.append(line)
    if path is not None: parts.append((path, "".join(cur), old))
    return parts

def build_payload(diff_text, includes, include_restricted, authorized, extra_withhold=(), excludes=()):
    """→ (payload_text, included_paths, withheld_paths)；违规直接 SystemExit。"""
    included, withheld, chunks = [], [], []
    rank = {"ok": 0, "restricted": 1, "secret": 2}
    for path, hunk, old in split_diff(diff_text):
        if _match(path, list(excludes)) and _match(old, list(excludes)): continue
        # 重命名 / 复制：hunk 里带着旧文件的内容 → 新旧路径都分类，取更严的
        kind = max(classify(path, extra_withhold), classify(old, extra_withhold), key=rank.get)
        if kind != classify(path, extra_withhold): path = f"{old} → {path}"
        if kind == "secret":
            sys.exit(f"拒发：评审包含凭证文件 `{path}`。这类内容没有授权开关——用 --exclude 去掉它再来。")
        if kind == "restricted" and not include_restricted:
            withheld.append(path); continue
        if kind == "restricted" and not authorized:
            sys.exit(f"拒发：`{path}` 属需授权内容（全局设计文档 / 名字涉及口令·权限的文件），发给第三方需要用户授权——先问用户，再带 --authorized \"<授权记录>\"。")
        included.append(path); chunks.append(hunk)
    for f in includes:
        kind = classify_file(f, extra_withhold)
        if kind == "secret":
            sys.exit(f"拒发：`{f}` 属密钥/凭证类路径，没有授权开关。")
        if not authorized:
            sys.exit(f"拒发：额外附带文件 `{f}` 需要用户授权——先问用户，再带 --authorized \"<授权记录>\"。")
        with open(f, encoding="utf-8", errors="replace") as fh:
            chunks.append(f"\n=== 附带文件：{f} ===\n{fh.read()}\n")
        included.append(f)
    return "".join(chunks), included, withheld

SECRET_RES = [r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"\bsk-[A-Za-z0-9_\-]{20,}", r"\bghp_[A-Za-z0-9]{30,}",
              r"\bxox[abps]-[A-Za-z0-9\-]{10,}", r"\bglpat-[A-Za-z0-9_\-]{20,}", r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.",
              r"(?i)(pass(word|wd)?|secret|token|api[_-]?key)\w*\s*[:=]\s*[^\s\"'{$<][^\s]{11,}", r"(?i)(pass(word|wd)?|secret|token|api[_-]?key)\w*\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"]

def scan_secrets(payload_dir, use_gitleaks=True):
    """发现疑似密钥 → SystemExit。不回显密钥本身。"""
    if use_gitleaks and shutil.which("gitleaks"):
        r = subprocess.run(["gitleaks", "dir", payload_dir, "--no-banner", "--redact", "--exit-code", "1"],
                           capture_output=True, text=True)
        if r.returncode == 1:
            rules = sorted(set(re.findall(r"RuleID:\s*(\S+)", r.stdout + r.stderr)))
            sys.exit(f"拒发：gitleaks 在评审包里扫到疑似密钥（规则：{', '.join(rules) or '见 gitleaks 输出'}）。先清掉再来。")
        if r.returncode == 0: return "gitleaks"
        sys.exit(f"拒发：gitleaks 运行异常（exit {r.returncode}）——不降级到弱扫描。先让 `gitleaks dir` 能正常跑。")
    for name in os.listdir(payload_dir):
        text = open(os.path.join(payload_dir, name), encoding="utf-8", errors="replace").read()
        for i, line in enumerate(text.splitlines(), 1):
            for rx in SECRET_RES:
                if re.search(rx, line):
                    sys.exit(f"拒发：评审包第 {i} 行疑似密钥（正则兜底扫描）。先清掉再来。")
    return "正则兜底（弱：未装 gitleaks，建议安装）"

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
    if not probe or not os.path.isabs(probe) or not os.path.isfile(probe) or not os.access(probe, os.R_OK):
        return False                      # 探针不存在时"读不到"是必然的——那种 BLOCKED 什么都没证明
    def can_read(path):
        cmd = ["codex", "sandbox", *CODEX_PROFILE, "--", "sh", "-c",
               'head -c 1 "$1" >/dev/null 2>&1 && echo READABLE || echo BLOCKED', "_", path]
        r = subprocess.run(cmd, cwd=payload_dir, capture_output=True, text=True, timeout=60)
        return r.stdout.strip().splitlines()[-1:] == ["READABLE"]
    # 正对照：评审包必须读得到（否则"全都读不到"也会显示 BLOCKED）；负对照：仓库探针必须读不到
    return can_read(os.path.join(payload_dir, "payload.diff")) and not can_read(probe)

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

# 默认模型名 2026-09-20 对照官方文档核实（api-docs.deepseek.com/quick_start/pricing、docs.bigmodel.cn 模型概览）。
# 模型换代：改这里一处，或用环境变量 XREVIEW_DEEPSEEK_MODEL / XREVIEW_GLM_MODEL 临时覆盖。评审用各家的旗舰档。
HTTP_VENDORS = {
    "deepseek": dict(url="https://api.deepseek.com/chat/completions", keys=["DEEPSEEK_API_KEY"], model="deepseek-v4-pro"),
    "glm": dict(url="https://open.bigmodel.cn/api/paas/v4/chat/completions", keys=["GLM_API_KEY", "ZHIPUAI_API_KEY"], model="glm-5.3"),
}

ALLOWED_HOSTS = {"api.deepseek.com", "open.bigmodel.cn", "api.z.ai"}   # 要加别的端点：改这里，是一次有意的动作

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None       # 不跟随重定向：key 和评审包只去我们点名的主机

def review_http(vendor, prompt, payload_text, timeout=600, _test_url=None):
    cfg = HTTP_VENDORS[vendor]; up = vendor.upper()
    key = next((os.environ[k] for k in cfg["keys"] if os.environ.get(k)), None)
    if not key: return None, f"环境变量 {' / '.join(cfg['keys'])} 未设置，跳过（key 只从环境变量取）"
    url = _test_url or os.environ.get(f"XREVIEW_{up}_URL", cfg["url"]); model = os.environ.get(f"XREVIEW_{up}_MODEL", cfg["model"])
    u = urllib.parse.urlparse(url)
    if not _test_url and (u.scheme != "https" or u.hostname not in ALLOWED_HOSTS):
        return None, f"拒发：{vendor} 的接口地址 `{u.scheme}://{u.hostname}` 不在白名单（只允许 https + {sorted(ALLOWED_HOSTS)}）"
    body = json.dumps({"model": model, "stream": False, "messages": [
        {"role": "user", "content": f"{prompt}\n=== 评审包开始 ===\n{payload_text}\n=== 评审包结束 ==="}]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"], f"{vendor}（{model}）"
    except Exception as e:                       # 不回显请求头 / key
        return None, f"{vendor} 调用失败：{type(e).__name__}: {str(e)[:200]}"

def bind_recipients(reviewers, authorized_for):
    """含需授权内容时：授权必须点名接收方，没点到名的评审方本次不发。→ (保留的评审方, 被去掉的)"""
    if not authorized_for:
        sys.exit("拒发：--authorized 必须配 --authorized-for <评审方>——授权要点名发给谁，\"PRD 给 codex\" 不等于也给 deepseek / glm。")
    allowed = {x.strip() for x in authorized_for.split(",") if x.strip()}
    rv = [x.strip() for x in reviewers.split(",") if x.strip()]
    return ",".join(x for x in rv if x in allowed), [x for x in rv if x not in allowed]

# ---- 主流程 -----------------------------------------------------------------
def run(args):
    if args.payload:
        kind = classify_file(args.payload, args.withhold)
        if kind == "secret": sys.exit(f"拒发：`{args.payload}` 属密钥/凭证类路径，没有授权开关。")
        if not args.authorized:
            sys.exit(f"拒发：整份文件 `{args.payload}` 发给第三方需要用户授权——先问用户，再带 --authorized \"<授权记录>\"。")
        payload = open(args.payload, encoding="utf-8", errors="replace").read(); included, withheld = [args.payload], []
    else:
        r = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--no-color", f"{args.base}...HEAD"], capture_output=True, text=True)
        if r.returncode != 0: sys.exit(f"git diff 失败：{r.stderr.strip()}")
        payload, included, withheld = build_payload(r.stdout, args.include, args.include_restricted, args.authorized, args.withhold, args.exclude)
    if args.authorized:
        args.reviewers, dropped = bind_recipients(args.reviewers, args.authorized_for)
        if dropped: print(f"未获授权 {', '.join(dropped)}：本次含需授权内容，只发给授权点了名的评审方")
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
        if withheld: print(f"已扣下   {len(withheld)} 个需授权文件（设计文档 / 名字涉及口令·权限；未发出）：{', '.join(withheld)}")
        if args.authorized: print(f"授权记录 {args.authorized}（接收方：{args.authorized_for}）")
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
                         f"- 已扣下（未发出）：{', '.join(withheld) or '无'}\n- 授权记录：{(args.authorized + '（接收方：' + args.authorized_for + '）') if args.authorized else '无（只发了代码 diff）'}\n"
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
                    ("src/app/credentials.py", "restricted"), ("PRD.md", "restricted"), ("doc/05_系统设计.md", "restricted"),
                    ("docs/reviews/M3_codex.md", "ok"), ("DECISIONS-ARCHIVE.md", "restricted"), ("src/auth/password_reset.py", "restricted"), ("config/权限表.yaml", "restricted"), ("src/api/routes.py", "ok"), ("PLAN.md", "ok")]:
        check(f"classify {p}", classify(p) == want)
    check("classify 项目追加的扣下规则", classify("spec/内部口径.md", ["spec/*"]) == "restricted")
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
    must_exit("--include-restricted 无授权", lambda: build_payload(diff, [], True, None), "需要用户授权")
    text, inc, wh = build_payload(diff, [], True, "用户 2026-09-20 同意：PRD 给 codex")
    check("授权后设计文档进包", "PRD.md" in inc and "new PRD.md" in text)
    must_exit("密钥路径拒发", lambda: build_payload(diff + d(".env"), [], True, "有授权也不行"), "没有授权开关")
    text, inc, wh = build_payload(diff + d(".env"), [], False, None, excludes=[".env"])
    check("--exclude 去掉密钥路径后可发", ".env" not in inc and "new .env" not in text)
    # —— 以下用例来自 Codex 对本脚本的隔离评审（docs/reviews/xreview-self_codex_20260920.md），逐条先复现后修 ——
    ren = ("diff --git a/.env b/config/app.txt\nsimilarity index 90%\nrename from .env\nrename to config/app.txt\n"
           "--- a/.env\n+++ b/config/app.txt\n@@ -1 +1 @@\n-DB_PASS=x\n+DB_PASS=y\n")
    must_exit("重命名绕过：.env → config/app.txt", lambda: build_payload(ren, [], False, None), "没有授权开关")
    ren2 = ren.replace(".env", "PRD.md").replace("DB_PASS", "scope")
    text, inc, wh = build_payload(d("src/a.py") + ren2, [], False, None)
    check("重命名绕过：PRD.md → 普通路径仍被扣下", len(wh) == 1 and "PRD.md" in wh[0] and "scope" not in text)
    for p_, want in [("SERVER.PEM", "secret"), ("Secrets/prod.yaml", "restricted"), ("prd.md", "restricted"), ("Docs/internal.md", "restricted"),
                     ("secret/.env.example", "restricted"), ("config/.env.example", "ok"), ("deploy/.ENV.production", "secret"),
                     ("backup.pem/.env.example", "secret")]:         # .env.example 只豁免 .env* 规则，盖不掉目录名命中的 *.pem
        check(f"大小写/逐级目录 classify {p_}", classify(p_) == want)
    check("授权须点名接收方", bind_recipients("codex,deepseek,glm", "codex") == ("codex", ["deepseek", "glm"]))
    must_exit("授权未点名接收方", lambda: bind_recipients("codex,glm", None), "点名")
    check("隔离预检：探针为空不得通过", codex_isolation_ok("/tmp", None) is False)
    check("隔离预检：探针不存在不得通过", codex_isolation_ok("/tmp", "/nonexistent/x'; echo BLOCKED; '") is False)
    ln_dir = tempfile.mkdtemp(); real = os.path.join(ln_dir, ".env"); link = os.path.join(ln_dir, "notes.md")
    open(real, "w").write("K=1"); os.symlink(real, link)
    try: must_exit("符号链接 notes.md → .env", lambda: build_payload("", [link], False, "用户同意附带 notes.md"), "符号链接")
    finally: shutil.rmtree(ln_dir, ignore_errors=True)
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
        check("干净评审包放行", scan_secrets(tmp, use_gitleaks=False).startswith("正则兜底"))
        open(os.path.join(tmp, "payload.diff"), "w").write("+  password: Sup3rS3cretValue99\n")
        must_exit("未加引号的 YAML 口令", lambda: scan_secrets(tmp, use_gitleaks=False), "疑似密钥")
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
        os.environ.update(DEEPSEEK_API_KEY="test-key-not-real", XREVIEW_DEEPSEEK_MODEL="m-test")
        t, info = review_http("deepseek", "提示词", "PAYLOAD-BODY", _test_url=f"http://127.0.0.1:{srv.server_port}/chat/completions")
        check("HTTP 返回解析", t == "[中] src/a.py:1 — 假发现" and "m-test" in info)
        check("HTTP 请求形态", seen.get("auth") == "Bearer test-key-not-real" and seen["body"]["model"] == "m-test" and "PAYLOAD-BODY" in seen["body"]["messages"][0]["content"])
        check("报告信息不含 key", "test-key-not-real" not in info)
        # 环境变量想把接口改到别处（明文 http / 非厂商域名）→ 拒发，且不发任何请求
        seen.clear()
        for bad in (f"http://127.0.0.1:{srv.server_port}/x", "https://evil.example.com/v1/chat/completions", "http://api.deepseek.com/chat/completions"):
            os.environ["XREVIEW_DEEPSEEK_URL"] = bad
            t, info = review_http("deepseek", "P", "X"); check(f"接口地址白名单 {bad[:24]}", t is None and "白名单" in info)
        check("被拒的地址没有收到请求", not seen)
        os.environ["XREVIEW_DEEPSEEK_URL"] = "https://api.deepseek.com/chat/completions"
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
    ap.add_argument("--include-restricted", action="store_true", help="把 diff 里被扣下的需授权文件（设计文档 / 名字涉及口令·权限）也发出去（须 --authorized）")
    ap.add_argument("--include", action="append", default=[], metavar="FILE", help="额外附带文件（须 --authorized）")
    ap.add_argument("--authorized", metavar="记录", help="用户授权记录：谁、何时、同意把什么发给谁")
    ap.add_argument("--authorized-for", metavar="评审方", help="这次授权点名的接收方（逗号分隔）。带了 --authorized 就必须带它；没点到名的评审方本次不发")
    ap.add_argument("--out", default="docs/reviews"); ap.add_argument("--max-bytes", type=int, default=400_000)
    ap.add_argument("--probe", help="Codex 隔离预检用的仓库内文件（默认取 git ls-files 第一个）")
    ap.add_argument("--dry-run", action="store_true", help="只显示会发什么，不发")
    args = ap.parse_args()
    sys.exit(selftest() if args.selftest else run(args))

if __name__ == "__main__":
    main()
