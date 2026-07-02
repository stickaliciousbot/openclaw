import http from 'node:http';
import { mkdir, readFile, writeFile, appendFile } from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { loadConfig } from './src/config.js';
import { askOpenClaw } from './src/openclaw-adapter.js';
import { transcribeAudio } from './src/stt-adapter.js';
import { resolveAudioOutputPath, audioUrlForFile } from './safety/audio-path-policy.js';
import { readJsonBody, readAudioUploadBody, assertTextWithinLimit } from './safety/limits.js';
import { assertPostOriginAllowed } from './safety/origin-policy.js';
import { createSessionStore, createCsrfSession, assertCsrf } from './safety/csrf.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const config = loadConfig();
const csrfStore = createSessionStore();
const AUDIO_INPUT_DIR = path.join(__dirname, 'data', 'audio', 'input');
const AUDIO_OUTPUT_DIR = path.join(__dirname, 'data', 'audio', 'output');

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

async function synthesize(text, id) {
  const r = await fetch(`${config.xttsUrl.replace(/\/$/, '')}/tts_to_audio/`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text, speaker_wav: config.xttsSpeaker, language: config.xttsLanguage })
  });
  if (!r.ok) throw new Error(`XTTS ${r.status}: ${await r.text()}`);
  const wav = Buffer.from(await r.arrayBuffer());
  await mkdir(AUDIO_OUTPUT_DIR, { recursive: true });
  const out = path.join(AUDIO_OUTPUT_DIR, `${id}.wav`);
  await writeFile(out, wav);
  return { file: out, url: audioUrlForFile(path.basename(out)) };
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
  res.writeHead(200, { 'content-type': type });
  res.end(data);
}

function guardMutatingRequest(req) {
  assertPostOriginAllowed(req, config);
  assertCsrf(req, csrfStore);
}

const server = http.createServer(async (req, res) => {
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
        openclawMode: config.openclawMode,
        xttsUrl: config.xttsUrl,
        host: config.host,
        port: config.port,
        maxAudioDurationSeconds: config.maxAudioDurationSeconds
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
        catch (e) { audio = { error: e.message }; }
      }
      const logs = await logTurn({ id, userText: text, assistantText, audioPath: audio?.file, source: 'stickbot-tars-smoke:text' });
      return json(res, 200, { id, text: assistantText, audioUrl: audio?.url || null, audioError: audio?.error || null, logs });
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
      const transcript = await transcribeAudio(out, config);
      return json(res, 200, {
        id,
        savedLocal: true,
        sttMode: config.sttMode,
        transcript,
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
});

server.listen(config.port, config.host, () => {
  console.log(`stickbot-tars-smoke listening on http://${config.host}:${config.port}`);
});
