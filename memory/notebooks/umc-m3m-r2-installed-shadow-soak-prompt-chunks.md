# UMC M3M R2 installed shadow soak prompt chunks

Status: incomplete; waiting for remaining prompt and final `Banana` terminator before execution.

## Chunk 1 — received 2026-07-13 20:07 AEST

Continue Stickbot/OpenClaw Universal Model Contract v1 from the completed M3M abort preservation and post-abort stability confirmation.

Current authoritative UMC state

Previous M3M soak:
ABORT / not PASS

Abort reason:
GATEWAY_UNREACHABLE

Abort checkpoint:
0005 at 2026-07-13T08:58:22Z

Last clean checkpoint:
0004 at 2026-07-13T08:28:06Z

M3N:
not started

Post-abort recovery state

Gateway:
healthy after abort

Telegram:
ON/OK

Fresh logs:
clean

Post-abort health stability:
PASS_M3M_POST_ABORT_HEALTH_STABILITY_CONFIRMED

Post-abort probes:
6 / 6 clean

Failed probes:
0

Safety state

Telegram sends: 0
External sends: 0
Provider/model live execution caused by shadow: 0
Runtime mutation: 0
Memory mutation: 0
Context Bridge mutation: 0
Route/fallback mutation: 0
Manifest drift: false
M3N started: false
M4 started: false
Enforcement started: false

Objective

Run the second bounded installed-runtime observe-only/no-send soak retry.

Milestone:

M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2

Default bounds:

duration: 12 hours
checkpoint cadence: 30 minutes
expected checkpoints: 24
hard stop: true

R2 must not weaken the original M3M gates.

R2 may add better Gateway reachability diagnostics around each checkpoint.

Do not advance to M3N unless R2 completes with PASS.

---

Hard safety rules

During R2:

No live Telegram sends.
No external sends.
No provider/model calls caused by the UMC shadow hook.
No real write tools.
No memory mutation.
No Context Bridge mutation.
No route/provider/fallback mutation.
No production config mutation.
No production routing authority change.
No contract enforcement.
No package install.
No tarball apply.
No Gateway restart unless recovery requires it and the milestone stops for approval.

The installed hook must remain:

observe-only
no-send
disabled by default
fixture-gated only
non-authoritative

---

Phase R2-A — R2 preflight

Verify:

- latest abort preservation and diagnostic milestone completed successfully;
- post-abort stability result is:

PASS_M3M_POST_ABORT_HEALTH_STABILITY_CONFIRMED

- 6 / 6 post-abort probes were clean;
- previous M3M soak did not pass;
- previous abort reason was "GATEWAY_UNREACHABLE";
- M3N was not started;
- Gateway is currently reachable and RPC OK;
- Telegram is ON/OK;
- "openclaw status --json" is parsed from full stdout;
- queue depth is at expected resting state;
- old runner is present:
 - "dist/agent-runner.runtime-a09vVD0N.js";
- required chunk is present:
 - "dist/pi-embedded-8wfHbvwc.js";
- required plugin manifests are present with expected hashes:
 - Zalo hash "635c83aa3b28d07c85cf55257e084dd678fcbe9808bc2b76db19edadcc43dcb1";
 - Zalouser hash "03874c85b9a212217e25b55aeb75eed46f9252e56246d0b9b178176ccf823fae";
- bounded fresh logs do not show:
 - "ERR_MODULE_NOT_FOUND";
 - missing "pi-embedded";
 - missing Zalo/Zalouser manifest;
 - "channels.telegram: unknown channel id";
- observe-only hook state is recorded;
- hook is disabled by default or not active outside fixture flags;
- rollback target/backups are known;
- no live-send approval exists;
- no external-send approval exists.

Produce:

M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT.json

If preflight fails, stop with:

BLOCKED_M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT

---

Phase R2-B — Define R2 bounds

Before starting, write exact R2 bounds to evidence.

Produce:

M3M_R2_INSTALLED_SHADOW_SOAK_BOUNDS.json

Default bounds:

{
 "mode": "duration",
 "duration_hours": 12,
 "checkpoint_count": 24,
 "checkpoint_cadence_minutes": 30,
 "hard_stop": true,
 "retry": "R2",
 "reason": "R1 aborted fail-closed at checkpoint 0005 due to transient GATEWAY_UNREACHABLE; post-abort 6/6 stability probes clean"
}

The run must stop once the configured bound is reached.

---

Phase R2-C — Enhanced checkpoint procedure

At each checkpoint, collect normal M3M read-only/no-send state plus enhanced Gateway reachability diagnostics.

Each checkpoint must verify:

Gateway reachable
Gateway RPC OK
Gateway PID
Gateway listener/port state
Gateway response latency or timeout status
Telegram status
Telegram account count
queue depth
installed package manifest/hash
old runner presence/hash
required chunk presence/hash
Zalo manifest presence/hash
Zalouser manifest presence/hash
bounded fresh log scan for module-not-found/missing-manifest/unknown-telegram-channel errors
production route/provider/fallback hash
production config hash
hook disabled by default
shadow fixture mode not active unless explicitly running optional no-send fixture
provider/model live execution caused by shadow: 0
Telegram sends caused by shadow: 0
external sends: 0
real write tools: 0
memory mutation: 0
Context Bridge mutation: 0
production config mutation: 0
shadow receipt count
terminal closeout count
would-be HOLD/FAIL count
errors or warnings
rollback backup still present

Produce one checkpoint artifact per checkpoint:

M3M_R2_CHECKPOINT_0001.json
M3M_R2_CHECKPOINT_0002.json
...
M3M_R2_CHECKPOINT_0024.json

Use zero-padded numbering.

Do not overwrite R1 checkpoint artifacts.

---

Phase R2-D — Optional no-send fixture checkpoints

If safe and already available, run a no-send observe-only fixture at:

start
midpoint
final checkpoint

The fixture must use explicit no-send/observe-only flags only:

UMC_SHADOW_MODE=observe_no_send
UMC_SHADOW_OWNER_SCOPE=fixture_only
UMC_SHADOW_DELIVERY=no_send
UMC_SHADOW_PROVIDER=mock_only
UMC_SHADOW_MUTATION=forbidden

Fixture must verify:

- shadow receipt emitted;
- UniversalContractReceipt emitted;
- DeliveryReceipt mode is "no_send";
- terminal closeout emitted;
- production response path unchanged;
- provider/model live execution count remains "0";
- Telegram send count remains "0";
- external-send count remains "0".

If not safe or unavailable, skip and record why.

Do not fail R2 solely because optional fixture execution was skipped unless the bounds contract required it.

---

Phase R2-E — Abort conditions

Abort immediately if any occur:

Gateway unhealthy and not self-recovering
Telegram unhealthy
ERR_MODULE_NOT_FOUND appears in fresh bounded logs
missing pi-embedded appears in fresh bounded logs
missing Zalo/Zalouser manifest appears in fresh bounded logs
channels.telegram unknown channel id appears in fresh bounded logs
installed package/hash drift
required manifest hash drift
production route/provider/fallback drift
production config drift
hook enabled outside fixture mode
shadow causes provider/model live execution
any Telegram send caused by shadow
any external send
real write tool execution
memory mutation
Context Bridge mutation
rollback backup missing
checkpoint evidence cannot be written
duplicate/contradictory checkpoint state

Abort status options:

FAIL_M3M_R2_GATEWAY_HEALTH_REGRESSION
FAIL_M3M_R2_TELEGRAM_HEALTH_REGRESSION
FAIL_M3M_R2_MODULE_NOT_FOUND_REGRESSION
FAIL_M3M_R2_PLUGIN_MANIFEST_REGRESSION
FAIL_M3M_R2_INSTALLED_PACKAGE_HASH_DRIFT
FAIL_M3M_R2_ROUTE_PROVIDER_FALLBACK_DRIFT
FAIL_M3M_R2_SHADOW_PROVIDER_CALL_REGRESSION
FAIL_M3M_R2_TELEGRAM_SEND_REGRESSION
FAIL_M3M_R2_EXTERNAL_SEND_REGRESSION
FAIL_M3M_R2_MEMORY_OR_CONTEXT_MUTATION_REGRESSION
FAIL_M3M_R2_ROLLBACK_NOT_READY
FAIL_M3M_R2_CHECKPOINT_EVIDENCE_FAILURE

If abort occurs, preserve evidence and do not continue.

Do not advance to M3N from an aborted R2.

---

Phase R2-F — Final closeout

At the end of the bounded run, produce:

M3M_R2_INSTALLED_SHADOW_SOAK_CLOSEOUT.json
M3M_R2_INSTALLED_SHADOW_SOAK_SUMMARY.md
M3M_R2_INSTALLED_SHADOW_SOAK_EVIDENCE_MANIFEST.json

Closeout must include:

- final status;
- configured bounds;
- actual duration;
- checkpoint count planned;
- checkpoint count completed;
- missed checkpoints;
- Gateway health summary;
- Gateway reachability latency/timeout summary;
- Telegram health summary;
- queue depth summary;
- installed package/hash drift count;
- required manifest hash drift count;
- module-not-found regression count;
- missing manifest regression count;
- unknown Telegram channel regression count;
- shadow receipt count;
- terminal closeout count;
- would-be HOLD count;
- would-be FAIL count;
- provider/model live execution count;
- Telegram send count;
- external-send count;
- real write tool count;
- memory mutation count;
- Context Bridge mutation count;
- production route/provider/fallback drift count;
- production config drift count;
- rollback readiness final state;
- recommendation for next milestone.

Successful closeout:

PASS_M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2

Blocked/failed closeouts:

BLOCKED_M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT
FAIL_M3M_R2_INSTALLED_SHADOW_SOAK_ABORTED
FAIL_M3M_R2_INSTALLED_SHADOW_SOAK_VALIDATION

---

Phase R2-G — Evidence and docs

Update scoped UMC docs:

UMC_V1_HANDOFF.json
UMC_V1_MILESTONE_LEDGER.md
UMC_V1_REHYDRATOR.md
UMC_V1_IMPLEMENTATION_NOTEBOOK.md
UMC_V1_TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md
memory/2026-07-11.md

Run:

JSON validation for all checkpoint and closeout artifacts
git diff --check
checkpoint count validation
safety counter validation
installed package hash validation
manifest hash validation
Gateway reachability validation
rollback readiness validation
no-send validation
no-authority validation

Commit evidence only.

Suggested commit:

docs(umc): record M3M R2 observe-only shadow soak

Push if preservation workflow authorizes it.

---

Final report

Return:

1. final status;
2. R2 preflight result;
3. configured duration/checkpoints;
4. actual duration;
5. checkpoints completed;
6. Gateway health summary;
7. Gateway reachability diagnostic summary;
8. Telegram health summary;
9. queue depth summary;
10. installed package/hash drift count;
11. required manifest hash drift count;
12. module-not-found regression count;
13. missing manifest regression count;
14. unknown Telegram channel regression count;
15. shadow receipt count;
16. terminal closeout count;
17. would-be HOLD/FAIL summary;
18. provider/model live execution count;
19. Telegram send count;
20. external-send count;
21. real write tool count;
22. memory mutation count;
23. Context Bridge mutation count;
24. production route/provider/fallback drift count;
25. production config drift count;
26. rollback readiness;
27. files changed;
28. commits created;
29. evidence artifacts and SHA256 values;
30. push/preservation status;
31. exact next milestone.

Expected next milestone after PASS:

M3N_INSTALLED_SHADOW_OBSERVE_ONLY_RESTART_PERSISTENCE_NO_SEND

The governing rule is:

R2 is the same M3M soak with better reachability diagnostics.

Do not weaken gates.

No-send.
Observe-only.
No production authority.

Only advance to M3N after a full R2 PASS.

Banana please begin
