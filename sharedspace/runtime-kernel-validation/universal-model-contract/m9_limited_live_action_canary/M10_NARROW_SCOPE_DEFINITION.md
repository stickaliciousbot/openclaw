# M10 Narrow Scope Definition

Status: `PASS_M10_NARROW_SCOPE_DEFINED`

Scope: `M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_ONLY`

Included only:

- Telegram direct owner chat `8495203551`
- Agent `main` / Stickbot owner direct path
- Existing owner-chat production response path only
- UMC PASS/HOLD/FAIL decision gate before UMC-controlled actions

Explicitly excluded:

- Web UI
- LAN/browser
- Gmail/Drive/Calendar
- Group chats and non-owner chats
- Write tools by default
- External sends and Telegram probes
- Provider/model policy expansion
- Fallback policy expansion
- Durable memory mutation
- Context Bridge mutation
- Cron/job mutation
- Broad Gateway/config mutation
- M10B/M10C future surfaces

No broad production enforcement.
