# M10A Control Path Schema

Status: `PASS_M10A_CONTROL_PATH_SCHEMA_DEFINED`

Control artifact path: `state/umc-v1/m10a-owner-telegram-direct-enforcement/control.json`

Enable flag: `m10a_enabled`

Disable flag: `m10a_enabled=false`

Status/readback path: `umc.m10a.ownerTelegramDirect.status`

Default: disabled. Scope is owner Telegram direct chat `8495203551`, agent `main`, contract-decision enforcement only. External sends, provider calls, write tools, durable memory mutation, Context Bridge mutation, broad enforcement, and production authority are false by default and forbidden by the enable validator.
