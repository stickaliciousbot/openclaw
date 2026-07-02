#!/usr/bin/env bash
set -euo pipefail

# M5 validation: run the local XTTS HTTP server and Node echo app together
# inside the accepted no-root unshare boundary. This proves serverization +
# Node voice integration without exposing LAN or touching real OpenClaw/Gateway.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PROJECT_ROOT/../.." && pwd)"
VENV="${TARS_VENV:-/home/stickai/stickbot-voice/venv-coqui}"
MODEL_SRC="${TARS_MODEL_ROOT:-/home/stickai/stickbot-voice/xtts_models/tars}"
SPEAKER_SRC="${TARS_SPEAKER_ROOT:-/home/stickai/stickbot-voice/speakers}"
HOST_OUTPUT="${TARS_OUTPUT_ROOT:-/home/stickai/stickbot-voice/output}"
TMPROOT="${TMPROOT:-/tmp/tars-m5-boundary}"
NODE_PORT="${NODE_PORT:-18788}"
XTTS_PORT="${XTTS_PORT:-18020}"
RESULT_DIR="$PROJECT_ROOT/docs/m5-local-serverization"

rm -rf "$TMPROOT"
mkdir -p "$TMPROOT"/{model,speakers,host-output,cache,home,empty-openclaw,empty-ssh,empty-codex,empty-config,logs,app,workspace/memory/context-bridge-events}
mkdir -p "$RESULT_DIR"

# Copy only the app files needed for the smoke so /home/stickai/.openclaw can be hidden.
cp "$PROJECT_ROOT/server.js" "$TMPROOT/app/server.js"
cp "$PROJECT_ROOT/package.json" "$TMPROOT/app/package.json"
cp -R "$PROJECT_ROOT/src" "$TMPROOT/app/src"
cp -R "$PROJECT_ROOT/safety" "$TMPROOT/app/safety"
cp -R "$PROJECT_ROOT/public" "$TMPROOT/app/public"
mkdir -p "$TMPROOT/app/scripts"
cp "$PROJECT_ROOT/scripts/xtts-local-server.py" "$TMPROOT/app/scripts/xtts-local-server.py"

cat > "$TMPROOT/node_voice_smoke.py" <<'PY'
import http.client, json, time

node_host = '127.0.0.1'
node_port = 18788

# Wait for Node health.
for _ in range(120):
    try:
        c = http.client.HTTPConnection(node_host, node_port, timeout=2)
        c.request('GET', '/health')
        r = c.getresponse()
        body = r.read().decode('utf-8')
        if r.status == 200:
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit('NODE_HEALTH_TIMEOUT')

# Establish CSRF session.
c = http.client.HTTPConnection(node_host, node_port, timeout=10)
c.request('GET', '/api/session')
r = c.getresponse()
session_body = json.loads(r.read().decode('utf-8'))
if r.status != 200 or 'csrfToken' not in session_body:
    raise SystemExit(f'BAD_SESSION status={r.status} body={session_body}')
cookie = r.getheader('set-cookie').split(';', 1)[0]
csrf = session_body['csrfToken']

payload = json.dumps({'text': 'M5 local voice echo smoke', 'voice': True}).encode('utf-8')
headers = {
    'content-type': 'application/json',
    'content-length': str(len(payload)),
    'cookie': cookie,
    'x-csrf-token': csrf,
    'origin': f'http://127.0.0.1:{node_port}',
}
c = http.client.HTTPConnection(node_host, node_port, timeout=900)
c.request('POST', '/api/chat', payload, headers)
r = c.getresponse()
body_raw = r.read().decode('utf-8')
try:
    body = json.loads(body_raw)
except Exception:
    raise SystemExit(f'BAD_JSON status={r.status} body={body_raw[:500]}')
print(json.dumps({'nodeStatus': r.status, 'body': body}, indent=2))
if r.status != 200:
    raise SystemExit(f'NODE_CHAT_FAILED status={r.status}')
if not body.get('audioUrl') or body.get('audioError'):
    raise SystemExit(f'NODE_VOICE_FAILED body={body}')
PY

cat > "$TMPROOT/namespace_run.sh" <<'SH'
#!/usr/bin/env sh
set -eux
xtts_pid=""
node_pid=""
mount --bind "$MODEL_SRC" "$TMPROOT/model"
mount -o remount,ro,bind "$TMPROOT/model"
mount --bind "$SPEAKER_SRC" "$TMPROOT/speakers"
mount -o remount,ro,bind "$TMPROOT/speakers"
mount --bind "$HOST_OUTPUT" "$TMPROOT/host-output"
mount --bind "$TMPROOT/empty-openclaw" /home/stickai/.openclaw
mount --bind "$TMPROOT/empty-ssh" /home/stickai/.ssh
mount --bind "$TMPROOT/empty-codex" /home/stickai/.codex
mount --bind "$TMPROOT/empty-config" /home/stickai/.config

echo boundary_identity; id
echo loopback_enable
if command -v ip >/dev/null 2>&1; then
  ip link set lo up
elif command -v ifconfig >/dev/null 2>&1; then
  ifconfig lo up
else
  echo LOOPBACK_TOOL_MISSING >&2
  exit 33
fi
cat /sys/class/net/lo/operstate >"$TMPROOT/logs/loopback-operstate.txt" 2>/dev/null || true
echo network_probe; (curl -fsS --connect-timeout 2 https://huggingface.co >"$TMPROOT/logs/network.txt" && echo NETWORK_UNEXPECTED) || echo NETWORK_BLOCKED_OR_UNAVAILABLE
echo secret_probe; for p in /home/stickai/.openclaw /home/stickai/.ssh /home/stickai/.codex /home/stickai/.config; do printf "%s " "$p"; ls -A "$p" 2>/dev/null | sed -n "1p" || true; done

HOME="$TMPROOT/home" \
XDG_CACHE_HOME="$TMPROOT/cache" \
HF_HOME="$TMPROOT/cache/hf" \
TRANSFORMERS_CACHE="$TMPROOT/cache/transformers" \
TARS_XTTS_HOST=127.0.0.1 \
TARS_XTTS_PORT="$XTTS_PORT" \
TARS_XTTS_MODEL_DIR="$TMPROOT/model" \
TARS_XTTS_SPEAKER_DIR="$TMPROOT/speakers" \
"$VENV/bin/python" "$TMPROOT/app/scripts/xtts-local-server.py" >"$TMPROOT/logs/xtts-server.log" 2>&1 &
xtts_pid=$!

cleanup() {
  if [ -n "${node_pid:-}" ]; then
    kill "$node_pid" 2>/dev/null || true
    wait "$node_pid" 2>/dev/null || true
  fi
  if [ -n "${xtts_pid:-}" ]; then
    kill "$xtts_pid" 2>/dev/null || true
    wait "$xtts_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# Wait for XTTS ready after model load.
for i in $(seq 1 900); do
  if curl -fsS "http://127.0.0.1:$XTTS_PORT/ready" >"$TMPROOT/logs/xtts-ready.json" 2>"$TMPROOT/logs/xtts-ready.err"; then
    break
  fi
  if ! kill -0 "$xtts_pid" 2>/dev/null; then
    echo XTTS_SERVER_EXITED >&2
    cat "$TMPROOT/logs/xtts-server.log" >&2 || true
    exit 31
  fi
  sleep 1
  if [ "$i" = 900 ]; then echo XTTS_READY_TIMEOUT >&2; exit 32; fi
done

cd "$TMPROOT/app"
HOME="$TMPROOT/home" \
WORKSPACE_DIR="$TMPROOT/workspace" \
HOST=127.0.0.1 \
PORT="$NODE_PORT" \
XTTS_URL="http://127.0.0.1:$XTTS_PORT" \
XTTS_SPEAKER=reference.wav \
OPENCLAW_MODE=echo \
node server.js >"$TMPROOT/logs/node-server.log" 2>&1 &
node_pid=$!

"$VENV/bin/python" "$TMPROOT/node_voice_smoke.py" >"$TMPROOT/logs/node-voice-smoke.json"

# Verify generated app audio exists and is a WAV.
find "$TMPROOT/app/data/audio/output" -maxdepth 1 -type f -name '*.wav' -print | sort >"$TMPROOT/logs/generated-audio-files.txt"
count=$(wc -l <"$TMPROOT/logs/generated-audio-files.txt")
[ "$count" -eq 1 ]
audio=$(cat "$TMPROOT/logs/generated-audio-files.txt")
sha256sum "$audio" >"$TMPROOT/logs/generated-audio.sha256"
stat -c 'bytes=%s path=%n' "$audio" >"$TMPROOT/logs/generated-audio.stat"
file "$audio" >"$TMPROOT/logs/generated-audio.file"

cat >"$TMPROOT/logs/result.json" <<EOF
{
  "classification": "STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS",
  "xttsServerReady": true,
  "nodeEchoVoicePass": true,
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "modelReadOnly": true,
  "speakerReadOnly": true,
  "openclawMode": "echo",
  "host": "127.0.0.1",
  "nodePort": $NODE_PORT,
  "xttsPort": $XTTS_PORT,
  "audioSha256": "$(awk '{print $1}' "$TMPROOT/logs/generated-audio.sha256")",
  "audioStat": "$(sed 's/"/\\"/g' "$TMPROOT/logs/generated-audio.stat")",
  "audioFileType": "$(sed 's/"/\\"/g' "$TMPROOT/logs/generated-audio.file")",
  "finishedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
cat "$TMPROOT/logs/result.json"
SH
chmod +x "$TMPROOT/namespace_run.sh"

printf 'M5_SANDBOXED_NODE_VOICE_SMOKE_START\n'
MODEL_SRC="$MODEL_SRC" SPEAKER_SRC="$SPEAKER_SRC" HOST_OUTPUT="$HOST_OUTPUT" TMPROOT="$TMPROOT" VENV="$VENV" NODE_PORT="$NODE_PORT" XTTS_PORT="$XTTS_PORT" \
  unshare -Urnm "$TMPROOT/namespace_run.sh"

cp "$TMPROOT/logs/result.json" "$RESULT_DIR/result.json"
cp "$TMPROOT/logs/node-voice-smoke.json" "$RESULT_DIR/node-voice-smoke.json"
cp "$TMPROOT/logs/xtts-ready.json" "$RESULT_DIR/xtts-ready.json"
cp "$TMPROOT/logs/generated-audio.sha256" "$RESULT_DIR/generated-audio.sha256"
cp "$TMPROOT/logs/generated-audio.stat" "$RESULT_DIR/generated-audio.stat"
cp "$TMPROOT/logs/generated-audio.file" "$RESULT_DIR/generated-audio.file"
printf 'M5_SANDBOXED_NODE_VOICE_SMOKE_COMPLETE\n'
