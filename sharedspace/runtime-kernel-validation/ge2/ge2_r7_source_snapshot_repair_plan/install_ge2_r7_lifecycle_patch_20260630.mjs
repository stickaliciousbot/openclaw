import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan';
const stamp = '20260630T0812Z';
const snapshotDir = path.join(artifactDir, `install_snapshots_${stamp}`);
const target = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js';
fs.mkdirSync(snapshotDir, { recursive: true });
function sha256(data) { return crypto.createHash('sha256').update(data).digest('hex'); }
function shaFile(file) { return sha256(fs.readFileSync(file)); }
const before = fs.readFileSync(target, 'utf8');
const beforeSha = sha256(before);
const snapshotPath = path.join(snapshotDir, path.basename(target));
fs.writeFileSync(snapshotPath, before);

if (before.includes('GE2_R7_COMMAND_REGISTRY_LIFECYCLE_START')) {
  throw new Error('R7 lifecycle marker already present; refusing duplicate patch');
}

const helper = `
// GE2_R7_COMMAND_REGISTRY_LIFECYCLE_START
const GE2_R7_NATIVE_PLUGIN_ID = "ge2-native";
const GE2_R7_NATIVE_PLUGIN_NAME = "GE2 Native Command Surface";
const GE2_R7_NATIVE_RUNTIME_ROOT = "/home/stickai/.openclaw/workspace/ge2-native-runtime";
const GE2_R7_NATIVE_STATE_DIR = "/home/stickai/.openclaw/workspace/state/ge2-native";
const GE2_R7_NATIVE_ARTIFACT_DIR = "/home/stickai/.openclaw/workspace/state/ge2-native/artifacts";
const GE2_R7_NATIVE_ROUTER_PATH = "/home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_command_router.mjs";
const GE2_R7_NATIVE_DISPATCHER_PATH = "/home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_dispatcher.mjs";
const GE2_R7_NATIVE_ROUTER_URL = "file:///home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_command_router.mjs";
const GE2_R7_NATIVE_DISPATCHER_URL = "file:///home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_dispatcher.mjs";
function formatGe2R7RunSummary(run) {
	const milestones = Array.isArray(run?.milestones) ? run.milestones.length : 0;
	const artifacts = Array.isArray(run?.artifacts) ? run.artifacts.length : 0;
	const errors = Array.isArray(run?.errors) ? run.errors.length : 0;
	return [
		"run_id: " + (run?.run_id ?? "unknown"),
		"status: " + (run?.status ?? "unknown"),
		"task: " + (run?.task ?? "n/a"),
		"milestones: " + milestones,
		"artifacts: " + artifacts,
		"errors: " + errors,
		"updated_at: " + (run?.updated_at ?? "n/a")
	].join("\\n");
}
function formatGe2R7DispatchResult(envelope, result, ge2HelpText) {
	if (!result || typeof result !== "object") return "⚠️ GE2 returned an empty result.";
	if (result.ok === false) return "⚠️ GE2 " + (result.error?.code ?? "ERROR") + ": " + (result.error?.message ?? "Unknown error");
	if (result.kind === "help") return ge2HelpText();
	if (result.kind === "run_accepted") return [
		"✅ GE2 run accepted.",
		"run_id: " + result.run_id,
		"status: " + result.status,
		"task: " + result.task,
		"Use /ge2 status " + result.run_id + " for progress."
	].join("\\n");
	if (result.kind === "status") return ["GE2 status:", formatGe2R7RunSummary(result.run)].join("\\n");
	if (result.kind === "artifacts") {
		const artifacts = Array.isArray(result.artifacts) ? result.artifacts : [];
		if (artifacts.length === 0) return "GE2 artifacts for " + result.run_id + ": none recorded.";
		return ["GE2 artifacts for " + result.run_id + ":", ...artifacts.map((artifact) => ("- " + (artifact.name ?? artifact.kind ?? "artifact") + ": " + (artifact.sha256 ?? "no-sha") + " " + (artifact.path ?? "")).trim())].join("\\n");
	}
	if (result.kind === "cancel_requested") return "GE2 cancel requested for " + result.run_id + ".";
	return "GE2 result:\\n" + JSON.stringify(result, null, 2);
}
async function handleNativeGe2Command(ctx = {}) {
	const [{ buildGe2Envelope, ge2HelpText }, { Ge2Dispatcher }] = await Promise.all([
		import(GE2_R7_NATIVE_ROUTER_URL),
		import(GE2_R7_NATIVE_DISPATCHER_URL)
	]);
	const args = typeof ctx.args === "string" ? ctx.args.trim() : "";
	const input = args ? "/ge2 " + args : "/ge2";
	const envelopeResult = buildGe2Envelope({
		input,
		origin: {
			surface: ctx.channel || "openclaw",
			channel: ctx.channel || null,
			sessionKey: ctx.sessionKey || null,
			sessionId: ctx.sessionId || null,
			accountId: ctx.accountId || null,
			messageId: ctx.messageId || null,
			senderId: ctx.senderId || null
		}
	});
	if (!envelopeResult.ok) return { text: "⚠️ GE2 " + (envelopeResult.error?.code ?? "PARSE_ERROR") + ": " + (envelopeResult.error?.message ?? "Invalid command") };
	const dispatcher = new Ge2Dispatcher({
		stateDir: GE2_R7_NATIVE_STATE_DIR,
		artifactDir: GE2_R7_NATIVE_ARTIFACT_DIR
	});
	const result = await dispatcher.dispatch(envelopeResult.envelope);
	return { text: formatGe2R7DispatchResult(envelopeResult.envelope, result, ge2HelpText) };
}
function createNativeGe2CommandDefinition() {
	return {
		name: "ge2",
		nativeName: "ge2",
		nativeNames: { default: "ge2", telegram: "ge2" },
		description: "Run and inspect native GE2 durable command-surface operations.",
		acceptsArgs: true,
		requireAuth: true,
		handler: handleNativeGe2Command
	};
}
function ge2R7CommandMatches(command) {
	if (!command || typeof command !== "object") return false;
	if (normalizeLowercaseStringOrEmpty(command.name) === "ge2") return true;
	if (normalizeLowercaseStringOrEmpty(command.nativeName) === "ge2") return true;
	for (const alias of Object.values(command.nativeNames ?? {})) if (normalizeLowercaseStringOrEmpty(alias) === "ge2") return true;
	return false;
}
function ensureNativeGe2CommandRegistered(registry) {
	const command = createNativeGe2CommandDefinition();
	const hasRegisteredGe2 = listRegisteredPluginCommands().some(ge2R7CommandMatches) || pluginCommands.has("/ge2");
	if (!hasRegisteredGe2) {
		const result = registerPluginCommand(GE2_R7_NATIVE_PLUGIN_ID, command, {
			pluginName: GE2_R7_NATIVE_PLUGIN_NAME,
			pluginRoot: GE2_R7_NATIVE_RUNTIME_ROOT
		});
		// GE2 native descriptor registered into pluginCommands
		if (!result.ok && !String(result.error ?? "").includes("already registered")) registry?.diagnostics?.push({
			level: "error",
			pluginId: GE2_R7_NATIVE_PLUGIN_ID,
			source: GE2_R7_NATIVE_ROUTER_PATH,
			message: "GE2 native descriptor registration failed: " + (result.error ?? "unknown error")
		});
	}
	if (registry && Array.isArray(registry.commands)) {
		const registryGe2Count = registry.commands.filter((entry) => ge2R7CommandMatches(entry?.command)).length;
		if (registryGe2Count === 0) registry.commands.push({
			pluginId: GE2_R7_NATIVE_PLUGIN_ID,
			pluginName: GE2_R7_NATIVE_PLUGIN_NAME,
			command,
			source: GE2_R7_NATIVE_ROUTER_PATH,
			rootDir: GE2_R7_NATIVE_RUNTIME_ROOT
		});
	}
	// idempotent no duplicate ge2
}
// GE2_R7_COMMAND_REGISTRY_LIFECYCLE_END
`;

const anchor = `function clearActivatedPluginRuntimeState() {
	clearAgentHarnesses();
	clearPluginCommands();
	clearCompactionProviders();
	clearDetachedTaskLifecycleRuntimeRegistration();
	clearPluginInteractiveHandlers();
	clearMemoryEmbeddingProviders();
	clearMemoryPluginState();
}
`;
if (!before.includes(anchor)) throw new Error('clearActivatedPluginRuntimeState anchor not found');
let next = before.replace(anchor, anchor + helper);

const cacheAnchor = `				restorePluginCommands(cached.state.commands ?? []);
				restoreRegisteredCompactionProviders(cached.state.compactionProviders);
`;
if (!next.includes(cacheAnchor)) throw new Error('cache restore anchor not found');
next = next.replace(cacheAnchor, `				restorePluginCommands(cached.state.commands ?? []);
				ensureNativeGe2CommandRegistered(cached.state.registry);
				restoreRegisteredCompactionProviders(cached.state.compactionProviders);
`);

const normalAnchor = `		if (cacheEnabled) setCachedPluginRegistry(cacheKey, {
			commands: listRegisteredPluginCommands(),
`;
if (!next.includes(normalAnchor)) throw new Error('normal cache anchor not found');
next = next.replace(normalAnchor, `		if (shouldActivate) ensureNativeGe2CommandRegistered(registry);
		if (cacheEnabled) setCachedPluginRegistry(cacheKey, {
			commands: listRegisteredPluginCommands(),
`);

for (const marker of [
  'GE2_R7_COMMAND_REGISTRY_LIFECYCLE_START',
  'GE2_R7_COMMAND_REGISTRY_LIFECYCLE_END',
  'ensureNativeGe2CommandRegistered',
  'GE2 native descriptor registered into pluginCommands',
  'idempotent no duplicate ge2'
]) {
  if (!next.includes(marker)) throw new Error(`missing marker after patch: ${marker}`);
}

const tmp = `${target}.ge2-r7-${stamp}.${process.pid}.tmp`;
fs.writeFileSync(tmp, next, { mode: 0o644 });
fs.renameSync(tmp, target);
const afterSha = shaFile(target);
const reverserPath = path.join(artifactDir, `reverser_ge2_r7_lifecycle_${stamp}.mjs`);
fs.writeFileSync(reverserPath, `#!/usr/bin/env node\nimport fs from 'node:fs';\nconst target = ${JSON.stringify(target)};\nconst snapshot = ${JSON.stringify(snapshotPath)};\nconst tmp = target + '.restore-' + Date.now() + '-' + process.pid + '.tmp';\nfs.copyFileSync(snapshot, tmp);\nfs.renameSync(tmp, target);\nconsole.log('restored ' + target + ' from ' + snapshot);\n`);
const manifest = {
  generatedAt: new Date().toISOString(),
  classification: 'GE2_R7_LIFECYCLE_PATCH_INSTALLED_LOCAL_VALIDATION_PENDING',
  productionMutationPerformed: true,
  target,
  snapshotPath,
  reverserPath,
  beforeSha256: beforeSha,
  afterSha256: afterSha,
  markers: {
    start: next.includes('GE2_R7_COMMAND_REGISTRY_LIFECYCLE_START'),
    end: next.includes('GE2_R7_COMMAND_REGISTRY_LIFECYCLE_END'),
    helper: next.includes('ensureNativeGe2CommandRegistered'),
    registeredMessage: next.includes('GE2 native descriptor registered into pluginCommands'),
    idempotentMessage: next.includes('idempotent no duplicate ge2')
  },
  touchedFiles: [target],
  hardStops: {
    gatewayRestartPerformed: false,
    liveGe2SmokePerformed: false,
    cronCloseoutApplyPerformed: false,
    rollbackPerformed: false
  }
};
const manifestPath = path.join(artifactDir, `install_manifest_ge2_r7_lifecycle_${stamp}.json`);
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ manifestPath, reverserPath, snapshotPath, beforeSha, afterSha, markers: manifest.markers }, null, 2));
