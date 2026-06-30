import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface';
const target = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js';
const manifestPath = path.join(artifactDir, 'install_manifest_20260630T0715Z.json');
const backupDir = path.join(artifactDir, 'snapshots_20260630T0715Z');
const backup = path.join(backupDir, 'commands-D2qp4St4.js.pre-ge2-r5');
const reverser = path.join(artifactDir, 'reverser_20260630T0715Z.mjs');

function sha256(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function writeAtomic(file, content) {
  const tmp = `${file}.tmp-${process.pid}-${Date.now()}`;
  fs.writeFileSync(tmp, content);
  fs.renameSync(tmp, file);
}

const insertion = String.raw`const MAX_ARGS_LENGTH = 4096;
// GE2_R5_NATIVE_COMMAND_SURFACE_START
const GE2_NATIVE_STATE_DIR = "/home/stickai/.openclaw/workspace/state/ge2-native";
const GE2_NATIVE_ARTIFACT_DIR = "/home/stickai/.openclaw/workspace/state/ge2-native/artifacts";
const GE2_NATIVE_ROUTER_URL = "file:///home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_command_router.mjs";
const GE2_NATIVE_DISPATCHER_URL = "file:///home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_dispatcher.mjs";
function formatGe2RunSummary(run) {
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
	].join("\n");
}
function formatGe2DispatchResult(envelope, result, ge2HelpText) {
	if (!result || typeof result !== "object") return "⚠️ GE2 returned an empty result.";
	if (result.ok === false) return "⚠️ GE2 " + (result.error?.code ?? "ERROR") + ": " + (result.error?.message ?? "Unknown error");
	if (result.kind === "help") return ge2HelpText();
	if (result.kind === "run_accepted") return [
		"✅ GE2 run accepted.",
		"run_id: " + result.run_id,
		"status: " + result.status,
		"task: " + result.task,
		"Use /ge2 status " + result.run_id + " for progress."
	].join("\n");
	if (result.kind === "status") return ["GE2 status:", formatGe2RunSummary(result.run)].join("\n");
	if (result.kind === "artifacts") {
		const artifacts = Array.isArray(result.artifacts) ? result.artifacts : [];
		if (artifacts.length === 0) return "GE2 artifacts for " + result.run_id + ": none recorded.";
		return ["GE2 artifacts for " + result.run_id + ":", ...artifacts.map((artifact) => ("- " + (artifact.name ?? artifact.kind ?? "artifact") + ": " + (artifact.sha256 ?? "no-sha") + " " + (artifact.path ?? "")).trim())].join("\n");
	}
	if (result.kind === "cancel_requested") return "GE2 cancel requested for " + result.run_id + ".";
	return "GE2 result:\n" + JSON.stringify(result, null, 2);
}
async function handleNativeGe2Command(ctx = {}) {
	const [{ buildGe2Envelope, ge2HelpText }, { Ge2Dispatcher }] = await Promise.all([
		import(GE2_NATIVE_ROUTER_URL),
		import(GE2_NATIVE_DISPATCHER_URL)
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
		stateDir: GE2_NATIVE_STATE_DIR,
		artifactDir: GE2_NATIVE_ARTIFACT_DIR
	});
	const result = await dispatcher.dispatch(envelopeResult.envelope);
	return { text: formatGe2DispatchResult(envelopeResult.envelope, result, ge2HelpText) };
}
function ensureNativeGe2CommandRegistered() {
	if (pluginCommands.has("/ge2")) return;
	pluginCommands.set("/ge2", {
		name: "ge2",
		nativeName: "ge2",
		nativeNames: { default: "ge2", telegram: "ge2" },
		description: "Run and inspect native GE2 durable command-surface operations.",
		acceptsArgs: true,
		requireAuth: true,
		pluginId: "ge2-native",
		pluginName: "GE2 Native Command Surface",
		ownership: "reserved",
		handler: handleNativeGe2Command
	});
}
ensureNativeGe2CommandRegistered();
// GE2_R5_NATIVE_COMMAND_SURFACE_END
`;

ensureDir(artifactDir);
ensureDir(backupDir);
const before = fs.readFileSync(target, 'utf8');
const beforeHash = sha256(before);
if (!fs.existsSync(backup)) fs.writeFileSync(backup, before);

const marker = 'GE2_R5_NATIVE_COMMAND_SURFACE_START';
if (!before.includes(marker)) {
  const needle = 'const MAX_ARGS_LENGTH = 4096;\n';
  if (!before.includes(needle)) throw new Error('Patch anchor not found: MAX_ARGS_LENGTH');
  writeAtomic(target, before.replace(needle, insertion));
}
const final = fs.readFileSync(target, 'utf8');
const afterHash = sha256(final);
const manifest = {
  manifest_id: 'GE2_R5_NATIVE_COMMAND_SURFACE_20260630T0715Z',
  created_at: new Date().toISOString(),
  classification: 'GE2_R5_NATIVE_COMMAND_SURFACE_INSTALL_APPLIED_PENDING_RESTART_VALIDATION',
  target,
  changes: [{ target, backup, action: 'modified', before_sha256: beforeHash, after_sha256: afterHash }],
  markers: {
    start: final.includes('GE2_R5_NATIVE_COMMAND_SURFACE_START'),
    end: final.includes('GE2_R5_NATIVE_COMMAND_SURFACE_END'),
    registered: final.includes('ensureNativeGe2CommandRegistered();'),
    dispatcher: final.includes('Ge2Dispatcher'),
    noPlaceholderSuccess: !final.includes('placeholder GE2 success')
  }
};
writeAtomic(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
writeAtomic(reverser, `import fs from 'node:fs';\nimport crypto from 'node:crypto';\nconst manifestPath = ${JSON.stringify(manifestPath)};\nfunction sha256(bytes){return crypto.createHash('sha256').update(bytes).digest('hex')}\nconst manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));\nconst results=[];\nfor (const change of manifest.changes){\n  const backup=fs.readFileSync(change.backup);\n  fs.writeFileSync(change.target, backup);\n  const restored=fs.readFileSync(change.target);\n  results.push({target:change.target, restored_sha256:sha256(restored), expected_sha256:change.before_sha256, ok:sha256(restored)===change.before_sha256});\n}\nconsole.log(JSON.stringify({manifest_id: manifest.manifest_id, ok: results.every(r=>r.ok), results}, null, 2));\n`);
console.log(JSON.stringify({ok:true, manifestPath, reverser, beforeHash, afterHash, markers:manifest.markers}, null, 2));
