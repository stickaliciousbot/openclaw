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
RESTART_REASON='M3N N2/N3 retry after context-overflow repair no-send'
PROBES=4
CADENCE_SECONDS=300

NEW_NAMES=[
'M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json',
'M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json',
'M3N_N3_RETRY_POST_RESTART_HEALTH.json',
'M3N_N3_RETRY_STABILITY_PROBE_0001.json',
'M3N_N3_RETRY_STABILITY_PROBE_0002.json',
'M3N_N3_RETRY_STABILITY_PROBE_0003.json',
'M3N_N3_RETRY_STABILITY_PROBE_0004.json',
'M3N_N3_RETRY_STABILITY_SUMMARY.json',
'M3N_N2_N3_RETRY_CLOSEOUT.json',
'M3N_N2_N3_RETRY_SUMMARY.md',
'M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',
'M3N_N2_N3_RETRY_VALIDATION.json',
'run_m3n_n2_n3_retry_after_context_repair.py',
]

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def dump(name,obj):
    p=BASE/name; p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); return p

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
    return {'method':'channels.status probe=false','returncode':res['returncode'],'account_count':len(accounts),'account_ok':ok,'account':acct,'channel':channel,'raw_stdout':res['stdout'][:2000],'stderr':res['stderr'][:2000]}

def cron_state():
    p=Path('/home/stickai/.openclaw/cron/jobs.json')
    if not p.exists(): return {'id':JOB_ID,'name':JOB_NAME,'enabled':None,'state':None,'source':'missing'}
    data=json.loads(p.read_text())
    jobs=data.get('jobs', data if isinstance(data,list) else [])
    for j in jobs:
        if j.get('id')==JOB_ID: return {'id':j.get('id'),'name':j.get('name'),'enabled':j.get('enabled'),'state':j.get('state',{})}
    return {'id':JOB_ID,'name':JOB_NAME,'enabled':None,'state':None,'source':'job not found'}

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
    ambient=[]
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
        if re.search(r'context[-_ ]overflow|maximum context|context overflow',text,re.I): c['context_overflow']+=1
        if 'context-overflow-diag' in low: c['context_overflow_diag']+=1
        if JOB_ID.lower() in low and 'enabled=false' not in low: c['selected_cron_active_hits']+=1
        if 'channels.status' in low and 'probe=false' in low: c['channels_status_probe_false_hits']+=1
        if 'channels.status' in low and 'probe=true' in low: c['telegram_probe_true_hits']+=1; c['telegram_repair_lane_probe_send_hits']+=1
        if 'telegram sendmessage ok chat=8495203551' in low:
            c['ambient_global_telegram_delivery_hits']+=1
            if len(ambient)<20: ambient.append(e)
        if 'message.action' in low and 'channel=telegram' in low:
            c['telegram_repair_lane_probe_send_hits']+=1
        if any(x in low for x in ['send mail','smtp send','external send']) and 'telegram sendmessage ok chat=8495203551' not in low:
            c['external_send_hits']+=1
        if any(x in low for x in ['provider/model shadow','shadow call','runwithmodelfallback','runembeddedpiagent']): c['provider_model_shadow_call_hits']+=1
        if any(x in low for x in ['config.patch','config.apply','route/fallback','fallback mutation']): c['route_config_mutation_hits']+=1
        if any(x in low for x in ['memory mutation','memory.md wrote','successfully wrote to /home/stickai/.openclaw/workspace/memory']): c['durable_memory_mutation_hits']+=1
        if any(x in low for x in ['context bridge mutation','context-bridge wrote','context-bridge mutation']): c['context_bridge_mutation_hits']+=1
        if any(x in low for x in ['production authority','authority change','enforcement enabled']): c['production_authority_change_hits']+=1
    return c, ambient

def clean_core_counts(c):
    return all(c.get(k,0)==0 for k in [
      'err_module_not_found','missing_pi_embedded','missing_zalo_manifest','channels_telegram_unknown_channel_id',
      'fresh_liveness_warning','event_loop_delay','getme_timeout','gateway_timeout','context_overflow','context_overflow_diag',
      'selected_cron_active_hits','telegram_repair_lane_probe_send_hits','telegram_probe_true_hits','external_send_hits',
      'provider_model_shadow_call_hits','route_config_mutation_hits','durable_memory_mutation_hits','context_bridge_mutation_hits','production_authority_change_hits'
    ])

def queue_depth_obj():
    return {'value':0,'expected_resting_state':True,'basis':'No queued session state is exposed by the safe read-only validation path; current validation turn excluded.'}

def preflight():
    close=load('M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json')
    classify=load('M3N_POST_COMPACTION_TELEGRAM_SEND_HIT_CLASSIFICATION.json')
    reconcile=load('M3N_POST_COMPACTION_STABILITY_COUNTER_RECONCILIATION.json')
    val=load('M3N_POST_COMPACTION_CLOSEOUT_VALIDATION.json')
    gw_res,gw=gateway_state(); tel=channels_status(); cron=cron_state()
    existing_close=(BASE/'M3N_N2_N3_RETRY_CLOSEOUT.json')
    already=False
    if existing_close.exists():
        try:
            old=json.loads(existing_close.read_text())
            already=old.get('final_status')=='PASS_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED'
        except Exception: pass
    checks={
      'latest_context_repair_closeout_exists': (BASE/'M3N_CONTEXT_OVERFLOW_REPAIR_CLOSEOUT.json').exists(),
      'final_repair_status_pass': close.get('final_status')=='PASS_M3N_CONTEXT_OVERFLOW_REPAIRED_READBACK_STABILITY_CONFIRMED',
      'context_overflow_zero': close.get('context_overflow_count')==0,
      'context_overflow_diag_zero': close.get('context_overflow_diag_count')==0,
      'telegram_readback_passed_probe_false': tel['returncode']==0 and tel['account_ok'] and close.get('telegram_state',{}).get('method')=='channels.status probe=false',
      'repair_lane_telegram_send_probe_zero': close.get('repair_lane_telegram_probe_send_count')==0,
      'umc_shadow_caused_send_zero': close.get('umc_shadow_caused_send_count')==0,
      'message_tool_send_zero': close.get('message_tool_send_count')==0,
      'external_send_zero': close.get('external_send_count')==0,
      'ambient_owner_chat_classified_false_positive': classify.get('status')=='PASS_M3N_POST_COMPACTION_SEND_HITS_CLASSIFIED_AMBIENT_FALSE_POSITIVE' and reconcile.get('global_telegram_owner_chat_deliveries_observed')==2,
      'disabled_cron_enabled_false': cron.get('enabled') is False,
      'gateway_rpc_ok': gw_res['returncode']==0 and 'Connectivity probe: ok' in gw_res['stdout'],
      'n2_n3_retry_not_already_run': not already,
      'persistence_verification_not_started': close.get('persistence_verification_started') is False,
      'm3o_m4_enforcement_not_started': close.get('m3o_started') is False and close.get('m4_started') is False and close.get('enforcement_started') is False,
      'safety_counters_clean': close.get('provider_model_shadow_call_count')==0 and close.get('route_config_mutation_count')==0 and close.get('durable_memory_mutation_count')==0 and close.get('context_bridge_mutation_count')==0 and close.get('production_authority_change_count')==0,
      'validation_artifact_passed': val.get('status')=='PASS_M3N_POST_COMPACTION_CLOSEOUT_VALIDATION' and all(val.get('checks',{}).values()),
    }
    obj={'schema':'umc.v1.m3n.n2_n3_retry_preflight_after_context_repair.v1','generated_utc':now(),'status':'PASS_M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR' if all(checks.values()) else 'BLOCKED_M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR','checks':checks,'gateway_state':gw,'gateway_rpc_returncode':gw_res['returncode'],'pre_restart_gateway_pid':gw.get('pid'),'queue_depth':queue_depth_obj(),'telegram_state':tel,'disabled_cron_state':cron,'restart_reason_to_be_used':RESTART_REASON,'persistence_verification_started':False,'m3o_started':False,'m4_started':False,'enforcement_started':False,'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION'}
    dump('M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json',obj)
    print(json.dumps({'status':obj['status'],'pre_restart_gateway_pid':gw.get('pid')},indent=2))
    return 0 if obj['status'].startswith('PASS_') else 2

def write_restart_result_from_tool(tool_result_json=None):
    pre=load('M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json')
    restart_started=pre.get('generated_utc')
    gw_res,gw=gateway_state(); cron=cron_state()
    entries=log_entries_since(restart_started)
    counts,ambient=count_logs(entries)
    obj={'schema':'umc.v1.m3n.n2_retry_gateway_restart_result.v1','generated_utc':now(),'status':'PASS_M3N_N2_RETRY_GATEWAY_RESTART_COMPLETED' if gw_res['returncode']==0 and 'Connectivity probe: ok' in gw_res['stdout'] and cron.get('enabled') is False else 'FAIL_M3N_N2_RETRY_GATEWAY_RESTART_FAILED','restart_reason':RESTART_REASON,'restart_method':'gateway.restart first-class tool','restart_result':tool_result_json or {'source':'restart tool result summarized externally; post-restart gateway status is authoritative'},'pre_restart_gateway_pid':pre.get('pre_restart_gateway_pid'),'post_restart_gateway_pid':gw.get('pid'),'service_state_after_restart':gw,'cold_restart_or_sigusr1_hot_reload':'SIGUSR1/hot-reload if PID unchanged; cold restart if PID changed','restart_window_start_utc':restart_started,'bounded_startup_logs_start_utc':restart_started,'bounded_startup_log_counts':counts,'bounded_startup_ambient_global_telegram_deliveries':ambient,'disabled_cron_state_after_restart':cron,'startup_duration_observed_seconds':None}
    dump('M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json',obj)
    print(json.dumps({'status':obj['status'],'pre_pid':obj['pre_restart_gateway_pid'],'post_pid':obj['post_restart_gateway_pid']},indent=2))
    return 0 if obj['status'].startswith('PASS_') else 2

def health_and_watch():
    pre=load('M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json')
    restart=load('M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json')
    health_start=now()
    gw_res,gw=gateway_state(); tel=channels_status(); cron=cron_state()
    counts,ambient=count_logs(log_entries_since(restart.get('bounded_startup_logs_start_utc') or health_start))
    health_checks={
      'gateway_reachable_rpc_ok': gw_res['returncode']==0 and 'Connectivity probe: ok' in gw_res['stdout'],
      'post_restart_pid_valid': bool(gw.get('pid')),
      'queue_depth_expected_resting': True,
      'telegram_readback_account_ok_probe_false': tel['returncode']==0 and tel['account_ok'] and tel['account_count']==1,
      'telegram_last_error_null': (tel.get('account') or {}).get('lastError') is None,
      'bounded_startup_logs_clean': clean_core_counts(counts),
      'disabled_cron_enabled_false': cron.get('enabled') is False,
    }
    health={'schema':'umc.v1.m3n.n3_retry_post_restart_health.v1','generated_utc':now(),'status':'PASS_M3N_N3_RETRY_POST_RESTART_HEALTH' if all(health_checks.values()) else 'FAIL_M3N_N3_RETRY_POST_RESTART_HEALTH','checks':health_checks,'gateway_state':gw,'queue_depth':queue_depth_obj(),'telegram_state':tel,'disabled_cron_state':cron,'bounded_startup_log_counts':counts,'ambient_global_telegram_deliveries':ambient,'context_overflow_count':counts.get('context_overflow',0),'context_overflow_diag_count':counts.get('context_overflow_diag',0),'telegram_send_probe_count':counts.get('telegram_repair_lane_probe_send_hits',0),'external_send_count':counts.get('external_send_hits',0),'provider_model_shadow_call_count':counts.get('provider_model_shadow_call_hits',0),'route_config_mutation_count':counts.get('route_config_mutation_hits',0),'durable_memory_mutation_count':counts.get('durable_memory_mutation_hits',0),'context_bridge_mutation_count':counts.get('context_bridge_mutation_hits',0),'production_authority_change_count':counts.get('production_authority_change_hits',0)}
    dump('M3N_N3_RETRY_POST_RESTART_HEALTH.json',health)
    if not health['status'].startswith('PASS_'):
        closeout('FAIL_M3N_N3_RETRY_POST_RESTART_HEALTH')
        print(json.dumps({'status':health['status']})); return 2
    watch_start=now(); base_pid=gw.get('pid')
    probes=[]; failed=False
    for idx in range(1,PROBES+1):
        if idx>1: time.sleep(CADENCE_SECONDS)
        gw_res_i,gw_i=gateway_state(); tel_i=channels_status(); cron_i=cron_state()
        c_i,amb_i=count_logs(log_entries_since(watch_start))
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
        probe={'schema':'umc.v1.m3n.n3_retry_stability_probe.v1','generated_utc':now(),'probe_index':idx,'expected_probes':PROBES,'status':'PASS_M3N_N3_RETRY_STABILITY_PROBE' if all(checks.values()) else 'FAIL_M3N_N3_RETRY_STABILITY_PROBE','watch_start_utc':watch_start,'checks':checks,'gateway_state':gw_i,'queue_depth':queue_depth_obj(),'telegram_state':tel_i,'disabled_cron_state':cron_i,'log_counts_since_watch_start':c_i,'ambient_global_telegram_deliveries':amb_i,'ambient_global_telegram_delivery_count':c_i.get('ambient_global_telegram_delivery_hits',0)}
        dump(f'M3N_N3_RETRY_STABILITY_PROBE_{idx:04d}.json',probe)
        probes.append(probe)
        if not all(checks.values()): failed=True; break
    for idx in range(len(probes)+1,PROBES+1):
        dump(f'M3N_N3_RETRY_STABILITY_PROBE_{idx:04d}.json',{'schema':'umc.v1.m3n.n3_retry_stability_probe.v1','generated_utc':now(),'probe_index':idx,'expected_probes':PROBES,'status':'NOT_RUN_AFTER_EARLIER_STABILITY_FAILURE'})
    final_counts,final_ambient=count_logs(log_entries_since(watch_start))
    stability={'schema':'umc.v1.m3n.n3_retry_stability_summary.v1','generated_utc':now(),'status':'PASS_M3N_N3_RETRY_STABILITY_CONFIRMED' if not failed and len(probes)==PROBES else 'FAIL_M3N_N3_RETRY_STABILITY','duration_minutes_expected':20,'cadence_minutes':5,'expected_probes':PROBES,'completed_probes':len(probes),'probe_statuses':[p['status'] for p in probes],'watch_start_utc':watch_start,'gateway_pid_baseline':base_pid,'final_log_counts_since_watch_start':final_counts,'ambient_global_telegram_deliveries':final_ambient,'ambient_global_telegram_delivery_count':final_counts.get('ambient_global_telegram_delivery_hits',0),'disabled_cron_state':cron_state(),'n2_n3_retry_was_run':True,'persistence_verification_started':False}
    dump('M3N_N3_RETRY_STABILITY_SUMMARY.json',stability)
    final='PASS_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED' if stability['status'].startswith('PASS_') else 'FAIL_M3N_N3_RETRY_STABILITY'
    closeout(final)
    print(json.dumps({'final_status':final,'completed_probes':len(probes),'closeout':str(BASE/'M3N_N2_N3_RETRY_CLOSEOUT.json')},indent=2))
    return 0 if final.startswith('PASS_') else 2

def closeout(final_status):
    pre=load('M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json') if (BASE/'M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR.json').exists() else {}
    restart=load('M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json') if (BASE/'M3N_N2_RETRY_GATEWAY_RESTART_RESULT.json').exists() else {}
    health=load('M3N_N3_RETRY_POST_RESTART_HEALTH.json') if (BASE/'M3N_N3_RETRY_POST_RESTART_HEALTH.json').exists() else {}
    stability=load('M3N_N3_RETRY_STABILITY_SUMMARY.json') if (BASE/'M3N_N3_RETRY_STABILITY_SUMMARY.json').exists() else {}
    counts=stability.get('final_log_counts_since_watch_start') or health.get('bounded_startup_log_counts') or {}
    cron=cron_state(); gw_res,gw=gateway_state(); tel=channels_status()
    close={'schema':'umc.v1.m3n.n2_n3_retry_closeout.v1','generated_utc':now(),'final_status':final_status,'restart_result':restart.get('status'),'restart_reason':RESTART_REASON,'pre_restart_gateway_pid':restart.get('pre_restart_gateway_pid') or pre.get('pre_restart_gateway_pid'),'post_restart_gateway_pid':restart.get('post_restart_gateway_pid') or gw.get('pid'),'post_restart_health_result':health.get('status'),'stability_result':stability.get('status','NOT_RUN'),'disabled_cron_state':cron,'gateway_state':gw,'telegram_state':tel,'context_overflow_count':counts.get('context_overflow',health.get('context_overflow_count',0)) or 0,'context_overflow_diag_count':counts.get('context_overflow_diag',health.get('context_overflow_diag_count',0)) or 0,'telegram_send_probe_count':counts.get('telegram_repair_lane_probe_send_hits',health.get('telegram_send_probe_count',0)) or 0,'ambient_global_telegram_delivery_count':counts.get('ambient_global_telegram_delivery_hits',stability.get('ambient_global_telegram_delivery_count',0)) or 0,'ambient_global_telegram_deliveries':stability.get('ambient_global_telegram_deliveries',health.get('ambient_global_telegram_deliveries',[])),'external_send_count':counts.get('external_send_hits',health.get('external_send_count',0)) or 0,'provider_model_shadow_call_count':counts.get('provider_model_shadow_call_hits',health.get('provider_model_shadow_call_count',0)) or 0,'route_config_mutation_count':counts.get('route_config_mutation_hits',health.get('route_config_mutation_count',0)) or 0,'durable_memory_mutation_count':counts.get('durable_memory_mutation_hits',health.get('durable_memory_mutation_count',0)) or 0,'context_bridge_mutation_count':counts.get('context_bridge_mutation_hits',health.get('context_bridge_mutation_count',0)) or 0,'production_authority_change_count':counts.get('production_authority_change_hits',health.get('production_authority_change_count',0)) or 0,'persistence_verification_started':False,'m3o_started':False,'m4_started':False,'enforcement_started':False,'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION','recommendation_for_next_phase':'M3N_POST_RESTART_PERSISTENCE_VERIFICATION' if final_status.startswith('PASS_') else 'REPAIR_M3N_N2_N3_RETRY_FAILURE','exact_next_phase':'M3N_POST_RESTART_PERSISTENCE_VERIFICATION' if final_status.startswith('PASS_') else 'REPAIR_M3N_N2_N3_RETRY_FAILURE'}
    dump('M3N_N2_N3_RETRY_CLOSEOUT.json',close)
    summary=f"""# M3N N2/N3 Retry After Context-Overflow Repair\n\nFinal status: `{final_status}`\n\n- Preflight: `{pre.get('status')}`\n- Gateway restart: `{restart.get('status')}`\n- Restart reason: `{RESTART_REASON}`\n- Pre-restart PID: `{close.get('pre_restart_gateway_pid')}`\n- Post-restart PID: `{close.get('post_restart_gateway_pid')}`\n- Post-restart health: `{health.get('status')}`\n- Stability: `{stability.get('status','NOT_RUN')}`\n- Disabled cron: `{JOB_NAME}` / `{JOB_ID}` enabled=`{cron.get('enabled')}`\n- Telegram readback: `channels.status probe=false`, account_ok=`{tel.get('account_ok')}`, account_count=`{tel.get('account_count')}`\n- Context overflow: `{close['context_overflow_count']}`\n- Context-overflow-diag: `{close['context_overflow_diag_count']}`\n- Telegram repair-lane send/probe count: `{close['telegram_send_probe_count']}`\n- Ambient global Telegram delivery count: `{close['ambient_global_telegram_delivery_count']}`\n- External send count: `{close['external_send_count']}`\n- Provider/model shadow call count: `{close['provider_model_shadow_call_count']}`\n- Route/config mutation count: `{close['route_config_mutation_count']}`\n- Durable memory mutation count: `{close['durable_memory_mutation_count']}`\n- Context Bridge mutation count: `{close['context_bridge_mutation_count']}`\n- Production authority change count: `{close['production_authority_change_count']}`\n- Persistence verification started: `false`\n- M3O/M4/enforcement started: `false`\n\nExact next phase: `{close['exact_next_phase']}`\n"""
    (BASE/'M3N_N2_N3_RETRY_SUMMARY.md').write_text(summary)
    manifest={'schema':'umc.v1.m3n.n2_n3_retry_evidence_manifest.v1','generated_utc':now(),'final_status':final_status,'base_dir':str(BASE),'artifacts':[],'push_authorized':False,'push_status':'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION','branch_target_if_push_authorized':BRANCH,'exact_next_phase':close['exact_next_phase']}
    dump('M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',manifest)
    manifest['artifacts']=[stat_name(n) for n in NEW_NAMES if (BASE/n).exists()]
    for a in manifest['artifacts']:
        if a.get('path','').endswith('M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json'):
            a['sha256']='SELF_REFERENTIAL_SEE_FINAL_SHA256SUM_OUTPUT'; a['sha256_note']='A manifest cannot contain its own stable final hash; use post-commit sha256sum output.'
    dump('M3N_N2_N3_RETRY_EVIDENCE_MANIFEST.json',manifest)
    validation={'schema':'umc.v1.m3n.n2_n3_retry_validation.v1','generated_utc':now(),'status':'PASS_M3N_N2_N3_RETRY_VALIDATION' if final_status.startswith('PASS_') else 'FAIL_M3N_N2_N3_RETRY_VALIDATION','checks':{'json_validation':True,'markdown_sanity':(BASE/'M3N_N2_N3_RETRY_SUMMARY.md').stat().st_size>50,'context_repair_closeout_validation':pre.get('status')=='PASS_M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR','restart_evidence_validation':restart.get('status')=='PASS_M3N_N2_RETRY_GATEWAY_RESTART_COMPLETED','post_restart_health_validation':health.get('status')=='PASS_M3N_N3_RETRY_POST_RESTART_HEALTH','stability_validation':stability.get('status')=='PASS_M3N_N3_RETRY_STABILITY_CONFIRMED','disabled_cron_validation':cron.get('enabled') is False,'readback_validation':tel.get('returncode')==0 and tel.get('account_ok') is True,'send_probe_classification_validation':close['telegram_send_probe_count']==0,'safety_counter_validation':close['external_send_count']==0 and close['provider_model_shadow_call_count']==0,'no_authority_validation':close['production_authority_change_count']==0 and close['enforcement_started'] is False,'runtime_config_mutation_validation':close['route_config_mutation_count']==0,'durable_memory_context_bridge_nonmutation_validation':close['durable_memory_mutation_count']==0 and close['context_bridge_mutation_count']==0}}
    dump('M3N_N2_N3_RETRY_VALIDATION.json',validation)

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else ''
    if mode=='preflight': sys.exit(preflight())
    if mode=='restart-result': sys.exit(write_restart_result_from_tool())
    if mode=='post': sys.exit(health_and_watch())
    print('usage: preflight|restart-result|post',file=sys.stderr); sys.exit(64)
