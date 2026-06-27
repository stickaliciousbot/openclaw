#!/usr/bin/env python3
"""Read-only guard for consuming the frozen M12-C1K evidence packet.

This script is the intended preflight for any downstream C1R16 replay. It runs
C1K kernel tests in memory, checks the frozen C1K artifacts on disk, and verifies
that no C1K evidence file changes during validation. It never rewrites the C1K
artifact directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0, str(ROOT / 'scripts'))

from test_m12_c1_artifact_qa_kernel import read_only_validate  # noqa: E402

CURRENT_ACCEPTED_C1K_EVIDENCE_SHA256 = '097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd'
PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA256 = '50527805a332a4ebecb8737bdb82354d9503edca2986b71fba536c20c0e27e75'


def guard_report(purpose: str) -> dict[str, Any]:
    validation = read_only_validate(CURRENT_ACCEPTED_C1K_EVIDENCE_SHA256)
    report = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1k.read_only_consumption_guard.v1',
        'purpose': purpose,
        'status': 'PASS' if validation.get('status') == 'PASS' else 'BLOCKED',
        'c1k_consumption_mode': 'read_only_validation_only',
        'current_accepted_c1k_evidence_sha256': CURRENT_ACCEPTED_C1K_EVIDENCE_SHA256,
        'prior_superseded_c1k_evidence_sha256': PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA256,
        'prior_sha_disposition': 'superseded_by_accepted_accidental_local_rerun; not valid for new C1R16 consumption',
        'c1r16_may_consume_c1k': validation.get('status') == 'PASS',
        'c1k_artifact_regenerated': bool(validation.get('artifact_hashes_changed')),
        'full_c1_readiness_rerun_performed': False,
        'c1r16_rerun_performed': False,
        'provider_model_calls': 0,
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'runtime_authority_mutated': False,
        'validation': validation,
    }
    if report['status'] != 'PASS':
        report['blockers'] = validation.get('failures', ['read_only_validation_failed'])
    else:
        report['blockers'] = []
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='M12-C1K read-only consumption guard')
    parser.add_argument('--purpose', default='c1r16_preflight', choices=['c1r16_preflight', 'freeze_validation', 'manual_read_only_check'])
    parser.add_argument('--report-out', default=None, help='optional path for guard report outside the frozen C1K artifact directory')
    args = parser.parse_args(argv)

    report = guard_report(args.purpose)
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report_out:
        out = Path(args.report_out)
        c1k_dir = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate/m12_c1k_deterministic_artifact_qa_kernel'
        try:
            out_resolved = out.resolve()
            c1k_resolved = c1k_dir.resolve()
            if c1k_resolved == out_resolved or c1k_resolved in out_resolved.parents:
                raise SystemExit('refusing to write guard report inside frozen C1K artifact directory')
        except FileNotFoundError:
            pass
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    print(text, end='')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
