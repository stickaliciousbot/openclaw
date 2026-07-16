#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const M10A_RELATIVE_PATH = "dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js";
const MANIFEST_RELATIVE_PATH = "M10A_SCOPED_OVERLAY_MANIFEST.json";
const REQUIRED_RUNTIME_DEPENDENCIES = Object.freeze({
  "dist/umc-m8-owner-contract-lane-CdxuqyX4.js":
    "70e580814a1649068dcd173d979ac31d579b5ef7ae85866753c1503133815ed7",
  "dist/umc-m7-model-eligibility-ovqh9OfD.js":
    "e25711e5809835085d4c5450f5b1fb4e479b6f9e29631b538fd1f9908e78b9bd",
  "dist/umc-m6-contract-build-lane-B49r9Ao5.js":
    "8416342de89bf8e525f477c4255c59b54f0a5a624d8a1c02dd2e783aa51a397a",
  "dist/umc-m5-capability-manifest-DBUsXqaz.js":
    "3f4dc6191a7e4ffced65b95aaeb9113964f2c9c36c1958c634fbdefb5d059745",
  "dist/umc-m4-verified-route-B8LC1Bgv.js":
    "8fd34dd344ec074204feb6231127ae0ff9bf7655f5273b864103cf5b457b5cc2",
  "dist/umc-m3-envelope-supervision-CZFFPUFB.js":
    "9af1b667eb69a32c7d7f9bd28c3bd72843e331d63cc8bf8e81399479a6a7dfba",
});

const DEFAULT_PRESERVED = Object.freeze({
  "package.json": "9585403b5d52ef6b56a6faf6b958eb1ae22d14f7a581def93da13b597087b0ad",
  "dist/extensions/telegram/openclaw.plugin.json":
    "a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd",
  "dist/auto-reply/reply/umc-m4-verified-route.js":
    "9012c1d9ef5e651dfcf3b0dff533fa33b5ce08f226e21d3a7733b8faef02cff6",
  "dist/auto-reply/reply/umc-m5-capability-manifest.js":
    "e5a1d1c32a97ace2fe33cc151d98bd8ff4afed17ae768a7cf351319ef15adfe2",
  "dist/auto-reply/reply/umc-m6-contract-build-lane.js":
    "9fb2893b5cc7c7a75c7aa15b93d3cfee53eac164970485ad597d72a47f7e8bbc",
  "dist/auto-reply/reply/umc-m7-model-eligibility.js":
    "85e80863ee7720453e57c62b5c7955a681a0e8398e80a9ab9d026fcb66c4f996",
  "dist/auto-reply/reply/umc-m8-owner-contract-lane.js":
    "27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db",
});

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      throw new Error(`Unexpected positional argument: ${arg}`);
    }
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = "true";
      continue;
    }
    args[key] = next;
    i += 1;
  }
  return args;
}

function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: "utf8", ...options });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(
      `${command} ${args.join(" ")} failed with code ${result.status}: ${result.stderr || result.stdout}`,
    );
  }
  return result.stdout;
}

function listOverlay(overlayPath) {
  return run("tar", ["-tf", overlayPath])
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((entry) => entry.replace(/^\.\//u, ""))
    .filter((entry) => entry.length > 0 && !entry.endsWith("/"));
}

function verifyOverlayEntries(entries) {
  const required = [
    M10A_RELATIVE_PATH,
    MANIFEST_RELATIVE_PATH,
    ...Object.keys(REQUIRED_RUNTIME_DEPENDENCIES),
  ];
  const allowed = new Set(required);
  const forbidden = entries.filter((entry) => !allowed.has(entry));
  if (forbidden.length > 0) {
    return { ok: false, status: "FAIL_M10A_PACKAGE_PRESERVATION_GUARD_ACCEPTED_DRIFT", forbidden };
  }
  for (const requiredEntry of required) {
    if (!entries.includes(requiredEntry)) {
      return {
        ok: false,
        status: "FAIL_M10A_PACKAGE_DRIFT_REPAIR_PACKAGE_DRY_RUN",
        missing: requiredEntry,
      };
    }
  }
  return { ok: true, status: "PASS_M10A_SCOPED_OVERLAY_FILE_LIST" };
}

function extractOverlay(overlayPath) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "m10a-overlay-"));
  run("tar", ["-xf", overlayPath, "-C", dir]);
  return dir;
}

function verifyPreserved(installedRoot, preserved = DEFAULT_PRESERVED) {
  const results = {};
  const failures = [];
  for (const [relativePath, expectedSha256] of Object.entries(preserved)) {
    const file = path.join(installedRoot, relativePath);
    if (!fs.existsSync(file)) {
      results[relativePath] = { ok: false, expectedSha256, actualSha256: null, reason: "missing" };
      failures.push(relativePath);
      continue;
    }
    const actualSha256 = sha256File(file);
    const ok = actualSha256 === expectedSha256;
    results[relativePath] = { ok, expectedSha256, actualSha256 };
    if (!ok) failures.push(relativePath);
  }
  return { ok: failures.length === 0, results, failures };
}

function copyFileAtomic(source, target) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const temp = `${target}.tmp-${process.pid}`;
  fs.copyFileSync(source, temp);
  fs.renameSync(temp, target);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const mode = args.mode ?? "dry-run";
  if (mode !== "dry-run" && mode !== "apply") {
    throw new Error(`Unsupported mode: ${mode}`);
  }
  const overlay = args.overlay;
  const installedRoot = args["installed-root"];
  const expectedOverlaySha256 = args["expected-overlay-sha256"];
  const expectedM10aSha256 = args["expected-m10a-sha256"];
  const backupPath = args["backup-path"];
  if (!overlay || !installedRoot || !expectedOverlaySha256 || !expectedM10aSha256) {
    throw new Error(
      "Required: --overlay --installed-root --expected-overlay-sha256 --expected-m10a-sha256",
    );
  }

  const overlaySha256 = sha256File(overlay);
  if (overlaySha256 !== expectedOverlaySha256) {
    throw new Error(
      `Overlay SHA mismatch: expected ${expectedOverlaySha256}, got ${overlaySha256}`,
    );
  }

  const entries = listOverlay(overlay);
  const overlayList = verifyOverlayEntries(entries);
  if (!overlayList.ok) {
    console.log(
      JSON.stringify({ status: overlayList.status, overlaySha256, entries, overlayList }, null, 2),
    );
    process.exit(1);
  }

  const extractDir = extractOverlay(overlay);
  const m10aSource = path.join(extractDir, M10A_RELATIVE_PATH);
  const m10aSha256 = sha256File(m10aSource);
  if (m10aSha256 !== expectedM10aSha256) {
    throw new Error(`M10A SHA mismatch: expected ${expectedM10aSha256}, got ${m10aSha256}`);
  }
  const dependencyChecks = {};
  for (const [relativePath, expectedSha256] of Object.entries(REQUIRED_RUNTIME_DEPENDENCIES)) {
    const dependencySource = path.join(extractDir, relativePath);
    if (!fs.existsSync(dependencySource)) {
      throw new Error(`Required runtime dependency missing from overlay: ${relativePath}`);
    }
    const actualSha256 = sha256File(dependencySource);
    dependencyChecks[relativePath] = {
      ok: actualSha256 === expectedSha256,
      expectedSha256,
      actualSha256,
    };
    if (actualSha256 !== expectedSha256) {
      throw new Error(
        `Required runtime dependency SHA mismatch for ${relativePath}: expected ${expectedSha256}, got ${actualSha256}`,
      );
    }
  }

  const before = verifyPreserved(installedRoot);
  if (!before.ok) {
    console.log(
      JSON.stringify(
        {
          status: "FAIL_M10A_PACKAGE_PRESERVATION_GUARD_PRESERVED_INPUT_DRIFT",
          overlaySha256,
          before,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }

  const installableEntries = [M10A_RELATIVE_PATH, ...Object.keys(REQUIRED_RUNTIME_DEPENDENCIES)];
  const expectedInstalledChanges = installableEntries.map((relativePath) => {
    const target = path.join(installedRoot, relativePath);
    return {
      operation: fs.existsSync(target) ? "replace" : "add",
      path: target,
      sha256:
        relativePath === M10A_RELATIVE_PATH
          ? m10aSha256
          : dependencyChecks[relativePath].actualSha256,
    };
  });
  if (mode === "apply") {
    if (!backupPath) {
      throw new Error("--backup-path is required in apply mode");
    }
    if (!fs.existsSync(backupPath)) {
      fs.mkdirSync(path.dirname(backupPath), { recursive: true });
      fs.cpSync(installedRoot, backupPath, {
        recursive: true,
        dereference: false,
        preserveTimestamps: true,
      });
    }
    for (const relativePath of installableEntries) {
      copyFileAtomic(path.join(extractDir, relativePath), path.join(installedRoot, relativePath));
    }
  }

  const after = verifyPreserved(installedRoot);
  if (!after.ok) {
    console.log(
      JSON.stringify(
        {
          status: "FAIL_M10A_PACKAGE_PRESERVATION_GUARD_ACCEPTED_DRIFT",
          overlaySha256,
          before,
          after,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }

  const output = {
    schema: "umc.v1.m10a.preservation_guard.result.v1",
    status:
      mode === "dry-run"
        ? "PASS_M10A_PACKAGE_PRESERVATION_GUARD_DRY_RUN"
        : "PASS_M10A_PACKAGE_PRESERVATION_GUARD_APPLY",
    mode,
    overlay,
    overlaySha256,
    entries,
    expectedInstalledChange: expectedInstalledChanges[0],
    expectedInstalledChanges,
    requiredRuntimeDependencies: dependencyChecks,
    preservedChecksBefore: before.results,
    preservedChecksAfter: after.results,
    m10aEnabled: false,
    productionAuthorityChanged: false,
    broadEnforcementEnabled: false,
    sideEffectCounters: {
      telegramSendProbeCount: 0,
      externalSendCount: 0,
      providerModelLiveCallCount: 0,
      writeToolExecutionCount: 0,
      durableMemoryMutationCount: 0,
      contextBridgeMutationCount: 0,
    },
  };
  console.log(JSON.stringify(output, null, 2));
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exit(1);
}
