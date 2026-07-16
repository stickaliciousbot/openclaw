# Final Operator Approval Text To Enable M10A

Do not run this unless Stick explicitly approves M10A production enablement.

Approved enable command would be:

```sh
node scripts/m10a-owner-telegram-direct-control.mjs --action enable --mode apply --state-root /home/stickai/.openclaw --scope-name M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_ONLY --owner-chat-id 8495203551 --channel telegram_direct --agent-id main --requested-by owner_approval
```

Required immediate follow-up after enablement:

```sh
node scripts/m10a-owner-telegram-direct-control.mjs --action status --mode dry-run --state-root /home/stickai/.openclaw
node scripts/m10a-owner-telegram-direct-observe.mjs --mode observe --state-root /home/stickai/.openclaw --duration-minutes 30 --cadence-minutes 5 --expected-probes 6
```

Rollback/off-switch command:

```sh
node scripts/m10a-owner-telegram-direct-control.mjs --action disable --mode apply --state-root /home/stickai/.openclaw --requested-by owner_off_switch
```
