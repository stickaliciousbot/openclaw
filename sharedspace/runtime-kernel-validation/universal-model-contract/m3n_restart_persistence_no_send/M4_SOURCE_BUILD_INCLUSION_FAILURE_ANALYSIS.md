# M4 Source Build Inclusion Failure Analysis

Status: `PASS_M4_SOURCE_BUILD_INCLUSION_FAILURE_ANALYZED`

Root cause: `SOURCE_FILE_NOT_INCLUDED_IN_BUILD_GRAPH`

Secondary classification: `SOURCE_FILE_NOT_IMPORTED_BY_RUNTIME`

## Summary

The M4 VerifiedRoute/firewall implementation existed in source, tests, and fixture scripts, but it was not part of the runtime build graph. No runtime seam imported it, and `tsdown.config.ts` did not declare it as a stable package dist entry. As a result, tsdown omitted it from `dist`, and `npm pack` omitted it from the tarball.

## Evidence

- M4 source file: `src/auto-reply/reply/umc-m4-verified-route.ts`
- M4 test file: `src/auto-reply/reply/umc-m4-verified-route.test.ts`
- Fixture script imported M4 directly from source: `scripts/run-m4-verified-route-fixtures.mjs`
- Runtime comparison:
  - M3/M2 symbols are present in `dist/agent-runner.runtime-DESbFJnG.js` because `followup-runner.ts` imports M3 envelope supervision and contains M2 queued route admission.
  - M4 had no equivalent runtime/build edge.
- Previous package validation recorded tarball SHA256 `92634bc0a599a16a687e4ef50575f8ca8ade7d367afc47a16090949c61b1f7e5` with M4 artifact absent.

## Ruled out

- `BUILD_OUTPUT_NOT_INCLUDED_IN_PACKAGE`: not primary; package includes `dist/`, but M4 was absent from `dist`.
- `PACKAGE_FILES_EXCLUDE_M4_ARTIFACT`: not primary; no M4 artifact existed to exclude.
- `WRONG_SOURCE_TREE_OR_BRANCH`: source branch/head matched the authoritative source commit.
- `BUILD_COMMAND_SKIPPED_RUNTIME_ENTRYPOINT`: not primary; build produced M2/M3 runtime symbols.
- `UI_BUILD_BLOCKING_PACKAGE_OUTPUT`: not primary for M4 runtime artifact; UI build is separate from this runtime module.

## Repair selected

Add `src/auto-reply/reply/umc-m4-verified-route.ts` as an explicit stable tsdown package dist entry under `buildDockerE2eHarnessEntries`, matching the existing package-internal harness entry pattern. This includes M4 in `dist`/package without enabling enforcement or mutating installed runtime.

## Safety

No install, no installed runtime mutation, no direct dist hotpatch, no Gateway restart, no Telegram send/probe, no provider/model live call, no route/config mutation, no durable memory mutation, no Context Bridge mutation, no production authority change, no enforcement, no M5.
