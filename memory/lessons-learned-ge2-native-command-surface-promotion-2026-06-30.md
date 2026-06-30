# Lessons learned — GE2 native command surface promotion (2026-06-30)

- Do not treat command registration selftests or hook logs as live command-surface proof. `registration.ok=true` and local import success only prove local/hook context.
- Command-list visibility, installed matcher/handler execution, adapter fixture execution, and real inbound Gateway execution are distinct proof levels. Preserve P1/P2/P3 wording so later reports do not overclaim.
- If `/ge2` is absent from `commands.list`, do not live-smoke it: invisible command text can fall through to model/chat handling and create fake evidence.
- Plugin registry lifecycle/cache boundaries can erase ad-hoc registration even when the patched chunk is imported. Durable repair must target the lifecycle path that seeds both the effective registry and public command list.
- Promotion should be docs/memory/context evidence only once runtime behavior is already proven; do not mutate runtime code/config/routes/cache/artifact-memory just to mark promotion.
- Keep fail-closed boundaries: fake command absent, existing commands preserved, no duplicate `/ge2`, no model/chat fallthrough, rollback/reverser present, DR bundle hashed, no-secrets scan PASS.
- Cron closeout retry is a separate owner-gated action; GE2 promotion alone does not authorize retrying production cron apply.
- When the workspace has a broad unrelated dirty tree, do not make a blanket commit for a production repair. First preserve a DR/handoff bundle, then selectively stage only GE2 source, hooks, notebooks, evidence, memory/context updates, and helper scripts needed to reproduce the repair.
- The clean from-scratch implementation path is: runtime kit -> hook/plugin registration layer -> authoritative loader/registry lifecycle registration -> command visibility gates -> P1 installed-dist matcher/handler -> P2 adapter fixtures -> P3 real inbound Telegram/WebUI -> R12 packet -> R13 promotion/handoff.
