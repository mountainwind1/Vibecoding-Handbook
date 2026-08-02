# 示例 · v5.3 PLAN 任务状态

```text
- [ ] M3-T4 · 支付 webhook 签名校验 —【重型】【单独+确认】（命门）
  状态：claimed
  Owner：codex-api-1
  Worktree：../wt/codex-api-1
  Writable Scope：apps/api/src/payments/**, packages/contracts/src/payment.ts, tests/payments/**
  Evidence：PR #42；checks pending
  内容：实现 Stripe webhook 签名校验、幂等处理和失败日志。
  依赖：M3-T1
  完成定义：单元测试覆盖伪造签名/重复事件/过期事件；安全审计无高危；CI 绿。
```

## Handoff Packet

```text
Task：M3-T4
Owner：codex-api-1
Branch/Worktree：agent/codex-api-1/M3-T4-webhook-signature
Changed Scope：apps/api/src/payments/**, packages/contracts/src/payment.ts
Current State：review
What changed：增加签名校验、幂等键、失败日志。
Evidence：commit abc123；test payments.webhook.spec.ts passed；PR #42。
Known risks：真实 Stripe CLI 尚未实走。
Next step：Integration Owner 跑端到端 webhook replay。
```
