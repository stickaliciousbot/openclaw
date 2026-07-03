#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${TARS_VENV:-/home/stickai/stickbot-voice/venv-coqui}"
MODEL_SRC="${TARS_MODEL_ROOT:-/home/stickai/stickbot-voice/xtts_models/tars}"
SPEAKER_SRC="${TARS_SPEAKER_ROOT:-/home/stickai/stickbot-voice/speakers}"
TMPROOT="${TMPROOT:-/tmp/tars-m7e-xtts-loopback-boundary}"
XTTS_PORT="${XTTS_PORT:-8020}"
LOG_DIR="${LOG_DIR:-/tmp/tars-m7e-xtts-loopback-logs}"

for p in "$PROJECT_ROOT" "$VENV/bin/python" "$MODEL_SRC" "$SPEAKER_SRC"; do
  case "$p" in /mnt/c/*|/mnt/c) echo "MNT_C_PATH_BLOCKED:$p" >&2; exit 31;; esac
  [ -e "$p" ] || { echo "MISSING_PATH:$p" >&2; exit 32; }
done
if [ "$XTTS_PORT" = "8787" ]; then echo "RESERVED_PORT_BLOCKED:8787" >&2; exit 33; fi
for name in config.json vocab.json model.pth speakers_xtts.pth; do
  [ -f "$MODEL_SRC/$name" ] || { echo "MISSING_MODEL_ARTIFACT:$MODEL_SRC/$name" >&2; exit 34; }
done
[ -f "$SPEAKER_SRC/reference.wav" ] || { echo "MISSING_SPEAKER:$SPEAKER_SRC/reference.wav" >&2; exit 35; }
command -v unshare >/dev/null 2>&1 || { echo "UNSHARE_MISSING" >&2; exit 36; }

rm -rf "$TMPROOT"
mkdir -p "$TMPROOT"/{model,speakers,home,cache,empty-openclaw,empty-ssh,empty-codex,empty-config,app/scripts}
mkdir -p "$LOG_DIR"
cp "$PROJECT_ROOT/scripts/xtts-local-server.py" "$TMPROOT/app/scripts/xtts-local-server.py"

cat > "$TMPROOT/run-inside.sh" <<'SH'
#!/usr/bin/env sh
set -eu
mount --bind "$MODEL_SRC" "$TMPROOT/model"
mount -o remount,ro,bind "$TMPROOT/model"
mount --bind "$SPEAKER_SRC" "$TMPROOT/speakers"
mount -o remount,ro,bind "$TMPROOT/speakers"
mount --bind "$TMPROOT/empty-openclaw" /home/stickai/.openclaw
mount --bind "$TMPROOT/empty-ssh" /home/stickai/.ssh
mount --bind "$TMPROOT/empty-codex" /home/stickai/.codex
mount --bind "$TMPROOT/empty-config" /home/stickai/.config

printf 'boundary_identity='; id
for p in /home/stickai/.openclaw /home/stickai/.ssh /home/stickai/.codex /home/stickai/.config; do
  printf 'secret_probe %s=' "$p"
  ls -A "$p" 2>/dev/null | sed -n '1p' || true
done

exec env \
  HOME="$TMPROOT/home" \
  XDG_CACHE_HOME="$TMPROOT/cache" \
  HF_HOME="$TMPROOT/cache/hf" \
  TRANSFORMERS_CACHE="$TMPROOT/cache/transformers" \
  TARS_XTTS_HOST=127.0.0.1 \
  TARS_XTTS_PORT="$XTTS_PORT" \
  TARS_XTTS_MODEL_DIR="$TMPROOT/model" \
  TARS_XTTS_SPEAKER_DIR="$TMPROOT/speakers" \
  "$VENV/bin/python" "$TMPROOT/app/scripts/xtts-local-server.py"
SH
chmod +x "$TMPROOT/run-inside.sh"

printf 'STICKBOT_TARS_M7E_XTTS_LOOPBACK_STARTING\n'
printf 'XTTS_URL=http://127.0.0.1:%s\n' "$XTTS_PORT"
printf 'BOUNDARY=unshare -Urm mount-isolated shared-host-loopback\n'
exec env MODEL_SRC="$MODEL_SRC" SPEAKER_SRC="$SPEAKER_SRC" TMPROOT="$TMPROOT" VENV="$VENV" XTTS_PORT="$XTTS_PORT" \
  unshare -Urm "$TMPROOT/run-inside.sh"
