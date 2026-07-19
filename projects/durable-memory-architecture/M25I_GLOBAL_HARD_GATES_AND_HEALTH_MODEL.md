# M25I Global Hard Gates and Health Model

## Hard gates

| ID | Group | Rule | Failure |
| --- | --- | --- | --- |
| M25I_HG_001 | Authority | no model/graph/vector/session summary becomes authority | STOP_PRESERVE_EVIDENCE |
| M25I_HG_002 | Authority | consequential claims require exact source/version/span | STOP_PRESERVE_EVIDENCE |
| M25I_HG_003 | Authority | UMC success requires valid receipt | STOP_PRESERVE_EVIDENCE |
| M25I_HG_004 | ReadOnly | no recall-time Ledger writes | STOP_PRESERVE_EVIDENCE |
| M25I_HG_005 | ReadOnly | no Context Bridge authority mutation | STOP_PRESERVE_EVIDENCE |
| M25I_HG_006 | ReadOnly | graph/index projections disposable | STOP_PRESERVE_EVIDENCE |
| M25I_HG_007 | ReadOnly | protected state hashes stable during read paths | STOP_PRESERVE_EVIDENCE |
| M25I_HG_008 | Privacy | no raw private packets in tracked evidence | STOP_PRESERVE_EVIDENCE |
| M25I_HG_009 | Privacy | no tokens/auth headers/raw chat/account/message IDs | STOP_PRESERVE_EVIDENCE |
| M25I_HG_010 | Privacy | surface disclosure matrix enforced | STOP_PRESERVE_EVIDENCE |
| M25I_HG_011 | Privacy | source content cannot override policy | STOP_PRESERVE_EVIDENCE |
| M25I_HG_012 | BrokerIntegrity | grant required | STOP_PRESERVE_EVIDENCE |
| M25I_HG_013 | BrokerIntegrity | wrong scope/surface/session denied | STOP_PRESERVE_EVIDENCE |
| M25I_HG_014 | BrokerIntegrity | receipt request/grant/packet binding exact | STOP_PRESERVE_EVIDENCE |
| M25I_HG_015 | BrokerIntegrity | duplicate/forged/replayed receipt denied | STOP_PRESERVE_EVIDENCE |
| M25I_HG_016 | BrokerIntegrity | bypass count zero once enforced | STOP_PRESERVE_EVIDENCE |
| M25I_HG_017 | Delivery | delivery-required job cannot end in bare NO_REPLY | STOP_PRESERVE_EVIDENCE |
| M25I_HG_018 | Delivery | delivery requires boundary allow | STOP_PRESERVE_EVIDENCE |
| M25I_HG_019 | Delivery | boundary hold/reject cannot deliver | STOP_PRESERVE_EVIDENCE |
| M25I_HG_020 | Delivery | sanitized payload required | STOP_PRESERVE_EVIDENCE |
| M25I_HG_021 | Delivery | idempotency key required | STOP_PRESERVE_EVIDENCE |
| M25I_HG_022 | Delivery | duplicate delivery zero | STOP_PRESERVE_EVIDENCE |
| M25I_HG_023 | Delivery | delivery result receipt required | STOP_PRESERVE_EVIDENCE |
| M25I_HG_024 | RuntimeSafety | handler dormant/unarmed outside proof window | STOP_PRESERVE_EVIDENCE |
| M25I_HG_025 | RuntimeSafety | proof job disabled/inert first | STOP_PRESERVE_EVIDENCE |
| M25I_HG_026 | RuntimeSafety | no recurring retry | STOP_PRESERVE_EVIDENCE |
| M25I_HG_027 | RuntimeSafety | proof job removed afterward | STOP_PRESERVE_EVIDENCE |
| M25I_HG_028 | RuntimeSafety | Gateway health before/after | STOP_PRESERVE_EVIDENCE |
| M25I_HG_029 | RuntimeSafety | route/model/fallback/memory route unchanged | STOP_PRESERVE_EVIDENCE |
| M25I_HG_030 | EvidenceGit | evidence manifest verified | STOP_PRESERVE_EVIDENCE |
| M25I_HG_031 | EvidenceGit | privacy scan PASS | STOP_PRESERVE_EVIDENCE |
| M25I_HG_032 | EvidenceGit | closeout not UNKNOWN | STOP_PRESERVE_EVIDENCE |
| M25I_HG_033 | EvidenceGit | tracked diff allowlist | STOP_PRESERVE_EVIDENCE |
| M25I_HG_034 | EvidenceGit | no DB/WAL/SHM/telemetry/private runtime state | STOP_PRESERVE_EVIDENCE |
| M25I_HG_035 | EvidenceGit | unrelated workspace dirt excluded through scoped commit/push | STOP_PRESERVE_EVIDENCE |
| M25I_HG_036 | MilestoneControl | no automatic successor | STOP_PRESERVE_EVIDENCE |
| M25I_HG_037 | MilestoneControl | no production mutation without owner approval | STOP_PRESERVE_EVIDENCE |
| M25I_HG_038 | MilestoneControl | rollback/off-switch proven before apply | STOP_PRESERVE_EVIDENCE |
| M25I_HG_039 | MilestoneControl | first failed hard gate stops work and preserves evidence | STOP_PRESERVE_EVIDENCE |

## Health states

- **GREEN:** all required checks pass; milestone may continue inside approved scope.
- **YELLOW:** safe degradation only; no authority/delivery success claims; milestone must declare allowed degradation.
- **RED:** fail closed, stop, preserve evidence, no successor.

## Health groups

| Group | Checks |
| --- | --- |
| Canonical data | Ledger integrity, source registry integrity, source resolution, graph parity, index freshness |
| Runtime services | Gateway live/readiness, RSB live/readiness, reconstruction service smoke, contract hash compatibility, receipt round trip, timeout/cancel |
| UMC | required service/action fixtures, postcondition verification, prose-success rejection, HOLD rendering |
| Surface/delivery | SSB policy intersection, render/redaction, delivery/dedupe, Telegram result, cross-surface denial |
| Safety | no-write sentinels, privacy/injection, authority bypass, duplicate receipt, duplicate delivery, hydration strict status |

## SRTR target gates and fixture health checks

| ID | Group | Rule | Failure |
| --- | --- | --- | --- |
| HG_TARGET_01 | Target | every external delivery requires a valid, unexpired SurfaceResponseTargetGrant | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_02 | Target | surface permission does not imply target permission | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_03 | Privacy | raw provider target identifiers never appear in tracked schemas, fixtures, evidence, Context Bridge, UMC prose or reconstruction packets | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_04 | Target | target aliases resolve only through the later private runtime registry | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_05 | Replay | cross-user/session/surface and stale-grant replay are denied | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_06 | LeastPrivilege | target resolution may narrow SSB permission but never broaden it | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_07 | Target | no automatic fallback to another target | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_08 | Binding | target grant, payload envelope and delivery result share idempotency key, surface, policy epoch and scoped grant chain | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_09 | Dedupe | current M25 delivery grants allow at most one delivery | STOP_PRESERVE_EVIDENCE |
| HG_TARGET_10 | Evidence | evidence uses keyed rotating non-correlatable aliases, not raw target IDs or stable public hashes | STOP_PRESERVE_EVIDENCE |

Fixture-only health checks HC_TARGET_01..HC_TARGET_10 cover private registry design/permissions, exact alias resolution, identity/session/capability binding, expiry/epoch, wrong-scope denial, HOLD-on-missing-alias/no-fallback, raw leakage scan, replay-after-use/expiry rejection, and adapter rejection without target grant.
