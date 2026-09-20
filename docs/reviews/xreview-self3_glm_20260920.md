# xreview · xreview-self3 · glm（glm-5.3）

- 日期：20260920
- 评审包：35845 字节，sha256 04180a69b0193232
- 包含：.gitignore, skills/xreview/xreview.py
- 已扣下（未发出）：无
- 授权记录：无（只发了代码 diff）
- 性质：读码推断，未经实测——采信前先复现

---

以下均为读码推断（无运行环境）；行号按本 diff 新文件计数，函数名一并给出以防行号偏移。

[高] skills/xreview/xreview.py:69（split_diff）— `str.splitlines` 认 \x0c/\x0b/\r/\x1c-\x1e/U+0085/U+2028/U+2029 这些 git 不当行界的字符，伪造文件头可把受限内容记到别的文件名下
被评审提交只要在 PRD.md 的改动行里嵌一段 `x\x0cdiff --git a/notes.md b/notes.md`，该 `+` 行被劈成两段，后半段被 ：70 当成真实文件头：PRD 的 hunk 里其余行（含 context 行中的真实 PRD 内容）全部归到 ok 的假路径 notes.md 下照发，而工具仍打印“已扣下 PRD.md”——被评审 diff 正是外部贡献者可控输入，“默认扣下”被整体绕过；`--exclude`（包括工具自己建议的“用 --exclude 去掉 .env”）同样按假路径放行内容，只剩 gitleaks 兜底。修法：只按 `\n` 断行并保留行尾（自行 split 补回换行；注意 bytes.splitlines 也切 \f/\v，不能用）；:129 的逐行扫描同根，密钥字符串被 \x0c 截断时弱正则也会漏。selftest 全是干净 fixture，测不到这个形态。

[中] skills/xreview/xreview.py:24（classify / RESTRICTED_GLOBS）— `"doc/*"`、`"docs/*"` 只匹配仓库根，嵌套 docs/ 目录整体漏网
`_hits`（:31-32）的逐级分量匹配对含 `/` 的 glob 无效，只剩整路径匹配且锚定在根：`app/docs/…`、`packages/x/docs/…` 里的设计文档只要名字不含 design/设计/密码 等词就按 ok 外发，与 ：30 注释“每一级目录名都拿去匹配”的意图相反。建议补 `*/docs/*`、`*/doc/*`。

[中] skills/xreview/xreview.py:95（build_payload）— `--include-restricted` 的“点名”按分量匹配，同名文件全放行
`_match` 会拿每级目录名/文件名去配 glob：用户点名 `PRD.md`（意为根目录那份）时，`docs/PRD.md`、`archive/PRD.md` 也命中 named 一并进包，与 help 里“只放行点到名的”相悖。授权应是全文件最窄的匹配器：include_restricted 建议只做整路径匹配、不做分量回退。

[中] skills/xreview/xreview.py:237（run）— git 输出按 locale 解码，非 UTF-8 locale 下非 ASCII 名字的分类静默失效
`text=True` 用 locale 编码：显式 latin-1 类 locale 时中文文件名被静默 mojibake，`*设计*`/`*密码*` 等非 ASCII glob 全部不命中，受限文档按 ok 外发（UTF-8 环境则是解码报错=拒发，方向相反，所以测试机复现不了）。ASCII 的 SECRET_GLOBS 与内容扫描不受影响。建议显式 `encoding="utf-8"`（strict 解不了即拒发）；:260 的 `git ls-files` 同理。

[中] skills/xreview/xreview.py:148-158（codex_isolation_ok / review_codex）— 预检负对照只有一个且 `--probe` 不校验在仓库内；预检与实跑走不同子命令（拿不准）
沙箱若允许读 $HOME 而仓库不在 $HOME 下，单个仓库探针照样 BLOCKED、预检照过；`--probe` 可指到任何“恰好读不到”的文件。且预检验证的是 `codex sandbox -- sh -c`，实跑是模型自己驱动命令的 `codex exec`，两者对 `-c` 权限档的解释若不一致（beta），预检证明不了实跑路径——而 payload.diff 本身就是被评审方可控的注入载体。建议探针集 {仓库文件、$HOME 下文件、/etc/passwd} 全部不可读才过，并拒绝仓库外的 --probe。codex 实际语义我无法验证。

[低] skills/xreview/xreview.py:26-27（RESTRICTED_OK）— fnmatch 的 `*` 可跨 `/`
`docs/reviews/<任意深层>/x_y_20260920.md` 也吃到 doc(s)/ 豁免，免授权面比“评审报告命名形态”宽。建议逐段校验目录深度或改用不跨目录的 `*` 语义。

[低] skills/xreview/xreview.py:57-63（classify_file）— 与 read_nofollow（:54）之间存在换名 TOCTOU
islink/nlink 检查后、打开前把另一文件 rename 到原路径，读到的就不是分类过的那份（O_NOFOLLOW 只挡符号链接，不挡整文件替换；密钥尚有 gitleaks 内容兜底，按名字 restricted 的判断则直接失真）。需本地并发进程配合，低危；可先 open 再 fstat 比对 (st_dev, st_ino)。另 O_NOFOLLOW 仅 POSIX，Windows 上 getattr 回退 0，只剩 islink 预检一层。

[低] skills/xreview/xreview.py:120-121（scan_secrets）— gitleaks 以仓库为 cwd 运行（拿不准）
若所用 gitleaks 版本会从 cwd 解析 `.gitleaksignore` 类忽略配置，被评审提交里塞一份宽泛 ignore 文件即可压掉内容扫描告警；该行为随版本而变，我无法核实。稳妥做法是 `cwd=payload_dir` 或显式固定 `--config`。

[低] skills/xreview/xreview.py:271（run）— `--task` 直拼进报告路径
`--task "../../x"` 可把含模型输出的报告写到 --out 之外；自用无害，但若被上层代理用不可信字符串拼参数，就是任意路径写文件口。建议校验 task 只含安全文件名字符。

[低] skills/xreview/xreview.py:230-235（run）— `--payload` 模式静默忽略 `--include` / `--include-restricted`
该分支不进 build_payload，--include 的文件既不读也不报错，授权记录与实际外发内容可能账实不符（当前偏“少发”、方向安全，但属遗漏的状态分支，后续改动容易翻转成多发）。

[低] skills/xreview/xreview.py selftest —「缺 gitleaks 默认拒发」用例在装有 gitleaks 的机器上没测到真实分支
lambda 先短路进一个假 sys.exit，scan_secrets 的“未装 gitleaks 且不允许弱扫→拒发”分支只在没装 gitleaks 的机器上才真正执行，而 needle 两种情况都命中——CI 绿不代表该分支被覆盖。建议 monkeypatch `shutil.which` 后直接调 scan_secrets。

未覆盖面：这份包没给我看、但我认为必须看的——① codex CLI 权限档（`permissions.xreview.filesystem`、`codex exec -o/--ephemeral`）的真实语义，整条 Codex 通道的安全性全押在它上面，这里只有调用方；② 所用 gitleaks 版本对 `dir` 的具体行为（ignore 文件来源、大小上限、退出码约定）；③ 上层“主控模型”如何构造命令行——`--exclude/--authorized/--task/--probe` 的来源是否含不可信输入决定了两条 [低] 是否升级；④ 对真实 `git diff` 产物的对抗性测试（空格/引号/控制字符路径、rename/copy、submodule、二进制），现有 selftest 全是手写字符串 fixture，[高] 正是从这个缝里漏的；⑤ 名字式分类的内容面盲区：设计文档整体搬进普通命名的新文件即可外发，密钥不走已知模式时只有 gitleaks 一层；⑥ 注入持久化链——评审报告写回 docs/reviews 且被 RESTRICTED_OK 豁免，被 diff 诱导出的模型输出会进入仓库并出现在下一轮评审包里；⑦ `XREVIEW_USE_PROXY=1` 时系统代理与 TLS 校验路径的行为。
