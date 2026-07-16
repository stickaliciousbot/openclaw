# M7 Model Eligibility Staged Install and Regression Closeout

Status: `PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION`

- Source head installed: `1557ff822e0c9b86eded7c827543bf4866676671`
- Tarball SHA256: `8814f2ee8e0cd5a6b7fbf8ba52f80f497a468404513ea865af9a729a8cd37717`
- Staged install: `PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_EXECUTED`
- Installed-runtime M7 verification: `PASS_M7_MODEL_ELIGIBILITY_INSTALLED_RUNTIME_VERIFIED`
- M3/M4/M5/M6 post-install regression: `PASS_M7_M3_M4_M5_M6_POST_INSTALL_REGRESSION`
- Fallback equivalence installed regression: `PASS_M7_FALLBACK_EQUIVALENCE_INSTALLED_REGRESSION`
- Post-install stability: `PASS_M7_POST_INSTALL_STABILITY_CONFIRMED`

## Key outcomes

- Eligible primary worker: `PASS_M7_MODEL_ELIGIBILITY_VERIFIED`
- Eligible fallback: `PASS_M7_MODEL_ELIGIBILITY_VERIFIED`
- Missing manifest: `HOLD_M7_CAPABILITY_MANIFEST_MISSING`
- Malformed manifest: `FAIL_M7_CAPABILITY_MANIFEST_INVALID`
- Fallback contract drop: `HOLD_M7_FALLBACK_CONTRACT_DROP`
- Raw provider/model authority: `FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS`
- Worker model route-authority: `false`

## Health and safety

- Gateway: `PASS_RUNNING_CONNECTIVITY_OK_ADMIN_CAPABLE`
- Telegram: `PASS_ENABLED_CONFIGURED_RUNNING_CONNECTED`
- Event-loop/cpu watch item: present, non-blocking during health/stability checks
- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Route/config mutation count outside approved package install: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Enforcement enabled: `false`
- M8 started: `false`

## Rollback

Rollback readiness: `READY`

Backup path: `/home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z/openclaw-installed-package`

Rollback command: `npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m6-package/openclaw-2026.5.7.tgz && openclaw gateway restart`

## Next milestone

`M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY`
