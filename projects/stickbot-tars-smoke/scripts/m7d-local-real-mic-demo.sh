#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-19890}"
HOST="${HOST:-127.0.0.1}"
WORKSPACE_DIR_DEMO="${WORKSPACE_DIR_DEMO:-/tmp/tars-m7d-workspace}"
LOG_DIR="${LOG_DIR:-/tmp/tars-m7d-real-mic-demo}"
WHISPER_BIN="${WHISPER_BIN:-/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli}"
WHISPER_MODEL="${WHISPER_MODEL:-/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin}"
FFMPEG_BIN="${FFMPEG_BIN:-/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg}"
FFPROBE_BIN="${FFPROBE_BIN:-/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe}"
VOICE_DEMO_ALLOW_LAN="${VOICE_DEMO_ALLOW_LAN:-${M7D_ALLOW_LAN:-false}}"
VOICE_DEMO_HTTPS="${VOICE_DEMO_HTTPS:-false}"
VOICE_DEMO_HTTPS_KEY="${VOICE_DEMO_HTTPS_KEY:-}"
VOICE_DEMO_HTTPS_CERT="${VOICE_DEMO_HTTPS_CERT:-}"

for p in "$WHISPER_BIN" "$WHISPER_MODEL" "$FFMPEG_BIN" "$FFPROBE_BIN" "$PROJECT_ROOT"; do
  case "$p" in /mnt/c/*|/mnt/c) echo "MNT_C_PATH_BLOCKED:$p" >&2; exit 31;; esac
  [ -e "$p" ] || { echo "MISSING_PATH:$p" >&2; exit 32; }
done
[ -x "$WHISPER_BIN" ] || { echo "WHISPER_BIN_NOT_EXECUTABLE:$WHISPER_BIN" >&2; exit 33; }
[ -x "$FFMPEG_BIN" ] || { echo "FFMPEG_BIN_NOT_EXECUTABLE:$FFMPEG_BIN" >&2; exit 34; }
[ -x "$FFPROBE_BIN" ] || { echo "FFPROBE_BIN_NOT_EXECUTABLE:$FFPROBE_BIN" >&2; exit 35; }

mkdir -p "$WORKSPACE_DIR_DEMO/memory/context-bridge-events" "$LOG_DIR"
case "$HOST" in
  127.*|localhost|::1|\[::1\]) ;;
  0.0.0.0|::|\[::\])
    if [ "$VOICE_DEMO_ALLOW_LAN" != "true" ]; then
      echo "LAN_BIND_REQUIRES_VOICE_DEMO_ALLOW_LAN_TRUE:$HOST" >&2
      exit 36
    fi
    ;;
  *)
    if [ "$VOICE_DEMO_ALLOW_LAN" != "true" ]; then
      echo "NON_LOOPBACK_HOST_REQUIRES_VOICE_DEMO_ALLOW_LAN_TRUE:$HOST" >&2
      exit 36
    fi
    ;;
esac
if [ "$PORT" = "8787" ]; then echo "RESERVED_PORT_BLOCKED:8787" >&2; exit 37; fi

export WHISPER_BIN WHISPER_MODEL FFMPEG_BIN FFPROBE_BIN
stt_args_json=$(python3 - <<'PY'
import json, os
print(json.dumps(['-m', os.environ['WHISPER_MODEL'], '-f', '{file}', '-nt', '-np', '-l', 'en']))
PY
)

cat > "$LOG_DIR/demo-env.json" <<EOF
{
  "classification": "STICKBOT_TARS_M7D_REAL_MIC_LOCAL_DEMO_READY",
  "url": "$([ "$VOICE_DEMO_HTTPS" = "true" ] && printf 'https' || printf 'http')://$HOST:$PORT/",
  "host": "$HOST",
  "port": $PORT,
  "allowLan": $VOICE_DEMO_ALLOW_LAN,
  "https": $VOICE_DEMO_HTTPS,
  "workspaceDir": "$WORKSPACE_DIR_DEMO",
  "whisperBin": "$WHISPER_BIN",
  "whisperModel": "$WHISPER_MODEL",
  "ffmpegBin": "$FFMPEG_BIN",
  "ffprobeBin": "$FFPROBE_BIN",
  "rawTranscriptPolicy": "browser_visible_and_tmp_runtime_only_not_committed",
  "browserWebSpeechApi": false,
  "cloudSpeechApiCalled": false,
  "openClawMutation": false
}
EOF

sha256sum "$WHISPER_BIN" > "$LOG_DIR/whisper-bin.sha256"
sha256sum "$WHISPER_MODEL" > "$LOG_DIR/whisper-model.sha256"
sha256sum "$FFMPEG_BIN" > "$LOG_DIR/ffmpeg.sha256"
sha256sum "$FFPROBE_BIN" > "$LOG_DIR/ffprobe.sha256"

cd "$PROJECT_ROOT"
printf 'STICKBOT_TARS_M7D_REAL_MIC_LOCAL_DEMO_READY\n'
if [ "$VOICE_DEMO_HTTPS" = "true" ]; then proto=https; else proto=http; fi
printf 'URL=%s://%s:%s/\n' "$proto" "$HOST" "$PORT"
printf 'LAN_ALLOW=%s\n' "$VOICE_DEMO_ALLOW_LAN"
printf 'HTTPS=%s\n' "$VOICE_DEMO_HTTPS"
printf 'Press Ctrl-C to stop the demo server.\n'
exec env \
  HOST="$HOST" \
  PORT="$PORT" \
  VOICE_DEMO_ALLOW_LAN="$VOICE_DEMO_ALLOW_LAN" \
  VOICE_DEMO_HTTPS="$VOICE_DEMO_HTTPS" \
  VOICE_DEMO_HTTPS_KEY="$VOICE_DEMO_HTTPS_KEY" \
  VOICE_DEMO_HTTPS_CERT="$VOICE_DEMO_HTTPS_CERT" \
  WORKSPACE_DIR="$WORKSPACE_DIR_DEMO" \
  STT_MODE=cli \
  STT_NORMALIZE_AUDIO=true \
  FFMPEG_BIN="$FFMPEG_BIN" \
  STT_BIN="$WHISPER_BIN" \
  STT_ARGS_JSON="$stt_args_json" \
  STT_TIMEOUT_MS=240000 \
  OPENCLAW_MODE=echo \
  node server.js
