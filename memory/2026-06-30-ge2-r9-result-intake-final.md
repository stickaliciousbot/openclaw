# 2026-06-30 — GE2-R9 final intake after banana

Stick completed the GE2-R9 prompt with `banana`. Implementation authorized.

Additional R9 invalid/fail classifications:

- If `/ge2 run` does not match native command: `GE2_R9_NATIVE_RUN_MATCH_FAILED`
- If run matches but falls through to model/chat: `GE2_R9_NATIVE_RUN_MODEL_FALLTHROUGH_FAIL`
- If run returns placeholder success without durable ledger/artifact: `GE2_R9_PLACEHOLDER_SUCCESS_FAIL`
- If ledger missing: `GE2_R9_LEDGER_MISSING_FAIL`
- If artifact missing/hash mismatch: `GE2_R9_ARTIFACT_HASH_FAIL`
- If status/artifacts cannot retrieve by `run_id`: `GE2_R9_STATUS_ARTIFACTS_RETRIEVAL_FAIL`
- If all P1 run/status/artifacts gates pass: `GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_PASS_P2_PENDING`

R9 report must include proof level P1 only, command results for run/status/artifacts, run_id, ledger path, artifact paths/SHA256s, milestone count, status result, artifacts result, compression summary, model/chat fallthrough check, fake command absent, duplicate `/ge2` count, existing commands preserved, production touched yes/no, Gateway restarted yes/no, rollback performed yes/no, and final classification.

If R9 P1 passes, do not promote. Next step becomes P2: `GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_HELP_STATUS_RUN_PENDING`.

Implementation revision:

- Keep proof level explicitly P1 and `noP2P3Claim:true`.
- Intended GE2 runtime state mutation from `/ge2 run r9-native-handler-smoke` is allowed; no production code/config/service mutation.
- Distinguish handler proof from runtime artifact contract proof.
- Use direct file hash verification for artifacts.
- Use bounded waits only; no busy loop.
