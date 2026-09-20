# xreview · xreview-self2 · deepseek（deepseek-v4-pro）

- 日期：20260920
- 评审包：56963 字节，sha256 abec87be603e3586
- 包含：CHANGELOG.md, ENGINEERING.md, README.en.md, README.md, Vibe-Coding-正式项目工作手册v6.md, docs/reviews/xreview-self_codex_20260920.md, skills/close/SKILL.md, skills/kof/SKILL.md, skills/xreview/SKILL.md, skills/xreview/__pycache__/xreview.cpython-314.pyc, skills/xreview/xreview.py
- 已扣下（未发出）：无
- 授权记录：无（只发了代码 diff）
- 性质：读码推断，未经实测——采信前先复现

---

[高] skills/xreview/xreview.py:81-85 — `--include-restricted` 是全局开关，且 `--authorized` 只是未绑定文件/哈希的自由文本。触发：diff 里同时有 `PRD.md` 和 `docs/权限设计.md`，用户只明确同意发 PRD 给 Codex；Agent 按 `--include-restricted --authorized "用户同意 PRD" --authorized-for codex` 执行时，两个文件都会被发出。修法：改为逐文件授权清单（路径 + 内容哈希 + 接收方），`build_payload` 对每个 restricted 文件核验；CLI 不支持按文件选择前，遇到多个需授权文件应拒绝并要求逐条授权。

[高] skills/xreview/xreview.py:48-51,92,202 — `classify_file` 的符号链接检查与后续 `open` 是分离的系统调用，存在 TOCTOU；且 `realpath` 不识别硬链接。触发：`--include note.md` 通过 `islink` 检查后，文件被替换为指向 `.env` 的符号链接；或 `note.md` 本来就是 `.env` 的硬链接（`os.path.islink` 为 False），路径分类会放行但实际读取凭证内容。修法：用 `os.open(O_NOFOLLOW)` 打开，先 `fstat` 确认普通文件并用同一 fd 读取；硬链接可考虑 `st_nlink == 1` 或直接在 fd 上做内容扫描后再决定是否发送。

[中] skills/xreview/xreview.py:181 — `urllib.request.build_opener(_NoRedirect)` 仍带默认 `ProxyHandler`，会读取 `https_proxy`/`HTTP_PROXY` 环境变量。触发：开发机或 CI 配置了代理（尤其企业 TLS 中间人代理）时，评审包和 Bearer key 会经过不在白名单里的代理，挑战“只去厂商域名”的约束。修法：显式传入 `urllib.request.ProxyHandler({})` 禁用代理；若允许走代理，代理本身也要作为可信边界单独声明和校验。

[中] skills/xreview/xreview.py:111-117 — gitleaks 未安装时降级到的正则扫描明显偏弱，quoted JSON key 可能漏过。触发：`+ "password": "hunter2hunter2"` 这行不满足现有正则的第一段（键前有引号），在无 gitleaks 的环境可能放行。修法：缺失 gitleaks 时考虑拒发或要求先安装；若保留兜底，至少覆盖 JSON/YAML quoted-key、`"api_key"` 等常见形态，并在 selftest 中显式构造这些漏网用例。

[中] skills/xreview/xreview.py:25,42 — `RESTRICTED_OK = ["docs/reviews/*"]` 过宽。触发：新增文件 `docs/reviews/PRD.md` 会被 `_match(path, RESTRICTED_OK)` 豁免，分类为 `ok`，不需要授权就进入 diff；而正常 xreview 报告名是 `{task}_{model}_{date}.md`，不需要整个目录豁免设计文档规则。修法：把白名单收窄到报告文件名模式，`PRD*.md`、`DESIGN*.md` 等仍应 restricted。

[低] skills/xreview/xreview.py:75 — `--exclude` 使用 AND 同时匹配新旧路径。触发：`rename .env -> config/app.txt` 时，`--exclude .env` 只有旧路径命中，新路径不命中，文件不会跳过，随后因旧路径 secret 拒发；这不会泄露，但 CLI 提示“用 --exclude 去掉”对重命名文件失效。修法：任一侧命中 exclude 就跳过该文件（或至少对 secret 旧路径也允许排除）。

[中] skills/xreview/SKILL.md:19-20 — SKILL 外发规则未说明 `--include-restricted` 会放行 diff 中所有被扣下的需授权文件，而不是只放行用户同意的那一份。触发：Agent 按“用户同意发 PRD”执行，diff 里还有其他 `design*`/`*权限*` 文件时，会按字面把全部受限文件发给点名接收方。修法：SKILL 应写明 dry-run 列出的每个 withheld 文件都要逐份获得用户授权；CLI 未支持 per-file 授权前，禁止在存在多个受限文件时只凭一个授权字符串放行。

未覆盖面：未看到实际 `codex` 权限档配置项在目标版本的解析结果、gitleaks 版本与规则库行为、CI/环境中 `https_proxy` 与 TLS CA 链的实际设置、`urllib` 在收到 302/301 时的具体异常形态，以及针对硬链接、TOCTOU 交换、JSON quoted-key 扫描、per-file 授权的真实集成测试。
