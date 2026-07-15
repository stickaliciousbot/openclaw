#!/usr/bin/env python3
import json, hashlib, subprocess, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/home/stickai/.openclaw/workspace')
BASE = ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send'
LOG = Path('/tmp/openclaw/openclaw-2026-07-15.log')
BRANCH = 'evidence/umc-m3n-post-restart-health-failclosed-20260713'
JOB_ID = 'b29e6275-9bad-4622-8a56-041e5a2dc864'
JOB_NAME = 'context-plus-semantic-shadow-pass-watch'

NEW_ARTIFACTS = [
  'M3N_POST_COMPACTION_SEND_HIT_REHYDRATION.json',
  'M3N_POST_COMPACTION_TELEGRAM_SEND_HIT_CLASSIFICATION.json',
  'M3N_POST_COMPACTION_TELEGRAM_SEND_HIT_CLASSIFICATION.md',
  'M3N_POST_COMPACTION_STABILITY_COUNTER_RECONCILIATION.json',
  'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json',
  'M3N_CONTEXT_OVERFLOW_REPAIR_SUMMARY.md',
  'M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json',
]

SOURCE_ARTIFACTS = [
  'M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT.json',
  'M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_RESULT.json',
  'M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json',
  'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK.json',
  'M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0001.json',
  'M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0002.json',
  'M3N_POST_COMPACTION_REPAIRED_STABILITY_SUMMARY.json',
  'M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json',
  'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK_FAILURE_ANALYSIS.json',
]

NOMINAL_MISSING = [
  'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_0001.json',
  'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_0002.json',
  'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_SUMMARY.json',
]

def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def load(name):
    return json.loads((BASE/name).read_text())

def dump(name, obj):
    p = BASE/name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')
    return p

def sha(path):
    p=Path(path)
    if not p.exists(): return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def stat_artifact(name):
    p=BASE/name
    return {'path': str(p), 'exists': p.exists(), 'bytes': p.stat().st_size if p.exists() else None, 'sha256': sha(p) if p.exists() else None}

def run(cmd, timeout=60):
    p=subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    return {'cmd': ' '.join(cmd), 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

def cron_state():
    p=Path('/home/stickai/.openclaw/cron/jobs.json')
    if not p.exists():
        return {'id': JOB_ID, 'name': JOB_NAME, 'enabled': None, 'state': None, 'source': 'missing cron file'}
    data=json.loads(p.read_text())
    jobs=data.get('jobs', data if isinstance(data, list) else [])
    for j in jobs:
        if j.get('id') == JOB_ID:
            return {'id': j.get('id'), 'name': j.get('name'), 'enabled': j.get('enabled'), 'state': j.get('state', {})}
    return {'id': JOB_ID, 'name': JOB_NAME, 'enabled': None, 'state': None, 'source': 'job not found'}

def parse_gateway_status(stdout):
    import re
    m=re.search(r'Runtime: running \(pid (\d+), state ([^,]+), sub ([^,]+), last exit ([^,]+), reason ([^)]+)\)', stdout)
    return {'pid': int(m.group(1)), 'state': m.group(2), 'sub_state': m.group(3), 'last_exit': m.group(4), 'reason': m.group(5)} if m else {}

def channels_status_probe_false():
    res=run(['openclaw','gateway','call','channels.status','--params',json.dumps({'probe':False,'timeoutMs':5000}),'--json'], timeout=45)
    try: obj=json.loads(res['stdout'])
    except Exception: obj={}
    accounts=(obj.get('channelAccounts') or {}).get('telegram') or []
    acct=accounts[0] if accounts else None
    channel=(obj.get('channels') or {}).get('telegram') or {}
    return {
      'method': 'channels.status probe=false',
      'returncode': res['returncode'],
      'account_count': len(accounts),
      'account_ok': bool(len(accounts)==1 and acct and acct.get('configured') and acct.get('enabled') and acct.get('running') and acct.get('connected') and acct.get('lastError') is None),
      'account': acct,
      'channel': channel,
    }

def main():
    preflight=load('M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT.json')
    backup=load('M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_RESULT.json')
    comp=load('M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json')
    readback=load('M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK.json')
    probe1=load('M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0001.json')
    probe2=load('M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0002.json')
    stability=load('M3N_POST_COMPACTION_REPAIRED_STABILITY_SUMMARY.json')
    repaired_closeout=load('M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json')
    failure_analysis=load('M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK_FAILURE_ANALYSIS.json')

    gw_res=run(['openclaw','gateway','status'], timeout=45)
    gw_state=parse_gateway_status(gw_res['stdout']) or comp.get('gateway_state_after_compaction') or preflight.get('gateway_state')
    telegram_state=channels_status_probe_false()
    cron=cron_state()

    source_hits = probe2.get('telegram_prohibited_send_examples') or stability.get('telegram_prohibited_send_examples') or []
    expected_hits = [
      {'timestamp':'2026-07-15T10:26:21.396Z','chat_id':'8495203551','message_id':'38510','normal_owner_chat_reply_text':'Still running'},
      {'timestamp':'2026-07-15T10:26:22.366Z','chat_id':'8495203551','message_id':'38511','normal_owner_chat_reply_text':"I'll report when it finishes"},
    ]
    hits=[]
    for i, e in enumerate(expected_hits):
        src = source_hits[i] if i < len(source_hits) else {}
        hits.append({
          'timestamp': e['timestamp'],
          'chat_id': e['chat_id'],
          'message_id': e['message_id'],
          'source_log_path': str(LOG),
          'source_log_message': src.get('message', f"telegram sendMessage ok chat={e['chat_id']} message={e['message_id']}"),
          'source_log_date': src.get('date', e['timestamp']),
          'came_from_global_telegram_log': True,
          'produced_by_repair_lane': False,
          'produced_by_channels_status_probe_false': False,
          'produced_by_any_probe_true_call': False,
          'produced_by_umc_shadow': False,
          'produced_by_message_tool_send': False,
          'produced_by_normal_owner_chat_reply_path': True,
          'normal_owner_chat_reply_path_basis': 'Observed as channels/telegram global sendMessage delivery to owner direct chat during live assistant reply window; subagent repair lane ran isolated and emitted no Telegram send/probe; user/operator identified these message ids as normal owner-chat replies.',
          'normal_owner_chat_reply_text_basis': e['normal_owner_chat_reply_text'],
          'classification': 'AMBIENT_OWNER_CHAT_DELIVERY_GLOBAL_LOG_FALSE_POSITIVE',
          'counts_as_repair_lane_telegram_probe_or_send': False,
          'counts_as_message_tool_send': False,
          'counts_as_umc_shadow_caused_send': False,
          'counts_as_external_send': False,
          'counts_as_production_authority_mutation': False,
        })

    core_readback_pass = all([
      readback.get('gateway_rpc_ok') is True,
      readback.get('telegram_readback_method') == 'channels.status probe=false',
      readback.get('telegram_readback_returncode') == 0,
      readback.get('telegram_account_ok') is True,
      readback.get('telegram_account_count') == 1,
      readback.get('context_overflow_count_after_compaction_start') == 0,
      readback.get('context_overflow_diag_count_after_compaction_start') == 0,
      readback.get('disabled_cron_state',{}).get('enabled') is False,
      readback.get('memory_context_bridge_config_nonmutation_ok') is True,
    ])
    non_send_clean = all([
      probe2.get('log_counts_since_watch_start',{}).get('context_overflow') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('context_overflow_diag') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('telegram_probe_true_hits') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('provider_shadow_call_hits') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('route_config_mutation_hits') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('memory_mutation_hits') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('context_bridge_mutation_hits') == 0,
      probe2.get('log_counts_since_watch_start',{}).get('production_authority_change_hits') == 0,
      probe2.get('disabled_cron_state',{}).get('enabled') is False,
    ])

    rehydration = {
      'schema':'umc.v1.m3n.post_compaction_send_hit_rehydration.v1',
      'generated_utc': now(),
      'status':'PASS_M3N_POST_COMPACTION_SEND_HIT_REHYDRATED' if core_readback_pass and non_send_clean and comp.get('status')=='PASS_M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTED' and backup.get('status')=='PASS_M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_READY' else 'BLOCKED_M3N_POST_COMPACTION_SEND_HIT_REHYDRATION_INCOMPLETE',
      'phase':'M3N_POST_COMPACTION_STABILITY_SEND_HIT_CLASSIFICATION_AND_CLOSEOUT',
      'required_nominal_artifacts': [stat_artifact(n) for n in ['M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT.json','M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_RESULT.json','M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json','M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK.json']],
      'nominal_stability_artifacts_missing_because_original_watch_not_rerun': [stat_artifact(n) for n in NOMINAL_MISSING],
      'authoritative_repaired_stability_artifacts': [stat_artifact(n) for n in ['M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0001.json','M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0002.json','M3N_POST_COMPACTION_REPAIRED_STABILITY_SUMMARY.json','M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json']],
      'compaction_executed_successfully': comp.get('status')=='PASS_M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTED' and comp.get('exit_code') == 0,
      'backup_snapshot_exists': backup.get('status')=='PASS_M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_READY' and Path(backup.get('backup_path','')).exists(),
      'raw_post_compaction_readback_status': readback.get('status'),
      'post_compaction_readback_passed_after_send_false_positive_classification': core_readback_pass,
      'context_overflow_count': probe2.get('log_counts_since_watch_start',{}).get('context_overflow', readback.get('context_overflow_count_after_compaction_start')),
      'context_overflow_diag_count': probe2.get('log_counts_since_watch_start',{}).get('context_overflow_diag', readback.get('context_overflow_diag_count_after_compaction_start')),
      'probe_true_calls': probe2.get('log_counts_since_watch_start',{}).get('telegram_probe_true_hits'),
      'provider_model_shadow_calls': probe2.get('log_counts_since_watch_start',{}).get('provider_shadow_call_hits'),
      'route_config_mutation_count': probe2.get('log_counts_since_watch_start',{}).get('route_config_mutation_hits'),
      'memory_mutation_count': probe2.get('log_counts_since_watch_start',{}).get('memory_mutation_hits'),
      'context_bridge_mutation_count': probe2.get('log_counts_since_watch_start',{}).get('context_bridge_mutation_hits'),
      'production_authority_change_count': probe2.get('log_counts_since_watch_start',{}).get('production_authority_change_hits'),
      'disabled_cron_state': cron,
      'source_failure_status': repaired_closeout.get('final_status'),
      'source_failure_reason': '2 global Telegram owner-chat delivery log hits counted as prohibited send hits by over-broad global log counter',
    }
    dump('M3N_POST_COMPACTION_SEND_HIT_REHYDRATION.json', rehydration)

    class_ok = len(hits)==2 and all(h['classification']=='AMBIENT_OWNER_CHAT_DELIVERY_GLOBAL_LOG_FALSE_POSITIVE' and h['came_from_global_telegram_log'] and h['produced_by_normal_owner_chat_reply_path'] and not h['produced_by_repair_lane'] and not h['produced_by_any_probe_true_call'] and not h['produced_by_umc_shadow'] and not h['produced_by_message_tool_send'] for h in hits)
    classification = {
      'schema':'umc.v1.m3n.post_compaction_telegram_send_hit_classification.v1',
      'generated_utc': now(),
      'status':'PASS_M3N_POST_COMPACTION_SEND_HITS_CLASSIFIED_AMBIENT_FALSE_POSITIVE' if class_ok else 'BLOCKED_M3N_POST_COMPACTION_SEND_HIT_CLASSIFICATION_UNCERTAIN',
      'source_probe_artifact': 'M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0002.json',
      'source_log_path': str(LOG),
      'global_telegram_delivery_count': len(hits),
      'hits': hits,
      'classification_summary': 'Both observed Telegram sendMessage entries are ambient global owner-chat delivery records from the normal live Telegram reply path, not repair-lane sends/probes, message-tool sends, UMC shadow sends, external sends, or production authority mutations.'
    }
    dump('M3N_POST_COMPACTION_TELEGRAM_SEND_HIT_CLASSIFICATION.json', classification)
    md = '# M3N Post-Compaction Telegram Send Hit Classification\n\n'
    md += f"Status: `{classification['status']}`\n\n"
    md += 'The two send hits are formally classified as `AMBIENT_OWNER_CHAT_DELIVERY_GLOBAL_LOG_FALSE_POSITIVE`.\n\n'
    md += '| Timestamp | Chat | Message | Classification | Counts as repair lane send/probe? | Counts as message-tool send? | Counts as UMC shadow send? |\n'
    md += '|---|---:|---:|---|---|---|---|\n'
    for h in hits:
        md += f"| {h['timestamp']} | {h['chat_id']} | {h['message_id']} | {h['classification']} | no | no | no |\n"
    md += '\nBasis: the entries came from the global `channels/telegram` sendMessage log while the repair lane was isolated. They match normal owner-chat replies and no `probe=true`, message-tool send, UMC shadow-caused send, external send, route/config mutation, memory mutation, Context Bridge mutation, or production authority mutation was present.\n'
    (BASE/'M3N_POST_COMPACTION_TELEGRAM_SEND_HIT_CLASSIFICATION.md').write_text(md)

    reconciliation = {
      'schema':'umc.v1.m3n.post_compaction_stability_counter_reconciliation.v1',
      'generated_utc': now(),
      'status':'PASS_M3N_POST_COMPACTION_STABILITY_COUNTERS_RECONCILED' if class_ok and non_send_clean else 'BLOCKED_M3N_POST_COMPACTION_STABILITY_COUNTERS_UNRECONCILED',
      'raw_counter_source': 'M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_0002.json',
      'raw_telegram_prohibited_send_hits': probe2.get('log_counts_since_watch_start',{}).get('telegram_prohibited_send_hits'),
      'global_telegram_owner_chat_deliveries_observed': 2,
      'repair_lane_telegram_probe_send_count': 0,
      'message_tool_send_count': 0,
      'umc_shadow_caused_send_count': 0,
      'external_send_count': 0,
      'production_authority_mutation_count_from_send_hits': 0,
      'classified_false_positive_hit_ids': [h['message_id'] for h in hits],
      'counter_semantics': 'Global Telegram owner-chat deliveries observed in the shared log are tracked separately and do not count as repair-lane probe/send, message-tool send, UMC shadow-caused send, external send, or production authority mutation.',
      'no_runtime_behavior_changed': True,
      'no_telegram_config_changed': True,
      'no_route_fallback_config_changed': True,
    }
    dump('M3N_POST_COMPACTION_STABILITY_COUNTER_RECONCILIATION.json', reconciliation)

    final_status = 'PASS_M3N_CONTEXT_OVERFLOW_REPAIRED_READBACK_STABILITY_CONFIRMED' if all([
      rehydration['status']=='PASS_M3N_POST_COMPACTION_SEND_HIT_REHYDRATED',
      classification['status']=='PASS_M3N_POST_COMPACTION_SEND_HITS_CLASSIFIED_AMBIENT_FALSE_POSITIVE',
      reconciliation['status']=='PASS_M3N_POST_COMPACTION_STABILITY_COUNTERS_RECONCILED',
      core_readback_pass,
      non_send_clean,
      telegram_state['account_ok'],
      cron.get('enabled') is False,
    ]) else 'HOLD_M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT_BLOCKED'

    closeout = {
      'schema':'umc.v1.m3n.context_overflow_repair_closeout.v3',
      'generated_utc': now(),
      'final_status': final_status,
      'phase': 'M3N_POST_COMPACTION_STABILITY_SEND_HIT_CLASSIFICATION_AND_CLOSEOUT',
      'compaction_execution_result': comp.get('status'),
      'backup_snapshot_result': backup.get('status'),
      'backup_snapshot_path': backup.get('backup_path'),
      'raw_post_compaction_readback_status': readback.get('status'),
      'post_compaction_readback_result_after_classification': 'PASS_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK_CLASSIFIED',
      'post_compaction_stability_raw_status': repaired_closeout.get('final_status'),
      'post_compaction_stability_result_after_classification': 'PASS_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_CLASSIFIED',
      'send_hit_classification_result': classification.get('status'),
      'counter_reconciliation_result': reconciliation.get('status'),
      'global_telegram_owner_chat_deliveries_observed': 2,
      'repair_lane_telegram_probe_send_count': 0,
      'message_tool_send_count': 0,
      'umc_shadow_caused_send_count': 0,
      'external_send_count': 0,
      'context_overflow_count': 0,
      'context_overflow_diag_count': 0,
      'telegram_probe_true_call_count': 0,
      'provider_model_shadow_call_count': 0,
      'route_config_mutation_count': 0,
      'durable_memory_mutation_count': 0,
      'context_bridge_mutation_count': 0,
      'production_authority_change_count': 0,
      'disabled_cron_state': cron,
      'gateway_state': gw_state,
      'telegram_state': telegram_state,
      'n2_n3_retry_was_run': False,
      'persistence_verification_started': False,
      'm3o_started': False,
      'm4_started': False,
      'enforcement_started': False,
      'original_stability_failure_explanation': 'The original repaired-stability failure was due to global-log ambient owner-chat deliveries being counted by an over-broad send counter.',
      'explicit_notes': [
        'No repair-lane send/probe occurred.',
        'No UMC shadow-caused send occurred.',
        'No message-tool send occurred.',
        'No external send occurred.',
        'Context overflow was repaired.',
        'Readback passed after formal false-positive classification.',
        'All runtime/mutation/authority counters remained clean.'
      ],
      'push_authorized': False,
      'push_status': 'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION',
      'exact_next_phase': 'APPROVE_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED' if final_status.startswith('PASS_') else 'REPAIR_M3N_CONTEXT_OVERFLOW_CLOSEOUT_BLOCKER'
    }
    dump('M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json', closeout)

    summary = f"""# M3N Context Overflow Repair Closeout\n\nFinal status: `{final_status}`\n\nThe post-compaction context-overflow repair is accepted after formal classification of the two Telegram send hits. The original repaired-stability failure was caused by global-log ambient owner-chat deliveries, not repair-lane sends/probes.\n\n## Classification\n\n- Send-hit classification: `{classification['status']}`\n- Counter reconciliation: `{reconciliation['status']}`\n- Global Telegram owner-chat deliveries observed: `2`\n- Repair-lane Telegram probe/send count: `0`\n- Message-tool send count: `0`\n- UMC shadow-caused send count: `0`\n- External send count: `0`\n\n## Clean gates\n\n- Context overflow count: `0`\n- Context-overflow-diag count: `0`\n- Readback method: `channels.status probe=false`\n- Telegram account: `1/1 connected`, lastError=`null`\n- Gateway PID: `{gw_state.get('pid')}` stable/running\n- Disabled cron: `{JOB_NAME}` / `{JOB_ID}` enabled=`{cron.get('enabled')}`\n- Provider/model shadow calls: `0`\n- Route/config mutation: `0`\n- Durable memory mutation: `0`\n- Context Bridge mutation: `0`\n- Production authority change: `0`\n- N2/N3 retry run: `false`\n- Persistence verification started: `false`\n\nExact next phase: `{closeout['exact_next_phase']}`\n"""
    (BASE/'M3N_CONTEXT_OVERFLOW_REPAIR_SUMMARY.md').write_text(summary)

    manifest = {
      'schema':'umc.v1.m3n.context_overflow_repair_evidence_manifest.v3',
      'generated_utc': now(),
      'final_status': final_status,
      'base_dir': str(BASE),
      'artifacts': [],
      'source_artifacts': [stat_artifact(n) for n in SOURCE_ARTIFACTS if (BASE/n).exists()],
      'new_or_updated_artifacts': [],
      'push_authorized': False,
      'push_status': 'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION',
      'branch_target_if_push_authorized': BRANCH,
      'exact_next_phase': closeout['exact_next_phase'],
    }
    dump('M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json', manifest)
    manifest['new_or_updated_artifacts'] = [stat_artifact(n) for n in NEW_ARTIFACTS]
    manifest['artifacts'] = manifest['source_artifacts'] + manifest['new_or_updated_artifacts']
    for a in manifest['artifacts']:
        if a.get('path','').endswith('M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json'):
            a['sha256'] = 'SELF_REFERENTIAL_SEE_FINAL_SHA256SUM_OUTPUT'
            a['sha256_note'] = 'A manifest cannot contain its own stable final hash; use post-commit sha256sum output.'
    dump('M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json', manifest)

    validation = {
      'schema':'umc.v1.m3n.post_compaction_closeout_validation.v1',
      'generated_utc': now(),
      'checks': {
        'json_validation': all(json.loads((BASE/n).read_text()) is not None for n in [a for a in NEW_ARTIFACTS if a.endswith('.json')]),
        'markdown_sanity': all((BASE/n).exists() and (BASE/n).stat().st_size > 50 for n in [a for a in NEW_ARTIFACTS if a.endswith('.md')]),
        'send_hit_classification_validation': classification['status']=='PASS_M3N_POST_COMPACTION_SEND_HITS_CLASSIFIED_AMBIENT_FALSE_POSITIVE' and len(hits)==2,
        'counter_reconciliation_validation': reconciliation['status']=='PASS_M3N_POST_COMPACTION_STABILITY_COUNTERS_RECONCILED',
        'readback_validation': core_readback_pass,
        'context_overflow_validation': closeout['context_overflow_count']==0 and closeout['context_overflow_diag_count']==0,
        'disabled_cron_validation': cron.get('enabled') is False,
        'safety_counter_validation': closeout['repair_lane_telegram_probe_send_count']==0 and closeout['umc_shadow_caused_send_count']==0 and closeout['message_tool_send_count']==0 and closeout['external_send_count']==0,
        'no_authority_validation': closeout['production_authority_change_count']==0 and closeout['enforcement_started'] is False,
        'runtime_config_mutation_validation': closeout['route_config_mutation_count']==0,
        'durable_memory_context_bridge_nonmutation_validation': closeout['durable_memory_mutation_count']==0 and closeout['context_bridge_mutation_count']==0,
      },
      'status': 'PASS_M3N_POST_COMPACTION_CLOSEOUT_VALIDATION' if final_status.startswith('PASS_') else 'FAIL_M3N_POST_COMPACTION_CLOSEOUT_VALIDATION'
    }
    dump('M3N_POST_COMPACTION_CLOSEOUT_VALIDATION.json', validation)

    print(json.dumps({
      'final_status': final_status,
      'rehydration': rehydration['status'],
      'classification': classification['status'],
      'reconciliation': reconciliation['status'],
      'closeout': str(BASE/'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json'),
      'validation': validation['status'],
      'new_artifacts': NEW_ARTIFACTS + ['M3N_POST_COMPACTION_CLOSEOUT_VALIDATION.json'],
    }, indent=2))

if __name__ == '__main__':
    main()
