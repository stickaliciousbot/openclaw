#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptPath = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(scriptPath), '..');
const workspaceRoot = path.resolve(repoRoot, '..', '..');
const now = new Date();
const stamp = now.toISOString().replace(/[:.]/g, '-');

const args = new Set(process.argv.slice(2));
const writeArtifacts = !args.has('--stdout-only');
const includeStatus = args.has('--status') || args.has('--with-status');
const jsonOnly = args.has('--json');
const mdOnly = args.has('--md');

const RUNTIME = Object.freeze({
  projectRoot: 'projects/stickbot-tars-smoke',
  runtimeRoot: '/home/stickai/stickbot-voice',
  branch: 'feature/stickbot-tars-m25-hardening-repair',
  remote: 'https://github.com/stickaliciousbot/webworkspace.git',
  lanUrl: 'https://192.168.1.107:19890/',
  loopbackUrl: 'https://127.0.0.1:19890/',
  xttsUrl: 'http://127.0.0.1:8020',
  reservedPort: 8787,
  windowsLanIp: '192.168.1.107',
  wslIp: '172.24.168.46',
  httpsCertDir: '/home/stickai/stickbot-voice/certs/m7d-https',
  whisperBin: '/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli',
  whisperModel: '/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin',
  ffmpegBin: '/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg',
  ffprobeBin: '/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe',
  tarsModelPath: '/home/stickai/stickbot-voice/xtts_models/tars',
  referenceWav: '/home/stickai/stickbot-voice/speakers/reference.wav',
  tarsModel: {
    hfRepo: 'Pyrater/TARS',
    revision: '7a1517d76eb0db89828b1c812682fa75125e5de7',
    status: 'private-demo-only until rights/branding review'
  }
});

const CURRENT = Object.freeze({
  latestClassification: 'STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_FUNCTIONAL_PASS_TELEMETRY_READBACK_PENDING',
  lastPushedMilestone: 'STICKBOT_TARS_REHYDRATION_PACKET_WRITTEN',
  liveBrowserMilestone: 'STICKBOT_TARS_M7P_LIVE_BROWSER_STREAMING_BARGEIN_PASS',
  nextRecommendedMilestones: [
    'M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_TIMING_PROOF',
    'M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH',
    'LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC',
    'AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE'
  ],
  latestKnownLiveSmoke: {
    masteringEnabled: true,
    outputFormat: { codec: 'pcm_s16le', sampleRate: 48000, channels: 1, bitRate: 768000 },
    masteredFrames: 3,
    finalDurationSecondsBeforeTailGuard: 4.255,
    finalDurationSecondsAfterTailGuardSmoke: 5.035,
    r4TailDrainPadMs: 900,
    r4TerminalTailHintApplied: true,
    r4HumanConfirmedSentenceFinishedPerfectly: true,
    r4BargeInStillWorks: true
  }
});

const SOURCE_FILES = [
  ['repo', 'README.md'],
  ['repo', 'IMPLEMENTATION_NOTEBOOK.md'],
  ['repo', 'package.json'],
  ['repo', 'server.js'],
  ['repo', 'scripts/stickbot-tars-rehydrate.mjs'],
  ['repo', 'src/config.js'],
  ['repo', 'src/stt-adapter.js'],
  ['repo', 'src/audio-normalizer.js'],
  ['repo', 'src/audio/dsp-polish-stage.js'],
  ['repo', 'src/audio/voice-body-mastering-stage.js'],
  ['repo', 'src/audio/audio-performance-pipeline.js'],
  ['repo', 'src/audio/streaming-frame-interface.js'],
  ['repo', 'src/audio/full-duplex-turn-controller.js'],
  ['repo', 'src/audio/duplex-event-ingress.js'],
  ['repo', 'src/audio/partial-stt-loop.js'],
  ['repo', 'src/audio/wav-stitcher.js'],
  ['repo', 'src/audio/xtts-chunk-conductor.js'],
  ['repo', 'src/prosody/prosody-score-engine.js'],
  ['repo', 'src/voice/tars-prosody-kernel.js'],
  ['repo', 'src/voice/tars-prosody-matrix.js'],
  ['repo', 'public/app.js'],
  ['repo', 'public/index.html'],
  ['repo', 'safety/audio-path-policy.js'],
  ['repo', 'safety/network-policy.js'],
  ['repo', 'scripts/m7d-local-real-mic-demo.sh'],
  ['repo', 'scripts/m7e-start-xtts-loopback.sh'],
  ['repo', 'scripts/xtts-local-server.py'],
  ['repo', 'state/status.json'],
  ['doc', 'docs/STICKBOT_TARS_REHYDRATION.md'],
  ['doc', 'docs/PRODUCTION_VOICE_STREAM_ARCHITECTURE.md'],
  ['doc', 'docs/LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md'],
  ['doc', 'docs/LOOPBACK_LAN_EXPOSURE_NOTEBOOK.md'],
  ['doc', 'docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md'],
  ['doc', 'docs/m3-model-provenance/M3_MODEL_ACQUIRED_HASHED_PROVENANCE_RECORDED_NO_LOAD.md'],
  ['doc', 'docs/m5-local-serverization/M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS.md'],
  ['doc', 'docs/m6-openclaw-adapter/M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7d-real-mic-local-demo/M7D_HTTPS_LAN_REAL_MIC_STT_ECHO_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7e-https-lan-xtts-voice-output/M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7h-prosody-score-engine/M7H_M55_PROSODY_SCORE_ENGINE_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7i-chunk-conductor/M7I_CHUNK_CONDUCTOR_LOCAL_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7jkl-dsp-stream-duplex/M7JKL_DSP_STREAM_DUPLEX_LOCAL_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7mno-streaming-partial-bargein/M7MNO_STREAMING_PARTIAL_BARGEIN_LOCAL_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7p-live-browser-streaming-bargein/M7P_LIVE_BROWSER_STREAMING_BARGEIN_PASS.md'],
  ['doc', 'docs/m7-local-stt/m56-voice-body-mastering/M56_VOICE_BODY_POSTPROCESS_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7q-true-partial-local-stt-loop/M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_LIVE_PASS.md'],
  ['doc', 'docs/m7-local-stt/m7r-low-latency-streaming-transport/M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_FUNCTIONAL_PASS.md'],
  ['memory', '../../memory/2026-07-03.md'],
  ['memory', '../../memory/lessons-learned-stickbot-tars-live-dashboard-refresh-2026-07-03.md'],
  ['memory', '../../memory/lessons-learned-stickbot-tars-m7r-live-transport-repair-2026-07-03.md']
];

function relFromWorkspace(filePath) {
  return path.relative(workspaceRoot, filePath).replaceAll(path.sep, '/');
}

function absFromSource(relPath) {
  return path.resolve(repoRoot, relPath);
}

function sha256(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

function safeReadJson(filePath) {
  try {
    if (!existsSync(filePath)) return null;
    return JSON.parse(readFileSync(filePath, 'utf8'));
  } catch (error) {
    return { parseError: String(error?.message || error) };
  }
}

function fileInfo(kind, relPath) {
  const filePath = absFromSource(relPath);
  if (!existsSync(filePath)) return { kind, path: relFromWorkspace(filePath), exists: false };
  const buf = readFileSync(filePath);
  const text = buf.toString('utf8');
  const headings = text
    .split(/\r?\n/)
    .filter((line) => /^#{1,3}\s+/.test(line))
    .slice(0, 10);
  return {
    kind,
    path: relFromWorkspace(filePath),
    exists: true,
    bytes: buf.length,
    lines: text.length ? text.split(/\r?\n/).length : 0,
    sha256: sha256(buf),
    mtime: statSync(filePath).mtime.toISOString(),
    headings
  };
}

function walk(root, predicate, out = []) {
  if (!existsSync(root)) return out;
  for (const name of readdirSync(root)) {
    const p = path.join(root, name);
    const st = statSync(p);
    if (st.isDirectory()) walk(p, predicate, out);
    else if (predicate(p, st)) out.push({ path: p, stat: st });
  }
  return out;
}

function latestFiles(root, predicate, limit = 10) {
  return walk(root, predicate)
    .sort((a, b) => b.stat.mtimeMs - a.stat.mtimeMs)
    .slice(0, limit)
    .map(({ path: p, stat }) => ({ path: relFromWorkspace(p), mtime: stat.mtime.toISOString(), bytes: stat.size }));
}

function gitInfo(root) {
  if (!includeStatus || !existsSync(path.join(root, '.git'))) return null;
  try {
    return {
      root: relFromWorkspace(root),
      branch: execFileSync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
      commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
      remote: execFileSync('git', ['config', '--get', 'remote.origin.url'], { cwd: root, encoding: 'utf8' }).trim(),
      statusShort: execFileSync('git', ['status', '--short'], { cwd: root, encoding: 'utf8' }).trim().split('\n').filter(Boolean).slice(0, 120)
    };
  } catch (error) {
    return { root: relFromWorkspace(root), error: String(error?.message || error) };
  }
}

function runtimePathInfo(label, filePath) {
  const exists = existsSync(filePath);
  const item = { label, path: filePath, exists };
  if (exists) {
    const st = statSync(filePath);
    item.bytes = st.size;
    item.mtime = st.mtime.toISOString();
    if (st.isFile() && st.size <= 16 * 1024 * 1024) item.sha256 = sha256(readFileSync(filePath));
  }
  return item;
}

const statusJsonPath = path.join(repoRoot, 'state/status.json');
const statusJson = safeReadJson(statusJsonPath);
const sourceInventory = SOURCE_FILES.map(([kind, relPath]) => fileInfo(kind, relPath));
const missingSources = sourceInventory.filter((item) => !item.exists).map((item) => item.path);

const outputDir = path.join(repoRoot, 'data/audio/output');
const artifacts = {
  latestGeneratedWavs: latestFiles(outputDir, (p) => /\.wav$/i.test(p), 20),
  latestMasteredChunks: latestFiles(outputDir, (p) => /\.master\.wav$/i.test(p), 20),
  latestRehydrationPackets: latestFiles(path.join(repoRoot, 'artifacts/rehydration/stickbot-tars'), (p) => /stickbot-tars-rehydration\.(md|json)$/.test(p), 10),
  prosodyMatrixState: fileInfo('artifact', 'state/prosody-matrix.json'),
  statusJson: fileInfo('artifact', 'state/status.json')
};

const runtimePaths = [
  runtimePathInfo('runtimeRoot', RUNTIME.runtimeRoot),
  runtimePathInfo('tarsModelPath', RUNTIME.tarsModelPath),
  runtimePathInfo('referenceWav', RUNTIME.referenceWav),
  runtimePathInfo('whisperBin', RUNTIME.whisperBin),
  runtimePathInfo('whisperModel', RUNTIME.whisperModel),
  runtimePathInfo('ffmpegBin', RUNTIME.ffmpegBin),
  runtimePathInfo('ffprobeBin', RUNTIME.ffprobeBin),
  runtimePathInfo('httpsCertDir', RUNTIME.httpsCertDir)
];

const rehydration = {
  generatedAt: now.toISOString(),
  script: relFromWorkspace(scriptPath),
  mode: includeStatus ? 'offline-with-local-git-status' : 'offline-deterministic',
  project: {
    name: 'Stickbot-TARS local voice smoke',
    thesis: 'A local-only TARS-like voice/audio stack for Stickbot: browser text+mic UI, local whisper.cpp STT, local XTTS voice generation, deterministic prosody/chunking, DSP/mastering, streaming-frame playback, and barge-in control without mutating OpenClaw production routing.',
    repoRoot: relFromWorkspace(repoRoot),
    runtime: RUNTIME,
    current: CURRENT
  },
  guardrails: [
    'Do not mutate OpenClaw Gateway config, production routing/default/fallbacks, NOA, Android, or provider settings for this project unless Stick explicitly authorizes it.',
    'Do not use port 8787; it is reserved for NOA bridge work.',
    'Do not use cloud STT by default and do not use browser Web Speech API.',
    'Do not durably store raw mic transcripts; public/controller summaries use hashes/counts where possible.',
    'Do not store runtime/model/audio/venv/cache artifacts under /mnt/c paths.',
    'Do not commit generated audio, model files, venvs, caches, private keys, cert private keys, or runtime output directories.',
    'Canonical assistant text is authoritative; prosody, DSP, mastering, mood, and audio polish must not rewrite response text.',
    'TARS voice/branding remains private-demo-only until rights/branding review.'
  ],
  resumeCommands: {
    rehydrate: 'npm run rehydrate:tars',
    rehydrateWithGitStatus: 'npm run rehydrate:tars -- --status',
    check: 'npm run check',
    startXtts: 'npm run m7e:xtts:start',
    startHttpsLanDemo: 'HOST=0.0.0.0 PORT=19890 VOICE_DEMO_ALLOW_LAN=true VOICE_DEMO_HTTPS=true VOICE_DEMO_HTTPS_KEY=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.key.pem VOICE_DEMO_HTTPS_CERT=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.cert.pem LOG_DIR=/tmp/tars-live-demo bash scripts/m7d-local-real-mic-demo.sh',
    healthChecks: [
      'curl -k -fsS https://127.0.0.1:19890/health',
      'curl -k -fsS https://192.168.1.107:19890/health',
      'curl -fsS http://127.0.0.1:8020/ready'
    ],
    liveBrowserUrl: RUNTIME.lanUrl
  },
  milestones: {
    proven: [
      'M3 model acquired/provenance recorded, no load',
      'M4 sandboxed XTTS local load',
      'M5 local serverization node voice pass',
      'M6 OpenClaw adapter fixture voice pass',
      'M7D HTTPS LAN real mic STT + echo pass',
      'M7E audible HTTPS LAN TARS voice output pass',
      'M7F prosody kernel local check pass',
      'M7G tuning console + JSON/matrix controls + audible XTTS slider mapping pass',
      'M7H/M55 prosody score engine pass',
      'M7I chunk conductor local pass',
      'M7J/K/L DSP + streaming frame + duplex controller local pass',
      'M7M/N/O streaming playback hooks + partial ingress + barge-in local pass',
      'M7P live browser streaming + barge-in pass',
      'M5.6 voice body/mastering postprocess pass with R2 tail-trim fix, R3 tail guard, and R4 terminal tail/drain live PASS',
      'M7Q true partial local STT loop live pass: browser mic partials seq 0-5, final transcript, local whisper slices, privacy guard off',
      'M7R low-latency streaming transport live functional pass: partial STT, reconstruction, Send, audio generation, and barge-in confirmed; strict telemetry readback pending'
    ],
    next: CURRENT.nextRecommendedMilestones
  },
  liveReadiness: {
    status: statusJson?.m7r?.classification || 'SEE_STATUS_JSON',
    url: RUNTIME.lanUrl,
    needsHumanEar: 'M7R live functional pass is confirmed; strict timing closeout still needs browser Streaming telemetry readback/screenshot with first-play and max-gap values.'
  },
  statusJson,
  runtimePaths,
  sourceInventory,
  missingSources,
  artifacts,
  git: { repo: gitInfo(repoRoot) }
};

function mdEscape(value) {
  return String(value).replaceAll('|', '\\|');
}

function renderMarkdown(data) {
  const sourceRows = data.sourceInventory
    .map((s) => `| ${mdEscape(s.kind)} | \`${mdEscape(s.path)}\` | ${s.exists ? 'yes' : 'NO'} | ${s.exists ? s.lines : ''} | ${s.exists ? '`' + s.sha256.slice(0, 12) + '`' : ''} |`)
    .join('\n');
  const runtimeRows = data.runtimePaths
    .map((r) => `| ${mdEscape(r.label)} | \`${mdEscape(r.path)}\` | ${r.exists ? 'yes' : 'NO'} | ${r.bytes ?? ''} | ${r.sha256 ? '`' + r.sha256.slice(0, 12) + '`' : ''} |`)
    .join('\n');
  const gitBlock = data.git.repo ? `\n## Local git status snapshot\n\n- branch: ${data.git.repo.branch || '?'}\n- commit: ${data.git.repo.commit || '?'}\n- remote: ${data.git.repo.remote || '?'}\n- changed paths shown: ${(data.git.repo.statusShort || []).length}\n\n${(data.git.repo.statusShort || []).slice(0, 60).map((line) => `- \`${line}\``).join('\n')}\n` : '';

  return `# Stickbot-TARS deterministic rehydration packet\n\nGenerated: ${data.generatedAt}\nMode: ${data.mode}\n\n## Thesis\n\n${data.project.thesis}\n\n## Current project state\n\n- Project root: \`${data.project.runtime.projectRoot}\`\n- Runtime root: \`${data.project.runtime.runtimeRoot}\`\n- Git branch: \`${data.project.runtime.branch}\`\n- Remote: \`${data.project.runtime.remote}\`\n- LAN URL: \`${data.project.runtime.lanUrl}\`\n- XTTS URL: \`${data.project.runtime.xttsUrl}\`\n- Latest classification: \`${data.project.current.latestClassification}\`\n- Live browser milestone: \`${data.project.current.liveBrowserMilestone}\`\n\n## Guardrails\n\n${data.guardrails.map((g) => `- ${g}`).join('\n')}\n\n## Resume commands\n\n\`\`\`bash\n${data.resumeCommands.rehydrate}\n${data.resumeCommands.rehydrateWithGitStatus}\n${data.resumeCommands.check}\n${data.resumeCommands.startXtts}\n${data.resumeCommands.startHttpsLanDemo}\n${data.resumeCommands.healthChecks.join('\n')}\n\`\`\`\n\nBrowser URL for Stick: \`${data.resumeCommands.liveBrowserUrl}\`\n\n## Proven milestones\n\n${data.milestones.proven.map((m) => `- ${m}`).join('\n')}\n\n## Next recommended milestones\n\n${data.milestones.next.map((m) => `- ${m}`).join('\n')}\n\n## Live readiness note\n\n- Status: \`${data.liveReadiness.status}\`\n- Needs human ear: ${data.liveReadiness.needsHumanEar}\n\n## Runtime/local path inventory\n\n| Label | Path | Exists | Bytes | SHA256 prefix |\n|---|---|---:|---:|---|\n${runtimeRows}\n\n## Curated source inventory\n\n| Kind | Path | Exists | Lines | SHA256 prefix |\n|---|---|---:|---:|---|\n${sourceRows}\n\n${data.missingSources.length ? `Missing expected sources:\n\n${data.missingSources.map((p) => `- \`${p}\``).join('\n')}\n` : 'All curated sources were found.\n'}\n## Latest local generated-artifact pointers\n\nGenerated audio is local/runtime evidence only and should not be committed. Latest pointers:\n\n${data.artifacts.latestGeneratedWavs.slice(0, 8).map((a) => `- \`${a.path}\` (${a.bytes} bytes, ${a.mtime})`).join('\n') || '- none found'}\n\nLatest mastered chunks:\n\n${data.artifacts.latestMasteredChunks.slice(0, 8).map((a) => `- \`${a.path}\` (${a.bytes} bytes, ${a.mtime})`).join('\n') || '- none found'}\n\n${gitBlock}\n## Rehydration instruction\n\nFor future sessions: run \`npm run rehydrate:tars -- --status\`, read \`artifacts/rehydration/stickbot-tars/latest.md\`, then open only the listed source files needed for the immediate task. This packet restores project/goals/locations/procedures; it is not a substitute for running \`npm run check\` or the relevant live browser/audio smoke before claiming readiness.\n`;
}

const markdown = renderMarkdown(rehydration);
const outputRoot = path.join(repoRoot, 'artifacts', 'rehydration', 'stickbot-tars');
const runRoot = path.join(outputRoot, stamp);
let outputs = {};

if (writeArtifacts) {
  mkdirSync(runRoot, { recursive: true });
  const jsonPath = path.join(runRoot, 'stickbot-tars-rehydration.json');
  const mdPath = path.join(runRoot, 'stickbot-tars-rehydration.md');
  writeFileSync(jsonPath, `${JSON.stringify(rehydration, null, 2)}\n`, 'utf8');
  writeFileSync(mdPath, markdown, 'utf8');
  mkdirSync(outputRoot, { recursive: true });
  copyFileSync(jsonPath, path.join(outputRoot, 'latest.json'));
  copyFileSync(mdPath, path.join(outputRoot, 'latest.md'));
  outputs = {
    json: relFromWorkspace(jsonPath),
    markdown: relFromWorkspace(mdPath),
    latestJson: relFromWorkspace(path.join(outputRoot, 'latest.json')),
    latestMarkdown: relFromWorkspace(path.join(outputRoot, 'latest.md'))
  };
}

rehydration.outputs = outputs;

if (jsonOnly && !mdOnly) {
  console.log(JSON.stringify(rehydration, null, 2));
} else if (mdOnly && !jsonOnly) {
  console.log(markdown);
} else {
  console.log(JSON.stringify({
    classification: 'STICKBOT_TARS_REHYDRATION_PACKET_WRITTEN',
    generatedAt: rehydration.generatedAt,
    mode: rehydration.mode,
    sourceCount: sourceInventory.length,
    missingSources,
    outputs
  }, null, 2));
}
