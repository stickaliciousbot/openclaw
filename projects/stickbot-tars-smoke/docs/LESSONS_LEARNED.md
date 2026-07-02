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

Do not proceed beyond M5 local-loopback serverization into LAN/mobile user testing without a separate owner approval and a fresh threat model.

## M5: private network namespaces need loopback enabled

The first M5 serverization smoke failed safely because the private `unshare -n` network namespace had external network isolation but loopback was down. XTTS loaded and listened, yet Node/curl could not reach `127.0.0.1:18020/ready`.

Durable rule: for local multi-process sandbox smokes, explicitly bring `lo` up inside the namespace, then verify both external network is blocked and local loopback works. Also initialize cleanup PIDs so early-stage failures do not mask the real failure classification.

## M5 passing local serverization stack

M5 local serverization passed with:

- minimal loopback XTTS HTTP server (`GET /health`, `GET /ready`, `POST /tts_to_audio/`);
- Node echo app in `OPENCLAW_MODE=echo`;
- private `unshare -Urnm` boundary;
- loopback enabled inside namespace;
- model/speaker read-only;
- secret dirs hidden;
- external network blocked/unavailable.

Generated Node voice smoke WAV SHA256: `1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec`.

## Future LAN/mobile demo access

Stick clarified on 2026-07-02 that before user testing, the TARS web app needs to be reachable from phone and laptop browsers. Preferred future path is host-PC proxy through the host PC's Tailscale connection/IP; the app does not need to run directly on a Tailscale-native host and can remain local/WSL-bound.

Do not blur this into M5. Treat it as a separate LAN/Tailscale milestone:

- explicit approval before starting;
- safe non-`8787` port;
- host-PC Tailscale proxy/reverse-proxy or restrictive portproxy plan;
- raw LAN exposure only as fallback;
- Origin/Host allowlist for phone/laptop URLs;
- CSRF still required;
- no wildcard CORS;
- XTTS kept loopback/private behind Node unless separately approved;
- phone and laptop browser validation before user testing.

## M6: adapter fixture before live provider/Gateway smoke

M6 proved the Node OpenClaw adapter path with a fixture CLI inside the sandbox before any live provider/Gateway call. This was the right safety sequence because the TARS `.pth` was loaded in the same boundary.

Durable adapter rules:

- Discover actual CLI shape from local docs/help before coding.
- Default raw inference shape is `openclaw infer model run --prompt {prompt} --json`.
- Full agent/session shape is `openclaw agent --message {prompt} --json` and should be explicit opt-in.
- Use `spawn(file,args,{shell:false})`, never shell interpolation.
- Require `{prompt}` placeholder to avoid ambiguous prompt concatenation.
- Bound stdout/stderr and enforce timeout/kill.
- Parse JSON and fail closed if no text is extractable.
- First adapter smoke can use a fixture CLI to prove process/JSON/prompt/voice wiring without provider or Gateway side effects.

M6 fixture result: Node `/api/chat` returned OpenClaw adapter fixture text and generated WAV SHA256 `fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0` inside the no-network, secret-hidden, read-only-model boundary. Live provider/Gateway smoke remains a separate approval gate.
