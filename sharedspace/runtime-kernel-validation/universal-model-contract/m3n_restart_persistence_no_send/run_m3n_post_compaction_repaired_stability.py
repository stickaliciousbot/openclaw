#!/usr/bin/env python3
import json, re, subprocess, time, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/stickai/.openclaw/workspace')
BASE = ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send'
LOG_PATH = Path('/tmp/openclaw/openclaw-2026-07-15.log')
SESSION_ID = '412b53c8-9047-4878-aeae-9040aaac5b05'
SESSION_PATH = Path('/home/stickai/.openclaw/agents/main/sessions')/(SESSION_ID + '.jsonl')
CRON_PATH = Path('/home/stickai/.openclaw/cron/jobs.json')
CONFIG_PATH = Path('/home/stickai/.openclaw/openclaw.json')
MEMORY_PATH = ROOT/'MEMORY.md'
CB_EVENTS = ROOT/'sharedspace/context-bridge/events.jsonl'
CB_ACTIONS = ROOT/'sharedspace/context-bridge/actions.json'
JOB_ID = 'b29e6275-9bad-4622-8a56-041e5a2dc864'
JOB_NAME = 'context-plus-semantic-shadow-pass-watch'
ARM_DELAY_SECONDS = 45
PROBE_COUNT = 4
PROBE_CADENCE_SECONDS = 300

def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def sha(path):
    path = Path(path)
    if not path.exists():
        return None
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_json(name, obj):
    p=BASE/name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')
    return p

def run(cmd, timeout=60):
    p=subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    return {'cmd':' '.join(cmd), 'returncode':p.returncode, 'stdout':p.stdout, 'stderr':p.stderr}

def parse_gateway_status(stdout):
    m=re.search(r'Runtime: running \(pid (\d+), state ([^,]+), sub ([^,]+), last exit ([^,]+), reason ([^)]+)\)', stdout)
    return {'pid': int(m.group(1)), 'state': m.group(2), 'sub_state': m.group(3), 'last_exit': m.group(4), 'reason': m.group(5)} if m else {}

def channel_status():
    # Safe readback only: probe=false. No Telegram send/probe.
    res=run(['openclaw','gateway','call','channels.status','--params',json.dumps({'probe': False, 'timeoutMs': 5000}),'--json'], timeout=45)
    try:
        obj=json.loads(res['stdout']) if res['stdout'].strip() else None
    except Exception:
        obj=None
    return res,obj

def account_ok(ch_obj):
    if not ch_obj:
        return False,0,None,None
    accounts=(ch_obj.get('channelAccounts') or {}).get('telegram') or []
    acct=accounts[0] if accounts else None
    channel=(ch_obj.get('channels') or {}).get('telegram')
    ok=bool(len(accounts)==1 and acct and acct.get('configured') and acct.get('enabled') and acct.get('running') and acct.get('connected') and acct.get('lastError') is None)
    return ok,len(accounts),acct,channel

def load_json(path):
    return json.loads(Path(path).read_text())

def cron_job():
    if not CRON_PATH.exists():
        return None
    data=load_json(CRON_PATH)
    jobs=data.get('jobs', data if isinstance(data, list) else [])
    for j in jobs:
        if j.get('id') == JOB_ID:
            return {'id': j.get('id'), 'name': j.get('name'), 'enabled': j.get('enabled'), 'state': j.get('state', {})}
    return None

def log_entries_since(iso_utc):
    if not LOG_PATH.exists():
        return []
    cutoff=datetime.fromisoformat(iso_utc.replace('Z','+00:00'))
    entries=[]
    for line in LOG_PATH.read_text(errors='replace').splitlines():
        try:
            j=json.loads(line)
        except Exception:
            continue
        date=((j.get('_meta') or {}).get('date'))
        if not date:
            continue
        try:
            dt=datetime.fromisoformat(date.replace('Z','+00:00'))
        except Exception:
            continue
        if dt < cutoff:
            continue
        msg=str(j.get('message') or j.get('1') or '')
        subsystem=str((j.get('_meta') or {}).get('name') or j.get('0') or '')
        entries.append({'date': date, 'subsystem': subsystem, 'message': msg})
    return entries

def count_entries(entries):
    counts={
        'fresh_liveness_warning': 0,
        'event_loop_delay': 0,
        'getme_timeout': 0,
        'gateway_timeout': 0,
        'context_overflow': 0,
        'context_overflow_diag': 0,
        'selected_cron_active_hits': 0,
        'telegram_prohibited_send_hits': 0,
        'telegram_probe_true_hits': 0,
        'provider_shadow_call_hits': 0,
        'route_config_mutation_hits': 0,
        'memory_mutation_hits': 0,
        'context_bridge_mutation_hits': 0,
        'production_authority_change_hits': 0,
        'channels_status_probe_false_hits': 0
    }
    send_examples=[]
    for e in entries:
        text=(e['subsystem']+' '+e['message'])
        low=text.lower()
        if 'liveness warning' in low:
            counts['fresh_liveness_warning'] += 1
        if 'event_loop_delay' in low:
            counts['event_loop_delay'] += 1
        if 'getme' in low and 'timeout' in low:
            counts['getme_timeout'] += 1
        if 'gateway' in low and 'timeout' in low:
            counts['gateway_timeout'] += 1
        if re.search(r'context[-_ ]overflow|maximum context|context overflow', text, re.I):
            counts['context_overflow'] += 1
        if 'context-overflow-diag' in low:
            counts['context_overflow_diag'] += 1
        if JOB_ID.lower() in low and 'enabled=false' not in low:
            counts['selected_cron_active_hits'] += 1
        if 'channels.status' in low and 'probe=false' in low:
            counts['channels_status_probe_false_hits'] += 1
        if 'channels.status' in low and 'probe=true' in low:
            counts['telegram_probe_true_hits'] += 1
        if 'telegram sendmessage ok' in low or 'message.action' in low and 'channel=telegram' in low:
            counts['telegram_prohibited_send_hits'] += 1
            if len(send_examples) < 5:
                send_examples.append(e)
        if any(s in low for s in ['provider/model shadow','shadow call','runwithmodelfallback','runembeddedpiagent']):
            counts['provider_shadow_call_hits'] += 1
        if any(s in low for s in ['config.patch','config.apply','route/fallback','fallback mutation']):
            counts['route_config_mutation_hits'] += 1
        if any(s in low for s in ['memory mutation','memory.md wrote','successfully wrote to /home/stickai/.openclaw/workspace/memory']):
            counts['memory_mutation_hits'] += 1
        if any(s in low for s in ['context bridge mutation','context-bridge wrote','context-bridge mutation']):
            counts['context_bridge_mutation_hits'] += 1
        if any(s in low for s in ['production authority','authority change','enforcement enabled']):
            counts['production_authority_change_hits'] += 1
    return counts, send_examples

def hashes():
    return {str(p): sha(p) for p in [CONFIG_PATH, MEMORY_PATH, CB_EVENTS, CB_ACTIONS] if p.exists()}

def safety_zero(counts):
    hard_keys=['telegram_prohibited_send_hits','telegram_probe_true_hits','provider_shadow_call_hits','route_config_mutation_hits','memory_mutation_hits','context_bridge_mutation_hits','production_authority_change_hits']
    return all(counts.get(k,0)==0 for k in hard_keys)

def probe(idx, watch_start, base_pid, pre_hashes):
    gw=run(['openclaw','gateway','status'], timeout=45)
    gw_state=parse_gateway_status(gw['stdout'])
    ch_res,ch_obj=channel_status()
    acct_ok,acct_count,acct,channel=account_ok(ch_obj)
    entries=log_entries_since(watch_start)
    counts,send_examples=count_entries(entries)
    cron=cron_job()
    post_hashes=hashes()
    ok=all([
        gw['returncode']==0 and 'Connectivity probe: ok' in gw['stdout'],
        base_pid is None or gw_state.get('pid') == base_pid,
        SESSION_PATH.exists(),
        ch_res['returncode']==0,
        acct_ok,
        acct_count==1,
        cron and cron.get('enabled') is False,
        counts.get('fresh_liveness_warning',0)==0,
        counts.get('event_loop_delay',0)==0,
        counts.get('getme_timeout',0)==0,
        counts.get('gateway_timeout',0)==0,
        counts.get('context_overflow',0)==0,
        counts.get('context_overflow_diag',0)==0,
        counts.get('selected_cron_active_hits',0)==0,
        safety_zero(counts),
        post_hashes == pre_hashes,
    ])
    obj={
        'schema':'umc.v1.m3n.post_compaction_repaired_stability_probe.v1',
        'generated_utc':now(),
        'probe_index':idx,
        'expected_probes':PROBE_COUNT,
        'status':'PASS_M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE' if ok else 'FAIL_M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE',
        'watch_start_utc':watch_start,
        'gateway_rpc_ok':gw['returncode']==0 and 'Connectivity probe: ok' in gw['stdout'],
        'gateway_state':gw_state,
        'gateway_pid_stable': base_pid is None or gw_state.get('pid') == base_pid,
        'selected_session_exists': SESSION_PATH.exists(),
        'telegram_readback_method':'channels.status probe=false',
        'telegram_readback_returncode': ch_res['returncode'],
        'telegram_account_ok':acct_ok,
        'telegram_account_count':acct_count,
        'disabled_cron_state':cron,
        'log_counts_since_watch_start':counts,
        'telegram_prohibited_send_examples':send_examples,
        'memory_context_bridge_config_nonmutation_ok':post_hashes == pre_hashes,
    }
    write_json(f'M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_{idx:04d}.json', obj)
    return obj

def main():
    BASE.mkdir(parents=True, exist_ok=True)
    arm_started=now()
    time.sleep(ARM_DELAY_SECONDS)
    watch_start=now()
    pre_hashes=hashes()
    prior_readback=load_json(BASE/'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK.json')
    prior_compaction=load_json(BASE/'M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json')
    failure_analysis=load_json(BASE/'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK_FAILURE_ANALYSIS.json')
    gw=run(['openclaw','gateway','status'], timeout=45)
    gw_state=parse_gateway_status(gw['stdout'])
    ch_res,ch_obj=channel_status()
    acct_ok,acct_count,acct,channel=account_ok(ch_obj)
    cron=cron_job()
    entries=log_entries_since(watch_start)
    counts,send_examples=count_entries(entries)
    preflight_ok=all([
        prior_compaction.get('status')=='PASS_M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTED',
        prior_readback.get('context_overflow_count_after_compaction_start')==0,
        prior_readback.get('context_overflow_diag_count_after_compaction_start')==0,
        failure_analysis.get('diagnosis',{}).get('classification')=='FAIL_CLOSED_AMBIGUOUS_TELEGRAM_SEND_COUNTERS_DURING_LIVE_OWNER_CHAT',
        gw['returncode']==0 and 'Connectivity probe: ok' in gw['stdout'],
        SESSION_PATH.exists(),
        ch_res['returncode']==0,
        acct_ok,
        acct_count==1,
        cron and cron.get('enabled') is False,
        counts.get('context_overflow',0)==0,
        counts.get('context_overflow_diag',0)==0,
        safety_zero(counts),
    ])
    preflight={
        'schema':'umc.v1.m3n.post_compaction_repaired_readback_preflight.v1',
        'generated_utc':now(),
        'arm_started_utc':arm_started,
        'arm_delay_seconds':ARM_DELAY_SECONDS,
        'watch_start_utc':watch_start,
        'status':'PASS_M3N_POST_COMPACTION_REPAIRED_READBACK_PREFLIGHT' if preflight_ok else 'FAIL_M3N_POST_COMPACTION_REPAIRED_READBACK_PREFLIGHT',
        'prior_compaction_status':prior_compaction.get('status'),
        'prior_readback_status':prior_readback.get('status'),
        'prior_failure_classification':failure_analysis.get('diagnosis',{}).get('classification'),
        'gateway_rpc_ok':gw['returncode']==0 and 'Connectivity probe: ok' in gw['stdout'],
        'gateway_state':gw_state,
        'selected_session_exists':SESSION_PATH.exists(),
        'telegram_readback_method':'channels.status probe=false',
        'telegram_readback_returncode':ch_res['returncode'],
        'telegram_account_ok':acct_ok,
        'telegram_account_count':acct_count,
        'disabled_cron_state':cron,
        'log_counts_since_watch_start':counts,
        'telegram_prohibited_send_examples':send_examples,
        'memory_context_bridge_config_hashes_before':pre_hashes,
        'n2_n3_retry_was_run':False,
        'persistence_verification_started':False,
        'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION'
    }
    write_json('M3N_POST_COMPACTION_REPAIRED_READBACK_PREFLIGHT.json', preflight)
    if not preflight_ok:
        closeout={
            'schema':'umc.v1.m3n.post_compaction_repaired_stability_closeout.v1',
            'generated_utc':now(),
            'final_status':'FAIL_M3N_POST_COMPACTION_REPAIRED_READBACK_PREFLIGHT',
            'watch_start_utc':watch_start,
            'completed_probes':0,
            'exact_next_phase':'REPAIR_M3N_POST_COMPACTION_READBACK_VALIDATION_HARNESS_OR_ENVIRONMENT',
            'n2_n3_retry_allowed':False,
            'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION'
        }
        write_json('M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json', closeout)
        print(json.dumps({'final_status':closeout['final_status'],'closeout':str(BASE/'M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json')}, indent=2))
        return 1

    probes=[]
    base_pid=gw_state.get('pid')
    final_status='PASS_M3N_CONTEXT_OVERFLOW_REPAIRED_READBACK_STABILITY_CONFIRMED'
    for idx in range(1, PROBE_COUNT+1):
        if idx > 1:
            time.sleep(PROBE_CADENCE_SECONDS)
        p=probe(idx, watch_start, base_pid, pre_hashes)
        probes.append(p)
        if not p['status'].startswith('PASS_'):
            final_status='FAIL_M3N_POST_COMPACTION_REPAIRED_STABILITY'
            break
    for idx in range(len(probes)+1, PROBE_COUNT+1):
        write_json(f'M3N_POST_COMPACTION_REPAIRED_STABILITY_PROBE_{idx:04d}.json', {
            'schema':'umc.v1.m3n.post_compaction_repaired_stability_probe.v1',
            'generated_utc':now(),
            'probe_index':idx,
            'expected_probes':PROBE_COUNT,
            'status':'NOT_RUN_AFTER_EARLIER_REPAIRED_STABILITY_FAILURE'
        })
    final_entries=log_entries_since(watch_start)
    final_counts,send_examples=count_entries(final_entries)
    summary={
        'schema':'umc.v1.m3n.post_compaction_repaired_stability_summary.v1',
        'generated_utc':now(),
        'status':'PASS_M3N_POST_COMPACTION_REPAIRED_STABILITY_CONFIRMED' if final_status.startswith('PASS_') else final_status,
        'watch_start_utc':watch_start,
        'duration_minutes_expected':20,
        'probe_count_expected':PROBE_COUNT,
        'probe_cadence_seconds':PROBE_CADENCE_SECONDS,
        'completed_probes':len(probes),
        'probe_statuses':[p.get('status') for p in probes],
        'final_log_counts_since_watch_start':final_counts,
        'telegram_prohibited_send_examples':send_examples,
        'disabled_cron_state':cron_job(),
        'n2_n3_retry_was_run':False,
        'persistence_verification_started':False,
        'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION'
    }
    write_json('M3N_POST_COMPACTION_REPAIRED_STABILITY_SUMMARY.json', summary)
    closeout={
        'schema':'umc.v1.m3n.post_compaction_repaired_stability_closeout.v1',
        'generated_utc':now(),
        'final_status':final_status,
        'watch_start_utc':watch_start,
        'preflight_status':preflight.get('status'),
        'stability_summary_status':summary.get('status'),
        'completed_probes':len(probes),
        'context_overflow_count':final_counts.get('context_overflow',0),
        'context_overflow_diag_count':final_counts.get('context_overflow_diag',0),
        'telegram_prohibited_send_hits':final_counts.get('telegram_prohibited_send_hits',0),
        'telegram_probe_true_hits':final_counts.get('telegram_probe_true_hits',0),
        'provider_shadow_call_hits':final_counts.get('provider_shadow_call_hits',0),
        'route_config_mutation_hits':final_counts.get('route_config_mutation_hits',0),
        'memory_mutation_hits':final_counts.get('memory_mutation_hits',0),
        'context_bridge_mutation_hits':final_counts.get('context_bridge_mutation_hits',0),
        'production_authority_change_hits':final_counts.get('production_authority_change_hits',0),
        'disabled_cron_state':cron_job(),
        'n2_n3_retry_was_run':False,
        'persistence_verification_started':False,
        'm3o_started':False,
        'm4_started':False,
        'enforcement_started':False,
        'exact_next_phase':'APPROVE_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED' if final_status.startswith('PASS_') else 'REPAIR_M3N_POST_COMPACTION_READBACK_VALIDATION_HARNESS_OR_ENVIRONMENT',
        'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION'
    }
    write_json('M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json', closeout)
    print(json.dumps({'final_status':final_status,'closeout':str(BASE/'M3N_POST_COMPACTION_REPAIRED_STABILITY_CLOSEOUT.json')}, indent=2))
    return 0 if final_status.startswith('PASS_') else 2

if __name__ == '__main__':
    raise SystemExit(main())
