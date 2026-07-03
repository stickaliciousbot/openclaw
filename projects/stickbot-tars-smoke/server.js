import http from 'node:http';
import https from 'node:https';
import { mkdir, readFile, writeFile, appendFile } from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { loadConfig } from './src/config.js';
import { askOpenClaw } from './src/openclaw-adapter.js';
import { transcribeAudio } from './src/stt-adapter.js';
import { normalizeAudio } from './src/audio-normalizer.js';
import { polishChunkArtifacts } from './src/audio/dsp-polish-stage.js';
import { masterVoiceBodyArtifacts } from './src/audio/voice-body-mastering-stage.js';
import { buildFinalSttControllerSummary, buildPartialSttControllerSummary, runSanitizedDuplexScenario } from './src/audio/duplex-event-ingress.js';
import { conductChunkedXtts, publicChunkConductorSummary } from './src/audio/xtts-chunk-conductor.js';
import { resolveAudioOutputPath, audioUrlForFile } from './safety/audio-path-policy.js';
import { readJsonBody, readAudioUploadBody, assertTextWithinLimit } from './safety/limits.js';
import { assertPostOriginAllowed } from './safety/origin-policy.js';
import { createSessionStore, createCsrfSession, assertCsrf } from './safety/csrf.js';
import { buildTarsProsodyPlan, publicProsodyPlanSummary } from './src/voice/tars-prosody-kernel.js';
import {
  establishTarsTuningBaseline,
  loadTarsTuningState,
  publicTuningSummary,
  resetActiveTarsTuning,
  restoreTarsTuningBaseline,
  updateActiveTarsTuning
} from './src/voice/tars-prosody-tuning.js';
import {
  loadTarsProsodyMatrixState,
  publicProsodyMatrixSummary,
  resetTarsProsodyMatrixJson,
  uploadTarsProsodyMatrixJson
} from './src/voice/tars-prosody-matrix.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const config = loadConfig();
const csrfStore = createSessionStore();
const AUDIO_INPUT_DIR = path.join(__dirname, 'data', 'audio', 'input');
const AUDIO_OUTPUT_DIR = path.join(__dirname, 'data', 'audio', 'output');
const AUDIO_NORMALIZED_DIR = path.join(__dirname, 'data', 'audio', 'normalized');

function json(res, status, obj, extraHeaders = {}) {
  const body = JSON.stringify(obj, null, 2);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
    ...extraHeaders
  });
  res.end(body);
}

function publicError(e) {
  return {
    status: e.statusCode || 500,
    body: {
      error: e.publicMessage || e.message || 'internal error',
      classification: e.classification || undefined
    }
  };
}

function stamp() {
  const now = new Date();
  return { iso: now.toISOString(), day: now.toISOString().slice(0, 10) };
}

function safeSummary(s, n = 180) {
  return String(s || '').replace(/\s+/g, ' ').trim().slice(0, n);
}

async function logTurn({ id, userText, assistantText, audioPath, source }) {
  const { iso, day } = stamp();
  const daily = path.join(config.workspace, 'memory', `${day}.md`);
  await mkdir(path.dirname(daily), { recursive: true });
  await appendFile(
    daily,
    `\n## ${iso} — Stickbot TARS voice smoke turn\n\n- id: \`${id}\`\n- source: ${source}\n- user: ${safeSummary(userText, 500)}\n- assistant: ${safeSummary(assistantText, 500)}\n${audioPath ? `- audio: project-local-output/${path.basename(audioPath)}\n` : ''}`,
    'utf8'
  );

  const evtDir = path.join(config.workspace, 'memory', 'context-bridge-events');
  await mkdir(evtDir, { recursive: true });
  const timeCompact = new Date().toISOString().slice(11, 19).replaceAll(':', '');
  const evt = {
    id: `evt-${day.replaceAll('-', '')}T${timeCompact}Z-stickbot-tars-voice-smoke-${id}`,
    timestamp: iso,
    localTime: iso,
    summary: `Stickbot TARS voice smoke turn logged: user='${safeSummary(userText, 80)}', assistant='${safeSummary(assistantText, 80)}'`,
    status: 'OBSERVED',
    classification: 'STICKBOT_TARS_VOICE_SMOKE_TURN',
    source,
    artifacts: { audioFile: audioPath ? path.basename(audioPath) : null },
    boundaries: {
      externalCloudSpeechRecognition: false,
      browserWebSpeechApi: false,
      xttsExpectedLocalOnly: true
    }
  };
  const evtPath = path.join(evtDir, `${evt.id}.json`);
  await writeFile(evtPath, `${JSON.stringify(evt, null, 2)}\n`, 'utf8');
  return { dailyWritten: true, eventWritten: true };
}

async function requestXttsAudio({ text, xttsParams }) {
  const r = await fetch(`${config.xttsUrl.replace(/\/$/, '')}/tts_to_audio/`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      text,
      speaker_wav: config.xttsSpeaker,
      language: config.xttsLanguage,
      temperature: xttsParams?.temperature,
      top_p: xttsParams?.topP,
      top_k: xttsParams?.topK,
      repetition_penalty: xttsParams?.repetitionPenalty,
      length_penalty: xttsParams?.lengthPenalty,
      speed: xttsParams?.speed
    })
  });
  if (!r.ok) throw new Error(`XTTS ${r.status}: ${await r.text()}`);
  return Buffer.from(await r.arrayBuffer());
}

async function synthesize(text, id) {
  const tuningState = await loadTarsTuningState(config.workspace);
  const voicePlan = buildTarsProsodyPlan(text, { tuning: tuningState.active, matrixState: tuningState.matrixState });
  if (!voicePlan.noSecretSpeech) {
    const e = new Error('TARS_NO_SECRET_SPEECH_FAIL: refusing to synthesize secret-like text');
    e.classification = 'TARS_NO_SECRET_SPEECH_FAIL';
    throw e;
  }
  await mkdir(AUDIO_OUTPUT_DIR, { recursive: true });
  const chunkDir = AUDIO_OUTPUT_DIR;
  const finalOut = path.join(AUDIO_OUTPUT_DIR, `${id}.wav`);
  const conductor = await conductChunkedXtts({
    turnId: id,
    score: voicePlan.prosodyScoreRaw,
    outputDir: chunkDir,
    finalOutPath: finalOut,
    ffmpegBin: config.ffmpegBin,
    stitchWorkDir: path.join(AUDIO_OUTPUT_DIR, `${id}-stitch`),
    dspProcessor: polishChunkArtifacts,
    dspOutputDir: AUDIO_OUTPUT_DIR,
    masteringProcessor: masterVoiceBodyArtifacts,
    masteringOutputDir: AUDIO_OUTPUT_DIR,
    timeoutMs: config.audioNormalizeTimeoutMs,
    synthesizeChunk: async ({ text: chunkText, renderText, effectiveXtts, renderTextSha256, terminalTailHintApplied }) => ({
      buffer: await requestXttsAudio({ text: renderText || chunkText, xttsParams: effectiveXtts }),
      synthesis: { provider: 'local_xtts_loopback', chunked: true, renderTextSha256, terminalTailHintApplied: Boolean(terminalTailHintApplied) }
    })
  });
  const publicPlan = publicProsodyPlanSummary(voicePlan);
  publicPlan.audioPerformance = publicChunkConductorSummary(conductor);
  publicPlan.delivery.renderer = conductor.output.renderer;
  return {
    file: conductor.output.file,
    url: audioUrlForFile(path.basename(conductor.output.file)),
    voicePlan: publicPlan,
    classification: conductor.classification
  };
}

async function xttsReady(timeoutMs = 1200) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const base = config.xttsUrl.replace(/\/$/, '');
    const r = await fetch(`${base}/ready`, { signal: controller.signal });
    if (!r.ok) return { ready: false, status: r.status };
    const body = await r.json().catch(() => ({}));
    return { ready: Boolean(body.ok ?? body.ready ?? true), status: r.status };
  } catch (e) {
    return { ready: false, error: e.name === 'AbortError' ? 'timeout' : e.message };
  } finally {
    clearTimeout(timer);
  }
}

async function staticFile(res, rel) {
  const full = path.join(__dirname, 'public', rel === '/' ? 'index.html' : rel);
  const data = await readFile(full);
  const ext = path.extname(full);
  const type = ext === '.html'
    ? 'text/html; charset=utf-8'
    : ext === '.js'
      ? 'text/javascript; charset=utf-8'
      : 'application/octet-stream';
  res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' });
  res.end(data);
}

function guardMutatingRequest(req) {
  assertPostOriginAllowed(req, config);
  assertCsrf(req, csrfStore);
}

const requestHandler = async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host || `${config.host}:${config.port}`}`);
    if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/app.js')) {
      return staticFile(res, url.pathname === '/app.js' ? 'app.js' : '/');
    }
    if (req.method === 'GET' && url.pathname === '/api/session') {
      const { csrfToken } = createCsrfSession(csrfStore, res);
      return json(res, 200, { csrfToken });
    }
    if (req.method === 'GET' && url.pathname.startsWith('/audio/')) {
      const raw = url.pathname.slice('/audio/'.length);
      const { full } = resolveAudioOutputPath(AUDIO_OUTPUT_DIR, raw);
      const data = await readFile(full);
      res.writeHead(200, { 'content-type': 'audio/wav' });
      return res.end(data);
    }
    if (req.method === 'GET' && url.pathname === '/health') {
      return json(res, 200, {
        ok: true,
        protocol: config.httpsEnabled ? 'https' : 'http',
        openclawMode: config.openclawMode,
        xttsUrl: config.xttsUrl,
        host: config.host,
        port: config.port,
        maxAudioDurationSeconds: config.maxAudioDurationSeconds
      });
    }
    if (req.method === 'GET' && url.pathname === '/api/capabilities') {
      const voice = await xttsReady();
      const tuningState = await loadTarsTuningState(config.workspace);
      return json(res, 200, {
        ok: true,
        openclawMode: config.openclawMode,
        sttMode: config.sttMode,
        voice: {
          enabled: voice.ready,
          xttsUrl: config.xttsUrl,
          reason: voice.ready ? 'xtts_ready' : 'xtts_not_ready',
          detail: voice.error || voice.status || null
        },
        prosodyTuning: {
          enabled: true,
          active: tuningState.active,
          baseline: tuningState.baseline,
          boundaries: tuningState.active.boundaries
        },
        boundaries: {
          browserWebSpeechApi: false,
          cloudSpeechApi: false
        }
      });
    }
    if (req.method === 'GET' && url.pathname === '/api/prosody') {
      const tuningState = await loadTarsTuningState(config.workspace);
      return json(res, 200, publicTuningSummary(tuningState));
    }
    if (req.method === 'GET' && url.pathname === '/api/prosody/matrix') {
      const matrixState = await loadTarsProsodyMatrixState(config.workspace);
      return json(res, 200, publicProsodyMatrixSummary(matrixState));
    }
    if (req.method === 'POST' && url.pathname === '/api/prosody/matrix') {
      guardMutatingRequest(req);
      const body = await readJsonBody(req, config.maxJsonBodyBytes);
      const matrixState = await uploadTarsProsodyMatrixJson(config.workspace, body);
      const tuningState = await loadTarsTuningState(config.workspace);
      return json(res, 200, { matrix: publicProsodyMatrixSummary(matrixState), prosody: publicTuningSummary(tuningState) });
    }
    if (req.method === 'POST' && url.pathname === '/api/prosody/matrix/reset') {
      guardMutatingRequest(req);
      const matrixState = await resetTarsProsodyMatrixJson(config.workspace);
      const tuningState = await loadTarsTuningState(config.workspace);
      return json(res, 200, { matrix: publicProsodyMatrixSummary(matrixState), prosody: publicTuningSummary(tuningState) });
    }
    if (req.method === 'POST' && url.pathname === '/api/prosody') {
      guardMutatingRequest(req);
      const body = await readJsonBody(req, config.maxJsonBodyBytes);
      const tuningState = await updateActiveTarsTuning(config.workspace, body);
      return json(res, 200, publicTuningSummary(tuningState));
    }
    if (req.method === 'POST' && url.pathname === '/api/prosody/reset') {
      guardMutatingRequest(req);
      const tuningState = await resetActiveTarsTuning(config.workspace);
      return json(res, 200, publicTuningSummary(tuningState));
    }
    if (req.method === 'POST' && url.pathname === '/api/prosody/baseline') {
      guardMutatingRequest(req);
      const tuningState = await establishTarsTuningBaseline(config.workspace);
      return json(res, 200, publicTuningSummary(tuningState));
    }
    if (req.method === 'POST' && url.pathname === '/api/prosody/restore-baseline') {
      guardMutatingRequest(req);
      const tuningState = await restoreTarsTuningBaseline(config.workspace);
      return json(res, 200, publicTuningSummary(tuningState));
    }
    if (req.method === 'POST' && url.pathname === '/api/duplex/scenario') {
      guardMutatingRequest(req);
      const body = await readJsonBody(req, config.maxJsonBodyBytes);
      const id = body.turnId || crypto.randomUUID();
      return json(res, 200, runSanitizedDuplexScenario(Array.isArray(body.events) ? body.events : [], { turnId: id }));
    }
    if (req.method === 'POST' && url.pathname === '/api/stt/partial') {
      guardMutatingRequest(req);
      const body = await readJsonBody(req, config.maxJsonBodyBytes);
      const id = body.turnId || crypto.randomUUID();
      return json(res, 200, {
        id,
        classification: 'STICKBOT_TARS_M7N_PARTIAL_STT_CONTROLLER_INGRESS_PASS',
        duplex: buildPartialSttControllerSummary({ turnId: id, partialText: body.partialText || '', confidence: body.confidence ?? null }),
        boundaries: {
          rawTranscriptDurableStorage: false,
          browserWebSpeechApi: false,
          cloudSpeechApi: false
        }
      });
    }
    if (req.method === 'POST' && url.pathname === '/api/chat') {
      guardMutatingRequest(req);
      const { text, voice = true } = await readJsonBody(req, config.maxJsonBodyBytes);
      assertTextWithinLimit(text, config.maxTextChars);
      const id = crypto.randomUUID();
      const assistantText = await askOpenClaw(text, config);
      let audio = null;
      if (voice) {
        try { audio = await synthesize(assistantText, id); }
        catch (e) { audio = { error: e.message, classification: 'PASS_WITH_VOICE_FAILURE' }; }
      }
      const logs = await logTurn({ id, userText: text, assistantText, audioPath: audio?.file, source: 'stickbot-tars-smoke:text' });
      return json(res, 200, {
        id,
        text: assistantText,
        audioUrl: audio?.url || null,
        audioError: audio?.error || null,
        voiceClassification: audio?.classification || (audio?.url ? 'VOICE_SYNTHESIS_PASS' : (voice ? null : 'VOICE_FALSE_TEXT_ONLY_PASS')),
        voicePlan: audio?.voicePlan || null,
        logs
      });
    }
    if (req.method === 'POST' && url.pathname === '/api/stt') {
      guardMutatingRequest(req);
      const id = crypto.randomUUID();
      const ct = req.headers['content-type'] || 'application/octet-stream';
      const ext = String(ct).includes('webm') ? 'webm' : 'bin';
      await mkdir(AUDIO_INPUT_DIR, { recursive: true });
      const out = path.join(AUDIO_INPUT_DIR, `${id}-input.${ext}`);
      const buf = await readAudioUploadBody(req, config.maxAudioUploadBytes);
      await writeFile(out, buf);
      if (config.sttMode === 'capture') {
        return json(res, 501, {
          id,
          savedLocal: true,
          sttMode: config.sttMode,
          maxAudioDurationSeconds: config.maxAudioDurationSeconds,
          error: 'Local STT engine not configured yet. Audio captured locally only; no cloud speech API used.'
        });
      }
      let sttInput = out;
      let normalized = null;
      if (config.audioNormalize) {
        await mkdir(AUDIO_NORMALIZED_DIR, { recursive: true });
        normalized = path.join(AUDIO_NORMALIZED_DIR, `${id}-normalized.wav`);
        await normalizeAudio(out, normalized, config);
        sttInput = normalized;
      }
      const transcript = await transcribeAudio(sttInput, config);
      return json(res, 200, {
        id,
        savedLocal: true,
        normalizedLocal: Boolean(normalized),
        sttMode: config.sttMode,
        transcript,
        duplex: buildFinalSttControllerSummary({ turnId: id, finalText: transcript }),
        maxAudioDurationSeconds: config.maxAudioDurationSeconds,
        boundaries: {
          browserWebSpeechApi: false,
          cloudSpeechApi: false
        }
      });
    }
    return json(res, 404, { error: 'not found' });
  } catch (e) {
    const { status, body } = publicError(e);
    return json(res, status, body);
  }
};

const server = http.createServer(requestHandler);

const listener = config.httpsEnabled
  ? https.createServer({
    key: await readFile(config.httpsKeyPath),
    cert: await readFile(config.httpsCertPath)
  }, requestHandler)
  : server;

listener.listen(config.port, config.host, () => {
  const protocol = config.httpsEnabled ? 'https' : 'http';
  console.log(`stickbot-tars-smoke listening on ${protocol}://${config.host}:${config.port}`);
});
