# VIBE-CLI.md · v6 deterministic CLI 设计

v6 的 CLI 先做薄层校验，不急着做完整调度器。第一版目标：读写 `.vibe/*.json`、验证状态迁移、检查 changed files 是否落在 writable scope、汇总 evidence 和 checks。

## 命令草案

```text
vibe status
vibe tasks list --state todo
vibe claim M3-T4 --owner codex-api-1 --worktree ../wt/codex-api-1
vibe start M3-T4
vibe block M3-T4 --reason "等待价格拍板"
vibe evidence add M3-T4 --type check --ref "test:payments:passed"
vibe handoff M3-T4 --to integration --summary "实现 webhook 签名校验"
vibe gate M3-T4
vibe integrate M3-T4 --pr 42
```

## Gate 检查

- task state 必须是 `review`。
- owner / worktree / writable_scope 必填。
- changed files 必须被 writable_scope 覆盖。
- protected scopes 变更必须有 owner approval evidence。
- checks 全部通过。
- handoff 非空。
- contract_refs 不处于 broken / thawing。

## 第一版不做

- 不做自动任务分配。
- 不做模型调用。
- 不做跨机器锁服务。
- 不替代 GitHub PR / CI，只读取和校验它们的证据。
