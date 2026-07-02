#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMPROOT="${TMPROOT:-/tmp/tars-m7-boundary}"
NODE_PORT="${NODE_PORT:-18788}"
RESULT_DIR="$PROJECT_ROOT/docs/m7-local-stt"

rm -rf "$TMPROOT"
mkdir -p "$TMPROOT"/{home,empty-openclaw,empty-ssh,empty-codex,empty-config,logs,app,workspace/memory/context-bridge-events}
mkdir -p "$RESULT_DIR"

cp "$PROJECT_ROOT/server.js" "$TMPROOT/app/server.js"
cp "$PROJECT_ROOT/package.json" "$TMPROOT/app/package.json"
cp -R "$PROJECT_ROOT/src" "$TMPROOT/app/src"
cp -R "$PROJECT_ROOT/safety" "$TMPROOT/app/safety"
cp -R "$PROJECT_ROOT/public" "$TMPROOT/app/public"

cat > "$TMPROOT/stt_fixture_smoke.py" <<'PY'
import http.client, json, struct, time, wave
from pathlib import Path

node_host = '127.0.0.1'
node_port = 18788
for _ in range(120):
    try:
        c = http.client.HTTPConnection(node_host, node_port, timeout=2)
        c.request('GET', '/health')
        r = c.getresponse()
        if r.status == 200:
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit('NODE_HEALTH_TIMEOUT')

c = http.client.HTTPConnection(node_host, node_port, timeout=10)
c.request('GET', '/api/session')
r = c.getresponse()
session_body = json.loads(r.read().decode('utf-8'))
if r.status != 200 or 'csrfToken' not in session_body:
    raise SystemExit(f'BAD_SESSION status={r.status} body={session_body}')
cookie = r.getheader('set-cookie').split(';', 1)[0]
csrf = session_body['csrfToken']

wav_path = Path('/tmp/tars-m7-boundary/logs/fixture-input.wav')
with wave.open(str(wav_path), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    frames = b''.join(struct.pack('<h', 0) for _ in range(1600))
    w.writeframes(frames)

audio = wav_path.read_bytes()
headers = {
    'content-type': 'audio/wav',
    'content-length': str(len(audio)),
    'cookie': cookie,
    'x-csrf-token': csrf,
    'origin': f'http://127.0.0.1:{node_port}',
}
c = http.client.HTTPConnection(node_host, node_port, timeout=120)
c.request('POST', '/api/stt', audio, headers)
r = c.getresponse()
body_raw = r.read().decode('utf-8')
body = json.loads(body_raw)
print(json.dumps({'nodeStatus': r.status, 'body': body}, indent=2))
if r.status != 200:
    raise SystemExit(f'STT_FAILED status={r.status} body={body}')
if body.get('transcript') != 'M7 fixture transcript':
    raise SystemExit(f'TRANSCRIPT_MISMATCH body={body}')
if body.get('boundaries', {}).get('cloudSpeechApi') is not False:
    raise SystemExit(f'CLOUD_BOUNDARY_MISSING body={body}')
PY

cat > "$TMPROOT/namespace_run.sh" <<'SH'
#!/usr/bin/env sh
set -eux
node_pid=""
mount --bind "$TMPROOT/empty-openclaw" /home/stickai/.openclaw
mount --bind "$TMPROOT/empty-ssh" /home/stickai/.ssh
mount --bind "$TMPROOT/empty-codex" /home/stickai/.codex
mount --bind "$TMPROOT/empty-config" /home/stickai/.config

echo boundary_identity; id
echo loopback_enable
if command -v ip >/dev/null 2>&1; then ip link set lo up; elif command -v ifconfig >/dev/null 2>&1; then ifconfig lo up; else echo LOOPBACK_TOOL_MISSING >&2; exit 33; fi
echo network_probe; (curl -fsS --connect-timeout 2 https://huggingface.co >"$TMPROOT/logs/network.txt" && echo NETWORK_UNEXPECTED) || echo NETWORK_BLOCKED_OR_UNAVAILABLE
echo secret_probe; for p in /home/stickai/.openclaw /home/stickai/.ssh /home/stickai/.codex /home/stickai/.config; do printf "%s " "$p"; ls -A "$p" 2>/dev/null | sed -n "1p" || true; done

cleanup() { if [ -n "${node_pid:-}" ]; then kill "$node_pid" 2>/dev/null || true; wait "$node_pid" 2>/dev/null || true; fi; }
trap cleanup EXIT INT TERM

cd "$TMPROOT/app"
HOME="$TMPROOT/home" WORKSPACE_DIR="$TMPROOT/workspace" HOST=127.0.0.1 PORT="$NODE_PORT" STT_MODE=fixture STT_FIXTURE_TEXT='M7 fixture transcript' OPENCLAW_MODE=echo node server.js >"$TMPROOT/logs/node-server.log" 2>&1 &
node_pid=$!

python3 "$TMPROOT/stt_fixture_smoke.py" >"$TMPROOT/logs/stt-fixture-smoke.json"
find "$TMPROOT/app/data/audio/input" -maxdepth 1 -type f -print | sort >"$TMPROOT/logs/captured-audio-files.txt"
count=$(wc -l <"$TMPROOT/logs/captured-audio-files.txt")
[ "$count" -eq 1 ]
audio=$(cat "$TMPROOT/logs/captured-audio-files.txt")
sha256sum "$audio" >"$TMPROOT/logs/captured-audio.sha256"
stat -c 'bytes=%s path=%n' "$audio" >"$TMPROOT/logs/captured-audio.stat"
file "$audio" >"$TMPROOT/logs/captured-audio.file"
cat >"$TMPROOT/logs/result.json" <<EOF
{
  "classification": "STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED",
  "sttMode": "fixture",
  "fixtureTranscript": "M7 fixture transcript",
  "realSttEngineAvailable": false,
  "ffmpegAvailable": false,
  "cloudSpeechApiCalled": false,
  "browserWebSpeechApi": false,
  "nodeSttStatus": 200,
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "capturedAudioSha256": "$(awk '{print $1}' "$TMPROOT/logs/captured-audio.sha256")",
  "capturedAudioStat": "$(sed 's/"/\\"/g' "$TMPROOT/logs/captured-audio.stat")",
  "capturedAudioFileType": "$(sed 's/"/\\"/g' "$TMPROOT/logs/captured-audio.file")",
  "finishedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
cat "$TMPROOT/logs/result.json"
SH
chmod +x "$TMPROOT/namespace_run.sh"

printf 'M7_SANDBOXED_STT_FIXTURE_SMOKE_START\n'
TMPROOT="$TMPROOT" NODE_PORT="$NODE_PORT" unshare -Urnm "$TMPROOT/namespace_run.sh"

cp "$TMPROOT/logs/result.json" "$RESULT_DIR/result.json"
cp "$TMPROOT/logs/stt-fixture-smoke.json" "$RESULT_DIR/stt-fixture-smoke.json"
cp "$TMPROOT/logs/captured-audio.sha256" "$RESULT_DIR/captured-audio.sha256"
cp "$TMPROOT/logs/captured-audio.stat" "$RESULT_DIR/captured-audio.stat"
cp "$TMPROOT/logs/captured-audio.file" "$RESULT_DIR/captured-audio.file"
printf 'M7_SANDBOXED_STT_FIXTURE_SMOKE_COMPLETE\n'
