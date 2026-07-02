#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMPROOT="${TMPROOT:-/tmp/tars-m7a-boundary}"
RESULT_DIR="$PROJECT_ROOT/docs/m7-local-stt/m7a-audio-normalization"
FFMPEG_BIN="${FFMPEG_BIN:-/usr/bin/ffmpeg}"
FFPROBE_BIN="${FFPROBE_BIN:-/usr/bin/ffprobe}"

if [ ! -x "$FFMPEG_BIN" ]; then echo "FFMPEG_MISSING:$FFMPEG_BIN" >&2; exit 31; fi
if [ ! -x "$FFPROBE_BIN" ]; then echo "FFPROBE_MISSING:$FFPROBE_BIN" >&2; exit 32; fi
case "$FFMPEG_BIN" in /mnt/c/*|/mnt/c) echo "FFMPEG_MNT_C_BLOCKED:$FFMPEG_BIN" >&2; exit 33;; esac
case "$FFPROBE_BIN" in /mnt/c/*|/mnt/c) echo "FFPROBE_MNT_C_BLOCKED:$FFPROBE_BIN" >&2; exit 34;; esac

rm -rf "$TMPROOT"
mkdir -p "$TMPROOT"/{home,empty-openclaw,empty-ssh,empty-codex,empty-config,logs,app/src,workspace/memory/context-bridge-events}
mkdir -p "$RESULT_DIR"

cp "$PROJECT_ROOT/package.json" "$TMPROOT/app/package.json"
cp "$PROJECT_ROOT/src/audio-normalizer.js" "$TMPROOT/app/src/audio-normalizer.js"

"$FFMPEG_BIN" -version > "$TMPROOT/logs/ffmpeg-version.txt"
"$FFPROBE_BIN" -version > "$TMPROOT/logs/ffprobe-version.txt"
sha256sum "$FFMPEG_BIN" > "$TMPROOT/logs/ffmpeg.sha256"
sha256sum "$FFPROBE_BIN" > "$TMPROOT/logs/ffprobe.sha256"
(dpkg-query -W -f='${Package} ${Version} ${Status}\n' ffmpeg 2>/dev/null || true) > "$TMPROOT/logs/ffmpeg-apt-package.txt"

cat > "$TMPROOT/normalize-fixture.mjs" <<'JS'
import { stat } from 'node:fs/promises';
import { normalizeAudio } from './app/src/audio-normalizer.js';
const tmp = process.env.TMPROOT;
const ffmpegBin = process.env.FFMPEG_BIN;
const result = await normalizeAudio(`${tmp}/logs/fixture-input.webm`, `${tmp}/logs/fixture-normalized.wav`, {
  workspace: `${tmp}/workspace`,
  ffmpegBin,
  audioNormalizeTimeoutMs: 60000,
  audioNormalizeMaxStderrBytes: 65536
});
const s = await stat(result.outputPath);
console.log(JSON.stringify({ ...result, bytes: s.size }, null, 2));
JS

cat > "$TMPROOT/namespace_run.sh" <<'SH'
#!/usr/bin/env sh
set -eux
mount --bind "$TMPROOT/empty-openclaw" /home/stickai/.openclaw
mount --bind "$TMPROOT/empty-ssh" /home/stickai/.ssh
mount --bind "$TMPROOT/empty-codex" /home/stickai/.codex
mount --bind "$TMPROOT/empty-config" /home/stickai/.config

echo boundary_identity; id
echo loopback_enable
if command -v ip >/dev/null 2>&1; then ip link set lo up; elif command -v ifconfig >/dev/null 2>&1; then ifconfig lo up; else echo LOOPBACK_TOOL_MISSING >&2; exit 35; fi
echo network_probe; (curl -fsS --connect-timeout 2 https://huggingface.co >"$TMPROOT/logs/network.txt" && echo NETWORK_UNEXPECTED) || echo NETWORK_BLOCKED_OR_UNAVAILABLE
echo secret_probe; for p in /home/stickai/.openclaw /home/stickai/.ssh /home/stickai/.codex /home/stickai/.config; do printf "%s " "$p"; ls -A "$p" 2>/dev/null | sed -n "1p" || true; done

"$FFMPEG_BIN" -nostdin -hide_banner -loglevel error -y -f lavfi -i sine=frequency=880:sample_rate=48000 -t 1 -c:a libopus "$TMPROOT/logs/fixture-input.webm"
node "$TMPROOT/normalize-fixture.mjs" > "$TMPROOT/logs/normalizer-result.json"
"$FFPROBE_BIN" -v error -select_streams a:0 -show_entries stream=codec_name,channels,sample_rate -of json "$TMPROOT/logs/fixture-normalized.wav" > "$TMPROOT/logs/normalized-ffprobe.json"
sha256sum "$TMPROOT/logs/fixture-input.webm" > "$TMPROOT/logs/fixture-input.sha256"
sha256sum "$TMPROOT/logs/fixture-normalized.wav" > "$TMPROOT/logs/fixture-normalized.sha256"
stat -c 'bytes=%s path=%n' "$TMPROOT/logs/fixture-input.webm" > "$TMPROOT/logs/fixture-input.stat"
stat -c 'bytes=%s path=%n' "$TMPROOT/logs/fixture-normalized.wav" > "$TMPROOT/logs/fixture-normalized.stat"
file "$TMPROOT/logs/fixture-input.webm" > "$TMPROOT/logs/fixture-input.file"
file "$TMPROOT/logs/fixture-normalized.wav" > "$TMPROOT/logs/fixture-normalized.file"
python3 - <<'PY'
import json, os, pathlib, sys
root = pathlib.Path(os.environ['TMPROOT']) / 'logs'
probe = json.loads((root / 'normalized-ffprobe.json').read_text())
streams = probe.get('streams') or []
if not streams:
    raise SystemExit('NO_AUDIO_STREAM')
s = streams[0]
if str(s.get('sample_rate')) != '16000':
    raise SystemExit(f'BAD_SAMPLE_RATE:{s}')
if int(s.get('channels', 0)) != 1:
    raise SystemExit(f'BAD_CHANNELS:{s}')
normalizer = json.loads((root / 'normalizer-result.json').read_text())
if normalizer.get('bytes', 0) <= 0:
    raise SystemExit(f'EMPTY_OUTPUT:{normalizer}')
result = {
  'classification': 'STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS',
  'ffmpegPath': os.environ['FFMPEG_BIN'],
  'ffprobePath': os.environ['FFPROBE_BIN'],
  'ffmpegSha256': (root / 'ffmpeg.sha256').read_text().split()[0],
  'ffprobeSha256': (root / 'ffprobe.sha256').read_text().split()[0],
  'aptPackage': (root / 'ffmpeg-apt-package.txt').read_text().strip(),
  'inputSha256': (root / 'fixture-input.sha256').read_text().split()[0],
  'normalizedSha256': (root / 'fixture-normalized.sha256').read_text().split()[0],
  'normalizedBytes': normalizer['bytes'],
  'normalizedProbe': s,
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

printf 'M7A_FFMPEG_NORMALIZATION_SMOKE_START\n'
TMPROOT="$TMPROOT" FFMPEG_BIN="$FFMPEG_BIN" FFPROBE_BIN="$FFPROBE_BIN" unshare -Urnm "$TMPROOT/namespace_run.sh"

cp "$TMPROOT/logs/result.json" "$RESULT_DIR/result.json"
cp "$TMPROOT/logs/ffmpeg-version.txt" "$RESULT_DIR/ffmpeg-version.txt"
cp "$TMPROOT/logs/ffprobe-version.txt" "$RESULT_DIR/ffprobe-version.txt"
cp "$TMPROOT/logs/ffmpeg.sha256" "$RESULT_DIR/ffmpeg.sha256"
cp "$TMPROOT/logs/ffprobe.sha256" "$RESULT_DIR/ffprobe.sha256"
cp "$TMPROOT/logs/ffmpeg-apt-package.txt" "$RESULT_DIR/ffmpeg-apt-package.txt"
cp "$TMPROOT/logs/normalizer-result.json" "$RESULT_DIR/normalizer-result.json"
cp "$TMPROOT/logs/normalized-ffprobe.json" "$RESULT_DIR/normalized-ffprobe.json"
cp "$TMPROOT/logs/fixture-input.sha256" "$RESULT_DIR/fixture-input.sha256"
cp "$TMPROOT/logs/fixture-normalized.sha256" "$RESULT_DIR/fixture-normalized.sha256"
cp "$TMPROOT/logs/fixture-input.stat" "$RESULT_DIR/fixture-input.stat"
cp "$TMPROOT/logs/fixture-normalized.stat" "$RESULT_DIR/fixture-normalized.stat"
cp "$TMPROOT/logs/fixture-input.file" "$RESULT_DIR/fixture-input.file"
cp "$TMPROOT/logs/fixture-normalized.file" "$RESULT_DIR/fixture-normalized.file"
printf 'M7A_FFMPEG_NORMALIZATION_SMOKE_COMPLETE\n'
