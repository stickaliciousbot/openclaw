# M10A Owner Telegram Direct Enforcement Approval Package — Revised

Status: `HOLD_M10A_FINAL_OPERATOR_APPROVAL_TEXT_READY`

The M10A command surface is installed and validated. M10A is **not enabled**. Production authority remains false. Broad enforcement remains false.

## Exact command surface

- Enable: `node scripts/m10a-owner-telegram-direct-control.mjs --action enable --mode apply --state-root /home/stickai/.openclaw --scope-name M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_ONLY --owner-chat-id 8495203551 --channel telegram_direct --agent-id main --requested-by owner_approval`
- Disable: `node scripts/m10a-owner-telegram-direct-control.mjs --action disable --mode apply --state-root /home/stickai/.openclaw --requested-by owner_off_switch`
- Status: `node scripts/m10a-owner-telegram-direct-control.mjs --action status --mode dry-run --state-root /home/stickai/.openclaw`
- Operator stop: `node scripts/m10a-owner-telegram-direct-control.mjs --action operator-stop --mode apply --state-root /home/stickai/.openclaw --requested-by operator_stop`
- Post-enable observation: `node scripts/m10a-owner-telegram-direct-observe.mjs --mode observe --state-root /home/stickai/.openclaw --duration-minutes 30 --cadence-minutes 5 --expected-probes 6`

Final owner approval is still required before production enablement.
