# M25I System Implementation Plan — M25J to M25Z

Status: dependency-aware design plan; no successor milestone starts automatically.

| Milestone | Title | Scope | Terminal | Successor rule |
| --- | --- | --- | --- | --- |
| M25J | Contract schemas and fixtures | schema/type skeletons; validation library; positive/negative fixtures; no runtime apply | M25J_CONTRACT_SCHEMA_SKELETON_TESTS_PASS_NO_LIVE_DELIVERY | Owner authorization required before successor |
| M25K | Delivery-required runtime classification | distinguish quiet vs delivery-required; bare NO_REPLY forbidden for delivery-required; no Telegram | M25K_RUNTIME_DELIVERY_CLASSIFICATION_PASS_NO_TELEGRAM | Owner authorization required before successor |
| M25L | Boundary decision envelope | explicit allow/hold/reject receipt; no Telegram | M25L_BOUNDARY_DECISION_ENVELOPE_PASS_NO_TELEGRAM | Owner authorization required before successor |
| M25M | Sanitized payload artifact | handler allow plus delivery-required contract creates sanitized payload artifact; no Telegram | M25M_SANITIZED_PAYLOAD_ARTIFACT_PASS_NO_TELEGRAM | Owner authorization required before successor |
| M25N | Delivery adapter canary | one controlled sanitized Telegram send; no retry machinery; idempotency and duplicate suppression | M25N_TELEGRAM_DELIVERY_ADAPTER_CANARY_PASS_ONE_SEND | Owner authorization required before successor |
| M25O | Final armed one-shot proof | one new disabled/inert job; exact handler arming; one execution; exactly one sanitized delivery; anchor; disarm/remove | M25O_ARMED_ONE_SHOT_FINAL_DELIVERY_PASS_LEDGER_V0_1_COMPLETE | Owner authorization required before successor |
| M25P | Post-completion observation | no delayed duplicate; handler dormant; no runnable retry; state unchanged | M25P_POST_COMPLETION_OBSERVATION_PASS | Owner authorization required before successor |
| M25Q | Source registry and context contract alignment | source/entity/claim/GUID schemas offline only | M25Q_SOURCE_REGISTRY_CONTEXT_CONTRACT_ALIGNMENT_PASS_NO_RUNTIME_INTEGRATION | Owner authorization required before successor |
| M25R | Offline durable-memory core | deterministic resolver and atomic records; no live runtime integration | M25R_OFFLINE_DURABLE_MEMORY_CORE_PASS_NO_RUNTIME_INTEGRATION | Owner authorization required before successor |
| M25S | Forward reconstruction graph shadow | graph/FTS/vector projections; packet/receipt/source readback; shadow only | M25S_FORWARD_CONTEXT_RECONSTRUCTION_SHADOW_PASS_NO_PROMPT_INJECTION | Owner authorization required before successor |
| M25T | Runtime Service Broker shadow path | grants, budgets, receipts, timeout/cancel; no user-visible answer change | M25T_RUNTIME_SERVICE_BROKER_SHADOW_PASS_NO_SURFACE_EXPANSION | Owner authorization required before successor |
| M25U | UMC receipt/postcondition integration | contract generalized; prose-success prevention; owner-direct no-send fixtures | M25U_UMC_RECEIPT_POSTCONDITION_PASS_NO_LIVE_SURFACE_CHANGE | Owner authorization required before successor |
| M25V | Surface Service Broker kernel | identity/session/privacy/render/delivery policy; no new surface | M25V_SURFACE_SERVICE_BROKER_KERNEL_PASS_NO_NEW_SURFACE | Owner authorization required before successor |
| M25W | Existing owner-direct path through SSB | parity with current accepted owner-direct behavior; bounded canary | M25W_OWNER_DIRECT_SSB_PARITY_PASS_BOUNDED_SCOPE | Owner authorization required before successor |
| M25X | Selected context reconstruction live canary | narrow owner-direct domain; read-only reconstruction; receipts; rollback proof | M25X_OWNER_DIRECT_CONTEXT_RECONSTRUCTION_CANARY_PASS_NO_AUTHORITY_PROMOTION | Owner authorization required before successor |
| M25Y | Full-system observation | T+0/T+2/T+8/T+24 or approved equivalent; health, dedupe, privacy, no-write | M25Y_FULL_SYSTEM_OBSERVATION_PASS | Owner authorization required before successor |
| M25Z | Production closeout | docs, rehydrator, rollback, architecture completion; no unresolved UNKNOWN | M25Z_DELIVERY_CONTEXT_BROKER_CONTRACT_REARCHITECTURE_COMPLETE | Owner authorization required before successor |

## Dependency graph summary

M25J -> M25K -> M25L -> M25M -> M25N -> M25O -> M25P -> M25Q -> M25R -> M25S -> M25T -> M25U -> M25V -> M25W -> M25X -> M25Y -> M25Z.

Delivery repair completes before durable-memory graph/broker live integration because exactly-one delivery and explicit postcondition receipts are the current systemic blocker. Source registry, graph, RSB, UMC and SSB then proceed from offline/shadow to bounded owner-direct canaries only after receipts, rollback, and owner authorization are proven.
