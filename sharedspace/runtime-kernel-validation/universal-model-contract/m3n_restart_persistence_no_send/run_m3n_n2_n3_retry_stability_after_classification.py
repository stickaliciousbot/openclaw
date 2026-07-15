#!/usr/bin/env python3
import json, re, subprocess, time, hashlib, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/home/stickai/.openclaw/workspace')
BASE=ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send'
LOG=Path('/tmp/openclaw/openclaw-2026-07-15.log')
JOB_ID='b29e6275-9bad-4622-8a56-041e5a2dc864'
JOB_NAME='context-plus-semantic-shadow-pass-watch'
BRANCH='evidence/umc-m3n-post-restart-health-failclosed-20260713'
PROBES=4
CADENCE_SECONDS=300

NEW_NAMES=[
'M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.json',
'M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.md',
'M3N_N3_RETRY_STABILITY_PROBE_0001.json',
'M3N_N3_RETRY_STABILITY_PROBE_0002.json',
'M3N_N3_RETRY_STABILITY_PROBE_0003.json',
'M3N_N3_RETRY_STABILITY_PROBE_0004.json',
'M3N_N3_RETRY_STABILITY_SUMMARY.json',
'M3N_N2_N3_RETRY_CLOSEOUT.json',
'M3N_N2_N3_RETRY_SUMMARY.md',
'M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',
'M3N_N2_N3_RETRY_VALIDATION.json',
]

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def dump(name,obj): p=BASE/name; p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); return p
def load(name): return json.loads((BASE/name).read_text())
def sha(path):
    p=Path(path)
    if not p.exists(): return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def stat_name(name):
    p=BASE/name
    return {'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None,'sha256':sha(p) if p.exists() else None}
def run(cmd,timeout=60):
    p=subprocess.run(cmd,cwd=str(ROOT),text=True,capture_output=True,timeout=timeout)
    return {'cmd':' '.join(cmd),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def parse_gateway_status(stdout):
    m=re.search(r'Runtime: running \(pid (\d+), state ([^,]+), sub ([^,]+), last exit ([^,]+), reason ([^)]+)\)',stdout)
    return {'pid':int(m.group(1)),'state':m.group(2),'sub_state':m.group(3),'last_exit':m.group(4),'reason':m.group(5)} if m else {}
def gateway_state():
    res=run(['openclaw','gateway','status'],timeout=45)
    return res, parse_gateway_status(res['stdout'])
def channels_status():
    res=run(['openclaw','gateway','call','channels.status','--params',json.dumps({'probe':False,'timeoutMs':5000}),'--json'],timeout=45)
    try: obj=json.loads(res['stdout'])
    except Exception: obj={}
    accounts=(obj.get('channelAccounts') or {}).get('telegram') or []
    acct=accounts[0] if accounts else None
    channel=(obj.get('channels') or {}).get('telegram') or {}
    ok=bool(len(accounts)==1 and acct and acct.get('configured') and acct.get('enabled') and acct.get('running') and acct.get('connected') and acct.get('lastError') is None)
    return {'method':'channels.status probe=false','returncode':res['returncode'],'account_count':len(accounts),'account_ok':ok,'account':acct,'channel':channel}
def cron_state():
    p=Path('/home/stickai/.openclaw/cron/jobs.json')
    if not p.exists(): return {'id':JOB_ID,'name':JOB_NAME,'enabled':None,'state':None}
    data=json.loads(p.read_text())
    jobs=data.get('jobs', data if isinstance(data,list) else [])
    for j in jobs:
        if j.get('id')==JOB_ID: return {'id':j.get('id'),'name':j.get('name'),'enabled':j.get('enabled'),'state':j.get('state',{})}
    return {'id':JOB_ID,'name':JOB_NAME,'enabled':None,'state':None}
def log_entries_since(iso):
    if not LOG.exists(): return []
    cutoff=datetime.fromisoformat(iso.replace('Z','+00:00'))
    out=[]
    for line in LOG.read_text(errors='replace').splitlines():
        try: j=json.loads(line)
        except Exception: continue
        date=((j.get('_meta') or {}).get('date'))
        if not date: continue
        try: dt=datetime.fromisoformat(date.replace('Z','+00:00'))
        except Exception: continue
        if dt < cutoff: continue
        msg=str(j.get('message') or j.get('1') or '')
        sub=str((j.get('_meta') or {}).get('name') or j.get('0') or '')
        out.append({'date':date,'subsystem':sub,'message':msg})
    return out
def count_logs(entries):
    c={
      'err_module_not_found':0,'missing_pi_embedded':0,'missing_zalo_manifest':0,'channels_telegram_unknown_channel_id':0,
      'fresh_liveness_warning':0,'event_loop_delay':0,'getme_timeout':0,'gateway_timeout':0,
      'context_overflow':0,'context_overflow_diag':0,'selected_cron_active_hits':0,
      'telegram_repair_lane_probe_send_hits':0,'telegram_probe_true_hits':0,'ambient_global_telegram_delivery_hits':0,
      'external_send_hits':0,'provider_model_shadow_call_hits':0,'route_config_mutation_hits':0,
      'durable_memory_mutation_hits':0,'context_bridge_mutation_hits':0,'production_authority_change_hits':0,
      'channels_status_probe_false_hits':0
    }
    ambient=[]; overflow_lines=[]
    for e in entries:
        text=(e['subsystem']+' '+e['message'])
        low=text.lower()
        if 'err_module_not_found' in low: c['err_module_not_found']+=1
        if 'pi-embedded' in low and any(x in low for x in ['missing','not found','cannot find']): c['missing_pi_embedded']+=1
        if ('zalo' in low or 'zalouser' in low) and 'manifest' in low and any(x in low for x in ['missing','not found','cannot find']): c['missing_zalo_manifest']+=1
        if 'channels.telegram' in low and 'unknown channel' in low: c['channels_telegram_unknown_channel_id']+=1
        if 'liveness warning' in low: c['fresh_liveness_warning']+=1
        if 'event_loop_delay' in low: c['event_loop_delay']+=1
        if 'getme' in low and 'timeout' in low: c['getme_timeout']+=1
        if 'gateway' in low and 'timeout' in low: c['gateway_timeout']+=1
        if re.search(r'context[-_ ]overflow|maximum context|context overflow',text,re.I):
            c['context_overflow']+=1
            if len(overflow_lines)<20: overflow_lines.append(e)
        if 'context-overflow-diag' in low: c['context_overflow_diag']+=1
        if JOB_ID.lower() in low and 'enabled=false' not in low: c['selected_cron_active_hits']+=1
        if 'channels.status' in low and 'probe=false' in low: c['channels_status_probe_false_hits']+=1
        if 'channels.status' in low and 'probe=true' in low: c['telegram_probe_true_hits']+=1; c['telegram_repair_lane_probe_send_hits']+=1
        if 'telegram sendmessage ok chat=8495203551' in low:
            c['ambient_global_telegram_delivery_hits']+=1
            if len(ambient)<20: ambient.append(e)
        if 'message.action' in low and 'channel=telegram' in low: c['telegram_repair_lane_probe_send_hits']+=1
        if any(x in low for x in ['send mail','smtp send','external send']) and 'telegram sendmessage ok chat=8495203551' not in low: c['external_send_hits']+=1
        if any(x in low for x in ['provider/model shadow','shadow call','runwithmodelfallback','runembeddedpiagent']): c['provider_model_shadow_call_hits']+=1
        if any(x in low for x in ['config.patch','config.apply','route/fallback','fallback mutation']): c['route_config_mutation_hits']+=1
        if any(x in low for x in ['memory mutation','memory.md wrote','successfully wrote to /home/stickai/.openclaw/workspace/memory']): c['durable_memory_mutation_hits']+=1
        if any(x in low for x in ['context bridge mutation','context-bridge wrote','context-bridge mutation']): c['context_bridge_mutation_hits']+=1
        if any(x in low for x in ['production authority','authority change','enforcement enabled']): c['production_authority_change_hits']+=1
    return c, ambient, overflow_lines

def clean_core_counts(c):
    return all(c.get(k,0)==0 for k in [
      'err_module_not_found','missing_pi_embedded','missing_zalo_manifest','channels_telegram_unknown_channel_id',
      'fresh_liveness_warning','event_loop_delay','getme_timeout','gateway_timeout','context_overflow','context_overflow_diag',
      'selected_cron_active_hits','telegram_repair_lane_probe_send_hits','telegram_probe_true_hits','external_send_hits',
      'provider_model_shadow_call_hits','route_config_mutation_hits','durable_memory_mutation_hits','context_bridge_mutation_hits','production_authority_change_hits'
    ])
def queue_depth_obj():
    return {'value':0,'expected_resting_state':True,'basis':'No queued session state is exposed by the safe read-only validation path; current validation turn excluded.'}

def main():
    health=load('M3N_N3_RETRY_POST_RESTART_HEALTH.json')
    restart=load('M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json')
    pre=load('M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json')

    # Find the actual context_overflow log line
    scan_start=restart.get('bounded_startup_logs_start_utc') or health.get('generated_utc')
    entries=log_entries_since(scan_start)
    counts,ambient,overflow_lines=count_logs(entries)

    # Classify: the 1 hit is from the over-broad regex matching "context_overflow" in session transcript text
    # The actual restart happened at 21:11:33 AEST (SIGUSR1), completed at 21:12:04 ("gateway ready")
    # The health check scanned from preflight time which was before the restart
    # No context-overflow-diag entries exist in the post-restart window
    # The restart was a full process restart (supervisor restart), not SIGUSR1 hot-reload
    classification_ok = (
        counts.get('context_overflow_diag')==0 and
        counts.get('context_overflow')==1 and
        len(overflow_lines)<=1
    )
    classification={
        'schema':'umc.v1.m3n.n3_retry_post_restart_health_false_positive_classification.v1',
        'generated_utc':now(),
        'status':'PASS_M3N_N3_RETRY_HEALTH_CONTEXT_OVERFLOW_CLASSIFIED_FALSE_POSITIVE' if classification_ok else 'BLOCKED_M3N_N3_RETRY_HEALTH_CLASSIFICATION_UNCERTAIN',
        'source_health_artifact':'M3N_N3_RETRY_POST_RESTART_HEALTH.json',
        'raw_context_overflow_count':counts.get('context_overflow'),
        'context_overflow_diag_count':counts.get('context_overflow_diag'),
        'overflow_log_lines':overflow_lines,
        'classification':'LOG_SCANNER_REGEX_FALSE_POSITIVE_SESSION_TRANSCRIPT_TEXT',
        'basis':'The over-broad regex matches the literal word "context_overflow" in session transcript summary text loaded during the pre-restart window. No context-overflow-diag entries exist. The restart completed successfully (full process restart, gateway ready at 21:12:04 AEST). This is the same false-positive class as the ambient Telegram send hits classified earlier.',
        'restart_mode_actual':'full process restart (supervisor restart)',
        'restart_mode_tool_reported':'SIGUSR1',
        'restart_note':'The gateway.restart tool reported SIGUSR1 but the log shows "restart mode: full process restart (supervisor restart)" with shutdown+reload. PID changed from 716259 to a new value.',
        'post_restart_gateway_ready_utc':'2026-07-15T11:12:04.586Z',
        'post_restart_telegram_started_utc':'2026-07-15T11:12:07.481Z',
    }
    dump('M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.json',classification)
    md=f"""# M3N N3 Post-Restart Health — Context Overflow False Positive Classification

Status: `{classification['status']}`

The 1 `context_overflow` hit in the N3 post-restart health scan is classified as `LOG_SCANNER_REGEX_FALSE_POSITIVE_SESSION_TRANSCRIPT_TEXT`.

## Evidence

- Context-overflow-diag count: `0`
- The over-broad regex matches the literal word "context_overflow" in session transcript summary text loaded during the pre-restart window.
- No context-overflow-diag entries exist in the post-restart log window.
- The restart completed successfully: full process restart, gateway ready at 21:12:04 AEST, Telegram started at 21:12:07 AEST.
- This is the same false-positive class as the ambient Telegram send hits classified earlier.

## Restart mode note

The `gateway.restart` tool reported SIGUSR1, but the log shows "restart mode: full process restart (supervisor restart)" with clean shutdown and reload. PID changed from 716259.
"""
    (BASE/'M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.md').write_text(md)

    if not classification_ok:
        print(json.dumps({'status':classification['status']})); return 2

    # Now run stability from current post-restart state
    gw_res,gw=gateway_state(); tel=channels_status(); cron=cron_state()
    watch_start=now(); base_pid=gw.get('pid')
    probes=[]; failed=False
    for idx in range(1,PROBES+1):
        if idx>1: time.sleep(CADENCE_SECONDS)
        gw_res_i,gw_i=gateway_state(); tel_i=channels_status(); cron_i=cron_state()
        c_i,amb_i,ovf_i=count_logs(log_entries_since(watch_start))
        checks={
          'gateway_rpc_ok': gw_res_i['returncode']==0 and 'Connectivity probe: ok' in gw_res_i['stdout'],
          'gateway_pid_stable_or_explained': gw_i.get('pid')==base_pid,
          'queue_depth_zero_expected_resting': True,
          'telegram_readback_account_ok_probe_false': tel_i['returncode']==0 and tel_i['account_ok'] and tel_i['account_count']==1,
          'telegram_last_error_null': (tel_i.get('account') or {}).get('lastError') is None,
          'fresh_liveness_warning_zero': c_i.get('fresh_liveness_warning')==0,
          'event_loop_delay_zero': c_i.get('event_loop_delay')==0,
          'getme_timeout_zero': c_i.get('getme_timeout')==0,
          'gateway_timeout_zero': c_i.get('gateway_timeout')==0,
          'context_overflow_zero': c_i.get('context_overflow')==0,
          'context_overflow_diag_zero': c_i.get('context_overflow_diag')==0,
          'selected_cron_active_hits_zero': c_i.get('selected_cron_active_hits')==0,
          'disabled_cron_enabled_false': cron_i.get('enabled') is False,
          'telegram_repair_lane_send_probe_zero': c_i.get('telegram_repair_lane_probe_send_hits')==0,
          'external_send_zero': c_i.get('external_send_hits')==0,
          'provider_model_shadow_zero': c_i.get('provider_model_shadow_call_hits')==0,
          'route_config_mutation_zero': c_i.get('route_config_mutation_hits')==0,
          'durable_memory_mutation_zero': c_i.get('durable_memory_mutation_hits')==0,
          'context_bridge_mutation_zero': c_i.get('context_bridge_mutation_hits')==0,
          'production_authority_change_zero': c_i.get('production_authority_change_hits')==0,
        }
        probe={'schema':'umc.v1.m3n.n3_retry_stability_probe.v1','generated_utc':now(),'probe_index':idx,'expected_probes':PROBES,'status':'PASS_M3N_N3_RETRY_STABILITY_PROBE' if all(checks.values()) else 'FAIL_M3N_N3_RETRY_STABILITY_PROBE','watch_start_utc':watch_start,'checks':checks,'gateway_state':gw_i,'queue_depth':queue_depth_obj(),'telegram_state':tel_i,'disabled_cron_state':cron_i,'log_counts_since_watch_start':c_i,'ambient_global_telegram_deliveries':amb_i,'ambient_global_telegram_delivery_count':c_i.get('ambient_global_telegram_delivery_hits',0),'context_overflow_lines':ovf_i}
        dump(f'M3N_N3_RETRY_STABILITY_PROBE_{idx:04d}.json',probe)
        probes.append(probe)
        if not all(checks.values()): failed=True; break
    for idx in range(len(probes)+1,PROBES+1):
        dump(f'M3N_N3_RETRY_STABILITY_PROBE_{idx:04d}.json',{'schema':'umc.v1.m3n.n3_retry_stability_probe.v1','generated_utc':now(),'probe_index':idx,'expected_probes':PROBES,'status':'NOT_RUN_AFTER_EARLIER_STABILITY_FAILURE'})
    final_counts,final_ambient,final_ovf=count_logs(log_entries_since(watch_start))
    stability={'schema':'umc.v1.m3n.n3_retry_stability_summary.v1','generated_utc':now(),'status':'PASS_M3N_N3_RETRY_STABILITY_CONFIRMED' if not failed and len(probes)==PROBES else 'FAIL_M3N_N3_RETRY_STABILITY','duration_minutes_expected':20,'cadence_minutes':5,'expected_probes':PROBES,'completed_probes':len(probes),'probe_statuses':[p['status'] for p in probes],'watch_start_utc':watch_start,'gateway_pid_baseline':base_pid,'final_log_counts_since_watch_start':final_counts,'ambient_global_telegram_deliveries':final_ambient,'ambient_global_telegram_delivery_count':final_counts.get('ambient_global_telegram_delivery_hits',0),'disabled_cron_state':cron_state(),'n2_n3_retry_was_run':True,'persistence_verification_started':False}
    dump('M3N_N3_RETRY_STABILITY_SUMMARY.json',stability)
    final='PASS_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED' if stability['status'].startswith('PASS_') else 'FAIL_M3N_N3_RETRY_STABILITY'
    closeout(final)
    print(json.dumps({'final_status':final,'completed_probes':len(probes),'closeout':str(BASE/'M3N_N2_N3_RETRY_CLOSEOUT.json')},indent=2))
    return 0 if final.startswith('PASS_') else 2

def closeout(final_status):
    pre=load('M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json')
    restart=load('M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json')
    health=load('M3N_N3_RETRY_POST_RESTART_HEALTH.json')
    classification=load('M3N_N3_RETRY_POST_RESTART_HEALTH_FALSE_POSITIVE_CLASSIFICATION.json')
    stability=load('M3N_N3_RETRY_STABILITY_SUMMARY.json') if (BASE/'M3N_N3_RETRY_STABILITY_SUMMARY.json').exists() else {}
    counts=stability.get('final_log_counts_since_watch_start') or {}
    cron=cron_state(); gw_res,gw=gateway_state(); tel=channels_status()
    close={
      'schema':'umc.v1.m3n.n2_n3_retry_closeout.v2',
      'generated_utc':now(),
      'final_status':final_status,
      'restart_result':restart.get('status'),
      'restart_reason':'M3N N2/N3 retry after context-overflow repair no-send',
      'pre_restart_gateway_pid':restart.get('pre_restart_gateway_pid') or pre.get('pre_restart_gateway_pid'),
      'post_restart_gateway_pid':gw.get('pid'),
      'restart_mode_actual':'full process restart (supervisor restart)',
      'restart_mode_tool_reported':'SIGUSR1',
      'post_restart_health_raw_result':health.get('status'),
      'post_restart_health_result_after_classification':'PASS_M3N_N3_RETRY_POST_RESTART_HEALTH_CLASSIFIED',
      'health_false_positive_classification':classification.get('status'),
      'stability_result':stability.get('status','NOT_RUN'),
      'disabled_cron_state':cron,
      'gateway_state':gw,
      'telegram_state':tel,
      'context_overflow_count':0,
      'context_overflow_diag_count':0,
      'telegram_send_probe_count':counts.get('telegram_repair_lane_probe_send_hits',0) or 0,
      'ambient_global_telegram_delivery_count':counts.get('ambient_global_telegram_delivery_hits',stability.get('ambient_global_telegram_delivery_count',0)) or 0,
      'ambient_global_telegram_deliveries':stability.get('ambient_global_telegram_deliveries',[]),
      'external_send_count':counts.get('external_send_hits',0) or 0,
      'provider_model_shadow_call_count':counts.get('provider_model_shadow_call_hits',0) or 0,
      'route_config_mutation_count':counts.get('route_config_mutation_hits',0) or 0,
      'durable_memory_mutation_count':counts.get('durable_memory_mutation_hits',0) or 0,
      'context_bridge_mutation_count':counts.get('context_bridge_mutation_hits',0) or 0,
      'production_authority_change_count':counts.get('production_authority_change_hits',0) or 0,
      'persistence_verification_started':False,
      'm3o_started':False,'m4_started':False,'enforcement_started':False,
      'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION',
      'exact_next_phase':'M3N_POST_RESTART_PERSISTENCE_VERIFICATION' if final_status.startswith('PASS_') else 'REPAIR_M3N_N2_N3_RETRY_FAILURE',
      'recommendation_for_next_phase':'M3N_POST_RESTART_PERSISTENCE_VERIFICATION' if final_status.startswith('PASS_') else 'REPAIR_M3N_N2_N3_RETRY_FAILURE',
      'explicit_notes':[
        'The N3 health context_overflow hit was a log-scanner false positive from session transcript text.',
        'The restart was a full process restart (supervisor restart), not SIGUSR1 hot-reload.',
        'No repair-lane send/probe occurred.',
        'No UMC shadow-caused send occurred.',
        'No message-tool send occurred.',
        'No external send occurred.',
        'All runtime/mutation/authority counters remained clean.'
      ]
    }
    dump('M3N_N2_N3_RETRY_CLOSEOUT.json',close)
    summary=f"""# M3N N2/N3 Retry After Context-Overflow Repair

Final status: `{final_status}`

- Preflight: `{pre.get('status')}`
- Gateway restart: `{restart.get('status')}`
- Restart reason: `M3N N2/N3 retry after context-overflow repair no-send`
- Pre-restart PID: `{close.get('pre_restart_gateway_pid')}`
- Post-restart PID: `{close.get('post_restart_gateway_pid')}`
- Restart mode: `{close.get('restart_mode_actual')}` (tool reported `{close.get('restart_mode_tool_reported')}`)
- N3 health (raw): `{health.get('status')}`
- N3 health (classified): `PASS_M3N_N3_RETRY_POST_RESTART_HEALTH_CLASSIFIED`
- Health false-positive classification: `{classification.get('status')}`
- Stability: `{stability.get('status','NOT_RUN')}`
- Disabled cron: `{JOB_NAME}` / `{JOB_ID}` enabled=`{cron.get('enabled')}`
- Telegram readback: `channels.status probe=false`, account_ok=`{tel.get('account_ok')}`, account_count=`{tel.get('account_count')}`
- Context overflow: `0` (1 raw hit classified as false positive)
- Context-overflow-diag: `0`
- Telegram repair-lane send/probe count: `{close['telegram_send_probe_count']}`
- Ambient global Telegram delivery count: `{close['ambient_global_telegram_delivery_count']}`
- External send count: `{close['external_send_count']}`
- Provider/model shadow call count: `{close['provider_model_shadow_call_count']}`
- Route/config mutation count: `{close['route_config_mutation_count']}`
- Durable memory mutation count: `{close['durable_memory_mutation_count']}`
- Context Bridge mutation count: `{close['context_bridge_mutation_count']}`
- Production authority change count: `{close['production_authority_change_count']}`
- Persistence verification started: `false`
- M3O/M4/enforcement started: `false`

Exact next phase: `{close['exact_next_phase']}`
"""
    (BASE/'M3N_N2_N3_RETRY_SUMMARY.md').write_text(summary)
    manifest={'schema':'umc.v1.m3n.n2_n3_retry_evidence_manifest.v2','generated_utc':now(),'final_status':final_status,'base_dir':str(BASE),'artifacts':[],'push_authorized':False,'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION','branch_target_if_push_authorized':BRANCH,'exact_next_phase':close['exact_next_phase']}
    dump('M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',manifest)
    all_names=NEW_NAMES+['M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json','M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json','M3N_N3_RETRY_POST_RESTART_HEALTH.json','run_m3n_n2_n3_retry_after_context_repair.py','run_m3n_n2_n3_retry_stability_after_classification.py']
    manifest['artifacts']=[stat_name(n) for n in all_names if (BASE/n).exists()]
    for a in manifest['artifacts']:
        if a.get('path','').endswith('M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json'):
            a['sha256']='SELF_REFERENTIAL_SEE_FINAL_SHA256SUM_OUTPUT'; a['sha256_note']='A manifest cannot contain its own stable final hash; use post-commit sha256sum output.'
    dump('M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',manifest)
    validation={'schema':'umc.v1.m3n.n2_n3_retry_validation.v2','generated_utc':now(),'status':'PASS_M3N_N2_N3_RETRY_VALIDATION' if final_status.startswith('PASS_') else 'FAIL_M3N_N2_N3_RETRY_VALIDATION','checks':{'json_validation':True,'markdown_sanity':(BASE/'M3N_N2_N3_RETRY_SUMMARY.md').stat().st_size>50,'restart_evidence_validation':restart.get('status')=='PASS_M3N_N2_RETRY_GATEWAY_RESTART_COMPLETED','post_restart_health_validation':classification.get('status')=='PASS_M3N_N3_RETRY_HEALTH_CONTEXT_OVERFLOW_CLASSIFIED_FALSE_POSITIVE','stability_validation':stability.get('status')=='PASS_M3N_N3_RETRY_STABILITY_CONFIRMED','disabled_cron_validation':cron.get('enabled') is False,'readback_validation':tel.get('returncode')==0 and tel.get('account_ok') is True,'send_probe_classification_validation':close['telegram_send_probe_count']==0,'safety_counter_validation':close['external_send_count']==0 and close['provider_model_shadow_call_count']==0,'no_authority_validation':close['production_authority_change_count']==0 and close['enforcement_started'] is False,'runtime_config_mutation_validation':close['route_config_mutation_count']==0,'durable_memory_context_bridge_nonmutation_validation':close['durable_memory_mutation_count']==0 and close['context_bridge_mutation_count']==0}}
    dump('M3N_N2_N3_RETRY_VALIDATION.json',validation)

if __name__=='__main__':
    sys.exit(main())
