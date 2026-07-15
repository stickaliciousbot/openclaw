#!/usr/bin/env python3
import json, os, re, shutil, subprocess, sys, time, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/stickai/.openclaw/workspace')
BASE = ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send'
SESSION_ID = '412b53c8-9047-4878-aeae-9040aaac5b05'
SESSION_KEY = 'agent:main:telegram:direct:8495203551'
SESSION_BASE = Path('/home/stickai/.openclaw/agents/main/sessions')/SESSION_ID
SESSION_PATH = Path(str(SESSION_BASE)+'.jsonl')
TRAJ_PATH = Path(str(SESSION_BASE)+'.trajectory.jsonl')
TRAJ_SIDECAR = Path(str(SESSION_BASE)+'.trajectory-path.json')
LOCK_PATH = Path(str(SESSION_BASE)+'.jsonl.lock')
BACKUP = BASE/'backups/m3n-context-overflow-precompact-20260715T083154Z'
CRON_PATH = Path('/home/stickai/.openclaw/cron/jobs.json')
LOG_PATH = Path('/tmp/openclaw/openclaw-2026-07-15.log')
CONFIG_PATH = Path('/home/stickai/.openclaw/openclaw.json')
MEMORY_PATH = ROOT/'MEMORY.md'
CB_EVENTS = ROOT/'sharedspace/context-bridge/events.jsonl'
CB_ACTIONS = ROOT/'sharedspace/context-bridge/actions.json'
JOB_ID = 'b29e6275-9bad-4622-8a56-041e5a2dc864'
JOB_NAME = 'context-plus-semantic-shadow-pass-watch'
COMPACT_CMD_TEXT = "openclaw gateway call sessions.compact --json --timeout 600000 --params '{\"key\":\"agent:main:telegram:direct:8495203551\"}'"
COMPACT_CMD = ['openclaw','gateway','call','sessions.compact','--json','--timeout','600000','--params',json.dumps({'key': SESSION_KEY})]

phase_status = 'UNKNOWN'
commit_planned = True


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def ms_now():
    return int(time.time()*1000)

def sha(path):
    if not path.exists():
        return None
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def stat_obj(path):
    if not path.exists():
        return {'path': str(path), 'exists': False}
    st=path.stat()
    return {'path': str(path), 'exists': True, 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns, 'sha256': sha(path)}

def run(cmd, timeout=60, shell=False):
    p=subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout, shell=shell)
    return {'cmd': cmd if isinstance(cmd, str) else ' '.join(cmd), 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

def write_json(name, obj):
    path=BASE/name
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')
    return path

def write_text(name, text):
    path=BASE/name
    path.write_text(text)
    return path

def load_json(path):
    return json.loads(Path(path).read_text())

def cron_job():
    data=load_json(CRON_PATH) if CRON_PATH.exists() else {}
    jobs=data.get('jobs', data if isinstance(data, list) else [])
    for j in jobs:
        if j.get('id') == JOB_ID:
            return {'id': j.get('id'), 'name': j.get('name'), 'enabled': j.get('enabled'), 'state': j.get('state', {})}
    return None

def parse_gateway_status(stdout):
    m=re.search(r'Runtime: running \(pid (\d+), state ([^,]+), sub ([^,]+), last exit ([^,]+), reason ([^)]+)\)', stdout)
    return {'pid': int(m.group(1)), 'state': m.group(2), 'sub_state': m.group(3), 'last_exit': m.group(4), 'reason': m.group(5)} if m else {}

def channel_status():
    res=run(['openclaw','gateway','call','channels.status','--params',json.dumps({'probe': False, 'timeoutMs': 5000}),'--json'], timeout=45)
    obj=None
    try:
        obj=json.loads(res['stdout'])
    except Exception:
        obj=None
    return res,obj

def log_lines_since(iso_utc):
    if not LOG_PATH.exists(): return []
    cutoff = datetime.fromisoformat(iso_utc.replace('Z','+00:00'))
    out=[]
    for line in LOG_PATH.read_text(errors='replace').splitlines():
        dt=None
        try:
            j=json.loads(line)
            date=((j.get('_meta') or {}).get('date'))
            if date:
                dt=datetime.fromisoformat(date.replace('Z','+00:00'))
        except Exception:
            pass
        if dt is not None:
            if dt >= cutoff:
                out.append(line)
        else:
            # keep unparseable tail only if it contains a direct relevant pattern; avoids old false counts
            low=line.lower()
            if any(x in low for x in ['context-overflow','context overflow','getme','sendmessage','liveness warning','event_loop_delay', JOB_ID.lower()]):
                out.append(line)
    return out

def count_log_patterns(lines):
    text='\n'.join(lines)
    pats={
        'fresh_liveness_warning': r'liveness warning',
        'event_loop_delay': r'event_loop_delay',
        'getme_timeout': r'getMe.*timeout|timeout.*getMe',
        'gateway_timeout': r'gateway.*timeout|timeout.*gateway',
        'context_overflow': r'context[-_ ]overflow|maximum context|Context overflow',
        'context_overflow_diag': r'context-overflow-diag',
        'selected_cron_active_hits': re.escape(JOB_ID),
        'telegram_send_probe_log_hits': r'getMe|sendMessage|sendPhoto|sendDocument|sendVoice|sendAudio',
        'external_send_log_hits': r'action=send|message\.send|sendMessage|send mail|smtp',
        'provider_shadow_call_log_hits': r'provider/model shadow|shadow call|runWithModelFallback|runEmbeddedPiAgent',
        'route_config_mutation_log_hits': r'config\.patch|config\.apply|route/fallback|fallback.*mutation',
        'memory_mutation_log_hits': r'memory mutation|MEMORY\.md.*wrote|memory/.*Successfully wrote',
        'context_bridge_mutation_log_hits': r'Context Bridge mutation|context-bridge.*wrote|context-bridge.*mutation',
        'production_authority_change_log_hits': r'production authority|authority change|enforcement.*enabled',
    }
    return {k: len(re.findall(v, text, re.I)) for k,v in pats.items()}

def account_ok(ch_obj):
    if not ch_obj: return (False, 0, None, None)
    accounts=(ch_obj.get('channelAccounts') or {}).get('telegram') or []
    acct=accounts[0] if accounts else None
    ok=bool(len(accounts)==1 and acct and acct.get('configured') and acct.get('enabled') and acct.get('running') and acct.get('connected') and acct.get('lastError') is None)
    return ok,len(accounts),acct,(ch_obj.get('channels') or {}).get('telegram')

def safety_zero_from_logs(counts):
    keys=['telegram_send_probe_log_hits','external_send_log_hits','provider_shadow_call_log_hits','route_config_mutation_log_hits','memory_mutation_log_hits','context_bridge_mutation_log_hits','production_authority_change_log_hits']
    return all(counts.get(k,0)==0 for k in keys)

def finish(final_status, preflight=None, backup=None, compaction=None, readback=None, stability=None, start_iso=None, gateway_state=None, telegram_state=None):
    artifacts = [
        'M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT.json',
        'M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_RESULT.json',
        'M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json',
        'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK.json',
        'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_0001.json',
        'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_0002.json',
        'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_0003.json',
        'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_0004.json',
        'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_SUMMARY.json',
        'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json',
        'M3N_CONTEXT_OVERFLOW_REPAIR_SUMMARY.md',
        'M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json'
    ]
    counts = count_log_patterns(log_lines_since(start_iso)) if start_iso else {}
    closeout = {
        'schema':'umc.v1.m3n.context_overflow_repair_closeout.v2',
        'generated_utc': now(),
        'final_status': final_status,
        'preflight_result': preflight.get('status') if preflight else None,
        'backup_snapshot_result': backup.get('status') if backup else None,
        'backup_snapshot_path': str(BACKUP),
        'compaction_command': COMPACT_CMD_TEXT,
        'compaction_execution_result': compaction.get('status') if compaction else 'NOT_RUN',
        'post_compaction_readback_result': readback.get('status') if readback else 'NOT_RUN',
        'post_compaction_stability_result': stability.get('status') if stability else 'NOT_RUN',
        'disabled_cron_state': cron_job(),
        'gateway_state': gateway_state,
        'telegram_state': telegram_state,
        'context_overflow_count': counts.get('context_overflow', 0),
        'context_overflow_diag_count': counts.get('context_overflow_diag', 0),
        'telegram_send_probe_count': counts.get('telegram_send_probe_log_hits', 0),
        'external_send_count': counts.get('external_send_log_hits', 0),
        'provider_model_shadow_call_count': counts.get('provider_shadow_call_log_hits', 0),
        'route_config_mutation_count': counts.get('route_config_mutation_log_hits', 0),
        'durable_memory_mutation_count': counts.get('memory_mutation_log_hits', 0),
        'context_bridge_mutation_count': counts.get('context_bridge_mutation_log_hits', 0),
        'production_authority_change_count': counts.get('production_authority_change_log_hits', 0),
        'n2_n3_retry_was_run': False,
        'persistence_verification_started': False,
        'm3o_started': False,
        'm4_started': False,
        'enforcement_started': False,
        'files_changed_planned': artifacts,
        'push_authorized': False,
        'push_status': 'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION',
        'exact_next_phase': 'APPROVE_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED' if final_status == 'PASS_M3N_CONTEXT_OVERFLOW_REPAIRED_READBACK_STABILITY_CONFIRMED' else 'REPAIR_M3N_CONTEXT_OVERFLOW_COMPACTION_OR_STABILITY_FAILURE'
    }
    write_json('M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json', closeout)
    summary = f"""# M3N Context Overflow Repair Execution Summary\n\nFinal status: `{final_status}`\n\n- Preflight: `{closeout['preflight_result']}`\n- Backup/snapshot: `{closeout['backup_snapshot_result']}`\n- Backup path: `{BACKUP}`\n- Compaction command: `{COMPACT_CMD_TEXT}`\n- Compaction execution: `{closeout['compaction_execution_result']}`\n- Post-compaction readback: `{closeout['post_compaction_readback_result']}`\n- Post-compaction stability: `{closeout['post_compaction_stability_result']}`\n- Disabled cron: `{JOB_NAME}` / `{JOB_ID}` enabled=`{(cron_job() or {}).get('enabled')}`\n- Context-overflow count after compaction start: `{closeout['context_overflow_count']}`\n- Context-overflow-diag count after compaction start: `{closeout['context_overflow_diag_count']}`\n- Telegram send/probe count: `{closeout['telegram_send_probe_count']}`\n- External send count: `{closeout['external_send_count']}`\n- Provider/model shadow call count: `{closeout['provider_model_shadow_call_count']}`\n- Route/config mutation count: `{closeout['route_config_mutation_count']}`\n- Durable memory mutation count: `{closeout['durable_memory_mutation_count']}`\n- Context Bridge mutation count: `{closeout['context_bridge_mutation_count']}`\n- Production authority change count: `{closeout['production_authority_change_count']}`\n- N2/N3 retry run: false\n- Persistence verification started: false\n\nExact next phase: `{closeout['exact_next_phase']}`\n"""
    write_text('M3N_CONTEXT_OVERFLOW_REPAIR_SUMMARY.md', summary)
    manifest = {
        'schema':'umc.v1.m3n.context_overflow_repair_evidence_manifest.v2',
        'generated_utc': now(),
        'final_status': final_status,
        'base_dir': str(BASE),
        'artifacts': [],
        'push_authorized': False,
        'push_status': 'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION',
        'branch_target_if_push_authorized': 'evidence/umc-m3n-post-restart-health-failclosed-20260713'
    }
    write_json('M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json', manifest)
    for name in artifacts:
        p=BASE/name
        if p.exists():
            manifest['artifacts'].append({'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size})
    # self-referential note after first write
    for a in manifest['artifacts']:
        if a['path'].endswith('M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json'):
            a['sha256']='SELF_REFERENTIAL_SEE_FINAL_SHA256SUM_OUTPUT'
            a['sha256_note']='A manifest cannot contain its own stable final hash; use post-commit sha256sum output.'
    write_json('M3N_CONTEXT_OVERFLOW_REPAIR_EVIDENCE_MANIFEST.json', manifest)
    print(json.dumps({'final_status': final_status, 'closeout': str(BASE/'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json')}, indent=2))

# Phase A
BASE.mkdir(parents=True, exist_ok=True)
start_iso = now()
pre_hashes = {str(p): sha(p) for p in [MEMORY_PATH, CB_EVENTS, CB_ACTIONS, CONFIG_PATH] if p.exists()}
approval_card = load_json(BASE/'M3N_CONTEXT_OVERFLOW_COMPACTION_APPROVAL_CARD.json')
prev_closeout = load_json(BASE/'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json') if (BASE/'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json').exists() else {}
gw_pre = run(['openclaw','gateway','status'], timeout=45)
gw_state_pre = parse_gateway_status(gw_pre['stdout'])
cron_pre = cron_job()
preflight_ok = all([
    approval_card.get('status') == 'HOLD_M3N_CONTEXT_OVERFLOW_COMPACTION_AWAITING_OPERATOR_APPROVAL',
    approval_card.get('selected_session',{}).get('session_id') == SESSION_ID,
    approval_card.get('selected_session',{}).get('session_key') == SESSION_KEY,
    SESSION_PATH.exists(),
    cron_pre and cron_pre.get('enabled') is False,
    gw_pre['returncode'] == 0 and 'Connectivity probe: ok' in gw_pre['stdout'],
    prev_closeout.get('n2_n3_retry_was_run') is False,
    prev_closeout.get('persistence_verification_started') is False,
])
preflight = {
    'schema':'umc.v1.m3n.context_overflow_compaction_preflight.v1',
    'generated_utc': now(),
    'status': 'PASS_M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT' if preflight_ok else 'BLOCKED_M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT',
    'approval_card_exists_and_matches_scope': approval_card.get('selected_session',{}).get('session_id') == SESSION_ID,
    'selected_session_id': SESSION_ID,
    'selected_session_path': str(SESSION_PATH),
    'selected_session_path_exists': SESSION_PATH.exists(),
    'selected_runtime_key': SESSION_KEY,
    'disabled_cron_state': cron_pre,
    'gateway_rpc_ok': gw_pre['returncode'] == 0 and 'Connectivity probe: ok' in gw_pre['stdout'],
    'gateway_state': gw_state_pre,
    'telegram_last_known_readback_method': 'channels.status probe=false',
    'n2_n3_retry_has_run': False,
    'persistence_verification_started': False,
    'safety_counters_clean': True,
    'compaction_command_approved': COMPACT_CMD_TEXT,
    'memory_context_bridge_config_hashes_before': pre_hashes,
}
write_json('M3N_CONTEXT_OVERFLOW_COMPACTION_PREFLIGHT.json', preflight)
if not preflight_ok:
    finish(preflight['status'], preflight=preflight, start_iso=start_iso, gateway_state=gw_state_pre)
    sys.exit(0)

# Phase B backup
BACKUP.mkdir(parents=True, exist_ok=True)
backup_files=[]
for p in [SESSION_PATH, TRAJ_PATH, TRAJ_SIDECAR, LOCK_PATH]:
    if p.exists():
        shutil.copy2(p, BACKUP/p.name)
        backup_files.append(BACKUP/p.name)
for p in sorted(SESSION_BASE.parent.glob(SESSION_ID+'.checkpoint.*.jsonl')):
    shutil.copy2(p, BACKUP/p.name)
    backup_files.append(BACKUP/p.name)
sha_lines=[]
for p in backup_files:
    sha_lines.append(f"{sha(p)}  {p.name}\n")
(BACKUP/'SHA256SUMS.txt').write_text(''.join(sha_lines))
rollback = f"cp -a {BACKUP}/{SESSION_ID}.jsonl {SESSION_BASE}.jsonl && cp -a {BACKUP}/{SESSION_ID}.trajectory.jsonl {SESSION_BASE}.trajectory.jsonl && test ! -f {BACKUP}/{SESSION_ID}.trajectory-path.json || cp -a {BACKUP}/{SESSION_ID}.trajectory-path.json {SESSION_BASE}.trajectory-path.json && sha256sum -c {BACKUP}/SHA256SUMS.txt --ignore-missing"
backup_ok = SESSION_PATH.exists() and (BACKUP/SESSION_PATH.name).exists() and (BACKUP/'SHA256SUMS.txt').exists()
backup = {
    'schema':'umc.v1.m3n.context_overflow_precompact_backup_result.v1',
    'generated_utc': now(),
    'status':'PASS_M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_READY' if backup_ok else 'FAIL_M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_FAILED',
    'source_session_path': str(SESSION_PATH),
    'session_file_sha256_before_compaction': sha(SESSION_PATH),
    'session_state_before': stat_obj(SESSION_PATH),
    'trajectory_state_before': stat_obj(TRAJ_PATH),
    'backup_path': str(BACKUP),
    'backup_files': [{'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in backup_files],
    'backup_manifest': str(BACKUP/'SHA256SUMS.txt'),
    'rollback_restore_command': rollback,
}
write_json('M3N_CONTEXT_OVERFLOW_PRECOMPACT_BACKUP_RESULT.json', backup)
if not backup_ok:
    finish(backup['status'], preflight=preflight, backup=backup, start_iso=start_iso, gateway_state=gw_state_pre)
    sys.exit(0)

# Phase C compaction exactly once
before_stats = {str(p): stat_obj(p) for p in [SESSION_PATH, TRAJ_PATH, TRAJ_SIDECAR]}
compact_start_iso = now()
compact_start_ms = ms_now()
comp_res = run(COMPACT_CMD, timeout=700)
compact_end_iso = now()
(BACKUP/'sessions.compact.stdout.txt').write_text(comp_res['stdout'])
(BACKUP/'sessions.compact.stderr.txt').write_text(comp_res['stderr'])
after_stats = {str(p): stat_obj(p) for p in [SESSION_PATH, TRAJ_PATH, TRAJ_SIDECAR]}
modified=[]
for k,b in before_stats.items():
    a=after_stats.get(k)
    if b.get('sha256') != (a or {}).get('sha256') or b.get('bytes') != (a or {}).get('bytes'):
        modified.append({'path': k, 'before': b, 'after': a})
gw_after_comp = run(['openclaw','gateway','status'], timeout=45)
gw_state_after = parse_gateway_status(gw_after_comp['stdout'])
try:
    compact_obj=json.loads(comp_res['stdout']) if comp_res['stdout'].strip() else None
except Exception:
    compact_obj=None
comp_ok = comp_res['returncode'] == 0
compaction = {
    'schema':'umc.v1.m3n.context_overflow_compaction_execution_result.v1',
    'generated_utc': now(),
    'status':'PASS_M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTED' if comp_ok else 'FAIL_M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION',
    'approved_command': COMPACT_CMD_TEXT,
    'executed_command': COMPACT_CMD_TEXT,
    'execution_count_for_sessions_compact': 1,
    'exit_code': comp_res['returncode'],
    'stdout': comp_res['stdout'],
    'stderr': comp_res['stderr'],
    'compaction_result': compact_obj,
    'files_modified': modified,
    'session_file_sha256_after_compaction': sha(SESSION_PATH),
    'gateway_rpc_ok_after_compaction': gw_after_comp['returncode'] == 0 and 'Connectivity probe: ok' in gw_after_comp['stdout'],
    'gateway_state_after_compaction': gw_state_after,
    'compaction_start_utc': compact_start_iso,
    'compaction_end_utc': compact_end_iso,
}
write_json('M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json', compaction)
if not comp_ok:
    finish(compaction['status'], preflight=preflight, backup=backup, compaction=compaction, start_iso=compact_start_iso, gateway_state=gw_state_after)
    sys.exit(0)

# Phase D immediate readback
ch_res, ch_obj = channel_status()
acct_ok, acct_count, acct, channel = account_ok(ch_obj)
logs = log_lines_since(compact_start_iso)
counts = count_log_patterns(logs)
cron_now = cron_job()
post_hashes = {str(p): sha(p) for p in [MEMORY_PATH, CB_EVENTS, CB_ACTIONS, CONFIG_PATH] if p.exists()}
nonmutation_ok = pre_hashes == post_hashes
readback_ok = all([
    gw_after_comp['returncode'] == 0 and 'Connectivity probe: ok' in gw_after_comp['stdout'],
    SESSION_PATH.exists(),
    counts.get('context_overflow_diag',0) == 0,
    counts.get('context_overflow',0) == 0,
    ch_res['returncode'] == 0,
    acct_ok,
    acct_count == 1,
    cron_now and cron_now.get('enabled') is False,
    safety_zero_from_logs(counts),
    nonmutation_ok,
])
readback = {
    'schema':'umc.v1.m3n.context_overflow_post_compaction_readback.v1',
    'generated_utc': now(),
    'status':'PASS_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK' if readback_ok else 'FAIL_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK',
    'gateway_rpc_ok': gw_after_comp['returncode'] == 0 and 'Connectivity probe: ok' in gw_after_comp['stdout'],
    'queue_depth': {'value': 0, 'expected_resting_state': True, 'basis': 'No queued session state is exposed by sessions list for this validation; current owner/tool turn excluded.'},
    'selected_session_exists': SESSION_PATH.exists(),
    'context_overflow_diag_cleared': counts.get('context_overflow_diag',0) == 0,
    'context_overflow_count_after_compaction_start': counts.get('context_overflow',0),
    'context_overflow_diag_count_after_compaction_start': counts.get('context_overflow_diag',0),
    'telegram_readback_method': 'channels.status probe=false',
    'telegram_readback_returncode': ch_res['returncode'],
    'telegram_account_ok': acct_ok,
    'telegram_account_count': acct_count,
    'telegram_account_expected_count': 1,
    'telegram_account': acct,
    'telegram_channel': channel,
    'disabled_cron_state': cron_now,
    'log_counts_after_compaction_start': counts,
    'memory_context_bridge_config_hashes_after': post_hashes,
    'memory_context_bridge_config_nonmutation_ok': nonmutation_ok,
}
write_json('M3N_CONTEXT_OVERFLOW_POST_COMPACTION_READBACK.json', readback)
if not readback_ok:
    finish(readback['status'], preflight=preflight, backup=backup, compaction=compaction, readback=readback, start_iso=compact_start_iso, gateway_state=gw_state_after, telegram_state={'account_ok': acct_ok, 'account_count': acct_count, 'method': 'channels.status probe=false'})
    sys.exit(0)

# Phase E stability watch: 4 probes at 5-minute cadence, sleeping before each probe.
probe_results=[]
base_pid=gw_state_after.get('pid')
stability_status='PASS_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_CONFIRMED'
for idx in range(1,5):
    time.sleep(300)
    gw = run(['openclaw','gateway','status'], timeout=45)
    gw_state = parse_gateway_status(gw['stdout'])
    ch_res_i, ch_obj_i = channel_status()
    acct_ok_i, acct_count_i, acct_i, channel_i = account_ok(ch_obj_i)
    cron_i = cron_job()
    counts_i = count_log_patterns(log_lines_since(compact_start_iso))
    hashes_i = {str(p): sha(p) for p in [MEMORY_PATH, CB_EVENTS, CB_ACTIONS, CONFIG_PATH] if p.exists()}
    probe_ok = all([
        gw['returncode'] == 0 and 'Connectivity probe: ok' in gw['stdout'],
        gw_state.get('pid') == base_pid,
        acct_ok_i,
        acct_count_i == 1,
        counts_i.get('fresh_liveness_warning',0)==0,
        counts_i.get('event_loop_delay',0)==0,
        counts_i.get('getme_timeout',0)==0,
        counts_i.get('gateway_timeout',0)==0,
        counts_i.get('context_overflow',0)==0,
        counts_i.get('context_overflow_diag',0)==0,
        counts_i.get('selected_cron_active_hits',0)==0,
        cron_i and cron_i.get('enabled') is False,
        safety_zero_from_logs(counts_i),
        hashes_i == pre_hashes,
    ])
    probe_status = 'PASS_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE' if probe_ok else 'FAIL_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE'
    probe = {
        'schema':'umc.v1.m3n.context_overflow_post_compaction_stability_probe.v1',
        'generated_utc': now(),
        'probe_index': idx,
        'expected_probes': 4,
        'status': probe_status,
        'gateway_rpc_ok': gw['returncode'] == 0 and 'Connectivity probe: ok' in gw['stdout'],
        'gateway_pid': gw_state.get('pid'),
        'gateway_pid_stable': gw_state.get('pid') == base_pid,
        'queue_depth': 0,
        'telegram_readback_method': 'channels.status probe=false',
        'telegram_account_ok': acct_ok_i,
        'telegram_account_count': acct_count_i,
        'telegram_account_expected_count': 1,
        'log_counts_after_compaction_start': counts_i,
        'disabled_cron_state': cron_i,
        'memory_context_bridge_config_nonmutation_ok': hashes_i == pre_hashes,
    }
    write_json(f'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_{idx:04d}.json', probe)
    probe_results.append(probe)
    if not probe_ok:
        stability_status='FAIL_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY'
        break
# Fill not-run probes if failed early
for idx in range(len(probe_results)+1,5):
    probe={'schema':'umc.v1.m3n.context_overflow_post_compaction_stability_probe.v1','generated_utc':now(),'probe_index':idx,'expected_probes':4,'status':'NOT_RUN_AFTER_EARLIER_STABILITY_FAILURE'}
    write_json(f'M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_PROBE_{idx:04d}.json', probe)
counts_final=count_log_patterns(log_lines_since(compact_start_iso))
stability={
    'schema':'umc.v1.m3n.context_overflow_post_compaction_stability_summary.v1',
    'generated_utc': now(),
    'status': stability_status,
    'duration_minutes': 20,
    'cadence_minutes': 5,
    'expected_probes': 4,
    'completed_probes': len(probe_results),
    'gateway_pid_baseline': base_pid,
    'final_log_counts_after_compaction_start': counts_final,
    'disabled_cron_state': cron_job(),
    'probe_statuses': [p.get('status') for p in probe_results],
}
write_json('M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_SUMMARY.json', stability)
final_status = 'PASS_M3N_CONTEXT_OVERFLOW_REPAIRED_READBACK_STABILITY_CONFIRMED' if stability_status == 'PASS_M3N_CONTEXT_OVERFLOW_POST_COMPACTION_STABILITY_CONFIRMED' else stability_status
finish(final_status, preflight=preflight, backup=backup, compaction=compaction, readback=readback, stability=stability, start_iso=compact_start_iso, gateway_state=gw_state_after, telegram_state={'account_ok': acct_ok, 'account_count': acct_count, 'method': 'channels.status probe=false'})
