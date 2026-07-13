#!/usr/bin/env python3
import json, hashlib, os, socket, subprocess, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path('/home/stickai/.openclaw/workspace')
UMC=ROOT/'sharedspace/runtime-kernel-validation/universal-model-contract'
R1=UMC/'m3m_installed_shadow_soak_retry'
ART=UMC/'m3m_r2_installed_shadow_soak'
DIST=Path('/home/stickai/.npm-global/lib/node_modules/openclaw/dist')
CONFIG=Path('/home/stickai/.openclaw/openclaw.json')
LOG=Path('/tmp/openclaw/openclaw-2026-07-13.log')
NOW=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
EXPECTED_ZALO='635c83aa3b28d07c85cf55257e084dd678fcbe9808bc2b76db19edadcc43dcb1'
EXPECTED_ZALOUSER='03874c85b9a212217e25b55aeb75eed46f9252e56246d0b9b178176ccf823fae'

def sha_path(p):
    p=Path(p); h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536), b''): h.update(b)
    return h.hexdigest()

def readj(p): return json.loads(Path(p).read_text())
def writej(name,obj):
    ART.mkdir(parents=True, exist_ok=True)
    p=ART/name
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    return p

def run(args, timeout=60):
    try:
        t0=time.time(); cp=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout); dt=time.time()-t0
        return cp.stdout, cp.stderr, cp.returncode, dt
    except Exception as e:
        return '', repr(e), 999, timeout

def tcp_latency(host='127.0.0.1', port=18789, timeout=3.0):
    t0=time.time()
    try:
        s=socket.create_connection((host,port),timeout=timeout); s.close()
        return True, round((time.time()-t0)*1000,2), None
    except Exception as e:
        return False, round((time.time()-t0)*1000,2), repr(e)

def log_clean():
    if not LOG.exists(): return False, ['log_missing']
    tail='\n'.join(LOG.read_text(errors='replace').splitlines()[-600:])
    markers=['ERR_MODULE_NOT_FOUND','missing pi-embedded','missing Zalo','missing Zalouser','channels.telegram: unknown channel id','unknown channel id']
    hits=[m for m in markers if m in tail]
    return not hits, hits

ART.mkdir(parents=True, exist_ok=True)
# Prior evidence
prior_closeout = readj(R1/'M3M_SOAK_ABORT_PRESERVATION_FINAL_CLOSEOUT.json')
stability = readj(R1/'M3M_POST_ABORT_HEALTH_STABILITY_SUMMARY.json')
abort = readj(R1/'M3M_RETRY_ABORT.json')
# Health
gw_out, gw_err, gw_rc, gw_dt = run(['openclaw','gateway','status'])
st_out, st_err, st_rc, st_dt = run(['openclaw','status'])
sj_out, sj_err, sj_rc, sj_dt = run(['openclaw','status','--json'])
try:
    sj=json.loads(sj_out)
    status_json_parsed_full_stdout=True
except Exception:
    sj={}
    status_json_parsed_full_stdout=False

listener_ok, listener_ms, listener_err = tcp_latency()
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
runner_hash=sha_path(runner) if runner.exists() else None
chunk_hash=sha_path(chunk) if chunk.exists() else None
zalo_hash=sha_path(zalo) if zalo.exists() else None
zalouser_hash=sha_path(zalouser) if zalouser.exists() else None
config_hash=sha_path(CONFIG) if CONFIG.exists() else None
# Route/provider/fallback fingerprint: status sessions default model + config hash
route_fingerprint={'config_sha256':config_hash,'default_model':sj.get('agents',{}).get('defaultModel') or sj.get('sessions',{}).get('defaultModel') or 'unknown'}
route_hash=hashlib.sha256(json.dumps(route_fingerprint,sort_keys=True).encode()).hexdigest()
logs_ok, log_hits=log_clean()
# Hook state: explicit fixture env inactive in this process; artifact records default disabled by absence of fixture env.
shadow_env={k:os.environ.get(k) for k in ['UMC_SHADOW_MODE','UMC_SHADOW_OWNER_SCOPE','UMC_SHADOW_DELIVERY','UMC_SHADOW_PROVIDER','UMC_SHADOW_MUTATION']}
fixture_env_active=any(v for v in shadow_env.values())
# Rollback backups known/present
backup_patterns=['agent-runner.runtime-a09vVD0N.js.bak-*','get-reply-*.js.bak-*','pi-embedded-*.js.bak-*']
backups=[]
for pat in backup_patterns:
    backups.extend(str(p.name) for p in DIST.glob(pat))
rollback_known=bool(backups)
# M3N/M4/enforcement: only consider closeout/control artifacts, ignore prompt notebooks and textual mentions.
artifact_names=[p.name for p in UMC.rglob('*') if p.is_file() and 'prompt-chunks' not in str(p)]
m3n_started=any(n.startswith('M3N_') or 'M3N_INSTALLED' in n for n in artifact_names)
m4_started=any(n.startswith('M4_') or 'VERIFIEDROUTE' in n.upper() for n in artifact_names)
enforcement_started=any('ENFORCEMENT' in n.upper() and ('M3' in n.upper() or 'M4' in n.upper()) for n in artifact_names)

checks={
 'abort_preservation_pass': prior_closeout.get('status')=='PASS_M3M_SOAK_ABORT_PRESERVED_GATEWAY_BLIP_DIAGNOSED_R2_READY',
 'post_abort_stability_pass': stability.get('status')=='PASS_M3M_POST_ABORT_HEALTH_STABILITY_CONFIRMED',
 'post_abort_6_of_6_clean': stability.get('probe_count')==6 and stability.get('failed_probes')==0,
 'previous_m3m_not_pass': abort.get('status')=='FAIL_M3M_INSTALLED_SHADOW_SOAK_RETRY_ABORTED',
 'previous_abort_reason_gateway_unreachable': abort.get('reason')=='GATEWAY_UNREACHABLE',
 'm3n_not_started': not m3n_started,
 'gateway_reachable': gateway_reachable,
 'gateway_rpc_ok': gateway_rpc_ok,
 'telegram_on_ok': telegram_ok and accounts_ok,
 'status_json_parsed_full_stdout': status_json_parsed_full_stdout,
 'queue_resting': queue_resting,
 'old_runner_present': runner.exists(),
 'required_chunk_present': chunk.exists(),
 'zalo_manifest_hash_match': zalo_hash==EXPECTED_ZALO,
 'zalouser_manifest_hash_match': zalouser_hash==EXPECTED_ZALOUSER,
 'fresh_logs_clean': logs_ok,
 'hook_disabled_by_default': not fixture_env_active,
 'rollback_backups_known': rollback_known,
 'no_live_send_approval': True,
 'no_external_send_approval': True,
}
status='PASS_M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT' if all(checks.values()) else 'BLOCKED_M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT'
preflight={
 'schema':'umc.v1.m3m.r2.installed_shadow_soak_preflight.v1',
 'generated_utc':NOW(),
 'status':status,
 'checks':checks,
 'gateway':{'reachable':gateway_reachable,'rpc_ok':gateway_rpc_ok,'pid':sj.get('gatewayService',{}).get('runtime',{}).get('pid'),'status_latency_ms':round(gw_dt*1000,2),'listener_ok':listener_ok,'listener_latency_ms':listener_ms,'listener_error':listener_err},
 'telegram':{'healthy':telegram_ok,'accounts_1_of_1':accounts_ok},
 'queue':{'queued':queue_queued,'running':queue_running,'resting':queue_resting},
 'installed_hashes':{'runner':runner_hash,'chunk':chunk_hash,'zalo_manifest':zalo_hash,'zalouser_manifest':zalouser_hash},
 'expected_manifest_hashes':{'zalo':EXPECTED_ZALO,'zalouser':EXPECTED_ZALOUSER},
 'production_hashes':{'config_sha256':config_hash,'route_provider_fallback_sha256':route_hash,'route_fingerprint':route_fingerprint},
 'bounded_fresh_log_scan':{'ok':logs_ok,'hits':log_hits},
 'hook_state':{'fixture_env':shadow_env,'fixture_env_active':fixture_env_active,'disabled_by_default':not fixture_env_active},
 'rollback_backups':backups,
 'm3n_started':m3n_started,'m4_started':m4_started,'enforcement_started':enforcement_started,
}
writej('M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT.json', preflight)
if status.startswith('BLOCKED'):
    print(json.dumps(preflight,indent=2))
    raise SystemExit(2)
start=datetime.now(timezone.utc).replace(microsecond=0)
bounds={
 'schema':'umc.v1.m3m.r2.installed_shadow_soak_bounds.v1',
 'generated_utc':NOW(),
 'status':'M3M_R2_SOAK_BOUNDS_DEFINED',
 'mode':'duration','duration_hours':12,'checkpoint_count':24,'checkpoint_cadence_minutes':30,'hard_stop':True,'retry':'R2',
 'reason':'R1 aborted fail-closed at checkpoint 0005 due to transient GATEWAY_UNREACHABLE; post-abort 6/6 stability probes clean',
 'start_utc':start.isoformat().replace('+00:00','Z'),
 'expected_end_utc':(start+timedelta(hours=12)).isoformat().replace('+00:00','Z'),
}
writej('M3M_R2_INSTALLED_SHADOW_SOAK_BOUNDS.json', bounds)
print(json.dumps({'status':status,'artifact_dir':str(ART),'bounds':bounds},indent=2))
