# Recommended GE2-R3 scope

Recommended scope: **packaging/bundle singleton repair**.

Reason: GE2 registration is visible through the hook registrar's imported registry but absent from live Gateway RPC commands.list. Same-process local probes show registrar/list identity works when loaded in one module realm, so R3 should focus on why the running Gateway has non-identical registry authority and repair canonical singleton/module resolution.

Secondary acceptable shape: a narrow registry bridge repair, if it calls the exact authoritative RPC command-list registry and preserves auth/visibility.

Not recommended as primary: startup load-order, command-list snapshot refresh, filter/visibility repair.

Do not start/apply GE2-R3 automatically.
