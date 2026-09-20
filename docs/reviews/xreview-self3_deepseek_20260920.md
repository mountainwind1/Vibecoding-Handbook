# xreview · xreview-self3 · deepseek（deepseek-v4-pro）

- 日期：20260920
- 评审包：35845 字节，sha256 04180a69b0193232
- 包含：.gitignore, skills/xreview/xreview.py
- 已扣下（未发出）：无
- 授权记录：无（只发了代码 diff）
- 性质：读码推断，未经实测——采信前先复现

---

[高] skills/xreview/xreview.py:102-107 — `classify_file` 与 `read_nofollow` 之间存在 TOCTOU。`classify_file` 在 102 行检查符号链接/硬链接/realpath，但到 107 行才重新打开文件；并发进程可在这段窗口把 `f` 替换为指向 `.env` 的硬链接或父目录符号链接，`O_NOFOLLOW` 只防最终组件 symlink，不防硬链接或中间 symlink 切换，外发守卫可被绕过。建议只打开一次，用 fd 做 `fstat`/`realpath` 等价检查，并读同一 fd。

[中] skills/xreview/xreview.py:148-168 — Codex 隔离预检只验证“仓库探针文件不可读”，未验证环境变量或网络外发。`codex exec` 子进程继承脚本环境（含 `DEEPSEEK_API_KEY`、`GLM_API_KEY` 等），而权限档只配了 filesystem；diff 内容若包含 prompt injection，可能诱导模型输出或外发环境变量。建议对 Codex 进程清空/白名单化环境变量，禁用网络或增加 env/egress 负对照；拿不准 Codex sandbox 默认是否隔离 env/network，但此处未显式防护。

[中] skills/xreview/xreview.py:26-27,43-47 — `RESTRICTED_OK` 豁免会放行 `docs/reviews` 下任意 `<任务>_<评审方>_<8位日期>.md` 形态文件。真正的 PRD/DESIGN 文档如果按这个命名形态提交，就会绕过 `doc(s)/` 扣下规则，默认外发且不需要授权。建议只豁免本次 `run` 实际生成的准确文件名，或写入不可伪造的报告生成标记后按内容判定。

[中] skills/xreview/xreview.py:70 — `split_diff` 的 diff 头解析对“空格后紧跟 `b/`”的路径有歧义，例如实际路径 `foo b/bar.md` 会被截成 old=`foo`、new=`bar.md b/foo b/bar.md`。这破坏路径不变量，使 `exclude`/`include_restricted` 在全路径模式下匹配错文件；常见 restricted basename 可能仍会在伪造 new path 末尾被捕获，但拿不准是否存在所有输入都绕过的形态。建议用 `git diff --name-status -z` 或解析 `---/+++` 行二次确认真实路径。

[低] skills/xreview/xreview.py:115-133 — `--allow-weak-scan` 在缺 gitleaks 时退回正则弱扫描。该正则漏掉短口令、base64/URL 编码 secret、无 `BEGIN` 标记的私钥等；如果 CI 为省事常开该开关，外发前密钥扫描就变成 fail-open。建议生产/CI 不接受该开关，缺 gitleaks 直接拒绝。

未覆盖面：这份评审包没给看 xreview 在 CI 中的实际调用参数（尤其 `--allow-weak-scan`、`--exclude`、`--include-restricted`、`--authorized-for` 的取值来源），也没给 Codex CLI 版本与其 sandbox 权限档对 env/network/tooling 的实际行为。另需看 `docs/reviews` 中已提交内容及评审报告如何进入后续 diff；以及主控模型合并报告时是否对评审方返回内容做二次敏感信息过滤/注入隔离。
