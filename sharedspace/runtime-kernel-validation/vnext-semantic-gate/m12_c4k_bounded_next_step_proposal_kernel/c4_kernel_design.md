# M12-C4K Deterministic Bounded Proposal Kernel Design

C4K accepts approved C1/C2/C3 evidence handles plus one C4 case and emits a deterministic `PROPOSAL`, `HOLD`, or `REJECT` envelope.

Core rule: proposal drafting is not action authority. Proposal outputs are non-executing text that require owner review and approved source citations. The kernel fails closed on missing, stale, ambiguous, unapproved, arbitrary-path, memory/context/daily-memory, prompt-injection-like, execution-seeking, mutation-seeking, scheduling, production-approval, safety-critical, or unsupported reconciliation cases.

Provider/model prose is disabled for authoritative generation. Provider/model authoritative calls remain `0`.
