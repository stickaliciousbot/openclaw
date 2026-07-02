#!/usr/bin/env python3
"""Minimal loopback-only XTTS HTTP server for Stickbot-TARS M5.

This server is intentionally small and local-only. It loads a local XTTS model
from an explicit WSL-native path and exposes the endpoint shape currently used
by the Node smoke app:

  POST /tts_to_audio/  {"text":"...", "speaker_wav":"reference.wav", "language":"en"}

It does not call OpenClaw, providers, STT, Android, Telegram, or Gateway APIs.
Run it inside the M5 sandbox launcher for validation.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


HOST = os.environ.get("TARS_XTTS_HOST", "127.0.0.1")
PORT = env_int("TARS_XTTS_PORT", 18020)
ALLOW_LAN = env_bool("VOICE_DEMO_ALLOW_LAN", False)
MODEL_DIR = Path(os.environ.get("TARS_XTTS_MODEL_DIR", "/tmp/tars-m5-boundary/model")).resolve()
SPEAKER_DIR = Path(os.environ.get("TARS_XTTS_SPEAKER_DIR", "/tmp/tars-m5-boundary/speakers")).resolve()
MAX_TEXT_CHARS = env_int("TARS_XTTS_MAX_TEXT_CHARS", 1000)
DEFAULT_LANGUAGE = os.environ.get("TARS_XTTS_LANGUAGE", "en")

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
SAFE_SPEAKER_RE = re.compile(r"^[A-Za-z0-9_.-]+\.wav$")

MODEL = None
CONFIG = None
STARTED_AT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
MODEL_LOADED_AT = None


def fail_start(message: str, code: int = 2) -> None:
    print(f"STICKBOT_TARS_M5_XTTS_SERVER_START_BLOCKED: {message}", file=sys.stderr)
    raise SystemExit(code)


def validate_startup() -> None:
    if HOST not in LOOPBACK_HOSTS and not ALLOW_LAN:
        fail_start(f"non-loopback host refused without VOICE_DEMO_ALLOW_LAN=true: {HOST}")
    if PORT == 8787:
        fail_start("reserved NOA port refused: 8787")
    for label, p in {"model": MODEL_DIR, "speaker": SPEAKER_DIR}.items():
        s = str(p)
        if s.startswith("/mnt/c/") or s == "/mnt/c":
            fail_start(f"{label} path under /mnt/c refused: {s}")
        if not p.exists():
            fail_start(f"{label} path missing: {s}")
    for name in ("config.json", "vocab.json", "model.pth", "speakers_xtts.pth"):
        if not (MODEL_DIR / name).is_file():
            fail_start(f"missing model artifact: {MODEL_DIR / name}")
    if not (SPEAKER_DIR / "reference.wav").is_file():
        fail_start(f"missing reference speaker: {SPEAKER_DIR / 'reference.wav'}")


def load_model() -> None:
    global MODEL, CONFIG, MODEL_LOADED_AT
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    import torch

    config = XttsConfig()
    config.load_json(str(MODEL_DIR / "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_path=str(MODEL_DIR / "model.pth"),
        vocab_path=str(MODEL_DIR / "vocab.json"),
        speaker_file_path=str(MODEL_DIR / "speakers_xtts.pth"),
        use_deepspeed=False,
    )
    model.to("cpu")
    MODEL = model
    CONFIG = config
    MODEL_LOADED_AT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(
        json.dumps(
            {
                "classification": "STICKBOT_TARS_M5_XTTS_SERVER_MODEL_LOADED",
                "modelDir": str(MODEL_DIR),
                "speakerDir": str(SPEAKER_DIR),
                "torchVersion": torch.__version__,
                "cudaAvailable": bool(torch.cuda.is_available()),
                "loadedAt": MODEL_LOADED_AT,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("content-length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler: BaseHTTPRequestHandler, status: int, message: str, classification: str) -> None:
    json_response(handler, status, {"ok": False, "error": message, "classification": classification})


def resolve_speaker(name: str) -> Path:
    speaker_name = name or "reference.wav"
    if not SAFE_SPEAKER_RE.fullmatch(speaker_name):
        raise ValueError("speaker_wav must be a simple .wav basename")
    speaker = (SPEAKER_DIR / speaker_name).resolve()
    if SPEAKER_DIR not in speaker.parents and speaker != SPEAKER_DIR:
        raise ValueError("speaker_wav escaped speaker directory")
    if not speaker.is_file():
        raise FileNotFoundError(f"speaker_wav not found: {speaker_name}")
    return speaker


class Handler(BaseHTTPRequestHandler):
    server_version = "StickbotTarsXTTS/0.1"

    def log_message(self, fmt: str, *args) -> None:  # keep stdout machine-readable-ish
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            return json_response(
                self,
                200,
                {
                    "ok": True,
                    "classification": "STICKBOT_TARS_M5_XTTS_SERVER_HEALTH",
                    "host": HOST,
                    "port": PORT,
                    "startedAt": STARTED_AT,
                    "modelLoaded": MODEL is not None,
                    "modelLoadedAt": MODEL_LOADED_AT,
                },
            )
        if path == "/ready":
            status = 200 if MODEL is not None else 503
            return json_response(
                self,
                status,
                {
                    "ok": MODEL is not None,
                    "classification": "STICKBOT_TARS_M5_XTTS_SERVER_READY" if MODEL is not None else "STICKBOT_TARS_M5_XTTS_SERVER_NOT_READY",
                    "modelLoaded": MODEL is not None,
                    "modelLoadedAt": MODEL_LOADED_AT,
                },
            )
        return error_response(self, 404, "not found", "STICKBOT_TARS_M5_XTTS_SERVER_NOT_FOUND")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/tts_to_audio/":
            return error_response(self, 404, "not found", "STICKBOT_TARS_M5_XTTS_SERVER_NOT_FOUND")
        if MODEL is None or CONFIG is None:
            return error_response(self, 503, "model not loaded", "STICKBOT_TARS_M5_XTTS_SERVER_NOT_READY")
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 65536:
                return error_response(self, 413, "request body too large", "STICKBOT_TARS_M5_XTTS_SERVER_BODY_LIMIT")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(payload.get("text", "")).strip()
            if not text:
                return error_response(self, 400, "text is required", "STICKBOT_TARS_M5_XTTS_SERVER_BAD_TEXT")
            if len(text) > MAX_TEXT_CHARS:
                return error_response(self, 413, "text too large", "STICKBOT_TARS_M5_XTTS_SERVER_TEXT_LIMIT")
            language = str(payload.get("language", DEFAULT_LANGUAGE) or DEFAULT_LANGUAGE)
            if language != DEFAULT_LANGUAGE:
                return error_response(self, 400, "unsupported language", "STICKBOT_TARS_M5_XTTS_SERVER_BAD_LANGUAGE")
            speaker = resolve_speaker(str(payload.get("speaker_wav", "reference.wav")))

            import soundfile as sf

            result = MODEL.synthesize(text, CONFIG, speaker_wav=str(speaker), language=language)
            audio = result["wav"] if isinstance(result, dict) and "wav" in result else result
            out = io.BytesIO()
            sf.write(out, audio, CONFIG.audio.output_sample_rate, format="WAV")
            wav = out.getvalue()
            self.send_response(200)
            self.send_header("content-type", "audio/wav")
            self.send_header("x-stickbot-tars-classification", "STICKBOT_TARS_M5_XTTS_SERVER_TTS_PASS")
            self.send_header("content-length", str(len(wav)))
            self.end_headers()
            self.wfile.write(wav)
        except Exception as e:  # keep server alive and return bounded public error
            traceback.print_exc()
            return error_response(self, 500, str(e)[:500], "STICKBOT_TARS_M5_XTTS_SERVER_TTS_FAILED")


def main() -> None:
    validate_startup()
    load_model()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        json.dumps(
            {
                "classification": "STICKBOT_TARS_M5_XTTS_SERVER_LISTENING",
                "url": f"http://{HOST}:{PORT}",
                "ready": True,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
