#!/usr/bin/env python3
"""Focused fixtures for M3M R2 route fingerprint parity repair."""
import copy
import json
from pathlib import Path
from datetime import datetime, timezone

from m3m_route_fingerprint import canonical_fingerprint_from_config, compare_fingerprints

ROOT = Path('/home/stickai/.openclaw/workspace')
ART = ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract/m3m_r2_fingerprint_parity_repair'
NOW = lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
BASE = {
    'agents': {
        'defaults': {
            'model': {
                'primary': 'openai-codex/gpt-5.5',
                'fallbacks': ['ollama/deepseek-v4-pro:cloud']
            }
        }
    }
}

def envelope(config, config_hash='CONFIG_A'):
    fp, h = canonical_fingerprint_from_config(config)
    return {
        'production_config_sha256': config_hash,
        'route_provider_fallback_fingerprint': fp,
        'route_provider_fallback_sha256': h,
    }

def assert_case(name, ok, detail):
    return {'name': name, 'ok': bool(ok), 'detail': detail}

cases=[]
# same config -> same fingerprint
cases.append(assert_case('same_config_same_preflight_checkpoint_fingerprint', compare_fingerprints(envelope(BASE), envelope(copy.deepcopy(BASE)))['hash_match'], compare_fingerprints(envelope(BASE), envelope(copy.deepcopy(BASE)))))
# same config with default_model -> same fingerprint
cases.append(assert_case('same_config_with_default_model_same_fingerprint', envelope(BASE)['route_provider_fallback_fingerprint']['default_model']=='openai-codex/gpt-5.5' and compare_fingerprints(envelope(BASE), envelope(copy.deepcopy(BASE)))['shape_parity'], envelope(BASE)['route_provider_fallback_fingerprint']))
# missing-vs-null default_model handled canonically
missing = {'agents': {'defaults': {'model': {'fallbacks': []}}}}
nullv = {'agents': {'defaults': {'model': {'primary': None, 'fallbacks': []}}}}
missing_cmp = compare_fingerprints(envelope(missing), envelope(nullv))
cases.append(assert_case('missing_vs_null_default_model_canonical', missing_cmp['hash_match'] and missing_cmp['shape_parity'], missing_cmp))
# real default_model change -> drift detected
changed_default = copy.deepcopy(BASE); changed_default['agents']['defaults']['model']['primary']='openai-codex/gpt-5.6-terra'
default_cmp = compare_fingerprints(envelope(BASE), envelope(changed_default))
cases.append(assert_case('real_default_model_change_drift_detected', default_cmp['route_provider_fallback_drift'], default_cmp))
# real provider change -> drift detected (provider is part of default_model string)
changed_provider = copy.deepcopy(BASE); changed_provider['agents']['defaults']['model']['primary']='openai/gpt-5.5'
provider_cmp = compare_fingerprints(envelope(BASE), envelope(changed_provider))
cases.append(assert_case('real_provider_change_drift_detected', provider_cmp['route_provider_fallback_drift'], provider_cmp))
# real fallback change -> drift detected
changed_fallback = copy.deepcopy(BASE); changed_fallback['agents']['defaults']['model']['fallbacks']=['ollama/minimax-m2.7:cloud']
fallback_cmp = compare_fingerprints(envelope(BASE), envelope(changed_fallback))
cases.append(assert_case('real_fallback_change_drift_detected', fallback_cmp['route_provider_fallback_drift'], fallback_cmp))
# real route config change -> drift detected (fallback order/content are route config)
changed_route = copy.deepcopy(BASE); changed_route['agents']['defaults']['model']['fallbacks'].append('openai-codex/gpt-5.4')
route_cmp = compare_fingerprints(envelope(BASE), envelope(changed_route))
cases.append(assert_case('real_route_config_change_drift_detected', route_cmp['route_provider_fallback_drift'], route_cmp))
# field-order-only difference -> no drift
ordered_a = {'agents': {'defaults': {'model': {'primary': 'openai-codex/gpt-5.5', 'fallbacks': ['ollama/deepseek-v4-pro:cloud']}}}}
ordered_b = {'agents': {'defaults': {'model': {'fallbacks': ['ollama/deepseek-v4-pro:cloud'], 'primary': 'openai-codex/gpt-5.5'}}}}
order_cmp = compare_fingerprints(envelope(ordered_a), envelope(ordered_b))
cases.append(assert_case('field_order_only_difference_no_drift', order_cmp['hash_match'] and not order_cmp['route_provider_fallback_drift'], order_cmp))
# shape mismatch in harness -> validator failure, not production drift
pre = envelope(BASE)
chk = copy.deepcopy(pre)
del chk['route_provider_fallback_fingerprint']['default_model']
chk['route_provider_fallback_sha256']='different-because-shape-is-wrong'
shape_cmp = compare_fingerprints(pre, chk)
cases.append(assert_case('shape_mismatch_validator_failure_not_production_drift', shape_cmp['validator_shape_mismatch'] and not shape_cmp['route_provider_fallback_drift'], shape_cmp))

ok = all(c['ok'] for c in cases)
result = {
    'schema': 'umc.v1.m3m.r2.route_fingerprint_parity_fixture_results.v1',
    'generated_utc': NOW(),
    'status': 'PASS_M3M_R2_ROUTE_FINGERPRINT_PARITY_FIXTURES' if ok else 'FAIL_M3M_R2_ROUTE_FINGERPRINT_PARITY_FIXTURES',
    'cases': cases,
}
ART.mkdir(parents=True, exist_ok=True)
(ART/'M3M_R2_ROUTE_FINGERPRINT_PARITY_FIXTURE_RESULTS.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if ok else 2)
