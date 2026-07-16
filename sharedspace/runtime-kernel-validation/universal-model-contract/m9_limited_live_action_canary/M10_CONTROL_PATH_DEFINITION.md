# M10 Control Path Definition

Status: `BLOCKED_M10_CONTROL_PATH_GAP`

Existing UMC installed modules found:

- `umc-m4-verified-route.js`
- `umc-m5-capability-manifest.js`
- `umc-m6-contract-build-lane.js`
- `umc-m7-model-eligibility.js`
- `umc-m8-owner-contract-lane.js`

Proposed M10A enforcement point:

- Owner Telegram direct path only
- After M8 enforced-no-send contract decision check
- Before any UMC-controlled action/reply side effect

Blocking gap:

No current installed runtime-backed M10A enable/disable flag was found. A proposed control artifact path can be defined, but approval text to enable M10A would be unsafe until source/staged install adds or proves the control reader.
