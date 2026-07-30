# Critical Apply Observation Harness v2 — M3 Verified Restore and Idempotent Recovery Fixtures

Status: M3 implementation artifact. Fixture/shadow roots only; no production mutation readiness claim.

## Scope

M3 adds a verified restore/recovery subsystem for future HRL-3 observer use. It supports explicit fixture/shadow roots, stable-source restore point capture, deterministic verified-directory-tree bundles, pure restore verification, target-state classification, recovery decisions, deterministic idempotency keys, durable recovery intent, sibling staging reconstruction, damaged-target preservation, post-recovery verification, interrupted recovery reconciliation, crash/tamper matrices, and an OpenClaw-like shadow fixture.

M3 does not implement `critical_applyd`, systemd units, supervisor adapters, blocked-child launch, npm/OpenClaw mutation plugins, live process-reference inspection, Gateway lifecycle actions, cron calls, provider/model/delivery calls, real owner approval, production restore points, or production recovery.

## Source modules

- `scripts/critical_apply_filesystem.py`
- `scripts/critical_apply_restore.py`
- `scripts/critical_apply_recovery.py`

Production M3 modules use only Python standard-library filesystem APIs and existing M0-M2 contracts. They do not import `subprocess` or `multiprocessing` and do not execute external commands.

## Restore point schema

Schema: `critical_apply.restore_point.v2`.

A restore point records transaction/campaign lineage, fixture or shadow-copy source classification, canonical source identity, capture wall/monotonic times, boot/actor identity, M2 authority envelope digest, restore boundary, recovery write-set/forbidden-set digests, capture/path/mode policies, deterministic verified-directory-tree bundle path and digest, inventory manifest path and digest, file/directory/symlink/logical byte counts, fixture metadata authorities, stable-source result, maximum release-time age, and immutable=true.

A restore point is immutable evidence, not recovery authority. Recovery authority remains separately bound to M2 authority and C1 release-time eligibility.

## Restore boundary

Schema: `critical_apply.restore_boundary.v2`.

The boundary declares target root, allowed relative paths, recovery write set, guard set, forbidden set, mount/symlink/hardlink/mode/filetype policies, count/size/depth/path-length limits, and digestable policy identity. Writes outside the declared recovery write set are rejected. Guard and forbidden surfaces remain read-only.

## Bundle format

M3 uses `verified-directory-tree-v1`: no generic archive extraction, no trust in archive/member order, no unsafe extraction path, and no direct writes to the official target. Capture populates an isolated bundle tree and immutable JSON inventory. Recovery populates a sibling staging directory, verifies complete staged inventory, then publishes by same-filesystem rename.

## Stable-source capture

Regular files are opened with no-follow semantics, pre/post descriptor metadata is compared, bytes are hashed and copied through the descriptor, and copied bytes are rehashed. A second bounded source inventory rejects additions, removals, substitutions, and type/metadata changes. Default retry count is zero.

## Recovery decision and idempotency

Schema: `critical_apply.recovery_decision.v2`.

Automatic fixture recovery is permitted only for missing, empty, or incomplete targets when restore verification passes, C1 eligibility is durably recorded, recovery authority is present, recovery count is zero, guard/conflict state is clear, filesystem policy matches, and recovery write-set digest matches. Exact candidate and intact pre-generation states do not require recovery. Coherent other, conflicting, or unknown states block.

The idempotency key binds transaction ID, ordinal 1, authority envelope SHA, recovery policy SHA, restore point ID, restore manifest SHA, target identity, recovery write-set digest, release-time eligibility receipt SHA, fencing generation, and boot policy.

## Durable recovery intent

Schema: `critical_apply.recovery_intent.v2`.

Before target mutation, M3 creates immutable `receipts/recovery-intent.json`, binding transaction, idempotency key, restore point, authority envelope, release-time eligibility, target pre-state, write/guard/forbidden digests, staging path, preservation path, algorithm, filesystem identity, fencing generation/token hash, live lock-set digest, actor, wall/monotonic time, and boot ID.

No staging or publication may proceed without durable intent. A second intent is rejected.

## Reconstruction algorithm

1. Verify fixture lockset and fencing.
2. Verify recovery decision is `RECOVERY_AUTHORISED_PENDING`.
3. Create durable recovery intent.
4. Reverify restore point and bundle.
5. Verify same filesystem.
6. Create sibling staging directory.
7. Populate and fsync staging.
8. Verify staged inventory.
9. Reclassify target.
10. Preserve empty/incomplete damaged target to a transaction/idempotency-bound sibling path.
11. Publish staging to official fixture target via same-filesystem rename.
12. Fsync parent.
13. Verify restored target, guards, and forbidden surfaces.
14. Write post-recovery receipt and classify PASS.

M3 never merges file-by-file into an incomplete target and never deletes the preserved damaged generation.

## Reconciliation

`reconcile_recovery` is read-first and classifies never-started, intent-only, partial staging, complete-unverified staging, verified-not-published staging, old-target-preserved target-missing, published durability/postcheck uncertainty, PASS confirmed, conflicting generations, tampered evidence, and unknown operator hold. Unknown evidence never maps to PASS.

## Gates

- `C2_PASS_VERIFIED_RESTORE_POINT_CREATION_AND_INTEGRITY`
- `C3_PASS_BOUNDED_FILESYSTEM_RECONSTRUCTION_AND_BOUNDARY_PROOF`
- `C4_PASS_IDEMPOTENT_RECOVERY_AND_INTERRUPTED_STATE_RECONCILIATION`
- `M3_G1_PASS_RESTORE_PATH_ARCHIVE_AND_FILETYPE_SAFETY`
- `M3_G2_PASS_STABLE_SOURCE_CAPTURE_ANTI_TOU`
- `M3_G3_PASS_RECOVERY_AUTHORITY_AND_ONE_SHOT_ENFORCEMENT`
- `M3_G4_PASS_SHADOW_PACKAGE_RECOVERY_MATRIX_NO_PRODUCTION_MUTATION`

Terminal when complete: `M3_PASS_VERIFIED_RESTORE_AND_IDEMPOTENT_RECOVERY_FIXTURES`.
