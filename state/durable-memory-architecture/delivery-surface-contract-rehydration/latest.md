# Delivery Surface Contract Rearchitecture — Rehydration Packet

Generated: `2026-07-19T08:08:20.700469Z`
Status: **PASS**
Authority: **non-authoritative navigation only**

## Mandatory interpretation

This packet restores design context and accepted M25H blocked-closeout coordinates. It does not authorize implementation, runtime mutation, handler arming, retry scheduling, delivery, Telegram sends, Ledger/Context Bridge/model-route changes, authority promotion, or M26/M2 successor work.

## Fixed boundaries

- No handler arming, retry scheduling, cron run, delivery, Telegram send, Gateway/config mutation, Ledger mutation, Context Bridge mutation, route/model mutation, authority promotion, or M26 start.
- This packet is not automatic prompt injection and not an implementation milestone.
- M25H remains accepted as pushed BLOCKED; future repair requires separate owner authorization.

## Initial contract focus

- Distinguish explicit NO_REPLY/silent policy from missing deliverable payload.
- Bind job/run/session -> boundary decision -> reply payload -> message_sending gate -> delivery runtime -> message_sent receipt -> closeout.
- Make exactly-one delivery and dedupe contract-level properties.
- Keep Surface Service Broker privacy/rendering/delivery policy separate from Runtime Service Broker source authority.
- Keep Surface Response Target Resolver grants separate from surface authorization and raw provider target handles.
- Require UMC postcondition receipts before prose claims delivery/source success.

## Bounded source summaries

```json
{
  "compaction_gap_latest_manifest": {
    "schema": "stickbot.durable_memory.compaction_gap_hydration.v1",
    "status": "PASS"
  },
  "m25h_evidence_manifest": {
    "evidence_root": "sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000",
    "restart_sentinel_validation": "PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE",
    "schema": "stickbot.memory_ledger.m25h.evidence_manifest.v1",
    "status": "M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY"
  },
  "m25h_post_validation": {
    "delivery_count": 0,
    "m25h_run_count": 1,
    "m26_started": false,
    "old_jobs_absent_not_runnable": true,
    "restart_sentinel_validation": "PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE",
    "schema": "stickbot.memory_ledger.m25h.post_validation.v1",
    "status": "PASS_POST_VALIDATION_BLOCKED_SAFE_CLEANUP",
    "terminal": "M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY"
  },
  "m25h_safety_report": {
    "restart_sentinel_validation": "PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE",
    "schema": "stickbot.memory_ledger.m25h.safety_report.v1",
    "status": "PASS_SAFE_BLOCKED_CLOSEOUT",
    "terminal": "M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY"
  },
  "m25h_status": {
    "restart_sentinel_validation": "PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE",
    "schema": "stickbot.memory_ledger.m25h.status.v1",
    "status": "M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY",
    "terminal_status": "M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY"
  },
  "m25h_summary": {
    "authority_promotion": false,
    "context_bridge_mutations": 0,
    "delivery_count": 0,
    "evidence_root": "sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000",
    "handler_ended_dormant_unarmed": true,
    "ledger_mutations": 0,
    "m25h_job_id_redacted": true,
    "m25h_job_id_sha256": "7118de2695ec45ac235ffdfac9da86be2ded8e5926a8e2a60d8fd105238e2f8f",
    "m25h_run_count": 1,
    "m26_started": false,
    "restart_sentinel_validation": "PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE",
    "retry_absent_not_runnable": true,
    "route_config_mutation": false,
    "schema": "stickbot.memory_ledger.m25h.summary.v1",
    "terminal_status": "M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY"
  },
  "m25i_dependency_graph": {
    "schema": "stickbot.m25i.contract_dependency_graph.v1"
  },
  "m25i_hard_gate_registry": {
    "schema": "stickbot.m25i.hard_gates.v1"
  },
  "m25i_health_model": {
    "schema": "stickbot.m25i.health_model.v1"
  },
  "m25i_inventory": {
    "schema": "stickbot.m25i.source_implementation_inventory.v1"
  },
  "m25j_allowlist": {
    "schema": "stickbot.m25j.file_allowlist_and_test_matrix.v1",
    "terminal": "M25J_R_SECURITY_FIXTURE_TARGET_RESOLVER_CONTRACTS_PASS_NO_LIVE_DELIVERY"
  },
  "m25j_srtr_repaired_security_fixture": {},
  "m25j_srtr_schema_registry": {
    "schema": "stickbot.m25j.schema_registry.v1",
    "status": "inert_no_live_delivery"
  }
}
```

## Source inventory

- `compaction_gap_proposal` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/COMPACTION_GAP_RECOVERY_PROPOSAL.md` — 16299 bytes — sha256:`91d81c0b58addf99e7543007c43ce305df767ee948a4e3c23ca7ee5dca47cc43` — design_reference_non_authoritative
- `systemic_lld` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD_AND_IMPLEMENTATION_PLAN.md` — 58539 bytes — sha256:`beb248ec6efdbbe77915a5b1adfa3774661285c32796ff5c5c8acf1bfc7cee61` — design_reference_non_authoritative
- `owner_supplied_broader_lld` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD.md` — 54689 bytes — sha256:`edd7284f2f591517b3536300ba476ab9b06abd0d01a02ec3b1500cc748f66de1` — owner_supplied_design_reference_non_authoritative
- `integration_order` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/LEDGER_BROKER_INTEGRATION_AND_BUILD_ORDER.md` — 11935 bytes — sha256:`1c49f34526c9d360d441108257541c6ab8a96b86dd880018bd5ff6a7c8e2dc3d` — design_reference_non_authoritative
- `delivery_surface_notebook` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/DELIVERY_SURFACE_CONTRACT_REARCHITECTURE_IMPLEMENTATION_TROUBLESHOOTING_REPAIR_NOTEBOOK.md` — 15489 bytes — sha256:`887336ad67d13e711204808bcd2f0c54d0a293a1f924cd737efb7384b38d71f6` — working_notebook_non_authoritative
- `m25i_lld` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_DELIVERY_CONTEXT_BROKER_CONTRACT_LLD.md` — 39021 bytes — sha256:`fb4e01d28bc829241cc6c330146b4f823baf3579fb0b8c2c6e9fe13adffc63d2` — m25i_design_baseline_non_authoritative
- `m25i_plan` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_SYSTEM_IMPLEMENTATION_PLAN_M25J_TO_M25Z.md` — 5028 bytes — sha256:`06e5478cc1b12e72d64e8bc55ca774f5346a6a604a44bc133a0c7488ec8851b0` — m25i_design_baseline_non_authoritative
- `m25i_gates_health` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_GLOBAL_HARD_GATES_AND_HEALTH_MODEL.md` — 6481 bytes — sha256:`3e8ce8874776989e66ec41f5d371679b4c8b1d034e05b027d098f7f419043c38` — m25i_design_baseline_non_authoritative
- `m25i_graph_contract` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_FORWARD_CONTEXT_RECONSTRUCTION_GRAPH_CONTRACT.md` — 1862 bytes — sha256:`c729280399f952950c35e12777ec986635936328a9037cca8d5a0b3543ce2e93` — m25i_design_baseline_non_authoritative
- `m25i_rsb_contract` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_RUNTIME_SERVICE_BROKER_CONTRACT.md` — 1180 bytes — sha256:`d86ae601a386c078772bc76092d07d93abece4037322fa12f989620558480f20` — m25i_design_baseline_non_authoritative
- `m25i_umc_contract` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_UMC_MODEL_CONTRACT_GENERALIZATION.md` — 999 bytes — sha256:`45676b53841645bc37dc899bbb6446b0a836e65333a97076833c48fbb5233dde` — m25i_design_baseline_non_authoritative
- `m25i_ssb_delivery_contract` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_SURFACE_SERVICE_BROKER_AND_DELIVERY_CONTRACT.md` — 2273 bytes — sha256:`7c583e81067e6b2034ebc353e4232692c1b1c2050c94101be298bd4eaf190a3b` — m25i_design_baseline_non_authoritative
- `m25i_rollback_plan` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_ROLLBACK_COMPATIBILITY_AND_MIGRATION_PLAN.md` — 1218 bytes — sha256:`2fee41002d8403179f3801ee2c92129cc652e01e411a8e4689f9a297a9844aab` — m25i_design_baseline_non_authoritative
- `m25i_test_strategy` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_TEST_FIXTURE_AND_OBSERVATION_STRATEGY.md` — 1521 bytes — sha256:`965827f94873767cb97b1480e8552d77bec2bf1e8ed0915c4969251044025f3f` — m25i_design_baseline_non_authoritative
- `m25i_adrs` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_ARCHITECTURE_DECISION_RECORDS.md` — 2317 bytes — sha256:`5a77722e5a69617c32fc4325f7a80fde9fe07efed5b151465ab246b0b9e792ea` — m25i_design_baseline_non_authoritative
- `m25j_prompt` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25J_CONTRACT_SCHEMA_SKELETON_IMPLEMENTATION_PROMPT.md` — 2069 bytes — sha256:`2c4090084bc6b774546a9ea4260489e05579612be67f86bc7136837d47c28511` — m25j_readiness_non_authoritative
- `compaction_gap_latest_manifest` — `/home/stickai/.openclaw/workspace/state/durable-memory-architecture/compaction-gap-hydration/latest.json` — 9239 bytes — sha256:`f394a0c2ff76582dc5615281b2e95ea81a94eb68beeacf671f50958afee82328` — generated_navigation_packet
- `m25h_status` — `/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/status.json` — 465 bytes — sha256:`91e0a4df84fcc374aaad44a57eb38764a3517135d6dc3567a47959b8ade4a68b` — accepted_blocked_closeout_evidence
- `m25h_summary` — `/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/summary.json` — 1618 bytes — sha256:`7b3d85f98dfd286fbf8adc18287ea3b883020d5fe1d0ab3328cf3670d35f89ff` — accepted_blocked_closeout_evidence
- `m25h_post_validation` — `/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/post_validation.json` — 2639 bytes — sha256:`bda5d0e41b1054530a59ddd5c410eb4d5d730ddc464a73c859afb9089866baf7` — accepted_blocked_closeout_evidence
- `m25h_safety_report` — `/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/safety_report.json` — 1676 bytes — sha256:`f88a2c53c4d50d3387bbdf92d8a382aa26cf29b6959ec9f6c931615f3ce4c9ec` — accepted_blocked_closeout_evidence
- `m25h_evidence_manifest` — `/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/evidence_manifest.json` — 5025 bytes — sha256:`06954e9e7a5ff9c389e7195903a6d91cb81871f42a18893d6fd9fa5a560fc945` — accepted_blocked_closeout_evidence
- `memory_chunks` — `/home/stickai/.openclaw/workspace/memory/notebooks/delivery-surface-contract-rearchitecture-chunks.md` — 7617 bytes — sha256:`8cb4b8633d67e872041c33988b6bbe3c5ea1e224f7570188c21b147b024b9d1b` — memory_navigation_non_authoritative
- `m25i_inventory` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_SOURCE_AND_IMPLEMENTATION_INVENTORY.json` — 8382 bytes — sha256:`b45e9e7809bdc02f73074ce0dc636d547677b86ed933e60e97bf017da3c7bfde` — m25i_design_inventory_non_authoritative
- `m25i_dependency_graph` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_CONTRACT_DEPENDENCY_GRAPH.json` — 3794 bytes — sha256:`bf4417a28a29a6b1b1f36768d26c0a6bb92328ca8207408cc2699657950d72a9` — m25i_design_inventory_non_authoritative
- `m25i_hard_gate_registry` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_HARD_GATE_REGISTRY.json` — 6597 bytes — sha256:`d9fd174a56d0baa793d20a36e1b03383586ab3ac8aa36d16ced5c428203f888f` — m25i_design_inventory_non_authoritative
- `m25i_health_model` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25I_HEALTH_MODEL.json` — 11345 bytes — sha256:`99e577fd6289c9a5771c15706f5b708bf7b4a40788a953199bb324b575d17d90` — m25i_design_inventory_non_authoritative
- `m25j_allowlist` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/M25J_FILE_ALLOWLIST_AND_TEST_MATRIX.json` — 3019 bytes — sha256:`d26d7d89131e8edb3320a3a347b24e22a2d27c9f9ceadd9970dff649cc14e173` — m25j_readiness_non_authoritative
- `m25j_srtr_schema_registry` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/contracts/m25j/schema_registry.json` — 14592 bytes — sha256:`8991546783a1f2b0161746a102411da3e013950ca3ebaf36627f270e718610e3` — m25j_srtr_contract_navigation_non_authoritative
- `m25j_srtr_validator` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/contracts/m25j/validators.py` — 13921 bytes — sha256:`e4d56220748e1b47ee67cdec74b94e0edb98f55da98d48eb452049cd3d95e3fb` — m25j_srtr_contract_navigation_non_authoritative
- `m25j_srtr_repaired_security_fixture` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/contracts/m25j/fixtures/security/raw_telegram_identifier.json` — 187 bytes — sha256:`ef9785b4c695bbeed943bf302b89004e7296b16f2187757d41a69f919627603e` — m25j_srtr_security_fixture_repair_non_authoritative

## Warnings

- None

## Errors

- None
