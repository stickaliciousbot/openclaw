# M10A Rollback / Off-Switch Source Behavior

Status: `PASS_M10A_ROLLBACK_OFF_SWITCH_SOURCE_DEFINED`

Exact off-switch: set `m10a_enabled=false` in `state/umc-v1/m10a-owner-telegram-direct-enforcement/control.json`.

Status/readback path: `umc.m10a.ownerTelegramDirect.status`.

The source off-switch resets M10A to disabled, clears contract-decision enforcement, preserves production_authority=false and broad_enforcement=false, and leaves excluded surfaces unaffected. Operator stop or abort threshold requests disable/hold M10A fail-closed.
