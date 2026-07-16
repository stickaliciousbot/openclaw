#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { buildM5SeedManifests } from "../src/auto-reply/reply/umc-m5-capability-manifest.ts";

const target = path.resolve(process.cwd(), "src/auto-reply/reply/umc-m5-seed-manifests.json");
const manifests = buildM5SeedManifests("2026-07-16T00:45:00.000Z");
const payload = {
  schema: "umc.v1.m5.seed_capability_manifests.v1",
  generated_utc: "2026-07-16T00:45:00Z",
  status: "PASS_M5_CAPABILITY_MANIFESTS_SEEDED_NO_SEND",
  manifests,
};
fs.writeFileSync(target, `${JSON.stringify(payload, null, 2)}\n`);
console.log(JSON.stringify({ target, count: manifests.length, status: payload.status }, null, 2));
