# M10A Installed Command Surface Discovery

Status: `M10A_COMMAND_SURFACE_PARTIAL`

The installed/source M10A control module exposes safe helper functions:

- `buildM10ADefaultControlState`
- `readM10AStatus`
- `applyM10AControlIntent`
- `disableM10AControlState`
- `evaluateM10AOwnerTelegramDirectContractDecision`

Those are not enough for production enablement approval. They are module-level helpers, not a proven persisted operator command surface.

Not proven: Gateway RPC, OpenClaw CLI, persistent control-artifact write/read, rollback command, post-enable observation runner, operator-stop handler, or installed admin command registration.

Decision: command surface is partial; final approval text must not be produced.
