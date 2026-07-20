#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

function usage() {
  console.error(
    "Usage: node scripts/check-openclaw-package-path-hygiene.mjs <package.tgz> [--json <path>]",
  );
}

const args = process.argv.slice(2);
const tarball = args[0];
if (!tarball || tarball.startsWith("-")) {
  usage();
  process.exit(2);
}
let jsonOut = null;
for (let i = 1; i < args.length; i += 1) {
  if (args[i] === "--json" && args[i + 1]) {
    jsonOut = args[i + 1];
    i += 1;
    continue;
  }
  usage();
  process.exit(2);
}

const tarballPath = path.resolve(tarball);
const packageRoot = process.cwd().replaceAll("\\", "/");
const configuredRoots = [
  packageRoot,
  process.env.OPENCLAW_PACKAGE_HYGIENE_SOURCE_ROOT,
  process.env.OPENCLAW_PACKAGE_HYGIENE_WORKSPACE_ROOT,
  process.env.OPENCLAW_PACKAGE_HYGIENE_BUILD_ROOT,
]
  .filter(Boolean)
  .map((value) => path.resolve(String(value)).replaceAll("\\", "/"));
const homeRoot = os.homedir().replaceAll("\\", "/");
const hostRoots = Array.from(
  new Set([...configuredRoots, homeRoot].filter((value) => value && value !== "/")),
);

function sha256Buffer(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function listExtractedFiles(root) {
  const files = [];
  const stack = [root];
  while (stack.length > 0) {
    const dir = stack.pop();
    for (const dirent of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, dirent.name);
      if (dirent.isDirectory()) {
        stack.push(fullPath);
      } else if (dirent.isFile()) {
        files.push(fullPath);
      }
    }
  }
  return files.sort();
}

function countNeedle(buffer, needle) {
  if (!needle.length) return 0;
  let count = 0;
  let offset = buffer.indexOf(needle);
  while (offset !== -1) {
    count += 1;
    offset = buffer.indexOf(needle, offset + 1);
  }
  return count;
}

const credentialPatterns = [
  /-----BEGIN (?:RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----[\s\S]{80,}-----END (?:RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----/u,
  /(?:GITHUB_TOKEN|TELEGRAM_BOT_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|OPENCLAW_[A-Z0-9_]*TOKEN)\s*[:=]\s*["'][A-Za-z0-9_./:+\-=]{20,}["']/u,
];

const broadNeedles = {
  slashHome: Buffer.from("/home/"),
  slashUsers: Buffer.from("/Users/"),
  wslMountC: Buffer.from("/mnt/c/"),
  wslMountD: Buffer.from("/mnt/d/"),
  fileUrl: Buffer.from("file:///"),
  windowsC: Buffer.from("C:\\"),
  windowsD: Buffer.from("D:\\"),
};

const tarballBytes = fs.readFileSync(tarballPath);
const extractRoot = fs.mkdtempSync(path.join(os.tmpdir(), "openclaw-package-path-hygiene-"));
try {
  const extract = spawnSync("tar", ["-xzf", tarballPath, "-C", extractRoot], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (extract.status !== 0) {
    throw new Error(`tar extract failed: ${extract.stderr || extract.stdout}`);
  }

  const files = listExtractedFiles(extractRoot);
  const findings = [];
  const broadCounts = Object.fromEntries(Object.keys(broadNeedles).map((key) => [key, 0]));
  let regionCommentCount = 0;

  for (const filePath of files) {
    const data = fs.readFileSync(filePath);
    const packageRelativePath = path
      .relative(path.join(extractRoot, "package"), filePath)
      .replaceAll("\\", "/");
    regionCommentCount += countNeedle(data, Buffer.from("//#region"));

    for (const [kind, needle] of Object.entries(broadNeedles)) {
      broadCounts[kind] += countNeedle(data, needle);
    }

    for (const root of hostRoots) {
      const count = countNeedle(data, Buffer.from(root));
      if (count > 0) {
        findings.push({ kind: "hostRootPath", packageRelativePath, count });
      }
    }

    if (data.length <= 8 * 1024 * 1024) {
      const text = data.toString("utf8");
      for (const pattern of credentialPatterns) {
        if (pattern.test(text)) {
          findings.push({ kind: "credentialOrSecretValue", packageRelativePath, count: 1 });
        }
      }
    }
  }

  const result = {
    schema: "openclaw.package_path_hygiene.v1",
    tarball: path.basename(tarballPath),
    tarballSha256: sha256Buffer(tarballBytes),
    tarballSizeBytes: tarballBytes.length,
    scannedFileCount: files.length,
    hostRootsScanned: hostRoots.map((root) =>
      root === homeRoot ? "<HOME>" : root === packageRoot ? "<SOURCE_ROOT>" : "<HOST_ROOT>",
    ),
    broadPathFormatCounts: broadCounts,
    generatedRegionCommentCount: regionCommentCount,
    actualHostPathFindingCount: findings.reduce((sum, finding) => sum + finding.count, 0),
    affectedFileCount: new Set(findings.map((finding) => finding.packageRelativePath)).size,
    findings,
    pass: findings.length === 0 && regionCommentCount === 0,
  };

  if (jsonOut) {
    fs.mkdirSync(path.dirname(path.resolve(jsonOut)), { recursive: true });
    fs.writeFileSync(jsonOut, `${JSON.stringify(result, null, 2)}\n`);
  }
  console.log(JSON.stringify(result, null, 2));
  if (!result.pass) {
    process.exit(1);
  }
} finally {
  fs.rmSync(extractRoot, { recursive: true, force: true });
}
