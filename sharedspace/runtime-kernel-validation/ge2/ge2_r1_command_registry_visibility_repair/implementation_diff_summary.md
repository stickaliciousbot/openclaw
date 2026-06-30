# Implementation Diff Summary

- Restored GE2 native runtime under workspace/ge2-native-runtime.
- Patched hooks/ge2-register/handler.js to validate/re-register through visible registry for diagnostics/backstop.
- Replaced stale plugins/ge2-command implementation with an official api.registerCommand plugin.
- Installed/staged managed GE2 plugin under ~/.openclaw/extensions/ge2-command with absolute imports to restored runtime.
- Added configSchema/commandAliases manifest metadata.
- Renamed duplicate workspace extension copy out of discovery: workspace/.openclaw/extensions/ge2-command.disabled-20260630T0408Z.

No cron production retry, model route, cache, provider, fallback, or memory promotion changes were made.
