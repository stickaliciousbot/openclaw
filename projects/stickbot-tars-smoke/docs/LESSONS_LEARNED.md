# Stickbot-TARS Lessons Learned

Last updated: 2026-07-02 18:31 AEST / 2026-07-02T08:31:00Z

## Documentation is part of the gate

Milestone PASS requires notebook updates, not just a working command:

- `IMPLEMENTATION_NOTEBOOK.md`
- `docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md`
- `docs/LESSONS_LEARNED.md`
- milestone status/closeout evidence

This keeps cold-resume safe and avoids rediscovering dependency/sandbox failures.

## M2.5: fail closed before model work

Hardening the Node demo before model acquisition was correct. Required gates included fail-closed config, loopback-by-default, reserved port refusal for `8787`, UUID-only audio paths, split upload limits, Origin checks, and CSRF/session nonce checks.

## M3: model provenance is not model safety

Hashing pinned model files gives provenance and repeatability only. `.pth` remains pickle-based and must not be loaded in the production OpenClaw/Gateway process or in a context that can see secrets.

## M4: isolation must include filesystem secrecy

Network isolation alone was insufficient. Plain `unshare -Urn` still exposed `/home/stickai/.openclaw`. The accepted no-root fallback was `unshare -Urnm` with model/speaker read-only mounts, output writable mount, network namespace, and empty bind mounts over `.openclaw`, `.ssh`, `.codex`, and `.config`.

A dedicated low-privilege user/container is still preferable later, but was blocked from Telegram context by sudo TTY/password requirements.

## M4: pin the XTTS dependency stack

Open-ended latest packages caused cascading failures:

- `xtts-api-server` pulled `pyaudio`, which needed `Python.h`.
- `transformers==5.12.1` broke Coqui XTTS imports.
- `torch==2.12.1+cpu` triggered Coqui's TorchCodec requirement.
- `torchcodec==0.14.0` failed native loading with the current CPU stack.

Known passing local M4 stack:

- `coqui-tts==0.27.5`
- `torch==2.8.0+cpu`
- `torchaudio==2.8.0+cpu`
- `transformers==4.57.6`
- CPU-only, `cuda_available False`

## Current state after M4

M4 passed: local TARS XTTS model load and first WAV generation succeeded inside the no-network, secret-hidden, read-only-model boundary.

Do not proceed to M5/integration/serverization without a separate owner approval and a fresh threat model.
