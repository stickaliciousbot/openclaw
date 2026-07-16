# M5 Install Approval Text for Operator

Status: `HOLD_M5_INSTALL_APPROVAL_TEXT_READY`

Use this exact approval text only if you intend to approve the M5 staged install. This approval authorizes only backup, SHA256 verification, installation of the exact tarball below, Gateway restart for activation, and post-install no-send/no-authority validation.

## Exact operator approval text

```text
APPROVE_M5_CAPABILITY_MANIFEST_STAGED_INSTALL

Approved milestone:
M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION

Approved source branch/head:
evidence/umc-m3g-observe-only-hook-source-20260711
3a9abe46293294da7c73432d74f6c32e3fd1deaf

Approved source commit:
3a9abe46293294da7c73432d74f6c32e3fd1deaf

Approved tarball path:
/home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz

Approved tarball SHA256:
13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06

Required backup path before install:
/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package

Approved backup command:
mkdir -p /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package && test -f /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package/package.json

Approved SHA256 verification command before install:
printf '%s  %s\n' 13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06 /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz | sha256sum -c -

Approved install command:
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz

Gateway restart requirement:
Required after package install for activation. Use OpenClaw's first-class Gateway restart action with reason: M5 capability manifest staged install activation.

Rollback readiness:
Rollback only if install/verification fails and recovery policy/approval requires it. Preserve evidence first.

Rollback command if separately required/approved:
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2/openclaw-2026.5.7.tgz && openclaw gateway restart

Post-install validation artifacts required:
M5_CAPABILITY_MANIFEST_STAGED_INSTALL_RESULT.json
M5_CAPABILITY_MANIFEST_INSTALLED_RUNTIME_VERIFICATION.json
M5_M3_M4_POST_INSTALL_REGRESSION_RESULT.json
M5_CAPABILITY_ROUTE_ELIGIBILITY_INSTALLED_REGRESSION_RESULT.json
M5_POST_INSTALL_STABILITY_PROBE_0001.json
M5_POST_INSTALL_STABILITY_PROBE_0002.json
M5_POST_INSTALL_STABILITY_PROBE_0003.json
M5_POST_INSTALL_STABILITY_PROBE_0004.json
M5_POST_INSTALL_STABILITY_SUMMARY.json
M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION_CLOSEOUT.json
M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION_SUMMARY.md
M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION_EVIDENCE_MANIFEST.json

No-send/no-authority boundary:
No Telegram send/probe.
No external send.
No provider/model live call.
No direct installed-dist hotpatch.
No manual tarball surgery.
No route/fallback/config production mutation outside approved package install.
No durable memory mutation.
No Context Bridge mutation.
No production authority change.
No cron re-enable.
No M6.
No enforcement.
```

## Exact approved execution sequence after operator approval

1. Backup installed package:

```sh
mkdir -p /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package && test -f /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package/package.json
```

2. Verify exact tarball SHA256:

```sh
printf '%s  %s\n' 13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06 /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz | sha256sum -c -
```

3. Install exact tarball:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz
```

4. Restart Gateway for activation:

Use OpenClaw's first-class Gateway restart action with reason: `M5 capability manifest staged install activation`.

## Key identifiers

- Tarball path: `/home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz`
- Tarball SHA256: `13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06`
- Source commit: `3a9abe46293294da7c73432d74f6c32e3fd1deaf`
- Backup path: `/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package`
- Rollback command: `npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2/openclaw-2026.5.7.tgz && openclaw gateway restart`
