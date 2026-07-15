#!/usr/bin/env python3
import json, pathlib, sys
base=pathlib.Path('sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send')
json_files=[
'M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.json',
'M3N_N3_RETRY_STABILITY_PROBE_0001.json',
'M3N_N3_RETRY_STABILITY_PROBE_0002.json',
'M3N_N3_RETRY_STABILITY_PROBE_0003.json',
'M3N_N3_RETRY_STABILITY_PROBE_0004.json',
'M3N_N3_RETRY_STABILITY_SUMMARY.json',
'M3N_N2_N3_RETRY_CLOSEOUT.json',
'M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',
'M3N_N2_N3_RETRY_VALIDATION.json',
]
for name in json_files:
    obj=json.loads((base/name).read_text())
    assert obj, name
close=json.loads((base/'M3N_N2_N3_RETRY_CLOSEOUT.json').read_text())
stability=json.loads((base/'M3N_N3_RETRY_STABILITY_SUMMARY.json').read_text())
classification=json.loads((base/'M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.json').read_text())
assert close['final_status']=='PASS_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED'
assert stability['status']=='PASS_M3N_N3_RETRY_STABILITY_CONFIRMED'
assert stability['completed_probes']==4
assert classification['status']=='PASS_M3N_N3_RETRY_HEALTH_CONTEXT_OVERFLOW_CLASSIFIED_FALSE_POSITIVE'
assert close['context_overflow_count']==0 and close['context_overflow_diag_count']==0
assert close['disabled_cron_state']['enabled'] is False
assert close['telegram_send_probe_count']==0
assert close['external_send_count']==0
assert close['provider_model_shadow_call_count']==0
assert close['route_config_mutation_count']==0
assert close['durable_memory_mutation_count']==0
assert close['context_bridge_mutation_count']==0
assert close['production_authority_change_count']==0
assert close['persistence_verification_started'] is False
assert close['m3o_started'] is False and close['m4_started'] is False and close['enforcement_started'] is False
assert close['exact_next_phase']=='M3N_POST_RESTART_PERSISTENCE_VERIFICATION'
for name in ['M3N_N2_N3_RETRY_SUMMARY.md','M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.md']:
    assert (base/name).stat().st_size > 50
print('VALIDATION_PASS')
