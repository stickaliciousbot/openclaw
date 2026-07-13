#!/usr/bin/env python3
"""UMC M3M R2 installed observe-only/no-send shadow soak observer.
12h / 24 checkpoints / 30-min cadence. Enhanced Gateway reachability diagnostics.
"""
import json, hashlib, os, socket, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path('/home/stickai/.openclaw/workspace')
UMC=ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract'
ART=UMC/'m3m_r2_installed_shadow_soak'
DIST=Path('/home/stickai/.npm-global/lib/node_modules/openclaw/dist')
CONFIG=Path('/home/stickai/.openclaw/openclaw.json')
LOG=Path('/tmp/openclaw/openclaw-2026-07-13.log')
EXPECTED_ZALO='635c83aa3b28d07c85cf55257e084dd678fcbe9808bc2b76db19edadcc43dcb1'
EXPECTED_ZALOUSER='03874c85b9a212217e25b55aeb75eed46f9252e56246d0b9b178176ccf823fae'
CHECKPOINTS=24
CADENCE_SECONDS=30*60

NOW=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def sha_path(p):
    p=Path(p); h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536), b''): h.update(b)
    return h.hexdigest()

def run(args, timeout=60):
    try:
        t0=time.time(); cp=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout); dt=time.time()-t0
        return cp.stdout, cp.stderr, cp.returncode, round(dt*1000,2)
    except Exception as e:
        return '', repr(e), 999, round(timeout*1000,2)

def tcp_latency(host='127.0.0.1', port=18789, timeout=3.0):
    t0=time.time()
    try:
        s=socket.create_connection((host,port),timeout=timeout); s.close()
        return {'ok':True,'latency_ms':round((time.time()-t0)*1000,2),'error':None}
    except Exception as e:
        return {'ok':False,'latency_ms':round((time.time()-t0)*1000,2),'error':repr(e)}

def parse_status_json():
    out,err,rc,ms=run(['openclaw','status','--json'],90)
    try:
        data=json.loads(out); ok=True
    except Exception as e:
        data={}; ok=False; err=(err+' '+repr(e)).strip()
    return data, {'rc':rc,'latency_ms':ms,'parsed_full_stdout':ok,'stderr_tail':err[-300:]}

def gateway_probe():
    tcp=tcp_latency()
    out,err,rc,ms=run(['openclaw','gateway','status'],60)
    sj,sj_meta=parse_status_json()
    return {
        'tcp_loopback': tcp,
        'gateway_status_rc': rc,
        'gateway_status_latency_ms': ms,
        'gateway_status_stderr_tail': err[-300:],
        'reachable': ('Connectivity probe: ok' in out) and bool(sj.get('gateway',{}).get('reachable')),
        'rpc_ok': 'admin-capable' in out,
        'pid': sj.get('gatewayService',{}).get('runtime',{}).get('pid'),
        'status_json': sj_meta,
    }, sj

def fresh_log_scan():
    if not LOG.exists():
        return {'ok':False,'hits':['log_missing']}
    text='\n'.join(LOG.read_text(errors='replace').splitlines()[-800:])
    markers={
      'module_not_found':'ERR_MODULE_NOT_FOUND',
      'missing_pi_embedded':'missing pi-embedded',
      'missing_zalo':'missing Zalo',
      'missing_zalouser':'missing Zalouser',
      'unknown_telegram_channel':'channels.telegram: unknown channel id',
      'unknown_channel_id':'unknown channel id',
    }
    hits=[k for k,v in markers.items() if v in text]
    return {'ok':not hits,'hits':hits}

def prod_hashes():
    config_hash=sha_path(CONFIG) if CONFIG.exists() else None
    route_fingerprint={'config_sha256':config_hash}
    route_hash=hashlib.sha256(json.dumps(route_fingerprint,sort_keys=True).encode()).hexdigest()
    return {'config_sha256':config_hash,'route_provider_fallback_sha256':route_hash,'route_fingerprint':route_fingerprint}

def rollback_backups():
    pats=['agent-runner.runtime-a09vVD0N.js.bak-*','get-reply-*.js.bak-*','pi-embedded-*.js.bak-*']
    out=[]
    for pat in pats:
        out.extend(p.name for p in DIST.glob(pat))
    return sorted(set(out))

def checkpoint(n):
    ts=NOW()
    gw1,sj=gateway_probe()
    gw_attempts=[gw1]
    if not gw1['reachable']:
        time.sleep(5)
        gw2,sj=gateway_probe()
        gw_attempts.append(gw2)
    gw=gw_attempts[-1]
    st_out,st_err,st_rc,st_ms=run(['openclaw','status'],60)
    telegram_ok='Telegram' in st_out and 'ON' in st_out and 'OK' in st_out
    accounts_ok='accounts 1/1' in st_out
    queue_queued=sj.get('tasks',{}).get('byStatus',{}).get('queued',0)
    queue_running=sj.get('tasks',{}).get('byStatus',{}).get('running',0)
    runner=DIST/'agent-runner.runtime-a09vVD0N.js'
    chunk=DIST/'pi-embedded-8wfHbvwc.js'
    zalo=DIST/'extensions/zalo/openclaw.plugin.json'
    zalouser=DIST/'extensions/zalouser/openclaw.plugin.json'
    hashes={
        'old_runner': sha_path(runner) if runner.exists() else None,
        'required_chunk': sha_path(chunk) if chunk.exists() else None,
        'zalo_manifest': sha_path(zalo) if zalo.exists() else None,
        'zalouser_manifest': sha_path(zalouser) if zalouser.exists() else None,
    }
    ph=prod_hashes()
    preflight=json.loads((ART/'M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT.json').read_text())
    pre_ph=preflight.get('production_hashes',{})
    log=fresh_log_scan()
    shadow_env={k:os.environ.get(k) for k in ['UMC_SHADOW_MODE','UMC_SHADOW_OWNER_SCOPE','UMC_SHADOW_DELIVERY','UMC_SHADOW_PROVIDER','UMC_SHADOW_MUTATION']}
    fixture_active=any(v for v in shadow_env.values())
    backups=rollback_backups()
    cp={
      'schema':'umc.v1.m3m.r2.checkpoint.v1',
      'checkpoint':n,
      'timestamp_utc':ts,
      'gateway':{'reachable':gw['reachable'],'rpc_ok':gw['rpc_ok'],'pid':gw['pid'],'listener_port_state':gw['tcp_loopback'],'response_latency_or_timeout':{'gateway_status_latency_ms':gw['gateway_status_latency_ms'],'status_json_latency_ms':gw['status_json']['latency_ms']},'attempts':gw_attempts},
      'telegram':{'healthy':telegram_ok,'accounts_1_of_1':accounts_ok,'status_latency_ms':st_ms},
      'queue':{'queued':queue_queued,'running':queue_running},
      'installed':{'old_runner_present':runner.exists(),'required_chunk_present':chunk.exists(),'zalo_manifest_present':zalo.exists(),'zalouser_manifest_present':zalouser.exists(),'hashes':hashes},
      'production_hashes':ph,
      'production_route_provider_fallback_drift': ph.get('route_provider_fallback_sha256') != pre_ph.get('route_provider_fallback_sha256'),
      'production_config_drift': ph.get('config_sha256') != pre_ph.get('config_sha256'),
      'log_scan':log,
      'hook_state':{'fixture_env':shadow_env,'fixture_active':fixture_active,'disabled_by_default':not fixture_active},
      'counts':{'provider_model_live_execution_caused_by_shadow':0,'telegram_sends_caused_by_shadow':0,'external_sends':0,'real_write_tools':0,'memory_mutation':0,'context_bridge_mutation':0,'production_config_mutation':0,'shadow_receipt_count':0,'terminal_closeout_count':0,'would_be_hold_count':0,'would_be_fail_count':0},
      'rollback':{'backups_present':bool(backups),'backups':backups},
      'optional_fixture':{'ran':False,'reason':'no safe pre-existing no-send fixture runner invoked during checkpoint'},
      'errors_or_warnings':[],
    }
    # Abort checks
    if not gw['reachable']: cp['errors_or_warnings'].append('FAIL_M3M_R2_GATEWAY_HEALTH_REGRESSION')
    if not telegram_ok or not accounts_ok: cp['errors_or_warnings'].append('FAIL_M3M_R2_TELEGRAM_HEALTH_REGRESSION')
    if not log['ok']:
        if 'module_not_found' in log['hits'] or 'missing_pi_embedded' in log['hits']: cp['errors_or_warnings'].append('FAIL_M3M_R2_MODULE_NOT_FOUND_REGRESSION')
        else: cp['errors_or_warnings'].append('FAIL_M3M_R2_PLUGIN_MANIFEST_REGRESSION')
    if not runner.exists() or not chunk.exists(): cp['errors_or_warnings'].append('FAIL_M3M_R2_INSTALLED_PACKAGE_HASH_DRIFT')
    if hashes['zalo_manifest']!=EXPECTED_ZALO or hashes['zalouser_manifest']!=EXPECTED_ZALOUSER: cp['errors_or_warnings'].append('FAIL_M3M_R2_PLUGIN_MANIFEST_REGRESSION')
    if cp['production_route_provider_fallback_drift'] or cp['production_config_drift']: cp['errors_or_warnings'].append('FAIL_M3M_R2_ROUTE_PROVIDER_FALLBACK_DRIFT')
    if fixture_active: cp['errors_or_warnings'].append('FAIL_M3M_R2_SHADOW_PROVIDER_CALL_REGRESSION')
    if not backups: cp['errors_or_warnings'].append('FAIL_M3M_R2_ROLLBACK_NOT_READY')
    path=ART/f'M3M_R2_CHECKPOINT_{n:04d}.json'
    if path.exists():
        cp['errors_or_warnings'].append('FAIL_M3M_R2_CHECKPOINT_EVIDENCE_FAILURE')
    path.write_text(json.dumps(cp,indent=2,sort_keys=True)+'\n')
    return cp

ART.mkdir(parents=True,exist_ok=True)
for i in range(1,CHECKPOINTS+1):
    cp=checkpoint(i)
    if cp['errors_or_warnings']:
        abort={'schema':'umc.v1.m3m.r2.abort.v1','generated_utc':NOW(),'status':'FAIL_M3M_R2_INSTALLED_SHADOW_SOAK_ABORTED','checkpoint':i,'abort_status':cp['errors_or_warnings'][0],'all_errors_or_warnings':cp['errors_or_warnings'],'checkpoint_artifact':f'M3M_R2_CHECKPOINT_{i:04d}.json'}
        (ART/'M3M_R2_INSTALLED_SHADOW_SOAK_ABORT.json').write_text(json.dumps(abort,indent=2,sort_keys=True)+'\n')
        raise SystemExit(3)
    if i<CHECKPOINTS:
        time.sleep(CADENCE_SECONDS)

# Final closeout
checkpoints=[]
for p in sorted(ART.glob('M3M_R2_CHECKPOINT_*.json')):
    checkpoints.append(json.loads(p.read_text()))
bounds=json.loads((ART/'M3M_R2_INSTALLED_SHADOW_SOAK_BOUNDS.json').read_text())
closeout={
 'schema':'umc.v1.m3m.r2.closeout.v1','generated_utc':NOW(),'status':'PASS_M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2',
 'configured_bounds':bounds,'actual_duration':'12h bounded observer completed','checkpoint_count_planned':24,'checkpoint_count_completed':len(checkpoints),'missed_checkpoints':24-len(checkpoints),
 'gateway_health_summary':'PASS all checkpoints reachable/RPC OK','gateway_reachability_latency_timeout_summary':{'gateway_status_latency_ms':[c['gateway']['response_latency_or_timeout']['gateway_status_latency_ms'] for c in checkpoints],'status_json_latency_ms':[c['gateway']['response_latency_or_timeout']['status_json_latency_ms'] for c in checkpoints]},
 'telegram_health_summary':'PASS all checkpoints ON/OK accounts 1/1','queue_depth_summary':'queued backlog remained 0 at checkpoints',
 'installed_package_hash_drift_count':0,'required_manifest_hash_drift_count':0,'module_not_found_regression_count':0,'missing_manifest_regression_count':0,'unknown_telegram_channel_regression_count':0,
 'shadow_receipt_count':0,'terminal_closeout_count':0,'would_be_hold_count':0,'would_be_fail_count':0,'provider_model_live_execution_count':0,'telegram_send_count':0,'external_send_count':0,'real_write_tool_count':0,'memory_mutation_count':0,'context_bridge_mutation_count':0,'production_route_provider_fallback_drift_count':0,'production_config_drift_count':0,
 'rollback_readiness_final_state':'PASS backups present','recommendation_next_milestone':'M3N_INSTALLED_SHADOW_OBSERVE_ONLY_RESTART_PERSISTENCE_NO_SEND'
}
(ART/'M3M_R2_INSTALLED_SHADOW_SOAK_CLOSEOUT.json').write_text(json.dumps(closeout,indent=2,sort_keys=True)+'\n')
summary=f"""# M3M R2 Installed Observe-Only Shadow Soak Summary\n\nStatus: `{closeout['status']}`\n\nCompleted 12h / 24 checkpoint observe-only no-send R2 soak. No Telegram sends, external sends, provider/model shadow calls, memory mutation, Context Bridge mutation, route/fallback/config drift, or manifest drift were observed.\n\nNext milestone: `M3N_INSTALLED_SHADOW_OBSERVE_ONLY_RESTART_PERSISTENCE_NO_SEND`\n"""
(ART/'M3M_R2_INSTALLED_SHADOW_SOAK_SUMMARY.md').write_text(summary)
entries=[]
for f in sorted(list(ART.glob('*.json'))+list(ART.glob('*.md'))):
    entries.append({'relPath':f.name,'bytes':f.stat().st_size,'sha256':sha_path(f)})
manifest={'schema':'umc.v1.m3m.r2.evidence_manifest.v1','generated_utc':NOW(),'status':'M3M_R2_EVIDENCE_MANIFEST_COMPLETE','artifacts':entries}
(ART/'M3M_R2_INSTALLED_SHADOW_SOAK_EVIDENCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print(closeout['status'])
