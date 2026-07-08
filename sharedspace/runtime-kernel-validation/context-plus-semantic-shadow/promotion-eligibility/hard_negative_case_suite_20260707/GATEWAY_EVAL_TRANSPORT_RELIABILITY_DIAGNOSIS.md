# Gateway Evaluation Transport Reliability Diagnosis

Classification: `HOLD_GATEWAY_TIMEOUT_ROOT_CAUSE_UNKNOWN`

## Scope

Diagnosis only from existing evidence. No new evaluation execution, resume execution, tail continuation, Gateway/model/provider calls, comparator run, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred while writing this diagnosis.

## Reset decision

Stop the current hard-negative evaluation continuation loop.

Current state is reclassified as:

`HOLD_EVALUATION_EXECUTION_UNSTABLE`

Reason:

- The original 240-case hard-negative evaluation did not complete.
- Provider-null / no-output command failure occurred at `hn-20260707-0056`.
- Resume became complicated because early evidence included legacy/partial journal state and the harness resume path was not designed as a first-class batch ledger.
- Tail continuation then failed with `GatewayTransportError` timeout after `120000ms` at `hn-20260707-0134`.
- We are now debugging execution mechanics instead of evaluating Context+.

## Promotion boundary

Only `PASS_FALSE_POSITIVE_BASELINE_IMPROVED` can lead to promotion eligibility.

Current clean same-suite baseline remains:

- Production: `0 / 440` false positives
- Context+: `0 / 440` false positives
- Result: `HOLD_EQUAL_ZERO_ZERO`
- Promotion: `BLOCKED`

Partial hard-negative results are **not** promotion evidence.

Do not run comparator, promotion, or M6 proposal from the current hard-negative artifacts.

## Partial / failed attempt inventory

### 1. Initial incomplete production-routing run

- Range attempted: `hn-20260707-0001` → `hn-20260707-0056`
- Count: `56`
- Located journal SHA256: `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`
- Terminal problem: provider-null / command failure evidence around `hn-20260707-0056`
- Classification: `HOLD_PROVIDER_NULL_EVIDENCE_INCOMPLETE`
- Failure type: parser/evidence gap plus command/no-output condition; not proven provider mismatch

### 2. Provider-null diagnosis

- Artifact: `PROVIDER_BOUNDARY_NULL_DIAGNOSIS.md`
- Stop case: `hn-20260707-0056`
- Summary: child `openclaw infer model run` failure/no-output condition; harness parsed `provider=null` because stdout was empty/invalid/missing provider metadata.
- Failure type: command failure / parser-evidence gap before provider verification
- Provider mismatch: not proven

### 3. Legacy resume crash attempt

- Dir: `hard_negative_remaining_resume_20260708T083000AEST/`
- Summary: resume validation crashed with `IsADirectoryError: [Errno 21] Is a directory: '.'` because legacy v1 attempted rows lacked repaired v2 raw path fields.
- Failure type: harness resume support/evidence-shape gap
- Provider calls: no usable live tail evidence from this failed preflight attempt

### 4. Partial remaining run

- Dir: `hard_negative_remaining_resume_20260708T083500AEST/`
- Selected original remaining range: `hn-20260707-0057` → `hn-20260707-0240`
- Completed: `77 / 184`
- Completed range: `hn-20260707-0057` → `hn-20260707-0133`
- Provider calls: `77`
- Provider boundary: `PASS_PROVIDER_CALL_BOUNDARY`
- Provider verified count: `77`
- Provider mismatch count: `0`
- Rate/cooldown: `HOLD_RATE_LIMIT_OR_COOLDOWN` at `hn-20260707-0133`
- Failure type: partial execution / rate-cooldown hold

### 5. Tail readiness preservation

- Artifact dir: `tail_continuation_readiness_20260708T0935AEST/`
- Commit: `07e5cfc04adcfda97a28206aa4f65a2c30a32ae2`
- Branch: `refs/heads/evidence/context-plus-hard-negative-tail-continuation-readiness-20260708`
- Summary: duplicate-safe tail plan proved `hn-20260707-0134` → `hn-20260707-0240` as a 107-case tail excluding 133 already-attempted cases.
- Failure type: none; planning evidence only

### 6. Tail continuation timeout attempt

- Dir: `hard_negative_remaining_tail_resume_20260708T0940AEST/`
- Approved tail range: `hn-20260707-0134` → `hn-20260707-0240`
- Tail count: `107`
- Attempted: `1 / 107`
- Case attempted: `hn-20260707-0134`
- Closeout: `FAIL_TAIL_RESUME_UNSAFE`
- Harness summary: `HOLD_EVALUATION_INCOMPLETE`
- Provider report: `HOLD_PROVIDER_CALL_BOUNDARY_INCOMPLETE`
- Command status: `HOLD_COMMAND_FAILURE_PROVIDER_UNVERIFIED`
- Provider null class: `PROVIDER_NULL_COMMAND_FAILURE_WITH_STDERR`
- Provider verified count: `0`
- Provider mismatch count: `0`
- Rate/cooldown: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`
- Failure type: Gateway transport timeout / command failure before provider verification

Raw stderr:

```text
GatewayTransportError: gateway timeout after 120000ms
Gateway target: ws://127.0.0.1:18789
Source: local loopback
Config: /home/stickai/.openclaw/openclaw.json
Bind: lan
```

## Failure classification table

| Evidence | Failure class | Provider mismatch? | Command failure? | Transport timeout? | Parser/evidence gap? |
|---|---:|---:|---:|---:|---:|
| `hn-20260707-0056` provider-null stop | `HOLD_PROVIDER_NULL_EVIDENCE_INCOMPLETE` | no proof | yes/unknown | unknown | yes |
| `083000AEST` resume crash | `HOLD_HARNESS_RESUME_EVIDENCE_SHAPE_GAP` | no | no live call | no | yes |
| `083500AEST` partial run | `HOLD_RATE_LIMIT_OR_COOLDOWN` | no | no | no | no |
| `0940AEST` tail case `0134` | `HOLD_GATEWAY_TRANSPORT_TIMEOUT` | no | yes | yes | no raw-output parse gap; stderr captured |

## Gateway/provider path stability assessment

Current evidence is insufficient to declare the Gateway/provider path stable enough for long sequential hard-negative evaluation runs.

Reasons:

- A 77-call segment completed with clean provider boundary, proving the path can work for a medium segment.
- The tail attempt then timed out on the first case after `120000ms`, proving the current execution method is not reliable enough for ad hoc long/continued runs.
- The timeout root cause is not classified: it may be Gateway transport, token-broker-vmesh queueing/stall, prompt-specific latency, CLI wrapper timeout behavior, or runtime load.

Conclusion:

`HOLD_GATEWAY_TIMEOUT_ROOT_CAUSE_UNKNOWN`

## Batching / retry / timeout / harness findings

- Batching is required before any more evaluation execution.
- Retry policy requires explicit operator approval. Default should remain `0` retries until approved.
- Timeout settings need review. The observed `120000ms` Gateway transport timeout occurred before provider verification; simply increasing timeout without batching would be another knob-turning attempt.
- Harness taxonomy is partly repaired: it distinguishes command failure/provider-null from provider mismatch in raw parse/provider reports. However, operational closeout must treat Gateway timeout as `HOLD_GATEWAY_TRANSPORT_TIMEOUT`, not as promotion-relevant provider-boundary failure.
- Harness can support batching by generated batch manifests with `--allow-fixture-manifest`, but the batch runner/ledger protocol must be explicit so resume is by batch ledger, not ad hoc case ranges.

## Required before rerun

Before any more provider calls:

1. Preserve this diagnosis and the batched evaluation plan.
2. Review and approve the batched execution protocol.
3. Decide retry policy for transport timeout (`0` default, or exactly `1` retry for transport timeout only).
4. Decide timeout setting per batch after reviewing Gateway reliability; do not blindly raise timeout.
5. Ensure every batch has a terminal closeout before the next batch starts.

## Closeout

Classification: `HOLD_GATEWAY_TIMEOUT_ROOT_CAUSE_UNKNOWN`

This does **not** authorize more live evaluation. Do not request live evaluation approval until the batched plan is preserved and the operator explicitly reopens execution under that plan.
