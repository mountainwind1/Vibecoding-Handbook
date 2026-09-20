# xreview · xreview-self · codex（CLI 默认模型）

- 日期：20260920
- 评审包：21860 字节，sha256 23072ea960b10471
- 包含：skills/xreview/xreview.py
- 已扣下（未发出）：无
- 授权记录：无（只发了代码 diff）
- 性质：读码推断，未经实测——采信前先复现

---

[高] skills/xreview/xreview.py:57 — diff 只按目标路径分类，重命名可绕过外发守卫  
将 `.env`、设计文档等敏感文件重命名到普通路径时，包含旧内容的 hunk 会按新路径放行。应可靠解析并同时分类旧、新路径，任一敏感即拒发或扣下；建议使用 Git 的 `--raw/--name-status -z`，不要只解析展示用 diff 头。

[高] skills/xreview/xreview.py:64 — 授权记录只是未绑定范围的非空字符串  
例如记录写着“PRD 给 codex”，默认配置仍会把内容发给 DeepSeek 和 GLM；同一记录也能被复用于任意附加文件。应把授权结构化并绑定文件或内容哈希、接收方和有效期，在每次向具体 reviewer 外发前逐项核验。

[高] skills/xreview/xreview.py:140 — 环境变量可把代码和厂商 API key 重定向至任意地址  
`XREVIEW_*_URL` 未限制协议和主机，错误或受污染的 CI 环境可令 payload 与 Bearer key 一并发往攻击者地址，明文 HTTP 也会被接受。应仅允许 HTTPS 和明确的厂商域名、禁用或逐跳校验重定向；测试端点需使用独立测试模式和假 key。

[高] skills/xreview/xreview.py:83 — gitleaks 异常时密钥扫描默认放行到明显不完备的正则  
gitleaks 因版本、参数、配置或执行错误返回非 0/1 时会静默降级；兜底正则又漏掉未加引号的 YAML/配置值、带引号的 JSON 键、JWT、`glpat-` 等常见凭证。正式外发应在 gitleaks 缺失或异常时拒发；若保留兜底，至少覆盖结构化格式与主要令牌类型并增加失败态测试。

[高] skills/xreview/xreview.py:114 — 隔离预检可由无效探针或 shell 注入伪造为 BLOCKED  
没有可用 tracked file 时 `None` 会作为不存在的文件并返回 `BLOCKED`；相对或不存在的 `--probe` 同样通过。探针又被直接拼进 shell，含单引号的参数或仓库文件名可注入 `echo BLOCKED`。应先验证探针是仓库外评审目录之外、存在且可读的绝对非空文件，并以无 shell 的 argv 执行；找不到可靠探针时拒跑。

[高] skills/xreview/xreview.py:68 — 附加文件和整文件模式存在符号链接及 TOCTOU 路径绕过  
代码分类的是参数文本，随后才按路径打开；普通名称的符号链接可指向 `.env` 或凭证文件，检查与打开之间也可被替换。应拒绝符号链接，使用 `O_NOFOLLOW` 打开后通过同一文件描述符读取，并对解析后的目标及 `fstat` 结果完成分类。

[中] skills/xreview/xreview.py:31 — 路径规则大小写敏感且安全例外会覆盖其他敏感命中  
`Secrets/prod.yaml`、`SERVER.PEM`、`prd.md`、`Docs/internal.md` 等可绕过分类；`secret/.env.example` 还会因 basename 命中 `SECRET_OK` 而抵消目录的敏感命中。应按规范化、大小写折叠后的 POSIX 路径匹配，并让模板例外只豁免对应的 `.env.*` 文件名规则，不能覆盖敏感目录规则。

未覆盖面：评审包未包含实际 Codex 权限档语义及版本兼容性、gitleaks 版本与配置、CI 中环境变量和命令行参数的来源、HTTP 代理及重定向策略，以及针对重命名、符号链接、扫描器故障、授权接收方不匹配和无效探针的集成测试。
