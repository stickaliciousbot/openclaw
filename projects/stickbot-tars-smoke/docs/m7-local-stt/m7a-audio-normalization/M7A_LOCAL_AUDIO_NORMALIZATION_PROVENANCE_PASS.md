# M7A Local Audio Normalization Provenance — PASS

Status: `STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`

Generated: 2026-07-02 20:50 AEST / 2026-07-02T10:50:00Z

## Summary

M7A acquired a WSL-native local FFmpeg/FFprobe toolchain and validated bounded audio normalization for the Stickbot-TARS local STT path.

No OpenClaw/Gateway/NOA mutation occurred. No cloud STT or browser Web Speech API was used. No audio binaries/models/runtime artifacts are committed.

## Acquisition path

Apt install was attempted only after tests passed, but the Telegram runtime lacked TTY/elevated sudo authority:

- Session: `faint-basil`
- Static validation inside that session: `39/39` tests passed.
- Stop reason: `sudo: a terminal is required to read the password`.

Approved fallback used:

- Source: John Van Sickle Linux amd64 static FFmpeg release build.
- Release URL: `https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz`
- MD5 URL: `https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz.md5`
- Local download path: `/home/stickai/stickbot-voice/tools/ffmpeg-static/downloads/ffmpeg-release-amd64-static.tar.xz`
- Local extract path: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/`

License posture:

- John Van Sickle static builds are GPLv3 and this build configuration includes `--enable-gpl --enable-version3`.
- This is acceptable for private/dev WSL validation.
- It should not be treated as the future distributable default; future distribution should use a stricter LGPL/GPL/source/build/license posture.

## Download verification

- Upstream MD5 file: `7fa72b652e19bf84c9461e332ea1cdf3  ffmpeg-release-amd64-static.tar.xz`
- `md5sum -c`: `OK`
- Download tarball SHA256: `abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67`
- Hash readback command/session: `e99266d2-a96c-4d0b-ab5f-a0e1f5ee82b5` / `briny-crustacean`
- Hash readback marker: `STICKBOT_TARS_M7A_STATIC_DOWNLOAD_HASH_READBACK_PASS`

## Binary provenance

FFmpeg:

- Path: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg`
- SHA256: `e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99`
- Version: `ffmpeg version 7.0.2-static https://johnvansickle.com/ffmpeg/`
- Build: `built with gcc 8 (Debian 8.3.0-6)`
- Config includes: `--enable-gpl --enable-version3 --enable-static --disable-debug --disable-ffplay ... --enable-libopus ...`

FFprobe:

- Path: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe`
- SHA256: `4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d`
- Version: `ffprobe version 7.0.2-static https://johnvansickle.com/ffmpeg/`

## Normalizer implementation

Added bounded local normalizer contract:

- `src/audio-normalizer.js`
- `test/audio-normalizer.test.mjs`
- `scripts/m7a-sandboxed-ffmpeg-normalization-smoke.sh`

Fixed command shape:

```sh
ffmpeg -nostdin -hide_banner -loglevel error -y \
  -i input.webm \
  -ac 1 -ar 16000 -f wav output.wav
```

Safety behavior:

- `spawn(file,args,{shell:false})`.
- Rejects `/mnt/c` binary/input/output paths.
- Bounded stdout/stderr.
- Timeout/kill.
- Non-zero exit fail-closed.
- Normalization is explicit via `STT_NORMALIZE_AUDIO`.

## Validation

### Static checks

Initial M7A bundle stopped because a test harness emitted `close` before fake stderr delivery. Repaired the test harness and reran:

- Tests: `39/39 PASS`.
- No install/smoke performed before that repair.

### Sandbox normalization smoke

Command/session:

- `02aed404-7c9e-417b-b309-13de64bde293` / `glow-valley`

Markers:

- `M7A_FFMPEG_NORMALIZATION_SMOKE_COMPLETE`
- `STICKBOT_TARS_M7A_STATIC_FFMPEG_ACQUIRE_AND_NORMALIZE_PASS`

Result:

```json
{
  "classification": "STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS",
  "ffmpegSha256": "e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99",
  "ffprobeSha256": "4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d",
  "inputSha256": "b2504afa2c2ab1c7fd7291c75343c3161322948b7cddda0f7605a751453aedd5",
  "normalizedSha256": "38e3b264d99a035f168d6913520d2541a943c6a931e3f896882daf756b66fb7f",
  "normalizedBytes": 32078,
  "normalizedProbe": {
    "codec_name": "pcm_s16le",
    "sample_rate": "16000",
    "channels": 1
  },
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "cloudSpeechApiCalled": false,
  "browserWebSpeechApi": false,
  "openClawMutation": false
}
```

Evidence files:

- `result.json`
- `ffmpeg-version.txt`
- `ffprobe-version.txt`
- `ffmpeg.sha256`
- `ffprobe.sha256`
- `ffmpeg-apt-package.txt`
- `normalizer-result.json`
- `normalized-ffprobe.json`
- `fixture-input.sha256`
- `fixture-normalized.sha256`
- `fixture-input.stat`
- `fixture-normalized.stat`
- `fixture-input.file`
- `fixture-normalized.file`

## Boundaries preserved

- No OpenClaw mutation.
- No Gateway config/routing/default/fallback mutation.
- No Gateway restart.
- No NOA mutation.
- No cloud STT.
- No browser Web Speech API.
- No Android/LAN/Tailscale exposure.
- No persistent service install.
- No `/mnt/c` model/audio/runtime paths.
- No audio/model/cache/venv/runtime artifacts committed.

## Final classification

`STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`

Next target:

`STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`
