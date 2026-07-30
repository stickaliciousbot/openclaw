# Critical Apply Contract

Status: M0-v2 contract draft — no production mutation authorised

## Contract summary

Critical production apply/deploy/install/recovery/runtime mutation is forbidden as a foreground chat/session process and is also forbidden as an ad hoc detached shell/background process. Production requires an HRL-3 observer: a pre-existing supervisor-managed service with durable journal, startup reconciliation, process/cgroup tracking, one-time authority consumption, and observer-owned postcheck/recovery.

This document is a local scaffold summary. The governing v2 materials are:

- `CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_V2_20260730.md`
- `CRITICAL_APPLY_HARNESS_V2_REVIEW_AND_STRENGTHENING_SUMMARY_20260730.md`
- `CRITICAL_APPLY_V2_ADOPTION_REVIEW_20260730.md`

The v2 architecture file is currently HOLD until the exact artifact matching SHA256 `1fecc6b04d6fce0baffcb86ea1bfd7ea5da559e83c14032d4eb95792d6f5ec3b` is received and verified.

## Production mutation boundary

No production mutation is authorized by this contract until the v2 gates through shadow promotion pass and Stick approves an exact production transaction. The current runner's `execute` command intentionally refuses mutation.

## Required v2 receipts/layout

Every transaction must be rehydratable from durable files and journal events. Required v2 receipt families include:

- spec: `transaction-spec.json`, `scope.json`, candidate/recovery/resource/environment policy files;
- authority: `approval-boundary.json`, `approval-receipt.json`, `approval-consumed.json`;
- journal: append-only `events.jsonl` plus `journal-head.json`;
- receipts: `prepare.json`, `restore-point.json`, `precheck.json`, `plan-seal.json`, `commit-locks.json`, `commit-revalidation.json`, `apply-intent.json`, `apply-spawned-blocked.json`, `apply-release.json`, `apply-exit.json`, `postcheck.json`, recovery receipts, `final-report.json`;
- projections: rebuilt `transaction.json` and `status.json`;
- logs: bounded stdout/stderr/observer logs;
- manifests and terminal seal: non-circular evidence manifest plus `terminal-seal.json`.

The superseded single `apply-start.json` model is not sufficient because it cannot prove child identity before mutation. v2 requires a blocked-child launch gate.

## Restore point contract

At mutation release, a restore point must be verified and within the configured freshness window, normally <= 3600 seconds. After release, that exact bound artifact remains eligible for recovery if release-time eligibility and current artifact integrity/seal verify. The one-hour freshness rule does not expire mid-transaction and thereby block the only safe recovery.

## Observer recovery contract

After apply failure or unknown execution, the observer must classify the execution/package/substrate/guard/recovery state vector. If the official package root is missing, empty, or incomplete and recovery is authorised, primary recovery is verified filesystem reconstruction into a same-filesystem staging directory followed by atomic rename. npm reinstall is secondary and only allowed when the package-manager substrate is independently coherent and explicitly authorised.

Hidden `.openclaw-*` staging directories are never deleted automatically and are never moved until process references prove inactive. Live-referenced hidden generations are left untouched.

## Separation contract

Package apply, Gateway restart, and functional smoke are separate transactions with separate restore points, authority envelopes, nonces, approvals, locks, and terminals. Predecessor seals may permit preparation of the next transaction but do not grant authority inheritance.

## Current implementation level

M0-v2 adoption scaffold exists:

- `scripts/critical_apply_contracts.py`
- `scripts/critical_apply_observer_runner.py`
- `scripts/critical_apply_plugins/openclaw_npm_package.py`

The runner currently supports `prepare`, `status`, `final-report`, `validate`, and an intentional `execute` refusal. It is not an HRL-3 service and cannot govern production mutation.

## Next safe milestone

M0-v2 strict contract finalization only:

- receive/verify architecture v2.0;
- strict schemas/enums;
- transition table;
- terminal derivation table;
- authority envelope and surface-set contracts;
- no mutation code beyond refusal/safe validation.

Expected terminal after completion:

`M0_PASS_CRITICAL_APPLY_V2_CONTRACT_FINALIZED_NO_MUTATION`
