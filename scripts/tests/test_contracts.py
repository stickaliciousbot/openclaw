#!/usr/bin/env python3
"""M0 Critical Apply v2 contract tests.

The suite is fixture-only and does not execute production mutation, network,
provider, Gateway, cron, package-manager, or service operations.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.critical_apply_contracts import (
    ApprovalState,
    AuthorityValidityState,
    ContractError,
    EvidenceIntegrityState,
    ExecutionState,
    GuardState,
    OfficialPackageState,
    PackageSubstrateState,
    Phase,
    RecoveryState,
    StateVector,
    Surface,
    SurfaceSetName,
    SurfaceSets,
    SurfaceType,
    Terminal,
    TransactionType,
    canonical_hash,
    canonical_json_dumps,
    consume_approval_once,
    derive_terminal,
    fixture_surface_profiles,
    is_sha256,
    legal_transition_pairs,
    parse_utc_rfc3339,
    strict_json_loads,
    terminal_derivation_table,
    transition_table,
    validate_approval_binding,
    validate_authority_envelope,
    validate_restore_release,
    validate_transition,
)

FIX = Path(__file__).parent / "fixtures" / "critical_apply" / "contracts"
VALID_ENV = json.loads((FIX / "valid_authority_envelope.json").read_text())


def mutate_env(field: str, value):
    env = copy.deepcopy(VALID_ENV)
    env[field] = value
    return env


def valid_approval(env=None):
    env = env or VALID_ENV
    return {"authority_envelope_sha256": canonical_hash(env), "one_time_nonce": env["one_time_nonce"]}


class SchemaCanonicalTransitionTests(unittest.TestCase):
    group = "schema_canonical_transition"

    def test_valid_authority_schema_passes(self):
        self.assertTrue(validate_authority_envelope(VALID_ENV).ok)

    def test_duplicate_json_keys_fail_closed(self):
        with self.assertRaises(ContractError) as cm:
            strict_json_loads((FIX / "duplicate_keys.json").read_text())
        self.assertEqual(cm.exception.code, "JSON_DUPLICATE_KEY")

    def test_unknown_authority_field_fails_closed(self):
        env = mutate_env("unexpected", "boom")
        self.assertFalse(validate_authority_envelope(env).ok)

    def test_missing_required_hash_fails_closed(self):
        env = copy.deepcopy(VALID_ENV); env.pop("runner_bundle_sha256")
        self.assertFalse(validate_authority_envelope(env).ok)

    def test_invalid_hash_format_fails_closed(self):
        self.assertFalse(validate_authority_envelope(mutate_env("runner_bundle_sha256", "A" * 64)).ok)

    def test_nan_rejected_by_canonical_json(self):
        with self.assertRaises(ContractError):
            canonical_json_dumps({"x": float("nan")})

    def test_infinity_rejected_by_canonical_json(self):
        with self.assertRaises(ContractError):
            canonical_json_dumps({"x": float("inf")})

    def test_canonical_hash_stability(self):
        a = {"b": [2, 1], "a": {"z": "x"}}
        b = {"a": {"z": "x"}, "b": [2, 1]}
        self.assertEqual(canonical_hash(a), canonical_hash(b))

    def test_canonical_list_order_is_semantic(self):
        self.assertNotEqual(canonical_hash(["a", "b"]), canonical_hash(["b", "a"]))

    def test_utc_rfc3339_accepted(self):
        self.assertEqual(parse_utc_rfc3339("2026-07-30T07:55:53Z").tzinfo.utcoffset(None).total_seconds(), 0)

    def test_ambiguous_timestamp_rejected(self):
        with self.assertRaises(ContractError):
            parse_utc_rfc3339("2026-07-30 07:55:53")

    def test_phase_count_exact(self):
        self.assertEqual(len(list(Phase)), 23)

    def test_terminal_count_exact(self):
        self.assertEqual(len(list(Terminal)), 17)

    def test_transition_table_covers_every_phase(self):
        phases = {row["phase"] for row in transition_table()}
        self.assertEqual(phases, {p.value for p in Phase})

    def test_legal_transition_enumerated(self):
        self.assertTrue(validate_transition(Phase.PLAN_SEALED, Phase.AWAITING_APPROVAL).ok)

    def test_unlisted_transition_fails(self):
        self.assertFalse(validate_transition(Phase.CREATED, Phase.MUTATION_RELEASED).ok)

    def test_mutation_released_requires_blocked_child(self):
        self.assertFalse(validate_transition(Phase.APPLY_CHILD_SPAWNED_BLOCKED, Phase.MUTATION_RELEASED, {}).ok)

    def test_mutation_released_requires_commit_revalidation(self):
        ctx = {"blocked_child_identity_durable": True, "restore_valid_at_release": True, "approval_consumed_atomically": True}
        self.assertFalse(validate_transition(Phase.APPLY_CHILD_SPAWNED_BLOCKED, Phase.MUTATION_RELEASED, ctx).ok)

    def test_mutation_released_requires_release_time_restore(self):
        ctx = {"blocked_child_identity_durable": True, "commit_revalidated": True, "approval_consumed_atomically": True}
        self.assertFalse(validate_transition(Phase.APPLY_CHILD_SPAWNED_BLOCKED, Phase.MUTATION_RELEASED, ctx).ok)

    def test_mutation_released_requires_atomic_approval_consumption(self):
        ctx = {"blocked_child_identity_durable": True, "commit_revalidated": True, "restore_valid_at_release": True}
        self.assertFalse(validate_transition(Phase.APPLY_CHILD_SPAWNED_BLOCKED, Phase.MUTATION_RELEASED, ctx).ok)

    def test_mutation_release_valid_when_all_receipts_present(self):
        ctx = {"blocked_child_identity_durable": True, "commit_revalidated": True, "restore_valid_at_release": True, "approval_consumed_atomically": True}
        self.assertTrue(validate_transition(Phase.APPLY_CHILD_SPAWNED_BLOCKED, Phase.MUTATION_RELEASED, ctx).ok)

    def test_recovery_running_before_intent_rejected(self):
        self.assertFalse(validate_transition(Phase.RECOVERY_DECIDING, Phase.RECOVERY_RUNNING).ok)

    def test_pass_terminal_without_seal_rejected(self):
        self.assertFalse(validate_transition(Phase.FINALIZING, Phase.TERMINAL, {"terminal": "PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART"}).ok)

    def test_second_primary_after_consumed_approval_rejected(self):
        self.assertFalse(validate_transition(Phase.COMMIT_VALIDATED, Phase.APPLY_INTENT_DURABLE, {"approval_already_consumed_before_new_primary": True}).ok)

    def test_every_phase_has_interruption_or_successor(self):
        rows = transition_table()
        by_phase = {row["phase"]: row for row in rows}
        for phase in Phase:
            self.assertIn("valid_terminal_derivations", by_phase[phase.value])

    def test_terminal_derivation_table_present(self):
        self.assertGreaterEqual(len(terminal_derivation_table()), 14)

    def test_unknown_execution_state_never_passes(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_UNKNOWN, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertNotIn("PASS", derive_terminal(state).value)

    def test_plugin_cannot_assert_pass_without_core_seal(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_ZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=False)
        self.assertNotEqual(derive_terminal(state), Terminal.PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART)

    def test_fail_safe_requires_exact_write_set_equality(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_NONZERO, OfficialPackageState.COHERENT_PRE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True, write_set_equal_pre_state=False, no_unresolved_mutation_evidence=True)
        self.assertNotEqual(derive_terminal(state), Terminal.FAIL_SAFE_NO_MUTATION)

    def test_effective_nonzero_candidate_holds_not_rollback(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_NONZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertEqual(derive_terminal(state), Terminal.APPLY_EFFECTIVE_EXIT_NONZERO_HOLD)

    def test_valid_package_pass_requires_seal(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_ZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertEqual(derive_terminal(state), Terminal.PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART)

    def test_evidence_tamper_maps_hold(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_ZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.TAMPERED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertEqual(derive_terminal(state), Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD)

    def test_surface_profiles_fixture_contains_required_profiles(self):
        profiles = fixture_surface_profiles()
        self.assertEqual(set(profiles), {"package_apply", "package_only_recovery", "gateway_restart", "functional_smoke", "guarded_cron_update", "protected_memory_writer_state", "model_route_apply"})

    def test_surface_wildcard_requires_bounded_expansion(self):
        s = Surface("bad", SurfaceType.FILE, "/tmp/*")
        self.assertFalse(s.validate().ok)

    def test_surface_path_traversal_rejected(self):
        s = Surface("bad", SurfaceType.FILE, "/tmp/../secret")
        self.assertFalse(s.validate().ok)

    def test_conflicting_surface_set_rejected(self):
        s = Surface("same", SurfaceType.FILE, "/tmp/same")
        sets = SurfaceSets((), (s,), (), (s,), ())
        self.assertFalse(sets.validate().ok)

    def test_package_apply_restart_boundary_forbidden(self):
        profiles = fixture_surface_profiles()
        self.assertTrue(any(x["identifier"] == "gateway_restart" for x in profiles["package_apply"]["forbidden_set"]))

    def test_restart_included_in_package_apply_rejected_when_missing_forbidden(self):
        sets = SurfaceSets((), (), (), (), ())
        self.assertFalse(sets.validate(TransactionType.PACKAGE_APPLY).ok)

    def test_smoke_failure_never_triggers_package_recovery(self):
        state = StateVector(TransactionType.FUNCTIONAL_SMOKE, ExecutionState.EXIT_NONZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNCHANGED, RecoveryState.NOT_AUTHORISED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, functional_smoke_authorised=True, terminal_seal_valid=True)
        self.assertEqual(derive_terminal(state), Terminal.FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY)

    def test_all_unlisted_transition_count_large(self):
        legal = legal_transition_pairs()
        self.assertLess(len(legal), len(list(Phase)) * len(list(Phase)))


class AuthorityApprovalDriftTests(unittest.TestCase):
    group = "authority_approval_drift"

    def test_valid_approval_binding_passes(self):
        self.assertTrue(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z").ok)

    def test_expired_approval_fails(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T09:00:00Z").ok)

    def test_wrong_nonce_fails(self):
        approval = valid_approval(); approval["one_time_nonce"] = "wrong"
        self.assertFalse(validate_approval_binding(VALID_ENV, approval, now_utc="2026-07-30T08:00:00Z").ok)

    def test_reused_nonce_fails(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", consumed_nonces={VALID_ENV["one_time_nonce"]}).ok)

    def test_authority_hash_mismatch_fails(self):
        approval = valid_approval(); approval["authority_envelope_sha256"] = "0" * 64
        self.assertFalse(validate_approval_binding(VALID_ENV, approval, now_utc="2026-07-30T08:00:00Z").ok)

    def test_candidate_change_invalidates(self):
        observed = {"candidate_authority_sha256": "0" * 64}
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes=observed).ok)

    def test_argv_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"exact_argv_exec_spec_sha256": "0" * 64}).ok)

    def test_environment_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"environment_policy_sha256": "0" * 64}).ok)

    def test_runner_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"runner_bundle_sha256": "0" * 64}).ok)

    def test_contract_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"contract_bundle_sha256": "0" * 64}).ok)

    def test_plugin_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"plugin_bundle_sha256": "0" * 64}).ok)

    def test_interpreter_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"interpreter_identity_sha256": "0" * 64}).ok)

    def test_supervisor_unit_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"supervisor_unit_sha256": "0" * 64}).ok)

    def test_restore_point_change_invalidates_hash_binding(self):
        env = mutate_env("restore_point_id", "different")
        self.assertNotEqual(canonical_hash(env), canonical_hash(VALID_ENV))

    def test_restore_manifest_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"restore_manifest_sha256": "0" * 64}).ok)

    def test_stale_restore_at_release_blocks(self):
        r = validate_restore_release("2026-07-30T07:00:00Z", "2026-07-30T08:00:01Z", created_monotonic_ns=1, release_monotonic_ns=2)
        self.assertFalse(r.ok)

    def test_restore_fresh_at_release_valid(self):
        r = validate_restore_release("2026-07-30T07:00:00Z", "2026-07-30T07:59:59Z", created_monotonic_ns=1, release_monotonic_ns=2)
        self.assertTrue(r.ok)

    def test_restore_after_one_hour_remains_eligible_if_valid_at_release(self):
        r = validate_restore_release("2026-07-30T07:00:00Z", "2026-07-30T07:30:00Z", created_monotonic_ns=1, release_monotonic_ns=2)
        self.assertTrue(r.details["remains_recovery_eligible_after_one_hour"])

    def test_clock_rollback_blocks_restore(self):
        self.assertFalse(validate_restore_release("2026-07-30T08:00:00Z", "2026-07-30T07:59:59Z", created_monotonic_ns=2, release_monotonic_ns=1).ok)

    def test_missing_monotonic_evidence_blocks_same_boot(self):
        self.assertFalse(validate_restore_release("2026-07-30T07:00:00Z", "2026-07-30T07:30:00Z").ok)

    def test_pre_state_change_invalidates(self):
        self.assertFalse(validate_approval_binding(VALID_ENV, valid_approval(), now_utc="2026-07-30T08:00:00Z", observed_hashes={"pre_state_fingerprint_sha256": "0" * 64}).ok)

    def test_allowed_field_level_drift_can_hold_or_pass_terminal(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_ZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.ALLOWED_DRIFT, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertEqual(derive_terminal(state), Terminal.PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART)

    def test_forbidden_drift_blocks(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_ZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.FORBIDDEN_DRIFT, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertEqual(derive_terminal(state), Terminal.FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED)

    def test_unknown_drift_never_passes(self):
        state = StateVector(TransactionType.PACKAGE_APPLY, ExecutionState.EXIT_ZERO, OfficialPackageState.COHERENT_CANDIDATE_GENERATION, PackageSubstrateState.COHERENT, GuardState.UNKNOWN, RecoveryState.NOT_REQUIRED, EvidenceIntegrityState.COMPLETE_SEALED, AuthorityValidityState.VALID_CONSUMED, terminal_seal_valid=True)
        self.assertNotIn("PASS", derive_terminal(state).value)

    def test_approval_consumption_once(self):
        state = ApprovalState(canonical_hash(VALID_ENV), VALID_ENV["one_time_nonce"])
        consumed = consume_approval_once(state, phase=Phase.MUTATION_RELEASED, receipt_sha256="a" * 64)
        self.assertTrue(consumed.consumed)

    def test_consumed_approval_replay_rejected(self):
        state = ApprovalState(canonical_hash(VALID_ENV), VALID_ENV["one_time_nonce"], consumed=True)
        with self.assertRaises(ContractError):
            consume_approval_once(state, phase=Phase.MUTATION_RELEASED, receipt_sha256="a" * 64)

    def test_consumption_wrong_phase_rejected(self):
        state = ApprovalState(canonical_hash(VALID_ENV), VALID_ENV["one_time_nonce"])
        with self.assertRaises(ContractError):
            consume_approval_once(state, phase=Phase.COMMIT_VALIDATED, receipt_sha256="a" * 64)

    def test_max_primary_mutations_must_be_one(self):
        self.assertFalse(validate_authority_envelope(mutate_env("max_primary_mutations", 2)).ok)

    def test_restart_authorised_flag_is_boolean(self):
        self.assertFalse(validate_authority_envelope(mutate_env("restart_authorised", "false")).ok)

    def test_functional_smoke_authorised_flag_is_boolean(self):
        self.assertFalse(validate_authority_envelope(mutate_env("functional_smoke_authorised", "false")).ok)

    def test_uppercase_hash_rejected(self):
        self.assertFalse(is_sha256("A" * 64))

    def test_package_restart_smoke_authority_separation_defaults_false(self):
        self.assertFalse(VALID_ENV["restart_authorised"])
        self.assertFalse(VALID_ENV["functional_smoke_authorised"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
