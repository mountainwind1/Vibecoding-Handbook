#!/usr/bin/env python3
"""map —— 项目地图：业务流程上的模块 × 页面/接口/数据/逻辑 × 当前在哪 × 问题在哪 × 精力花在哪。只读。
数字全部由 PLAN.md + 模块地图 + git 现算，不凭会话记忆；PLAN 的读法与 prog 一致。

    python3 map.py [--repo .] [--out 目录] [--no-archify] [--publish] [--quiet]
    python3 map.py --selftest

产物（默认 ~/.cache/vibe-map/<项目名>/，不进仓库）：
    index.html              自带页面：阶段 / 线路图 / 模块卡片 / 问题原文 / 投入热力图
    archify.html            装了 archify skill 时：交互架构图（index.html 的线路图页签内嵌它）
    map.architecture.json   交给 archify 的 spec（布局按网格算好，不让 agent 手摆坐标）

模块地图写在项目 ENGINEERING.md 的「模块地图」一节（没有就按目录自动分组）：
    数据流：上游 → 导入 → 数据库 → 查询 API      一行一条业务线，箭头 = 流程顺序；没进业务线的模块算「横切」
    | 导入 | 接口 | src/x/ingest/*cli.py |        层 = 页面/接口/数据/逻辑/测试/外部/关键词；路径是 glob（* 可跨目录），首条命中为准
    发布：<命令，{dir} = 产物目录>                  可选：--publish 时执行（云端托管由项目自己定，任何工具都能跑）
"""
import argparse, collections, datetime, fnmatch, json, os, re, shlex, subprocess, sys, tempfile, urllib.error, urllib.request

LAYERS = ["页面", "接口", "数据", "逻辑"]            # 卡片上显示的层；测试只计入投入
MS_RE = re.compile(r"^## (?:[^M]*[:：] *)?(M[-A-Za-z0-9.]*[0-9][A-Za-z0-9]*)\s*[·:：]?\s*(.*)$")   # 同 prog：只认二级标题
CLOSED_RE = re.compile(r"已收口|✅")
BOX_RE = re.compile(r"^- \[([ xX])\] (.*)$")                                              # 同 prog：顶格复选框，缩进的子项不计
ROW_RE = re.compile(r"^\| *([A-Za-z][-A-Za-z0-9.]*-[A-Za-z]+[0-9]+[A-Za-z0-9]*) *\|(.*)$")  # 同 prog：表格行 | M3-T4 | 内容 | ✅ |
ID_RE = re.compile(r"^([A-Za-z][-A-Za-z0-9.]*[0-9][A-Za-z0-9]*(?: v\d+)?)\s*[·:：]?\s*(.*)$")   # 「EXT-9 v2」是另一条，版本号算进编号
FLAG_RE = re.compile(r"^(待拍板|偏差)[:：]\s*(.*)$")
TASK_ID = re.compile(r"^M(?:-[A-Z]+)?\d")
MS_IN_SUBJ = re.compile(r"(?<![A-Za-z0-9])(M(?:-[A-Z]+)?\d+[a-z]?)(?![0-9])")
FILE_TOK = re.compile(r"[A-Za-z0-9_./-]*[A-Za-z0-9_-]\.(?:py|pyi|tsx?|jsx?|mjs|vue|svelte|html|css|scss|sql|ya?ml|json|toml|sh|go|rs|java|kt|swift|rb|php|cs|mod|sum|ini|cfg|md)\b")
# 投入只算代码与文档：数据文件、锁文件会把比例冲垮（实测一个项目的基准 JSON 占全部改动行 98%）
NOT_EFFORT = re.compile(r"\.(json|geojson|csv|tsv|log|txt|lock|sum|svg|snap|parquet|xml|map)$|(^|/)(uv|package-lock|yarn|pnpm-lock|poetry|Cargo)\.", re.I)
CATEGORY = {"SEC": "安全", "EXT": "外部依赖"}
RANK = {"待拍板": 4, "安全": 3, "偏差": 2, "欠账": 2, "外部依赖": 1}
PAGE_MARK = "<!-- vibe-map-page -->"                            # 发布后自查：不登录能取到带这个标记的页面 = 访问控制没生效
LEGEND = {"frontend": "页面为主", "backend": "逻辑 / 接口为主", "database": "数据为主", "cloud": "部署 / 基建",
          "security": "鉴权 / 安全", "external": "跨仓库"}      # 类型是按文件分层推出来的，图例照实说


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, "-c", "core.quotepath=off", *a], capture_output=True, text=True, check=True).stdout


def clean(s):
    return re.sub(r"\*\*|`", "", s).strip(" —–-")


def trim(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


# ---- 模块地图 ------------------------------------------------------------------
def parse_map(text):
    lanes, rules, kw, publish = [], [], collections.defaultdict(list), None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^发布[：:]\s*(.+)$", s)
        if m:
            publish = m.group(1).strip().strip("`") if "{dir}" in m.group(1) or "{" not in m.group(1) else None
            continue
        if "{" in s:                                            # 模板占位没填 = 不算
            continue
        m = re.match(r"^([^|#>`*\-\s][^：:|]{0,20})[：:]\s*(.+→.+)$", s)
        if m:
            lanes.append(dict(name=m.group(1).strip(), mods=[x.strip() for x in m.group(2).split("→") if x.strip()]))
            continue
        if s.startswith("|"):
            c = [x.strip() for x in s.strip("|").split("|")]
            if len(c) < 3 or c[0] == "模块" or not c[0].strip("-: "):
                continue
            items = [p.strip().strip("`") for p in re.split(r"[,，、]", c[2]) if p.strip().strip("`")]
            (kw[c[0]].extend(items) if c[1] == "关键词" else rules.append((c[0], c[1], items)))
    return lanes, rules, dict(kw), publish


def guess_layer(p):
    q = p.lower()
    if re.search(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]*$|\.(test|spec)\.", q): return "测试"
    if re.search(r"\.(html|css|scss|tsx|jsx|vue|svelte)$|(^|/)(static|pages|components|views|ui)/", q): return "页面"
    if re.search(r"(^|/)(models?|migrations?|alembic|contracts?|schemas?|db)(/|\.py$)|\.sql$", q): return "数据"
    if re.search(r"(^|/)(api|routes?|endpoints?)(/|\.py$)|cli\.py$", q): return "接口"
    return "逻辑"


def auto_rules(files):
    """没有地图时：顶层目录 = 模块；src/app/lib/packages 这类容器目录往里一层（只有一个包名目录时再往里一层）。"""
    roots = {"src", "app", "lib", "packages", "apps", "backend", "frontend"}
    kids = collections.defaultdict(set)
    for f in files:
        parts = f.split("/")
        for i in range(1, len(parts)):
            kids["/".join(parts[:i])].add(parts[i])
    mods = {}
    for f in files:
        parts = f.split("/")
        i = 0
        while i < len(parts) - 1 and (parts[i] in roots or (i > 0 and parts[i - 1] in roots and len(kids["/".join(parts[:i])]) == 1)):
            i += 1
        if i < len(parts) - 1:
            mods["/".join(parts[:i + 1])] = parts[i]
    return [(name, "*", [prefix + "/*"]) for prefix, name in sorted(mods.items())] + [("（根目录）", "*", ["*"])]


class Mapper:
    def __init__(self, rules):
        self.rules, self.cache = rules, {}

    def __call__(self, path):
        if path not in self.cache:
            hit = ("未归类", "逻辑")
            for mod, layer, globs in self.rules:
                if any(fnmatch.fnmatchcase(path, g) or (g.endswith("/") and path.startswith(g)) for g in globs):
                    hit = (mod, guess_layer(path) if layer == "*" else layer)
                    break
            self.cache[path] = hit
        return self.cache[path]


# ---- PLAN.md（读法同 prog）--------------------------------------------------------
def parse_plan(text):
    mss, debts, flags = [], [], []
    ms = item = None
    heading = ""
    for line in text.splitlines():
        if line.startswith("## "):
            m = MS_RE.match(line)
            ms = m and dict(id=m.group(1), name=clean(re.split(r"——|（", m.group(2))[0]), closed=bool(CLOSED_RE.search(line)), tasks=[])
            if ms: mss.append(ms)
            item, heading = None, line[3:].strip()
            continue
        if line.startswith("#"):
            heading = line.lstrip("# ").strip()
            continue
        m, r = BOX_RE.match(line), ROW_RE.match(line)
        if m or r:
            if m:
                bold = re.match(r"\*\*(.+?)\*\*", m.group(2))
                head = clean(bold.group(1) if bold else m.group(2).split("—")[0])
                idm = ID_RE.match(head)
                iid, title, done, body = (idm.group(1) if idm else ""), clean(idm.group(2) if idm else head), m.group(1) != " ", clean(m.group(2))
            else:
                cells = [c.strip() for c in r.group(2).split("|")]
                iid, title, body = r.group(1), clean(cells[0]), clean(" ".join(cells[:-1]))
                done = "✅" in next((c for c in reversed(cells) if c), "")
            item = dict(id=iid, title=title, done=done, text=body, ms=ms["id"] if ms else "", context=heading)
            if ms: ms["tasks"].append(item)                       # 同 prog：里程碑下的复选框全算进度（含 EXT-/SEC-）
            if iid and not TASK_ID.match(iid) and not done: debts.append(item)
            continue
        if item:
            if line[:1] in (" ", "\t") and line.strip():
                item["text"] += "\n" + line.strip()
            f = FLAG_RE.match(line.strip())
            if f and ms and not ms["closed"]:
                flags.append(dict(kind=f.group(1), text=f.group(2), task=item["id"], title=item["title"], ms=ms["id"]))
    return mss, debts, flags


# ---- 定位：问题在哪个模块 / 哪一层 ---------------------------------------------------
class Locator:
    def __init__(self, files, mapper, kw):
        self.mapper, self.kw = mapper, kw
        self.suffix = collections.defaultdict(set)
        for f in files:
            parts = f.split("/")
            for i in range(len(parts)):
                self.suffix["/".join(parts[i:])].add(f)

    def __call__(self, title, text, context=""):
        hits, where = {}, []
        allt = [t.lstrip("./") for t in FILE_TOK.findall(text)]
        toks = [t for t in allt if not t.endswith(".md")]          # .md 提及多半是"见某文档"，最后才用
        qualified = [t for t in toks if "/" in t and t in self.suffix]
        for tok in qualified or toks:                             # 带目录的提及比裸文件名可靠：有就只用它们
            cls = {self.mapper(p) for p in self.suffix.get(tok, ())}
            if len({c[0] for c in cls}) == 1:                     # 同名文件分属多个模块 = 说不清，跳过
                mod = next(iter(cls))[0]
                layers = {c[1] for c in cls if c[1] in LAYERS}
                hits.setdefault(mod, set()).update(layers if len(layers) == 1 else [])
                where.append(tok)
        if hits:
            return [dict(mod=m, layers=sorted(l)) for m, l in hits.items()], "文件：" + "、".join(dict.fromkeys(where))
        for scope in (title, context, text):                     # 标题 → 所在小节标题 → 正文；同一处命中多个取最先提到的
            pos = {m: min(p for w in words if (p := self.find(w, scope)) >= 0) for m, words in self.kw.items()
                   if any(self.find(w, scope) >= 0 for w in words)}
            if pos:
                return [dict(mod=min(pos, key=pos.get), layers=[])], "关键词"
        docs = {self.mapper(p)[0] for t in allt if t.endswith(".md") for p in self.suffix.get(t, ())}
        if len(docs) == 1:
            return [dict(mod=docs.pop(), layers=[])], "文档：" + "、".join(dict.fromkeys(t for t in allt if t.endswith(".md")))
        return [], ""

    @staticmethod
    def find(word, s):
        if not word.isascii():
            return s.find(word)
        m = re.search(r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])", s, re.I)
        return m.start() if m else -1


# ---- git：投入与当前位置 ---------------------------------------------------------
def churn(repo, mapper, cur_id):
    out = git(repo, "log", "--no-merges", "--no-renames", "--numstat", "--format=\x1e%s")
    per = collections.defaultdict(lambda: collections.defaultdict(int))     # 模块 -> 里程碑 -> 行数
    now = collections.defaultdict(int)                                      # (模块, 层) -> 当前里程碑行数
    file_all, file_now = collections.Counter(), collections.Counter()
    for chunk in out.split("\x1e")[1:]:
        lines = chunk.split("\n")
        m = MS_IN_SUBJ.search(lines[0])
        ms = m.group(1) if m else "其他"
        for l in lines[1:]:
            p = l.split("\t")
            if len(p) == 3 and p[0] != "-" and not NOT_EFFORT.search(p[2]):
                mod, layer = mapper(p[2])
                n = int(p[0]) + int(p[1])
                per[mod][ms] += n
                file_all[p[2]] += n
                if ms == cur_id:
                    now[(mod, layer)] += n
                    file_now[p[2]] += n
    return per, now, file_all, file_now


def build(repo, map_text, plan_text):
    files = [f for f in git(repo, "ls-files", "-z").split("\0") if f]
    lanes, rules, kw, publish = parse_map(map_text) if map_text else ([], [], {}, None)
    mapped = bool(rules)
    rules = rules or auto_rules(files)
    mapper = Mapper(rules)
    mss, debts, flags = parse_plan(plan_text)
    open_ms = [m for m in mss if not m["closed"] and m["tasks"]]
    cur = open_ms[0] if open_ms else None
    nxt = next((t for t in cur["tasks"] if not t["done"]), None) if cur else None

    order = [m for lane in lanes for m in lane["mods"]]
    for mod, _, _ in rules:
        if mod not in order: order.append(mod)
    locate = Locator(files, mapper, {m: [m] + kw.get(m, []) for m in order})   # 模块名本身也算关键词

    def newmod(name):
        return dict(name=name, flow=any(name in l["mods"] for l in lanes), files=collections.Counter(), issues=[],
                    now=collections.Counter(), dirty=collections.Counter(), effort=0, heat={})
    mods = {name: newmod(name) for name in order + ["未归类"]}
    for f in files:
        mod, layer = mapper(f)
        mods[mod]["files"][layer] += 1

    issues = [dict(id=d["id"], title=d["title"], kind=CATEGORY.get(d["id"].split("-")[0], "欠账"), text=d["text"], ms=d["ms"], context=d["context"])
              for d in debts]
    issues += [dict(id=f["task"], title=f["title"], kind=f["kind"], text=f["text"], ms=f["ms"], context="") for f in flags]
    unplaced = []
    for idx, i in enumerate(issues):
        i["pins"], i["how"] = locate(i["title"], i["text"], i["context"])
        if not i["pins"]:
            unplaced.append(idx)
        for p in i["pins"]:
            mods.setdefault(p["mod"], newmod(p["mod"]))["issues"].append(dict(idx=idx, layers=p["layers"]))

    per, now, file_all, file_now = churn(repo, mapper, cur["id"] if cur else None)
    total = sum(sum(v.values()) for v in per.values()) or 1
    for mod, row in per.items():
        mods.setdefault(mod, newmod(mod))
        mods[mod]["effort"], mods[mod]["heat"] = sum(row.values()), dict(row)
    for (mod, layer), n in now.items():
        mods[mod]["now"][layer] += n
    for l in git(repo, "status", "--porcelain", "-z", "--untracked-files=all").split("\0"):
        if len(l) > 3:
            mod, layer = mapper(l[3:])
            mods.setdefault(mod, newmod(mod))["dirty"][layer] += 1

    rep = {}                                                      # 每个模块每层的代表文件：本里程碑改得最多，没有就历史上最多
    for f in files:
        key, score = mapper(f), (file_now[f], file_all[f])
        if key not in rep or score > rep[key][1]:
            rep[key] = (f, score)
    now_by = {n: sum(m["now"].values()) for n, m in mods.items()}
    focus = max(now_by, key=now_by.get) if any(now_by.values()) else None
    if not focus and nxt:                                         # 里程碑刚开、还没提交：看下一个任务提到哪个模块
        pins, _ = locate(nxt["title"], nxt["text"])
        focus = pins[0]["mod"] if pins else None

    ms_cols = [m["id"] for m in mss if any(m["id"] in v["heat"] for v in mods.values())]
    ms_cols += sorted({k for v in mods.values() for k in v["heat"]} - set(ms_cols) - {"其他"}) + ["其他"]
    return dict(
        project=os.path.basename(os.path.abspath(repo)),
        generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        branch=git(repo, "branch", "--show-current").strip() or "(detached)",
        head=git(repo, "log", "-1", "--format=%h %s").strip()[:90] if file_all else "",
        mapped=mapped, publish=publish, focus=focus,
        progress=dict(closed=sum(m["closed"] for m in mss), total=len(mss)),
        current=cur and dict(id=cur["id"], name=cur["name"], done=sum(t["done"] for t in cur["tasks"]), total=len(cur["tasks"])),
        next=nxt and dict(id=nxt["id"], title=nxt["title"], gate=bool(re.search(r"收口|命门|单独", nxt["title"] + nxt["text"][:300]))),
        waiting=sum(i["kind"] == "待拍板" for i in issues),
        lanes=lanes, total=total, ms_cols=ms_cols, ms_names={m["id"]: m["name"] for m in mss},
        modules=[dict(name=v["name"], flow=v["flow"], files=dict(v["files"]), now=dict(v["now"]), dirty=dict(v["dirty"]),
                      effort=v["effort"], heat=v["heat"], issues=v["issues"],
                      rep={l: rep[(v["name"], l)][0] for l in [*LAYERS, "外部"] if (v["name"], l) in rep})
                 for v in mods.values() if v["files"] or v["effort"] or v["issues"]],
        issues=[dict(id=i["id"], title=i["title"], kind=i["kind"], text=i["text"][:900], ms=i["ms"], pins=i["pins"], how=i["how"]) for i in issues],
        unplaced=unplaced,
    )


# ---- archify：同一份事实画成交互架构图 ---------------------------------------------
def ids_short(ids):
    """SEC-11 SEC-12 SEC-15 → SEC-11、12、15（同前缀只写一次）"""
    out, last = [], None
    for i in ids:
        pre, _, num = i.rpartition("-")
        out.append(num if pre == last and num else i)
        last = pre
    return "、".join(out)


def to_archify(d, repo):
    mods = {m["name"]: m for m in d["modules"]}
    lanes = [[n for n in l["mods"] if n in mods] for l in d["lanes"]]
    quiet = lambda m: not m["issues"] and not sum(m["now"].values()) and m["effort"] < 0.01 * d["total"]   # 横切里没问题、没在改、投入 <1% 的不上图
    cross = [m["name"] for m in d["modules"] if not any(m["name"] in l for l in lanes) and m["name"] != "未归类" and not quiet(m)]
    cols = max([len(l) for l in lanes] + [min(len(cross), 5), 1])
    ids = {n: f"m{i}" for i, n in enumerate(mods)}
    cur = d["current"]["id"] if d["current"] else ""
    now = {n: sum(m["now"].values()) for n, m in mods.items()}
    focus = d["focus"]

    def kind_of(m):
        f = m["files"]
        if f.get("外部") and not any(f.get(l) for l in LAYERS): return "external"
        if re.search(r"鉴权|安全|auth|security", m["name"], re.I): return "security"
        if re.search(r"部署|deploy|infra|基建|CI", m["name"], re.I): return "cloud"
        top = max(LAYERS, key=lambda l: f.get(l, 0))
        return {"页面": "frontend", "数据": "database"}.get(top, "backend") if f.get(top) else "backend"

    def issue_line(m):
        c = collections.Counter(d["issues"][x["idx"]]["kind"] for x in m["issues"])
        return " · ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda kv: -RANK.get(kv[0], 0)))

    revision, link_mode, url, at_rev = None, "local-only", None, set()
    try:                                                          # 源码证据钉在最后一个已推送的提交上，私有仓库登录后也能点开
        url = git(repo, "remote", "get-url", "origin").strip()
        up = subprocess.run(["git", "-C", repo, "rev-parse", "@{u}"], capture_output=True, text=True)
        pushed = git(repo, "merge-base", "HEAD", up.stdout.strip()).strip() if up.returncode == 0 else ""
        revision = pushed or git(repo, "rev-parse", "HEAD").strip()
        link_mode = "web" if pushed and re.match(r"https://(github|gitee)\.com/[\w.-]+/[\w.-]+(\.git)?$", url) else "local-only"
        at_rev = set(git(repo, "ls-tree", "-r", "--name-only", revision).split("\n"))
    except subprocess.CalledProcessError:
        url = None

    comps = []
    def comp(name, row, col):
        m, n = mods[name], now[name]
        parts = ["▶ 你在这里"] if name == focus else []           # 副标题要短：太长会被 archify 缩字号，最要紧的一句反而最小
        parts += [issue_line(m)] if m["issues"] else [] if name == focus else [f"改 {n:,} 行"] if n else []
        sub = " · ".join(parts) or f"投入 {100 * m['effort'] / d['total']:.0f}%"
        c = dict(id=ids[name], type=kind_of(m), label=trim(name, 12), sublabel=trim(sub, 18), row=row, col=col)
        if name == focus and n:
            c["tag"] = f"{cur} 改 {n:,} 行"                        # tag 是节点下方的小字注记，只放次要信息
        if url:
            src = [dict(path=f, label=f"{l} · {m['files'].get(l, 0)} 个文件") for l, f in m["rep"].items() if f in at_rev][:3]   # archify 上限 3
            if src: c["sources"] = src
        comps.append(c)
    for r, lane in enumerate(lanes):
        for c, name in enumerate(lane):
            comp(name, r, c)
    for i, name in enumerate(cross):
        comp(name, len(lanes) + i // cols, i % cols)

    conns = []
    for lane in lanes:
        for a, b in zip(lane, lane[1:]):
            ext = kind_of(mods[a]) == "external" or kind_of(mods[b]) == "external"
            conns.append({"id": f"{ids[a]}-{ids[b]}", "from": ids[a], "to": ids[b],
                          "variant": "emphasis" if now[a] and now[b] else "dashed" if ext else "default"})
    bounds = [dict(kind="region", label=l["name"], wraps=[ids[n] for n in lane]) for l, lane in zip(d["lanes"], lanes) if lane]
    if cross and lanes:
        bounds.append(dict(kind="region", label="横切 · 不在业务线上", wraps=[ids[n] for n in cross]))

    on_map = {n for l in lanes for n in l} | set(cross)
    touched = sorted((n for n in on_map if now[n]), key=lambda n: -now[n])
    with_issues = [n for n in on_map if mods[n]["issues"]]
    waiting = [n for n in on_map if any(d["issues"][x["idx"]]["kind"] == "待拍板" for x in mods[n]["issues"])]
    ext = [n for n in on_map if kind_of(mods[n]) == "external"]
    top = sorted(on_map, key=lambda n: -mods[n]["effort"])[:3]
    pct = lambda n: f"{100 * mods[n]['effort'] / d['total']:.0f}%"
    nx = d["next"]
    here = touched or ([focus] if focus in on_map else [])
    views = []
    if here:
        views.append(dict(id="here", label="你在这里", focus=[ids[n] for n in here],
                          note=trim(f"{cur} 完成 {d['current']['done']}/{d['current']['total']}；下一步 {nx['id'] + ' ' + nx['title'] if nx else '—'}"
                                    f"{'（需要你到场）' if nx and nx['gate'] else ''}"
                                    + (f"。本阶段改动最多：{touched[0]} {now[touched[0]]:,} 行" if touched else ""), 140)))
    if waiting:
        views.append(dict(id="waiting", label="等你拍板", focus=[ids[n] for n in waiting],
                          note=trim("先处理这些，下一步才走得动：" + "、".join(waiting), 140)))
    if with_issues:
        views.append(dict(id="issues", label="问题在哪", focus=[ids[n] for n in with_issues],
                          note=trim("；".join(f"{n}：{issue_line(mods[n])}" for n in with_issues)
                                    + (f"；另有 {len(d['unplaced'])} 个没定位到模块" if d["unplaced"] else ""), 140)))
    if top and mods[top[0]]["effort"]:
        views.append(dict(id="effort", label="投入最多", focus=[ids[n] for n in top],
                          note=trim("按全部历史改动行数（代码 + 文档）：" + "、".join(f"{n} {pct(n)}" for n in top), 140)))
    if ext:
        views.append(dict(id="external", label="跨仓库依赖", focus=[ids[n] for n in ext],
                          note=trim("要等别的仓库交付：" + "；".join(f"{n}：{issue_line(mods[n]) or '无挂账'}" for n in ext), 140)))

    by_mod = collections.defaultdict(list)
    for it in d["issues"]:
        for p in it["pins"]:
            by_mod[(p["mod"], it["kind"])].append(it["id"])
    heavy = max(((c, sum(m["heat"].get(c, 0) for m in d["modules"])) for c in d["ms_cols"] if c != "其他"), key=lambda x: x[1], default=None)
    cards = [dict(dot="emerald", title="当前阶段", items=[x for x in [
                 d["current"] and f"{cur} {trim(d['current']['name'], 22)}（{d['current']['done']}/{d['current']['total']}）",
                 nx and f"下一步 {nx['id']} {trim(nx['title'], 20)}" + ("（需要你到场）" if nx["gate"] else ""),
                 f"等你拍板 {d['waiting']} 件"] if x]),
             dict(dot="rose", title="问题在哪", items=[trim(f"{m} · {k}：{ids_short(v)}", 40) for (m, k), v in
                  sorted(by_mod.items(), key=lambda kv: -RANK.get(kv[0][1], 0))][:6]
                  + ([f"没定位到模块：{len(d['unplaced'])} 个"] if d["unplaced"] else []) or ["PLAN.md 里没有挂着的问题"]),
             dict(dot="cyan", title="投入分布", items=[f"{n} {pct(n)}" for n in sorted(on_map, key=lambda n: -mods[n]["effort"])[:4]]
                  + ([f"最重的里程碑 {heavy[0]}：{heavy[1]:,} 行"] if heavy and heavy[1] else []))]
    spec = dict(schema_version=1, diagram_type="architecture",
                meta=dict(title=f"{d['project']} 项目地图", locale="zh-CN", quality_profile="showcase", views=views[:5],
                          legend=dict(mode="auto", entries={k: dict(label=v) for k, v in LEGEND.items()})),
                layout=dict(mode="grid", origin=[32, 110], cols=cols, gapX=52, gapY=96, cellW=172, cellH=72),
                components=comps, boundaries=bounds, connections=conns, cards=cards)
    if url and any("sources" in c for c in comps):
        spec["meta"]["repository"] = dict(url=re.sub(r"\.git$", "", url) if link_mode == "web" else url, link_mode=link_mode, revision=revision)
    return spec


def find_archify():
    cands = [os.environ.get("ARCHIFY", "")] + [os.path.expanduser(f"~/{d}/skills/archify/bin/archify.mjs")
                                               for d in (".claude", ".agents", ".codex", ".cursor", ".config/opencode")]
    return next((c for c in cands if c and os.path.isfile(c)), None)


def render_page(data):
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.html.tpl"), encoding="utf-8").read()
    return tpl.replace("__TITLE__", data["project"] + " 项目地图").replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


def publicly_readable(url):
    """像匿名浏览器一样取发布出去的网址（跟随跳转、不带登录）：最后拿到的是地图页面 → True；
    拿到的是登录页或 401 / 403 → False；连不上 → None。"""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "vibe-map-check"}), timeout=10) as r:
            return r.status == 200 and PAGE_MARK in r.read(3_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError:
        return False
    except Exception:
        return None


def read_map(repo, path=None):
    if path:
        return open(path, encoding="utf-8").read()
    eng = os.path.join(repo, "ENGINEERING.md")
    if not os.path.exists(eng):
        return ""
    m = re.search(r"^##+\s*模块地图.*?(?=^##\s|\Z)", open(eng, encoding="utf-8").read(), re.M | re.S)
    return m.group(0) if m else ""


def run(repo, out, map_path=None, use_archify=True, publish=False, quiet=False):
    say = (lambda *a: None) if quiet else print
    data = build(repo, read_map(repo, map_path), open(os.path.join(repo, "PLAN.md"), encoding="utf-8").read())
    os.makedirs(out, exist_ok=True)
    tool = find_archify() if use_archify else None
    data["archify"] = None
    if tool:
        spec_path = os.path.join(out, "map.architecture.json")
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(to_archify(data, repo), f, ensure_ascii=False, indent=1)
        common = ["--quality", "showcase", "--repo-root", os.path.abspath(repo), "--json"]
        r = subprocess.run(["node", tool, "validate", "architecture", spec_path, *common], capture_output=True, text=True)
        if r.returncode == 0:
            r = subprocess.run(["node", tool, "deliver", "architecture", spec_path, os.path.join(out, "archify.html"), *common], capture_output=True, text=True)
        if r.returncode == 0:
            data["archify"] = "archify.html"
        else:                                                     # 出不了图不挡自带页面；把 archify 的诊断原样留给人看
            print(f"map：archify 没通过（exit {r.returncode}），只出自带页面。诊断：{(r.stdout or r.stderr)[-800:]}", file=sys.stderr)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_page(data))
    n = len(data["issues"])
    say(f"项目地图：{os.path.join(out, 'index.html')}（{len(data['modules'])} 个模块，{n} 个问题，{n - len(data['unplaced'])} 个已定位"
        f"{'；含 archify 架构图' if data['archify'] else ''}）")
    if publish:
        if not data["publish"]:
            sys.exit("map：ENGINEERING.md「模块地图」里没有「发布：」命令，--publish 无事可做")
        cmd = data["publish"].replace("{dir}", shlex.quote(os.path.abspath(out)))
        r = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"map：发布失败（exit {r.returncode}）：{(r.stderr or r.stdout)[-600:]}")
        urls = list(dict.fromkeys(u.rstrip(".,;") for u in re.findall(r"https?://[^\s'\"<>()]+", r.stdout + r.stderr)))[:8]
        seen = {u: publicly_readable(u) for u in urls}
        exposed = [u for u, v in seen.items() if v]
        if exposed:                                                # 页面里有安全欠账原文：公开可读必须响亮地失败
            sys.exit(f"map：发布出去的页面不用登录就能打开：{exposed[0]}——页面里有安全欠账原文，立刻收紧访问控制（如 Cloudflare Access），再重新发布")
        if any(v is False for v in seen.values()):
            say(f"已发布；不登录访问被拒，访问控制生效：{next(u for u, v in seen.items() if v is False)}")
        else:
            say("已发布；没法自动确认访问控制（输出里没有网址或连不上）——请用无痕窗口打开一次，应该先看到登录页")
    return data


# ---- 自检：先证明它能失败（改守卫前后都跑；CI 没装 archify，只验 spec 形状）--------------------
def selftest():
    fails = []
    def check(name, cond):
        if not cond: fails.append(name)
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "demo")
        g = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        def write(p, s):
            os.makedirs(os.path.dirname(os.path.join(repo, p)) or repo, exist_ok=True)
            open(os.path.join(repo, p), "w", encoding="utf-8").write(s)
        def commit(msg):
            subprocess.run(g + ["add", "-A"], check=True); subprocess.run(g + ["commit", "-qm", msg], check=True)
        os.makedirs(repo)
        subprocess.run(["git", "init", "-q", repo], check=True)
        subprocess.run(g + ["remote", "add", "origin", "https://github.com/example/demo.git"], check=True)   # 有 origin 才出源码证据
        write("src/app/ingest/loader.py", "x = 1\n" * 30)
        write("src/app/api/routes.py", "y = 1\n" * 10)
        write("src/app/api/cli.py", "c = 1\n")
        write("src/app/api/models.py", "m = 1\n")
        write("src/app/api/service.py", "v = 1\n")
        write("src/app/ingest/cli.py", "c = 2\n")
        write("tests/test_api.py", "def test(): pass\n" * 5)
        commit("M1-T1: 初版")
        write("src/app/static/index.html", "<p>\n" * 40)
        write("bench/data.json", "[]\n" * 5000)                 # 数据文件：不能算进投入
        commit("M2-T1: 页面 + 基准数据")
        write("ENGINEERING.md", "# E\n\n## 模块地图\n\n数据流：上游 → 导入 → 查询 API\n{业务线}：{模块A} → {模块B}\n\n"
              "| 模块 | 层 | 路径 |\n|---|---|---|\n| {模块} | {层} | {路径} |\n| 上游 | 外部 | docs/upstream* |\n| 上游 | 关键词 | upstream |\n"
              "| 导入 | 接口 | src/app/ingest/*cli.py |\n| 导入 | 逻辑 | src/app/ingest/* |\n| 查询 API | 页面 | src/app/static/* |\n"
              "| 查询 API | 数据 | src/app/api/models.py |\n| 查询 API | 逻辑 | src/app/api/service.py |\n| 查询 API | 接口 | src/app/api/* |\n| 查询 API | 测试 | tests/test_api* |\n\n发布：cp -R {dir} " + shlex.quote(os.path.join(tmp, "pub")) + "\n")
        write("docs/upstream_contract.md", "契约\n")
        commit("docs: 地图")
        plan = ("# PLAN\n\n## M1 · 地基 ✅\n- [x] **M1-T1 · 初版** —【常规】\n"
                "### 外部依赖 · upstream 侧\n- [ ] **EXT-1 · 等对方补字段** — Owner：对方\n- [ ] **EXT-1 v2 · 第二版对接** — Owner：对方\n\n"
                "## M2 · 页面与查询\n### M2a · 子段（不是里程碑）\n- [x] **M2-T1 · 页面** —【常规】\n  偏差：没测大文件\n"
                "- [ ] **M2-T2 · 查询提速** —【重型】【单独+确认】（命门）\n  待拍板：缓存放哪\n"
                "  - [ ] 缩进的子项不算任务\n"
                "- [ ] **SEC-1 · 路由缺鉴权** — 见 `api/routes.py:3`，它调用了 loader.py；另见 `doc/x.md`\n"
                "- [ ] **SEC-2 · 说不清在哪的问题** — 状态：todo\n"
                "- [ ] **SEC-3 · 同名文件** — `cli.py` 两个模块都有，定位不了；但 </script><b>x</b> 不能炸页面\n"
                "| M2-T3 | 表格写法的任务 | ✅ |\n"
                "## M3 · 以后\n- [ ] **M3-T1 · 占位**\n")
        write("PLAN.md", plan)
        write("src/app/api/routes.py", "y = 2\n" * 12)           # 未提交改动
        d = build(repo, read_map(repo), plan)
        mod = {m["name"]: m for m in d["modules"]}
        iss = {i["id"]: i for i in d["issues"]}
        # 1 PLAN 读法与 prog 一致
        check("当前里程碑 = M2（### 子段不算里程碑）", d["current"] and d["current"]["id"] == "M2")
        check(f"M2 进度 = 2/6（顶格复选框含 SEC-、表格行；缩进子项不算）：{d['current']}", d["current"] and (d["current"]["done"], d["current"]["total"]) == (2, 6))
        check("下一步 = M2-T2，且识别为要人到场", d["next"] and d["next"]["id"] == "M2-T2" and d["next"]["gate"])
        check("等你拍板 = 1", d["waiting"] == 1)
        check("里程碑 1/3 已收口", d["progress"] == dict(closed=1, total=3))
        prog = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prog", "prog.sh")
        if os.path.exists(prog):                                 # 与 prog 交叉核对：同一份 PLAN，两个工具报同样的数
            r = subprocess.run(["bash", prog, os.path.join(repo, "PLAN.md")], capture_output=True, text=True, cwd=repo, env=dict(os.environ, PROG_NO_GH="1"))
            check(f"与 prog 同口径：{r.stdout.strip().splitlines()[:3]}", "2/6 个任务" in r.stdout and "M2-T2" in r.stdout and "1/3 个里程碑" in r.stdout)
        # 2 问题定位
        check(f"SEC-1 按带目录的文件提及定到 查询 API·接口：{iss['SEC-1']['pins']}", iss["SEC-1"]["pins"] == [dict(mod="查询 API", layers=["接口"])])
        check(f"EXT-1 按所在小节标题的关键词定到 上游：{iss['EXT-1']['pins']}", iss["EXT-1"]["pins"] == [dict(mod="上游", layers=[])])
        check("SEC-2 定位不到 → 未定位", list(d["issues"]).index(iss["SEC-2"]) in d["unplaced"])
        check(f"SEC-3 同名文件分属两个模块 → 不瞎定：{iss['SEC-3']['pins']}", not iss["SEC-3"]["pins"])
        check("「EXT-1 v2」与「EXT-1」是两条", {"EXT-1", "EXT-1 v2"} <= set(iss))
        check("偏差 / 待拍板 都挂上了", {i["kind"] for i in d["issues"]} >= {"偏差", "待拍板"})
        check("模板占位行不进地图", "{模块A}" not in {m["name"] for m in d["modules"]} and not any("{" in l["name"] for l in d["lanes"]))
        # 3 投入与当前位置
        check(f"数据文件不算投入（bench/data.json 5000 行）：总计 {d['total']}", d["total"] < 300)
        check(f"M2 动到的是 查询 API·页面：{mod['查询 API']['now']}", mod["查询 API"]["now"].get("页面") == 40 and d["focus"] == "查询 API")
        check("未提交改动记在 查询 API", mod["查询 API"]["dirty"].get("接口") == 1)
        check("发布命令读到了", d["publish"] and d["publish"].startswith("cp -R {dir}"))
        # 4 archify spec 形状（archify 的硬上限）
        s = to_archify(d, repo)
        idset = {c["id"] for c in s["components"]}
        srcs = {c["label"]: [x["label"].split(" ·")[0] for x in c.get("sources", [])] for c in s["components"]}
        check(f"源码证据每节点 ≤ 3，四层都有时取页面 / 接口 / 数据：{srcs.get('查询 API')}", srcs.get("查询 API") == ["页面", "接口", "数据"]
              and all(len(v) <= 3 for v in srcs.values()))
        check("没推送过的仓库：源码证据钉在 HEAD、不出网页链接", s["meta"].get("repository", {}).get("link_mode") == "local-only")
        check("id 合法", all(re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", i) for i in idset))
        check("章节 ≤ 5、标题 ≤ 48、说明 ≤ 140、聚焦的节点都在图上", len(s["meta"]["views"]) <= 5 and all(
            len(v["label"]) <= 48 and len(v.get("note", "")) <= 140 and set(v["focus"]) <= idset for v in s["meta"]["views"]))
        check("网格不重格、不越界", len({(c["row"], c["col"]) for c in s["components"]}) == len(s["components"])
              and all(c["col"] < s["layout"]["cols"] for c in s["components"]))
        check("连线两端都在图上", all(c["from"] in idset and c["to"] in idset for c in s["connections"]))
        check("「你在这里」在副标题里且够短", any(c["sublabel"].startswith("▶ 你在这里") and len(c["sublabel"]) <= 18 for c in s["components"]))
        # 5 页面与发布
        out = os.path.join(tmp, "out")
        os.environ.pop("ARCHIFY", None)
        run(repo, out, use_archify=False, publish=True, quiet=True)
        page = open(os.path.join(out, "index.html"), encoding="utf-8").read()
        check("问题原文里的 </script> 被转义", "</script><b>" not in page and "<\\/script>" in page)
        check("发布命令执行了（{dir} 换成产物目录）", os.path.exists(os.path.join(tmp, "pub", "index.html")))
        # 6 发布后的公开可读自查
        import http.server, threading
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/open"):
                    self.send_response(200); self.end_headers(); self.wfile.write(page.encode("utf-8"))
                elif self.path.startswith("/signin"):
                    self.send_response(200); self.end_headers(); self.wfile.write("请先登录".encode("utf-8"))
                else:                                            # /moved → 公开页面；/login → 登录页
                    self.send_response(301 if self.path.startswith("/moved") else 302)
                    self.send_header("Location", "/open" if self.path.startswith("/moved") else "/signin"); self.end_headers()
            def log_message(self, *a):
                pass
        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base_url = f"http://127.0.0.1:{srv.server_address[1]}"
        eng = open(os.path.join(repo, "ENGINEERING.md"), encoding="utf-8").read()
        def publish_with(line):
            open(os.path.join(repo, "ENGINEERING.md"), "w", encoding="utf-8").write(re.sub(r"(?m)^发布：.*$", line, eng))
            try:
                run(repo, out, use_archify=False, publish=True, quiet=True); return "ok"
            except SystemExit as e:
                return str(e)
        check("发布到公开可读的地址 → 响亮地失败", "不用登录就能打开" in publish_with(f"发布：echo Deployed {base_url}/open {{dir}}"))
        check("跳转之后落到公开页面 → 也算公开（http→https 这类跳转）", "不用登录就能打开" in publish_with(f"发布：echo Deployed {base_url}/moved {{dir}}"))
        check("发布到要登录的地址 → 放行", publish_with(f"发布：echo Deployed {base_url}/login {{dir}}") == "ok")
        srv.shutdown()
        open(os.path.join(repo, "ENGINEERING.md"), "w", encoding="utf-8").write(eng)
        # 7 没有地图也能跑（按目录分组）
        d2 = build(repo, "", plan)
        check(f"无地图：按目录分组：{sorted(m['name'] for m in d2['modules'])}", {"ingest", "api", "static"} <= {m["name"] for m in d2["modules"]} and not d2["mapped"])
    if fails:
        print("selftest FAIL:\n  " + "\n  ".join(fails)); sys.exit(1)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description="项目地图（只读）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--map", help="模块地图 Markdown；缺省读 ENGINEERING.md 的「模块地图」一节，再没有就按目录分组")
    ap.add_argument("--out", help="产物目录；缺省 ~/.cache/vibe-map/<项目名>/")
    ap.add_argument("--no-archify", action="store_true", help="不出 archify 架构图，只出自带页面")
    ap.add_argument("--publish", action="store_true", help="生成后执行「模块地图」里的「发布：」命令")
    ap.add_argument("--quiet", action="store_true", help="成功时什么都不输出（任务收尾静默刷新用）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    out = a.out or os.path.join(os.path.expanduser("~/.cache/vibe-map"), os.path.basename(os.path.abspath(a.repo)))
    run(a.repo, out, a.map, not a.no_archify, a.publish, a.quiet)


if __name__ == "__main__":
    main()
