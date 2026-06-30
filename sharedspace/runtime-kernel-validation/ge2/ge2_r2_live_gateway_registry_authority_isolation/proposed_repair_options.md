# Proposed GE2-R3 repair options (not applied)

1. **Packaging/bundle singleton repair — recommended.** Ensure hook registrar, plugin activation, and Gateway RPC commands.list resolve one canonical command registry singleton/module authority. This may require source-level rebuild or canonical exported registry bridge.
2. Registry bridge repair: expose a safe internal registration bridge from hook/plugin startup into the exact RPC command-list registry object. Must preserve auth and not expose hidden commands.
3. Startup load-order repair: only if R3 proves plugin activation runs before the authoritative registry exists or gets cleared after hook registration. Current R2 evidence points more strongly to registry non-identity than pure load order.
4. Command-list snapshot refresh repair: not recommended based on R2; commands.list appears live, not static.
5. Filter/visibility repair: not recommended; /ge2 is absent before filtering.

Do not hardcode /ge2 into commands.list.
