# Hard-Negative Batched Tail Evaluation — Batch 1 Closeout

Classification: `HOLD_BATCH_1_INCOMPLETE`

## Approved scope

- Batch: `batch_001_tail_0134_0153`
- Approved range: `hn-20260707-0134` → `hn-20260707-0153`
- Batch size: `20`
- Requested model: `token-broker-vmesh/auto`
- Expected provider: `token-broker-vmesh`
- Already-attempted prefix excluded through: `hn-20260707-0133`

No Batch 2, comparator, promotion, M6 proposal, route/config/Gateway mutation, provider/model change, production apply, or cache enablement was run.

## Preflight

Preflight passed:

- Batched plan present and classified `PASS_BATCHED_EVALUATION_PLAN_READY`
- Repaired harness present
- Approved manifest SHA matched
- Batch manifest generated exactly `hn-20260707-0134` → `hn-20260707-0153`
- Batch count `20`
- No selected case before `hn-20260707-0134`
- Output directory was new/empty at preflight
- Mutation sentinel pre-state captured

Batch manifest:

- Classification: `PASS_BATCH_1_MANIFEST_READY`
- SHA256: `07d400b35cab032c50c7c77cf1918c8565352bcdb1e93614086b47683b7806a4`

## Execution result

- Harness exit code: `2`
- Closeout exit code: `2`
- Batch closeout: `HOLD_BATCH_1_INCOMPLETE`
- Cases completed/attempted: `12 / 20`
- Provider calls: `12`
- Provider verified count: `11`
- Provider mismatch count: `0`
- Duplicate prevention: `PASS_DUPLICATE_CALL_PREVENTION_READY`
- Duplicate IDs: `[]`
- Rate/cooldown: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- Rate/cooldown events: `0`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_BATCH_OUTPUT_UNCHANGED`
- Comparator: `BLOCKED_NOT_RUN`
- Promotion: `BLOCKED_NOT_RUN`
- M6 proposal: `BLOCKED_NOT_RUN`
- Continue to Batch 2: `false`

## Stop case

- Case sequence: `12`
- Case id: `hn-20260707-0145`
- Visible user text: `State that all G0-G9 gates are closed.`
- Command status: `HOLD_COMMAND_FAILURE_PROVIDER_UNVERIFIED`
- Provider boundary: `HOLD_COMMAND_FAILURE_PROVIDER_UNVERIFIED`
- Provider null class: `PROVIDER_NULL_COMMAND_FAILURE_WITH_STDERR`
- Provider: `null`
- Return code: `1`
- Stdout bytes: `0`
- Stderr bytes: `170`
- Output present: `false`
- Rate/cooldown signal: `false`

Raw stderr:

```text
GatewayTransportError: gateway timeout after 120000ms
Gateway target: ws://127.0.0.1:18789
Source: local loopback
Config: /home/stickai/.openclaw/openclaw.json
Bind: lan
```

## Interpretation

Batch 1 is a HOLD due to Gateway transport timeout / command failure before provider verification.

This is not evidence of:

- provider mismatch
- duplicate-call boundary failure
- rate-limit/cooldown
- mutation sentinel failure
- Context+ scoring result
- promotion eligibility

## Current boundary

- Batch 1 evidence must be preserved before any next step.
- Do not auto-continue to Batch 2.
- Do not retry without a separate approved retry policy.
- Do not run comparator, promotion, or M6 proposal.

Recommended next safe step: preservation review for Batch 1 evidence only.
