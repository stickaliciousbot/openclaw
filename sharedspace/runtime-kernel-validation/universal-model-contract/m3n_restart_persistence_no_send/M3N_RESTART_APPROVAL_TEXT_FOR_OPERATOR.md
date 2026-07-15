# M3N restart approval text for operator

Status: `HOLD_M3N_RESTART_APPROVAL_TEXT_READY`

Copy/paste the following exact approval text if you want the controlled Gateway restart to proceed:

```text
APPROVE_M3N_TELEGRAM_READBACK_RECOVERY_RESTART

I approve exactly one controlled Gateway restart for M3N Telegram readback recovery, using this exact OpenClaw tool call and no other mutation:

gateway.restart(
  reason="M3N Telegram readback stability failed after safe no-send verification; restart requested before any N2/N3 retry.",
  note="M3N Telegram readback restart approved: no-send readback passed but stability watch failed; after boot verify Telegram readback/account health before N2/N3 retry.",
  continuationMessage="Continue M3N after approved restart: verify Gateway PID changed from pre-restart PID 122580 and Gateway is active; run Telegram channels.status probe=false readback; run 20-minute/4-probe no-send stability watch; keep cron context-plus-semantic-shadow-pass-watch (b29e6275-9bad-4622-8a56-041e5a2dc864) disabled; do not run N2/N3 unless readback and stability pass."
)

Restart reason:
- Closed M3N status is FAIL_M3N_TELEGRAM_READBACK_STABILITY at commit ca67140db7b8.
- Safe readback method channels.status probe=false passed.
- Stability watch failed due a fresh Telegram getMe timeout during probe 3.

Pre-restart Gateway PID:
- 122580

Artifacts to write after restart:
- M3N_TELEGRAM_READBACK_POST_RESTART_GATEWAY_HEALTH.json/.md
- M3N_TELEGRAM_READBACK_POST_RESTART_NO_SEND_VERIFICATION.json/.md
- M3N_TELEGRAM_READBACK_POST_RESTART_STABILITY_WATCH_PROBE_0001.json through 0004.json
- M3N_TELEGRAM_READBACK_POST_RESTART_STABILITY_WATCH_SUMMARY.json/.md
- M3N_TELEGRAM_READBACK_POST_RESTART_RECOVERY_DECISION.json/.md
- M3N_TELEGRAM_READBACK_POST_RESTART_EVIDENCE_MANIFEST.json

Post-restart validation plan:
1. Verify Gateway PID changed from 122580, Gateway is active/running, and local connectivity is OK.
2. Verify disabled cron state remains context-plus-semantic-shadow-pass-watch / b29e6275-9bad-4622-8a56-041e5a2dc864 enabled=false.
3. Run only Telegram readback via channels.status probe=false.
4. Run 20-minute / 4-probe stability watch using read-only local/Gateway status and logs.
5. If and only if readback and stability pass, prepare a separate N2/N3 approval/readiness gate; do not run N2/N3 under this approval.

Disabled cron state:
- Job: context-plus-semantic-shadow-pass-watch
- Job ID: b29e6275-9bad-4622-8a56-041e5a2dc864
- Required state across restart: enabled=false

No-send/no-probe boundary:
- This approval does not authorize Telegram sendMessage, sendTyping, message tool sends, Telegram Bot API getMe/getWebhookInfo probes, channels.status probe=true, or any external send/probe.

No-authority/no-mutation boundary:
- This approval does not authorize provider/model shadow calls, package install, tarball apply, route/fallback/config mutation, memory mutation, Context Bridge mutation, production authority change, persistence verification, M3O, M4, or enforcement.

N2/N3 boundary:
- N2/N3 retry is explicitly not approved by this restart approval.
```
