# M6 Contract-Build Lane Staged Install and Regression Closeout

Status: `PASS_M6_CONTRACT_BUILD_LANE_STAGED_INSTALL_AND_REGRESSION`

## Results

- Closeout preflight: `PASS_M6_FINAL_CLOSEOUT_PREFLIGHT`
- Install execution: `PASS_M6_CONTRACT_BUILD_LANE_STAGED_INSTALL_EXECUTED`
- Tarball SHA verification: `PASS`
- Backup path: `/home/stickai/.openclaw/backups/openclaw-m6-contract-build-lane-install-20260716T030734Z/openclaw-installed-package`
- Gateway restart: `PASS_GATEWAY_RESTART_SETTLED_HEALTHY`
- Installed-runtime M6 verification: `PASS_M6_CONTRACT_BUILD_LANE_INSTALLED_RUNTIME_VERIFIED`
- M3/M4/M5 regression: `PASS_M6_M3_M4_M5_POST_INSTALL_REGRESSION`
- Contract-build lane installed regression: `PASS_M6_CONTRACT_BUILD_LANE_INSTALLED_REGRESSION`
- Post-install stability: `PASS_M6_POST_INSTALL_STABILITY_CONFIRMED` (4/4 probes)

## Key outcomes

- Valid route intent lane build: `PASS_M6_CONTRACT_BUILD_LANE_BUILT`
- Raw provider/model bypass: `FAIL_M6_RAW_MODEL_AUTHORITY_BYPASS`
- Missing manifest HOLD: `HOLD_M6_CAPABILITY_MANIFEST_MISSING`
- Fallback without preservation: `HOLD_M6_CAPABILITY_MANIFEST_MISSING`
- Fallback preserving contract: `PASS_M6_CONTRACT_BUILD_LANE_BUILT`
- Worker model route authority: `false`

## Safety counters

- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Route/config mutation count outside approved install: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Enforcement enabled: `false`
- M7 started: `false`

## Health

- Gateway: `PASS_RUNNING_CONNECTIVITY_OK_ADMIN_CAPABLE`
- Telegram: `PASS_ENABLED_CONFIGURED_RUNNING_CONNECTED`

## Rollback readiness

Rollback point: `/home/stickai/.openclaw/backups/openclaw-m6-contract-build-lane-install-20260716T030734Z/openclaw-installed-package`

## Next milestone

`M7_MODEL_ELIGIBILITY_AND_FALLBACK_EQUIVALENCE_NO_SEND`
