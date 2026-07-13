#!/usr/bin/env python3
"""M3M R2B preflight and bounds after canonical route fingerprint parity repair."""
import json, os, socket, subprocess, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

from m3m_route_fingerprint import canonical_fingerprint_from_config_file, sha256_path

ROOT=Path('/home/stickai/.openclaw/workspace')
UMC=ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract'
R1=UMC/'m3m_installed_shadow_soak_retry'
FAILED_R2=UMC/'m3m_r2_installed_shadow_soak'
REPAIR=UMC/'m3m_r2_fingerprint_parity_repair'
ART=UMC/'m3m_r2b_installed_shadow_soak'
DIST=Path('/home/stickai/.npm-global/lib/node_modules/openclaw/dist')
CONFIG=Path('/home/stickai/.openclaw/openclaw.json')
LOG=Path('/tmp/openclaw/openclaw-2026-07-13.log')
NOW=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
EXPECTED_ZALO='635c83aa3b28d07c85cf55257e084dd678fcbe9808bc2b76db19edadcc43dcb1'
EXPECTED_ZALOUSER='03874c85b9a212217e25b55aeb75eed46f9252e56246d0b9b178176ccf823fae'

def readj(p): return json.loads(Path(p).read_text())
def writej(name,obj):
    ART.mkdir(parents=True, exist_ok=True)
    p=ART/name
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    return p

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
        return True, round((time.time()-t0)*1000,2), None
    except Exception as e:
        return False, round((time.time()-t0)*1000,2), repr(e)

def log_clean():
    if not LOG.exists(): return False, ['log_missing']
    tail='\n'.join(LOG.read_text(errors='replace').splitlines()[-800:])
    markers=['ERR_MODULE_NOT_FOUND','missing pi-embedded','missing Zalo','missing Zalouser','channels.telegram: unknown channel id','unknown channel id']
    hits=[m for m in markers if m in tail]
    return not hits, hits

# Required prior/repair evidence.
r1_abort=readj(R1/'M3M_RETRY_ABORT.json')
r1_stability=readj(R1/'M3M_POST_ABORT_HEALTH_STABILITY_SUMMARY.json')
r2_closeout=readj(FAILED_R2/'M3M_R2_INSTALLED_SHADOW_SOAK_CLOSEOUT.json')
repair=readj(REPAIR/'M3M_R2_ROUTE_FINGERPRINT_PARITY_REPAIR_RESULT.json')
fixtures=readj(REPAIR/'M3M_R2_ROUTE_FINGERPRINT_PARITY_FIXTURE_RESULTS.json')
# Health.
gw_out, gw_err, gw_rc, gw_ms = run(['openclaw','gateway','status'],60)
st_out, st_err, st_rc, st_ms = run(['openclaw','status'],60)
sj_out, sj_err, sj_rc, sj_ms = run(['openclaw','status','--json'],90)
try:
    sj=json.loads(sj_out); status_json_parsed=True
except Exception:
    sj={}; status_json_parsed=False
listener_ok, listener_ms, listener_err=tcp_latency()
gateway_reachable=('Connectivity probe: ok' in gw_out) and bool(sj.get('gateway',{}).get('reachable'))
gateway_rpc_ok='admin-capable' in gw_out
telegram_ok='Telegram' in st_out and 'ON' in st_out and 'OK' in st_out
accounts_ok='accounts 1/1' in st_out
queue_queued=sj.get('tasks',{}).get('byStatus',{}).get('queued',0)
queue_running=sj.get('tasks',{}).get('byStatus',{}).get('running',0)
queue_resting=(queue_queued==0 and queue_running<=1)
runner=DIST/'agent-runner.runtime-a09vVD0N.js'
chunk=DIST/'pi-embedded-8wfHbvwc.js'
zalo=DIST/'extensions/zalo/openclaw.plugin.json'
zalouser=DIST/'extensions/zalouser/openclaw.plugin.json'
logs_ok, log_hits=log_clean()
fingerprint=canonical_fingerprint_from_config_file(CONFIG)
failed_r2_preflight=readj(FAILED_R2/'M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT.json')
failed_r2_config_hash=failed_r2_preflight.get('production_hashes',{}).get('config_sha256')
shadow_env={k:os.environ.get(k) for k in ['UMC_SHADOW_MODE','UMC_SHADOW_OWNER_SCOPE','UMC_SHADOW_DELIVERY','UMC_SHADOW_PROVIDER','UMC_SHADOW_MUTATION']}
fixture_env_active=any(v for v in shadow_env.values())
backups=[]
for pat in ['agent-runner.runtime-a09vVD0N.js.bak-*','get-reply-*.js.bak-*','pi-embedded-*.js.bak-*']:
    backups.extend(p.name for p in DIST.glob(pat))
artifact_names=[p.name for p in UMC.rglob('*') if p.is_file() and 'prompt-chunks' not in str(p)]
m3n_started=any(n.startswith('M3N_') or 'M3N_INSTALLED' in n for n in artifact_names)
checks={
 'failed_r2_status_preserved': r2_closeout.get('status')=='FAIL_M3M_R2_INSTALLED_SHADOW_SOAK_ABORTED',
 'failed_r2_false_drift_classified': r2_closeout.get('fingerprint_shape_mismatch_detected') is True,
 'r1_abort_not_pass': r1_abort.get('status')=='FAIL_M3M_INSTALLED_SHADOW_SOAK_RETRY_ABORTED',
 'r1_abort_reason_gateway_unreachable': r1_abort.get('reason')=='GATEWAY_UNREACHABLE',
 'post_abort_stability_pass': r1_stability.get('status')=='PASS_M3M_POST_ABORT_HEALTH_STABILITY_CONFIRMED',
 'repair_implemented': repair.get('status')=='PASS_M3M_R2_ROUTE_FINGERPRINT_PARITY_REPAIR_IMPLEMENTED',
 'fixtures_pass': fixtures.get('status')=='PASS_M3M_R2_ROUTE_FINGERPRINT_PARITY_FIXTURES',
 'production_config_hash_unchanged_from_failed_r2': fingerprint['production_config_sha256']==failed_r2_config_hash,
 'gateway_reachable': gateway_reachable,
 'gateway_rpc_ok': gateway_rpc_ok,
 'telegram_on_ok': telegram_ok and accounts_ok,
 'status_json_parsed': status_json_parsed,
 'queue_resting': queue_resting,
 'old_runner_present': runner.exists(),
 'required_chunk_present': chunk.exists(),
 'zalo_manifest_hash_match': sha256_path(zalo)==EXPECTED_ZALO if zalo.exists() else False,
 'zalouser_manifest_hash_match': sha256_path(zalouser)==EXPECTED_ZALOUSER if zalouser.exists() else False,
 'fresh_logs_clean': logs_ok,
 'hook_disabled_by_default': not fixture_env_active,
 'rollback_backups_known': bool(backups),
 'm3n_not_started': not m3n_started,
}
status='PASS_M3M_R2B_INSTALLED_SHADOW_SOAK_PREFLIGHT' if all(checks.values()) else 'BLOCKED_M3M_R2B_INSTALLED_SHADOW_SOAK_PREFLIGHT'
preflight={
 'schema':'umc.v1.m3m.r2b.installed_shadow_soak_preflight.v1','generated_utc':NOW(),'status':status,'checks':checks,
 'failed_r2_root':str(FAILED_R2.relative_to(UMC)),'repair_root':str(REPAIR.relative_to(UMC)),
 'gateway':{'reachable':gateway_reachable,'rpc_ok':gateway_rpc_ok,'pid':sj.get('gatewayService',{}).get('runtime',{}).get('pid'),'gateway_status_latency_ms':gw_ms,'status_json_latency_ms':sj_ms,'listener_ok':listener_ok,'listener_latency_ms':listener_ms,'listener_error':listener_err},
 'telegram':{'healthy':telegram_ok,'accounts_1_of_1':accounts_ok},
 'queue':{'queued':queue_queued,'running':queue_running,'resting':queue_resting},
 'installed_hashes':{'runner':sha256_path(runner) if runner.exists() else None,'chunk':sha256_path(chunk) if chunk.exists() else None,'zalo_manifest':sha256_path(zalo) if zalo.exists() else None,'zalouser_manifest':sha256_path(zalouser) if zalouser.exists() else None},
 'production_hashes':fingerprint,
 'failed_r2_production_config_sha256':failed_r2_config_hash,
 'bounded_fresh_log_scan':{'ok':logs_ok,'hits':log_hits},
 'hook_state':{'fixture_env':shadow_env,'fixture_env_active':fixture_env_active,'disabled_by_default':not fixture_env_active},
 'rollback_backups':sorted(set(backups)),'m3n_started':m3n_started,
 'safety_counters':{'provider_model_shadow_calls':0,'telegram_sends':0,'external_sends':0,'memory_mutation':0,'context_bridge_mutation':0,'route_fallback_mutation':0,'real_write_tools':0},
}
writej('M3M_R2B_INSTALLED_SHADOW_SOAK_PREFLIGHT.json', preflight)
if status.startswith('BLOCKED'):
    print(json.dumps(preflight,indent=2,sort_keys=True))
    raise SystemExit(2)
start=datetime.now(timezone.utc).replace(microsecond=0)
bounds={'schema':'umc.v1.m3m.r2b.installed_shadow_soak_bounds.v1','generated_utc':NOW(),'status':'M3M_R2B_SOAK_BOUNDS_DEFINED','mode':'duration','duration_hours':12,'checkpoint_count':24,'checkpoint_cadence_minutes':30,'hard_stop':True,'retry':'R2B','reason':'R2 false drift abort repaired via canonical route fingerprint helper','start_utc':start.isoformat().replace('+00:00','Z'),'expected_end_utc':(start+timedelta(hours=12)).isoformat().replace('+00:00','Z')}
writej('M3M_R2B_INSTALLED_SHADOW_SOAK_BOUNDS.json', bounds)
print(json.dumps({'status':status,'artifact_dir':str(ART),'bounds':bounds},indent=2,sort_keys=True))
