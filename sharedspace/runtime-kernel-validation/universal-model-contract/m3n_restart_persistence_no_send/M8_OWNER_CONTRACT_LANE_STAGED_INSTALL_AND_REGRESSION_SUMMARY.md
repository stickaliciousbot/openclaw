# M8 Owner Contract Lane Staged Install and Regression Closeout

Status: `FAIL_M8_OWNER_CONTRACT_LANE_INSTALLED_RUNTIME_VERIFICATION`

## What passed

- R2 approval received: `APPROVE_M8_OWNER_CONTRACT_LANE_STAGED_INSTALL_R2`
- Backup present: `/home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-r2-20260716T0524Z/openclaw-installed-package`
- Tarball SHA gate passed: `c9b71a74644e871b413d1a5f7b1d3110934a99b39ca16758b6f8596483200da7`
- Staged install executed: `PASS_M8_OWNER_CONTRACT_LANE_STAGED_INSTALL_EXECUTED`
- Gateway restarted and is reachable/admin-capable.
- Telegram read-only health recovered to enabled/configured/running/connected.
- Installed M8 file is present: `ab0b66fb9578f1b99320b46590825a1a956a83152d5c653f0d00ca2386cdb44f`
- Installed M7 file replaced as approved by R2: `85e80863ee7720453e57c62b5c7955a681a0e8398e80a9ab9d026fcb66c4f996`
- M4/M5/M6/plugin/package preservation hashes match expected values.

## Blocking failure

Installed-runtime M8 verification failed on the Phase-D/R2 contract requirement:

- Required: `authority_mode === enforced_no_send`
- Actual installed valid-path evidence: `authority_mode === observe_only`
- Failure id: `authority_mode_enforced_no_send_literal_missing`
- Artifact: `M8_OWNER_CONTRACT_LANE_INSTALLED_RUNTIME_VERIFICATION.json`
- Artifact SHA256: `d27b151802fb968f2b35720a18ec79b42256b61aed774579016a096c4503911e`

Because installed-runtime verification failed, I stopped before installed canary regression, M3/M4/M5/M6/M7 post-install regression, and 20-minute stability.

## Boundaries

- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Route/config production mutation count: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Live-action canary enabled: `false`
- Broad production enforcement enabled: `false`
- M9 started: `false`

## Rollback readiness

Rollback is ready but was not executed automatically because the approved recovery policy said to stop and preserve evidence unless rollback was required.

- Rollback tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz`
- Rollback tarball SHA256: `8814f2ee8e0cd5a6b7fbf8ba52f80f497a468404513ea865af9a729a8cd37717`

## Next decision

Choose one recovery path:

1. Source repair + R3 staged install approval: change M8 authority evidence/contract vocabulary to satisfy `enforced_no_send` literally.
2. Roll back to M7 using the known rollback tarball.
3. Revise the M8 contract to accept existing `observe_only` as the intended no-send authority vocabulary, then rerun approval/verification.
