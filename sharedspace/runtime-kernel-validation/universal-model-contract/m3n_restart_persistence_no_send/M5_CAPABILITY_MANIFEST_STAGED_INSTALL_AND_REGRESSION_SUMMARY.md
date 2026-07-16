# M5 Capability Manifest Staged Install and Regression Summary

Final status: `PASS_M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION`

## What happened

- Backed up installed OpenClaw package before install.
- Verified exact M5 tarball SHA256 before install.
- Installed exact M5 source-build tarball.
- Restarted Gateway via first-class `gateway.restart` for activation.
- Verified installed M5 registry/schema/seed manifests and M4/Telegram artifact preservation.
- Ran installed-runtime M5 route eligibility fixtures.
- Ran M3/M4 post-install regression evidence.
- Ran 4-probe bounded read-only stability watch.

## Key identifiers

- Source commit: `3a9abe46293294da7c73432d74f6c32e3fd1deaf`
- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz`
- Tarball SHA256: `13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06`
- Backup: `/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package`

## Results

- Staged install: `PASS_M5_CAPABILITY_MANIFEST_STAGED_INSTALL_EXECUTED`
- Installed-runtime M5 verification: `PASS_M5_CAPABILITY_MANIFEST_INSTALLED_RUNTIME_VERIFIED`
- M3/M4 regression: `PASS_M5_M3_M4_POST_INSTALL_REGRESSION`
- Route eligibility regression: `PASS_M5_CAPABILITY_ROUTE_ELIGIBILITY_INSTALLED_REGRESSION`
- Stability: `PASS_M5_POST_INSTALL_STABILITY_CONFIRMED`

## Boundary counters

- Telegram send/probe: `0`
- External send: `0`
- Provider/model live call: `0`
- Route/config mutation outside package install: `0`
- Durable memory mutation: `0`
- Context Bridge mutation: `0`
- Production authority change: `0`
- Cron re-enable: `0`
- M6 started: `false`
- Enforcement enabled: `false`

## Watch item

Event-loop/cpu degradation remains a known non-blocking watch item. It did not worsen during the 4-probe stability window and did not correlate with Gateway/Telegram health failure.

## Next milestone

`M6_TOKEN_BROKER_VMESH_CONTRACT_BUILD_LANE`
