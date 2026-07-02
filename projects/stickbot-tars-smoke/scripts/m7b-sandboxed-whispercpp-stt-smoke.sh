#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMPROOT="${TMPROOT:-/tmp/tars-m7b-boundary}"
RESULT_DIR="$PROJECT_ROOT/docs/m7-local-stt/m7b-whispercpp-local-stt"
NODE_PORT="${NODE_PORT:-19889}"
WHISPER_BIN="${WHISPER_BIN:?WHISPER_BIN is required}"
WHISPER_MODEL="${WHISPER_MODEL:?WHISPER_MODEL is required}"
FFMPEG_BIN="${FFMPEG_BIN:?FFMPEG_BIN is required}"
FFPROBE_BIN="${FFPROBE_BIN:?FFPROBE_BIN is required}"
M7B_FIXTURE_WAV="${M7B_FIXTURE_WAV:-/home/stickai/stickbot-voice/output/m4-first-generation.wav}"

for p in "$WHISPER_BIN" "$WHISPER_MODEL" "$FFMPEG_BIN" "$FFPROBE_BIN" "$M7B_FIXTURE_WAV"; do
  case "$p" in /mnt/c/*|/mnt/c) echo "MNT_C_PATH_BLOCKED:$p" >&2; exit 31;; esac
  [ -e "$p" ] || { echo "MISSING_PATH:$p" >&2; exit 32; }
done
[ -x "$WHISPER_BIN" ] || { echo "WHISPER_BIN_NOT_EXECUTABLE:$WHISPER_BIN" >&2; exit 33; }
[ -x "$FFMPEG_BIN" ] || { echo "FFMPEG_BIN_NOT_EXECUTABLE:$FFMPEG_BIN" >&2; exit 34; }
[ -x "$FFPROBE_BIN" ] || { echo "FFPROBE_BIN_NOT_EXECUTABLE:$FFPROBE_BIN" >&2; exit 35; }

rm -rf "$TMPROOT"
mkdir -p "$TMPROOT"/{home,empty-openclaw,empty-ssh,empty-codex,empty-config,logs,traces,app,workspace/memory/context-bridge-events}
mkdir -p "$RESULT_DIR"

cp "$PROJECT_ROOT/server.js" "$TMPROOT/app/server.js"
cp "$PROJECT_ROOT/package.json" "$TMPROOT/app/package.json"
cp -R "$PROJECT_ROOT/src" "$TMPROOT/app/src"
cp -R "$PROJECT_ROOT/safety" "$TMPROOT/app/safety"
cp -R "$PROJECT_ROOT/public" "$TMPROOT/app/public"
cp "$M7B_FIXTURE_WAV" "$TMPROOT/logs/fixture-input.wav"

sha256sum "$WHISPER_BIN" > "$TMPROOT/logs/whisper-bin.sha256"
sha256sum "$WHISPER_MODEL" > "$TMPROOT/logs/whisper-model.sha256"
sha256sum "$TMPROOT/logs/fixture-input.wav" > "$TMPROOT/logs/fixture-input.sha256"
"$WHISPER_BIN" --help > "$TMPROOT/logs/whisper-help.txt" 2>&1 || true
if basename "$WHISPER_BIN" | grep -Eq '^main$'; then
  echo "WHISPER_DEPRECATED_MAIN_BLOCKED:$WHISPER_BIN" >&2
  exit 37
fi
"$FFMPEG_BIN" -version > "$TMPROOT/logs/ffmpeg-version.txt"
"$FFPROBE_BIN" -version > "$TMPROOT/logs/ffprobe-version.txt"

cat > "$TMPROOT/stt_smoke.py" <<'PY'
import hashlib, http.client, json, os, pathlib, time
node_host = '127.0.0.1'
node_port = int(os.environ['NODE_PORT'])
logs = pathlib.Path(os.environ['TMPROOT']) / 'logs'
traces = pathlib.Path(os.environ['TMPROOT']) / 'traces'
for _ in range(180):
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

audio = (logs / 'fixture-input.wav').read_bytes()
headers = {
    'content-type': 'audio/wav',
    'content-length': str(len(audio)),
    'cookie': cookie,
    'x-csrf-token': csrf,
    'origin': f'http://127.0.0.1:{node_port}',
}
c = http.client.HTTPConnection(node_host, node_port, timeout=240)
c.request('POST', '/api/stt', audio, headers)
r = c.getresponse()
body_raw = r.read().decode('utf-8')
body = json.loads(body_raw)
if r.status != 200:
    (logs / 'stt-error-response.json').write_text(json.dumps(body, indent=2) + '\n')
    raise SystemExit(f'STT_HTTP_FAILED status={r.status}')
transcript = (body.get('transcript') or '').strip()
if not transcript:
    raise SystemExit('EMPTY_TRANSCRIPT')
(traces / 'transcript.txt').write_text(transcript + '\n')
summary = {
    'nodeStatus': r.status,
    'id': body.get('id'),
    'savedLocal': body.get('savedLocal'),
    'normalizedLocal': body.get('normalizedLocal'),
    'sttMode': body.get('sttMode'),
    'transcriptChars': len(transcript),
    'transcriptSha256': hashlib.sha256(transcript.encode('utf-8')).hexdigest(),
    'boundaries': body.get('boundaries'),
    'rawTranscriptPolicy': 'trace_only_not_committed'
}
if summary.get('normalizedLocal') is not True:
    raise SystemExit(f'NORMALIZATION_NOT_APPLIED:{summary}')
(logs / 'stt-response-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
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
if command -v ip >/dev/null 2>&1; then ip link set lo up; elif command -v ifconfig >/dev/null 2>&1; then ifconfig lo up; else echo LOOPBACK_TOOL_MISSING >&2; exit 36; fi
echo network_probe; (curl -fsS --connect-timeout 2 https://huggingface.co >"$TMPROOT/logs/network.txt" && echo NETWORK_UNEXPECTED) || echo NETWORK_BLOCKED_OR_UNAVAILABLE
echo secret_probe; for p in /home/stickai/.openclaw /home/stickai/.ssh /home/stickai/.codex /home/stickai/.config; do printf "%s " "$p"; ls -A "$p" 2>/dev/null | sed -n "1p" || true; done

cleanup() { if [ -n "${node_pid:-}" ]; then kill "$node_pid" 2>/dev/null || true; wait "$node_pid" 2>/dev/null || true; fi; }
trap cleanup EXIT INT TERM

stt_args_json=$(python3 - <<'PY'
import json, os
print(json.dumps(['-m', os.environ['WHISPER_MODEL'], '-f', '{file}', '-nt', '-np', '-l', 'en']))
PY
)
cd "$TMPROOT/app"
HOME="$TMPROOT/home" WORKSPACE_DIR="$TMPROOT/workspace" HOST=127.0.0.1 PORT="$NODE_PORT" \
  STT_MODE=cli STT_NORMALIZE_AUDIO=true FFMPEG_BIN="$FFMPEG_BIN" \
  STT_BIN="$WHISPER_BIN" STT_ARGS_JSON="$stt_args_json" STT_TIMEOUT_MS=240000 \
  OPENCLAW_MODE=echo node server.js >"$TMPROOT/logs/node-server.log" 2>&1 &
node_pid=$!
python3 "$TMPROOT/stt_smoke.py" >"$TMPROOT/logs/stt-smoke-run.json"

find "$TMPROOT/app/data/audio" -maxdepth 3 -type f -print | sort >"$TMPROOT/logs/local-audio-files.txt"
normalized=$(find "$TMPROOT/app/data/audio/normalized" -maxdepth 1 -type f -name '*-normalized.wav' | sort | tail -n 1)
[ -n "$normalized" ]
sha256sum "$normalized" >"$TMPROOT/logs/normalized-audio.sha256"
stat -c 'bytes=%s path=%n' "$normalized" >"$TMPROOT/logs/normalized-audio.stat"
file "$normalized" >"$TMPROOT/logs/normalized-audio.file"
"$FFPROBE_BIN" -v error -select_streams a:0 -show_entries stream=codec_name,channels,sample_rate -of json "$normalized" >"$TMPROOT/logs/normalized-audio-ffprobe.json"
python3 - <<'PY'
import json, os, pathlib
root = pathlib.Path(os.environ['TMPROOT']) / 'logs'
summary = json.loads((root / 'stt-response-summary.json').read_text())
probe = json.loads((root / 'normalized-audio-ffprobe.json').read_text())
stream = (probe.get('streams') or [{}])[0]
if str(stream.get('sample_rate')) != '16000' or int(stream.get('channels', 0)) != 1:
    raise SystemExit(f'BAD_NORMALIZED_AUDIO:{stream}')
if summary.get('transcriptChars', 0) <= 0:
    raise SystemExit(f'EMPTY_TRANSCRIPT_SUMMARY:{summary}')
result = {
  'classification': 'STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS',
  'whisperBin': os.environ['WHISPER_BIN'],
  'whisperModel': os.environ['WHISPER_MODEL'],
  'whisperBinSha256': (root / 'whisper-bin.sha256').read_text().split()[0],
  'whisperModelSha256': (root / 'whisper-model.sha256').read_text().split()[0],
  'fixtureInputSha256': (root / 'fixture-input.sha256').read_text().split()[0],
  'normalizedAudioSha256': (root / 'normalized-audio.sha256').read_text().split()[0],
  'normalizedProbe': stream,
  'nodeStatus': summary['nodeStatus'],
  'sttMode': summary['sttMode'],
  'normalizedLocal': summary['normalizedLocal'],
  'transcriptChars': summary['transcriptChars'],
  'transcriptSha256': summary['transcriptSha256'],
  'rawTranscriptPolicy': 'trace_only_not_committed',
  'networkRequiredDuringTranscription': False,
  'networkBlockedOrUnavailable': True,
  'secretDirsHidden': True,
  'cloudSpeechApiCalled': False,
  'browserWebSpeechApi': False,
  'openClawMutation': False,
  'finishedAt': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
}
(root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
PY
cat "$TMPROOT/logs/result.json"
SH
chmod +x "$TMPROOT/namespace_run.sh"

printf 'M7B_WHISPERCPP_LOCAL_STT_SMOKE_START\n'
TMPROOT="$TMPROOT" NODE_PORT="$NODE_PORT" WHISPER_BIN="$WHISPER_BIN" WHISPER_MODEL="$WHISPER_MODEL" FFMPEG_BIN="$FFMPEG_BIN" FFPROBE_BIN="$FFPROBE_BIN" unshare -Urnm "$TMPROOT/namespace_run.sh"

cp "$TMPROOT/logs/result.json" "$RESULT_DIR/result.json"
cp "$TMPROOT/logs/stt-response-summary.json" "$RESULT_DIR/stt-response-summary.json"
cp "$TMPROOT/logs/whisper-help.txt" "$RESULT_DIR/whisper-help.txt"
cp "$TMPROOT/logs/whisper-bin.sha256" "$RESULT_DIR/whisper-bin.sha256"
cp "$TMPROOT/logs/whisper-model.sha256" "$RESULT_DIR/whisper-model.sha256"
cp "$TMPROOT/logs/fixture-input.sha256" "$RESULT_DIR/fixture-input.sha256"
cp "$TMPROOT/logs/normalized-audio.sha256" "$RESULT_DIR/normalized-audio.sha256"
cp "$TMPROOT/logs/normalized-audio.stat" "$RESULT_DIR/normalized-audio.stat"
cp "$TMPROOT/logs/normalized-audio.file" "$RESULT_DIR/normalized-audio.file"
cp "$TMPROOT/logs/normalized-audio-ffprobe.json" "$RESULT_DIR/normalized-audio-ffprobe.json"
printf 'M7B_WHISPERCPP_LOCAL_STT_SMOKE_COMPLETE\n'
