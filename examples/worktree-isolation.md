# 示例 · Worktree Isolation

```text
main
├─ ../wt/codex-api-1      agent/codex-api-1/M3-T4-webhook-signature
├─ ../wt/claude-ui-1      agent/claude-ui-1/M3-T5-payment-status-ui
└─ ../wt/integration-m3   integration/M3-payment
```

规则：

- API Agent 只写 API / contract / API tests。
- UI Agent 只写 UI / DESIGN 引用 / UI tests。
- contract freeze 后两边并行；contract 变更只能由 Contract Owner 合并。
- Integration Owner 在 integration 分支汇合、解决冲突、跑门禁、写 Evidence。
