# GE2-R9 Native Run Lifecycle Proof — Intake Hold

Status: `GE2_R9_INTAKE_HOLD_UNTIL_BANANA`

Stick instructed: read the entire prompt until `banana`, save bits to memory and implementation notebooks before implementing. The current received segment has not included `banana`, so R9 implementation is held.

## Carry-forward

Current classification:

`GE2_R8_HELP_STATUS_NATIVE_EXECUTION_PASS_RUN_PENDING`

R8 proof level achieved:

- P1 installed-dist native matcher/handler harness
- Do not overclaim P2 Telegram/WebUI fixture proof or P3 real inbound Gateway proof.

R8 artifacts:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r8_native_execution_route_discovery/GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_REPORT_20260630.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r8_native_execution_route_discovery/GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_REPORT_20260630.md`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r8_native_execution_route_discovery/r8_native_execution_route_discovery_and_harness_20260630.mjs`

## R9 target from partial prompt

Use installed-dist native handler harness first to prove:

1. `/ge2 run r9-native-handler-smoke`
2. extract returned `run_id`
3. `/ge2 status <run_id>`
4. `/ge2 artifacts <run_id>`

No P2/P3 overclaim.

## Hard boundaries

- no production patch
- no Gateway restart
- no rollback
- no cron apply
- no model/chat spoofing
- no outbound bot spoofing
- no promotion

## Required proof categories from partial prompt

### Run proof

- native command match: `ge2`
- pluginId: `ge2-native`
- `continueAgent:false`
- no model/chat fallthrough
- returned `run_id`
- durable run record created
- lifecycle/status transitions recorded
- milestone events emitted
- at least one artifact written
- artifact SHA256 computed
- terminal status successful
- no placeholder success
- response bounded; no unbounded raw payload dumped

### Status proof

- exact `run_id`
- current/final status
- milestone count
- artifact count
- no model/chat fallthrough

### Artifacts proof

- artifact list returned
- paths included
- SHA256 values included
- artifact files exist
- response SHA256 matches computed SHA256

### Ledger/artifact proof

- ledger file exists
- `run_id` recorded
- origin/session metadata present
- milestone history present
- artifact inventory present
- terminal file check after terminal write if written:
  - `status.json`
  - `summary.json`
  - `evidence_manifest.json`
- no terminal PASS if terminal artifacts missing

### Compression gate proof

- visible handler response bounded
- full raw payload stored in artifact/ledger if large
- response includes artifact refs/hashes
- no massive raw logs in command response

## Expert augmentation to apply after banana

1. Add explicit proof-level field to report: `proofLevel: P1`.
2. Add `noP2P3Claim:true` in JSON artifacts.
3. Include response-size measurements for run/status/artifacts responses.
4. Poll/wait boundedly for terminal run state if `/ge2 run` is asynchronous; do not busy-loop.
5. If runtime completes but terminal artifacts are missing, classify as runtime/artifact-contract failure rather than surface failure.
6. Separate handler proof from runtime proof:
   - handler matched/executed can pass while runtime artifact contract fails.
7. Use direct file reads/hash verification of ledger/artifacts after command responses.
8. Do not mutate state beyond the intended GE2 run record/artifacts created by `/ge2 run r9-native-handler-smoke`.

## Gate

Await the rest of the prompt and literal `banana` before implementation.
