const log = document.getElementById('log');
const text = document.getElementById('text');
const voice = document.getElementById('voice');
const mic = document.getElementById('mic');
const voiceStatus = document.getElementById('voice-status');
const prosodyParameters = document.getElementById('prosody-parameters');
const prosodyRandomness = document.getElementById('prosody-randomness');
const prosodyMatrixXtts = document.getElementById('prosody-matrix-xtts');
const prosodyMatrixDelivery = document.getElementById('prosody-matrix-delivery');
const prosodyStatus = document.getElementById('prosody-status');
const prosodyMood = document.getElementById('prosody-mood');
const prosodyJsonFile = document.getElementById('prosody-json-file');
const prosodyJsonPreview = document.getElementById('prosody-json-preview');

let csrfToken = null;
let voiceAvailable = false;
let prosodyState = null;
let activePlayback = null;

const PARAMETER_LABELS = {
  pitch: 'Pitch',
  timbre: 'Timbre',
  speed: 'Speed',
  compression: 'Compression',
  verbalGait: 'Verbal gait',
  verbosity: 'Verbosity',
  clip: 'Clip guard'
};

const RANDOMNESS_LABELS = {
  global: 'Randomness',
  threshold: 'Random threshold',
  pitch: 'Pitch random',
  timbre: 'Timbre random',
  speed: 'Speed random',
  compression: 'Compression random',
  verbalGait: 'Gait random',
  verbosity: 'Verbosity random',
  clip: 'Clip random'
};

const XTTS_LABELS = {
  temperature: 'Temperature',
  topP: 'Top P',
  topK: 'Top K',
  repetitionPenalty: 'Repeat penalty',
  lengthPenalty: 'Length penalty',
  speed: 'XTTS speed'
};

const XTTS_RANGES = {
  temperature: [0.55, 0.9, 0.01],
  topP: [0.75, 0.95, 0.01],
  topK: [35, 80, 1],
  repetitionPenalty: [8, 12, 0.1],
  lengthPenalty: [0.9, 1.15, 0.01],
  speed: [0.88, 1.12, 0.01]
};

const DELIVERY_LABELS = {
  maxCharsPerChunk: 'Max chars',
  sentencePauseMs: 'Sentence pause',
  commaPauseMs: 'Comma pause',
  lineBreakPauseMs: 'Line pause'
};

const DELIVERY_RANGES = {
  maxCharsPerChunk: [60, 230, 1],
  sentencePauseMs: [50, 500, 10],
  commaPauseMs: [50, 500, 10],
  lineBreakPauseMs: [50, 500, 10]
};

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c]));
}

function safeFilename(s, fallback = 'stickbot-tars-prosody-sample') {
  const safe = String(s || fallback)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 96);
  return safe || fallback;
}

function voiceProfileName(voicePlan = {}) {
  return safeFilename(
    voicePlan?.delivery?.moodId
      || voicePlan?.tuning?.moodId
      || voicePlan?.prosodySheet?.[0]?.moodId
      || 'stickbot-tars-prosody-sample'
  );
}

function voiceSaveHtml(j) {
  if (!j.audioUrl || !j.voicePlan) return '';
  const profileName = voiceProfileName(j.voicePlan);
  const payload = {
    profileName,
    text: j.text || '',
    audioUrl: j.audioUrl,
    voicePlan: j.voicePlan,
    boundaries: {
      canonicalTextAuthoritative: true,
      textRewriteAllowed: false,
      localOnly: true
    }
  };
  const encoded = encodeURIComponent(JSON.stringify(payload));
  return `<div class="voice-save-row"><a class="button-link" href="${escapeHtml(j.audioUrl)}" download="${escapeHtml(profileName)}.wav">Save WAV</a><button class="secondary save-prosody-json" type="button" data-profile="${escapeHtml(profileName)}" data-json="${encoded}">Save prosody JSON</button></div>`;
}

function downloadJson(filename, payload) {
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function add(html) {
  const div = document.createElement('div');
  div.className = 'turn';
  div.innerHTML = html;
  log.prepend(div);
  return div;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, Number(ms || 0))));
}

function nowMs() {
  return globalThis.performance?.now ? performance.now() : Date.now();
}

function roundMs(value) {
  return Math.round(Number(value || 0));
}

function chunkAudioUrlFromFrame(frame) {
  const name = frame?.payload?.mastering?.outputFileBasename || frame?.payload?.dsp?.outputFileBasename || frame?.payload?.fileBasename;
  return name ? `/audio/${encodeURIComponent(name)}` : null;
}

function waitForAudioCanPlay(audio, timeoutMs = 1200) {
  if (!audio) return Promise.resolve(false);
  if (audio.readyState >= 3) return Promise.resolve(true);
  return new Promise((resolve) => {
    let done = false;
    const finish = (ok) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      audio.removeEventListener('canplay', onReady);
      audio.removeEventListener('canplaythrough', onReady);
      audio.removeEventListener('error', onError);
      resolve(ok);
    };
    const onReady = () => finish(true);
    const onError = () => finish(false);
    const timer = setTimeout(() => finish(false), Math.max(50, Number(timeoutMs || 1200)));
    audio.addEventListener('canplay', onReady, { once: true });
    audio.addEventListener('canplaythrough', onReady, { once: true });
    audio.addEventListener('error', onError, { once: true });
    try { audio.load(); }
    catch (_) { finish(false); }
  });
}

function buildTransportQueue(audioFrames, turnId, transport = {}) {
  const queueStartedAt = nowMs();
  const entries = audioFrames.map((frame, index) => {
    const audio = new Audio(chunkAudioUrlFromFrame(frame));
    audio.preload = index < (transport.queueDepthTarget || 2) ? 'auto' : 'metadata';
    audio.controls = true;
    audio.autoplay = false;
    audio.dataset.turnId = turnId || '';
    registerPlaybackAudio(audio, turnId, { removeSourceOnStop: true });
    return {
      frame,
      audio,
      index,
      queuedAt: nowMs(),
      canPlayAt: null,
      playStartedAt: null,
      endedAt: null
    };
  });
  return { queueStartedAt, entries };
}

function summarizeTransportTelemetry({ telemetry, transport }) {
  const first = telemetry.entries.find((entry) => entry.playStartedAt);
  const played = telemetry.entries.filter((entry) => entry.playStartedAt);
  const gaps = [];
  for (let i = 1; i < telemetry.entries.length; i++) {
    const prev = telemetry.entries[i - 1];
    const current = telemetry.entries[i];
    if (prev.endedAt && current.playStartedAt) gaps.push(Math.max(0, current.playStartedAt - prev.endedAt));
  }
  return {
    schema: 'stickbot.tars.client-stream-telemetry.v1',
    classification: 'STICKBOT_TARS_M7R_LOW_LATENCY_CLIENT_TELEMETRY',
    queueBuiltMs: roundMs((telemetry.queueBuiltAt || telemetry.queueStartedAt) - telemetry.queueStartedAt),
    firstFrameCanPlayMs: telemetry.firstFrameCanPlayAt ? roundMs(telemetry.firstFrameCanPlayAt - telemetry.queueStartedAt) : null,
    firstAudioPlayMs: first ? roundMs(first.playStartedAt - telemetry.queueStartedAt) : null,
    maxInterChunkGapMs: gaps.length ? roundMs(Math.max(...gaps)) : 0,
    playedFrameCount: played.length,
    cancelled: Boolean(telemetry.cancelled),
    target: {
      firstAudioTargetMs: transport.firstAudioTargetMs || 1200,
      interChunkGapTargetMs: transport.interChunkGapTargetMs || 120
    },
    boundaries: {
      localOnly: true,
      rawTranscriptDurableStorage: false,
      browserWebSpeechApi: false,
      cloudSpeechApi: false,
      textRewriteAllowed: false
    }
  };
}

function stopAudioElement(audio, { removeSource = false } = {}) {
  if (!audio) return;
  audio.pause();
  if (removeSource) {
    audio.removeAttribute('src');
    audio.load();
    return;
  }
  try { audio.currentTime = 0; }
  catch (_) { /* Some browsers reject currentTime before metadata; pause is enough. */ }
}

function registerPlaybackAudio(audio, turnId, { removeSourceOnStop = false } = {}) {
  if (!audio) return;
  const markActive = () => {
    if (activePlayback?.audio && activePlayback.audio !== audio) {
      activePlayback.cancelled = true;
      stopAudioElement(activePlayback.audio, { removeSource: Boolean(activePlayback.removeSourceOnStop) });
    }
    activePlayback = { turnId, cancelled: false, audio, removeSourceOnStop };
  };
  audio.addEventListener('play', markActive);
  audio.addEventListener('ended', () => {
    if (activePlayback?.audio === audio) activePlayback = null;
  });
  audio.addEventListener('pause', () => {
    if (activePlayback?.audio === audio && !activePlayback.cancelled) activePlayback = null;
  });
  if (!audio.paused && !audio.ended) markActive();
}

function stopActivePlayback(reason = 'stopped') {
  let stopped = activePlayback;
  if (activePlayback) {
    activePlayback.cancelled = true;
    stopAudioElement(activePlayback.audio, { removeSource: Boolean(activePlayback.removeSourceOnStop) });
    activePlayback = null;
  } else {
    const playingAudio = Array.from(document.querySelectorAll('audio')).filter((audio) => !audio.paused && !audio.ended);
    playingAudio.forEach((audio) => stopAudioElement(audio));
    if (playingAudio.length) stopped = { turnId: playingAudio[0].dataset.turnId || null, audio: playingAudio[0], fallbackScan: true };
  }
  if (!stopped) return false;
  add(`<b>Playback:</b> stopped<br><span class="muted">${escapeHtml(reason)}</span>`);
  return stopped;
}

async function postBargeInSmoke(turnId) {
  try {
    const { r, j } = await csrfFetchJson('/api/duplex/scenario', {
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        turnId,
        events: [
          { type: 'listen_start' },
          { type: 'final_transcript', payload: { textSha256: '0'.repeat(64), charCount: 0 } },
          { type: 'assistant_text_ready', payload: { canonicalTextSha256: '0'.repeat(64) } },
          { type: 'audio_frame_ready', payload: { seq: 1, frameType: 'audio_chunk_ready' } },
          { type: 'barge_in', payload: { reason: 'mic_capture_started' } },
          { type: 'resume_listening' }
        ]
      })
    });
    if (r.ok) add(`<b>Duplex:</b> barge-in smoke ${escapeHtml(j.state || 'ok')}<br><span class="muted">Privacy guard: raw mic transcript is not durably stored (${escapeHtml(j.boundaries?.rawTranscriptDurableStorage === false ? 'off' : 'check')}).</span>`);
  } catch (e) {
    add(`<b>Duplex:</b> barge-in smoke failed<br><span class="muted">${escapeHtml(e.message)}</span>`);
  }
}

async function playRealtimeFrames(j, container) {
  const manifest = j.voicePlan?.audioPerformance?.realtime;
  const frames = manifest?.frames || [];
  const transport = manifest?.transport || {};
  const audioFrames = frames.filter((frame) => frame.type === 'audio_chunk_ready' && chunkAudioUrlFromFrame(frame));
  if (!audioFrames.length) return false;
  const queue = buildTransportQueue(audioFrames, j.id, transport);
  const playback = { turnId: j.id, cancelled: false, audio: queue.entries[0]?.audio, removeSourceOnStop: true };
  activePlayback = playback;
  queue.queueBuiltAt = nowMs();
  if (queue.entries[0]) container.appendChild(queue.entries[0].audio);
  add(`<b>Streaming transport:</b> ${escapeHtml(audioFrames.length)} chunk frames preloaded<br><span class="muted">M7R ${escapeHtml(transport.mode || 'browser_preload_queue_then_serial_playback')}; target first audio ${escapeHtml(transport.firstAudioTargetMs || 1200)}ms; final WAV remains fallback.</span>`);
  const firstReady = queue.entries[0] ? await waitForAudioCanPlay(queue.entries[0].audio, transport.preloadTimeoutMs || 1200) : false;
  if (firstReady) queue.firstFrameCanPlayAt = nowMs();
  for (const entry of queue.entries) {
    if (playback.cancelled) break;
    playback.audio = entry.audio;
    if (!entry.audio.parentElement) container.appendChild(entry.audio);
    const next = queue.entries[entry.index + 1];
    if (next) waitForAudioCanPlay(next.audio, transport.preloadTimeoutMs || 1200).then((ok) => { if (ok && !next.canPlayAt) next.canPlayAt = nowMs(); });
    try { await playback.audio.play(); }
    catch (e) {
      add(`<b>Streaming:</b> browser blocked autoplay<br><span class="muted">Use audio controls or click Send again after user activation. ${escapeHtml(e.message)}</span>`);
      break;
    }
    entry.playStartedAt = nowMs();
    await new Promise((resolve) => {
      playback.audio.onended = resolve;
      playback.audio.onerror = resolve;
    });
    entry.endedAt = nowMs();
    if (playback.cancelled) break;
    await sleep(entry.frame.timing?.pauseAfterMs || 0);
  }
  queue.cancelled = playback.cancelled;
  if (activePlayback === playback) activePlayback = null;
  const summary = summarizeTransportTelemetry({ telemetry: queue, transport });
  add(`<b>Streaming telemetry:</b> first play ${escapeHtml(summary.firstAudioPlayMs ?? 'n/a')}ms; max gap ${escapeHtml(summary.maxInterChunkGapMs)}ms; played ${escapeHtml(summary.playedFrameCount)}/${escapeHtml(audioFrames.length)}<br><span class="muted">${escapeHtml(summary.classification)}; local-only, no transcript/audio cloud path.</span>`);
  return true;
}

log.addEventListener('click', (event) => {
  const button = event.target.closest('.save-prosody-json');
  if (!button) return;
  try {
    const profile = safeFilename(button.dataset.profile || 'stickbot-tars-prosody-sample');
    const payload = JSON.parse(decodeURIComponent(button.dataset.json || '{}'));
    downloadJson(`${profile}.json`, payload);
  } catch (e) {
    add(`<b>Save:</b> prosody JSON failed<br><span class="muted">${escapeHtml(e.message)}</span>`);
  }
});

async function ensureSession() {
  if (csrfToken) return csrfToken;
  const r = await fetch('/api/session', { method: 'GET', credentials: 'same-origin' });
  const j = await r.json();
  csrfToken = j.csrfToken;
  return csrfToken;
}

async function csrfHeaders(extra = {}) {
  return { ...extra, 'x-csrf-token': await ensureSession() };
}

async function readJsonResponse(r) {
  return r.json().catch(() => ({ error: `HTTP ${r.status}` }));
}

function isCsrfRejected(j, r) {
  return r.status === 403 && (j.classification === 'CSRF_REJECTED' || /csrf/i.test(j.error || ''));
}

async function csrfFetchJson(path, { headers = {}, body = '{}', method = 'POST' } = {}, retry = true) {
  const r = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: await csrfHeaders(headers),
    body
  });
  const j = await readJsonResponse(r);
  if (!r.ok && retry && isCsrfRejected(j, r)) {
    csrfToken = null;
    await ensureSession();
    return csrfFetchJson(path, { headers, body, method }, false);
  }
  return { r, j };
}

async function refreshCapabilities() {
  try {
    const r = await fetch('/api/capabilities', { method: 'GET', credentials: 'same-origin' });
    const j = await r.json();
    voiceAvailable = Boolean(j.voice?.enabled);
    voice.disabled = !voiceAvailable;
    if (!voiceAvailable) voice.checked = false;
    voiceStatus.textContent = voiceAvailable
      ? '(local XTTS backend ready)'
      : '(local XTTS backend not running; text/echo only)';
  } catch (e) {
    voiceAvailable = false;
    voice.checked = false;
    voice.disabled = true;
    voiceStatus.textContent = '(voice status unavailable; text/echo only)';
  }
}

function sliderHtml(kind, key, value, label) {
  const id = `prosody-${kind}-${key}`;
  const safeValue = Number(value || 0).toFixed(2);
  return `<label class="slider-row" for="${id}"><span>${escapeHtml(label)}</span><input id="${id}" data-kind="${kind}" data-key="${key}" type="range" min="0" max="1" step="0.01" value="${safeValue}"><output>${safeValue}</output></label>`;
}

function rangedSliderHtml(kind, key, value, label, range) {
  const id = `prosody-${kind}-${key}`;
  const [min, max, step] = range;
  const decimals = String(step).includes('.') ? 2 : 0;
  const safe = Number.isFinite(Number(value)) ? Number(value) : min;
  const safeValue = Math.min(max, Math.max(min, safe));
  return `<label class="slider-row" for="${id}"><span>${escapeHtml(label)}</span><input id="${id}" data-matrix-kind="${kind}" data-key="${key}" type="range" min="${min}" max="${max}" step="${step}" value="${safeValue}"><output>${safeValue.toFixed(decimals)}</output></label>`;
}

function bindSliderOutputs(root) {
  root.querySelectorAll('input[type="range"]').forEach((input) => {
    const out = input.parentElement.querySelector('output');
    input.addEventListener('input', () => {
      const step = input.getAttribute('step') || '0.01';
      out.textContent = Number(input.value).toFixed(step.includes('.') ? 2 : 0);
    });
  });
}

function moodPreset(id) {
  return (prosodyState?.matrix?.moods || []).find((mood) => mood.id === id) || null;
}

function renderMatrixControls(matrix) {
  const m = matrix || {};
  prosodyMatrixXtts.innerHTML = Object.entries(XTTS_LABELS)
    .map(([key, label]) => rangedSliderHtml('xttsParams', key, m.xttsParams?.[key] ?? m.recommendedXttsParams?.[key], label, XTTS_RANGES[key]))
    .join('');
  prosodyMatrixDelivery.innerHTML = Object.entries(DELIVERY_LABELS)
    .map(([key, label]) => rangedSliderHtml('delivery', key, m.delivery?.[key] ?? m.recommendedDelivery?.[key], label, DELIVERY_RANGES[key]))
    .join('');
  bindSliderOutputs(prosodyMatrixXtts);
  bindSliderOutputs(prosodyMatrixDelivery);
}

function matrixFromMoodPreset(id) {
  const mood = moodPreset(id);
  if (!mood) return null;
  return {
    moodId: mood.id,
    label: mood.label,
    expressionToken: mood.expressionToken,
    xttsParams: mood.xttsParams,
    recommendedXttsParams: mood.xttsParams,
    delivery: mood.delivery,
    recommendedDelivery: mood.delivery
  };
}

function renderProsody(state) {
  prosodyState = state;
  const active = state.active || { parameters: {}, randomness: {} };
  const moods = state.controls?.moodPresets || [];
  prosodyMood.innerHTML = moods
    .map((mood) => `<option value="${escapeHtml(mood.id)}" title="${escapeHtml(mood.purpose || '')}"${mood.id === active.moodId ? ' selected' : ''}>${escapeHtml(`${mood.expressionToken || '🎚️'} ${mood.label}`)}</option>`)
    .join('');
  prosodyParameters.innerHTML = Object.entries(PARAMETER_LABELS)
    .map(([key, label]) => sliderHtml('parameters', key, active.parameters[key], label))
    .join('');
  prosodyRandomness.innerHTML = Object.entries(RANDOMNESS_LABELS)
    .map(([key, label]) => sliderHtml('randomness', key, active.randomness[key], label))
    .join('');
  renderMatrixControls(active.matrix || matrixFromMoodPreset(active.moodId));
  bindSliderOutputs(prosodyParameters);
  bindSliderOutputs(prosodyRandomness);
  const updated = active.updatedAt ? ` Updated ${escapeHtml(active.updatedAt)}.` : '';
  const mood = active.matrix?.label || active.moodId || 'baseline_deadpan';
  prosodyStatus.textContent = `Active: ${active.label || 'Active tuning'} / ${mood}.${updated} Canonical text remains authoritative.`;
}

function collectProsody() {
  const body = { moodId: prosodyMood.value || 'baseline_deadpan', parameters: {}, randomness: {}, matrix: { xttsParams: {}, delivery: {} } };
  document.querySelectorAll('[data-kind][data-key]').forEach((input) => {
    body[input.dataset.kind][input.dataset.key] = Number(input.value);
  });
  document.querySelectorAll('[data-matrix-kind][data-key]').forEach((input) => {
    body.matrix[input.dataset.matrixKind][input.dataset.key] = Number(input.value);
  });
  body.matrix.moodId = body.moodId;
  return body;
}

prosodyMood.onchange = () => {
  const matrix = matrixFromMoodPreset(prosodyMood.value);
  if (!matrix) return;
  renderMatrixControls(matrix);
  prosodyStatus.textContent = `Loaded JSON values for ${matrix.expressionToken || '🎚️'} ${matrix.label}. Hit Apply tuning to persist.`;
};

async function postProsody(path, body = {}) {
  const { r, j } = await csrfFetchJson(path, {
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(j.error || `prosody ${r.status}`);
  renderProsody(j);
  return j;
}

async function refreshProsody() {
  try {
    const r = await fetch('/api/prosody', { method: 'GET', credentials: 'same-origin' });
    const j = await r.json();
    renderProsody(j);
  } catch (e) {
    prosodyStatus.textContent = `Prosody unavailable: ${e.message}`;
  }
}

async function refreshProsodyMatrixPreview() {
  const r = await fetch('/api/prosody/matrix', { method: 'GET', credentials: 'same-origin' });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || `matrix ${r.status}`);
  prosodyJsonPreview.textContent = JSON.stringify(j, null, 2);
  prosodyStatus.textContent = `Active JSON matrix: ${j.source || 'default'} / ${j.moods?.length || 0} moods. Canonical text remains authoritative.`;
  return j;
}

document.getElementById('prosody-save').onclick = async () => {
  try {
    prosodyStatus.textContent = 'Applying tuning...';
    await postProsody('/api/prosody', collectProsody());
  } catch (e) { prosodyStatus.textContent = `Apply failed: ${e.message}`; }
};

document.getElementById('prosody-baseline').onclick = async () => {
  try {
    prosodyStatus.textContent = 'Saving current tuning as baseline...';
    await postProsody('/api/prosody', collectProsody());
    await postProsody('/api/prosody/baseline');
  } catch (e) { prosodyStatus.textContent = `Baseline failed: ${e.message}`; }
};

document.getElementById('prosody-restore').onclick = async () => {
  try {
    prosodyStatus.textContent = 'Restoring baseline...';
    await postProsody('/api/prosody/restore-baseline');
  } catch (e) { prosodyStatus.textContent = `Restore failed: ${e.message}`; }
};

document.getElementById('prosody-reset').onclick = async () => {
  try {
    prosodyStatus.textContent = 'Resetting to factory default...';
    await postProsody('/api/prosody/reset');
  } catch (e) { prosodyStatus.textContent = `Reset failed: ${e.message}`; }
};

document.getElementById('prosody-json-read').onclick = async () => {
  try {
    prosodyStatus.textContent = 'Reading active prosody JSON...';
    await refreshProsodyMatrixPreview();
  } catch (e) { prosodyStatus.textContent = `Read failed: ${e.message}`; }
};

document.getElementById('prosody-json-upload').onclick = async () => {
  try {
    if (!prosodyJsonFile.files.length) throw new Error('choose a JSON file first');
    prosodyStatus.textContent = 'Uploading prosody JSON...';
    const matrix = JSON.parse(await prosodyJsonFile.files[0].text());
    const { r, j } = await csrfFetchJson('/api/prosody/matrix', {
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ matrix })
    });
    if (!r.ok) throw new Error(j.error || `matrix upload ${r.status}`);
    prosodyJsonPreview.textContent = JSON.stringify(j.matrix, null, 2);
    renderProsody(j.prosody);
    prosodyStatus.textContent = `Uploaded sanitized local matrix: ${j.matrix.moods?.length || 0} moods. Text rewrite still blocked.`;
  } catch (e) { prosodyStatus.textContent = `Upload failed: ${e.message}`; }
};

document.getElementById('prosody-json-reset').onclick = async () => {
  try {
    prosodyStatus.textContent = 'Resetting prosody JSON to built-in default...';
    const { r, j } = await csrfFetchJson('/api/prosody/matrix/reset', {
      headers: { 'content-type': 'application/json' },
      body: '{}'
    });
    if (!r.ok) throw new Error(j.error || `matrix reset ${r.status}`);
    prosodyJsonPreview.textContent = JSON.stringify(j.matrix, null, 2);
    renderProsody(j.prosody);
    prosodyStatus.textContent = 'Prosody JSON reset to built-in default.';
  } catch (e) { prosodyStatus.textContent = `Reset JSON failed: ${e.message}`; }
};

document.getElementById('send').onclick = async () => {
  const input = text.value.trim();
  if (!input) return;
  add(`<b>You:</b> ${escapeHtml(input)}<br><span class="muted">Sending...</span>`);
  const { r, j } = await csrfFetchJson('/api/chat', {
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text: input, voice: voiceAvailable && voice.checked })
  });
  if (!r.ok) {
    add(`<b>Stickbot:</b> request failed<br><span class="muted">${escapeHtml(j.error || `HTTP ${r.status}`)}</span>`);
    return;
  }
  const selectedScoreChunk = j.voicePlan?.prosodyScore?.chunks?.[0] || j.voicePlan?.prosodySheet?.[0] || null;
  const realtimeFrames = j.voicePlan?.audioPerformance?.realtime?.frames || [];
  const hasStreamingFrames = realtimeFrames.some((frame) => frame.type === 'audio_chunk_ready' && chunkAudioUrlFromFrame(frame));
  const voicePlan = j.voicePlan?.delivery
    ? `<br><span class="muted">Voice score: mood ${escapeHtml(j.voicePlan.delivery.moodLabel || j.voicePlan.delivery.moodId || 'n/a')}, base temp ${escapeHtml(j.voicePlan.delivery.baseXttsParams?.temperature ?? 'n/a')}, effective temp ${escapeHtml(j.voicePlan.delivery.xttsParams?.temperature ?? 'n/a')}, top_p ${escapeHtml(j.voicePlan.delivery.xttsParams?.topP ?? 'n/a')}, XTTS speed ${escapeHtml(j.voicePlan.delivery.xttsParams?.speed ?? 'n/a')}, chunk ${escapeHtml(j.voicePlan.delivery.maxCharsPerChunk || 'n/a')}</span>${selectedScoreChunk ? `<br><span class="muted">Selected chunk: ${escapeHtml(selectedScoreChunk.chunkId || 'c001')} role ${escapeHtml(selectedScoreChunk.phraseRole || 'n/a')}; Δ ${escapeHtml(JSON.stringify(selectedScoreChunk.deltas || {}))}; effective ${escapeHtml(JSON.stringify(selectedScoreChunk.effectiveXtts || selectedScoreChunk.xttsParams || {}))}</span>` : ''}${hasStreamingFrames ? `<br><span class="muted">Streaming frames: ${escapeHtml(realtimeFrames.length)} / target ${escapeHtml(j.voicePlan.audioPerformance?.realtime?.target || 'streaming_full_duplex_mesh')}</span>` : ''}`
    : '';
  const turn = add(`<b>Stickbot:</b> ${escapeHtml(j.text || j.error)}${j.audioUrl ? `<audio controls data-turn-id="${escapeHtml(j.id || '')}" ${hasStreamingFrames ? '' : 'autoplay'} src="${j.audioUrl}"></audio>${voiceSaveHtml(j)}` : ''}${j.audioError ? `<br><span class="muted">Voice: ${escapeHtml(j.audioError)}</span>` : ''}${voicePlan}`);
  turn.querySelectorAll('audio[src]').forEach((audio) => registerPlaybackAudio(audio, j.id, { removeSourceOnStop: false }));
  if (hasStreamingFrames) playRealtimeFrames(j, turn).catch((e) => add(`<b>Streaming:</b> failed<br><span class="muted">${escapeHtml(e.message)}</span>`));
};

let rec;
let chunks = [];
let micTurnId = null;
let partialSeq = 0;
let stoppingMic = false;
let partialQueue = Promise.resolve();

function newClientTurnId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `turn-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function queuePartialAudio(blob, turnId, seq) {
  if (!blob?.size || !turnId) return;
  partialQueue = partialQueue.then(async () => {
    const { r, j } = await csrfFetchJson(`/api/stt/partial-audio?turnId=${encodeURIComponent(turnId)}&seq=${encodeURIComponent(seq)}`, {
      headers: { 'content-type': blob.type || 'audio/webm' },
      body: blob
    });
    if (r.status === 501) {
      add(`<b>Partial STT:</b> capture-only<br><span class="muted">${escapeHtml(j.error || 'local STT not configured')}; no cloud speech API used.</span>`);
      return;
    }
    if (!r.ok) throw new Error(j.error || `partial STT ${r.status}`);
    if (j.partialTranscript) {
      add(`<b>Partial STT:</b> ${escapeHtml(j.partialTranscript)}<br><span class="muted">seq ${escapeHtml(j.seq)}; local whisper slice; privacy guard: raw transcript durable storage is ${escapeHtml(j.boundaries?.rawTranscriptDurableStorage === false ? 'off' : 'check')}.</span>`);
    } else {
      add(`<b>Partial STT:</b> listening…<br><span class="muted">seq ${escapeHtml(j.seq)}; ${escapeHtml(j.error || 'no transcript yet')}; local-only.</span>`);
    }
  }).catch((e) => add(`<b>Partial STT:</b> failed<br><span class="muted">${escapeHtml(e.message)}</span>`));
}

mic.onclick = async () => {
  if (rec && rec.state === 'recording') {
    mic.textContent = 'Processing mic capture...';
    mic.disabled = true;
    stoppingMic = true;
    rec.stop();
    return;
  }
  const stoppedPlayback = stopActivePlayback('M7O barge-in: mic capture started');
  if (stoppedPlayback?.turnId) postBargeInSmoke(stoppedPlayback.turnId).catch(() => {});
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    add(`<b>Mic:</b> unavailable<br><span class="muted">${escapeHtml(e.message || String(e))}. If this is a LAN URL, browser secure-origin policy may block microphone permission over plain HTTP; use localhost or HTTPS.</span>`);
    return;
  }
  chunks = [];
  micTurnId = newClientTurnId();
  partialSeq = 0;
  stoppingMic = false;
  partialQueue = Promise.resolve();
  rec = new MediaRecorder(stream, { mimeType: 'audio/webm' });
  rec.ondataavailable = (e) => {
    if (!e.data?.size) return;
    chunks.push(e.data);
    if (!stoppingMic) queuePartialAudio(new Blob(chunks, { type: e.data.type || 'audio/webm' }), micTurnId, partialSeq++);
  };
  rec.onstop = async () => {
    try {
      stream.getTracks().forEach((t) => t.stop());
      await partialQueue.catch(() => {});
      const blob = new Blob(chunks, { type: 'audio/webm' });
      const { r, j } = await csrfFetchJson('/api/stt', {
        headers: { 'content-type': 'audio/webm' },
        body: blob
      });
      if (j.transcript) {
        text.value = j.transcript;
        add(`<b>Mic transcript:</b> ${escapeHtml(j.transcript)}<br><span class="muted">Saved locally; click Send text to ask Stickbot. Duplex state: ${escapeHtml(j.duplex?.state || 'n/a')}; privacy guard: raw mic transcript durable storage is ${escapeHtml(j.duplex?.boundaries?.rawTranscriptDurableStorage === false ? 'off' : 'check')}.</span>`);
      } else {
        add(`<b>Mic capture:</b> saved locally<br><span class="muted">${escapeHtml(j.error || JSON.stringify(j))}</span>`);
      }
    } finally {
      micTurnId = null;
      stoppingMic = false;
      mic.textContent = 'Start mic capture';
      mic.disabled = false;
    }
  };
  rec.start(2500);
  mic.textContent = 'Recording… tap to stop/send';
  add('<b>Mic:</b> recording with local partial STT slices… tap the mic button again to stop and transcribe');
};

ensureSession().catch((e) => add(`<span class="muted">Session setup failed: ${escapeHtml(e.message)}</span>`));
refreshCapabilities().catch(() => {});
refreshProsody().catch(() => {});
