const log = document.getElementById('log');
const text = document.getElementById('text');
const voice = document.getElementById('voice');

let csrfToken = null;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c]));
}

function add(html) {
  const div = document.createElement('div');
  div.className = 'turn';
  div.innerHTML = html;
  log.prepend(div);
}

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

document.getElementById('send').onclick = async () => {
  const input = text.value.trim();
  if (!input) return;
  add(`<b>You:</b> ${escapeHtml(input)}<br><span class="muted">Sending...</span>`);
  const r = await fetch('/api/chat', {
    method: 'POST',
    credentials: 'same-origin',
    headers: await csrfHeaders({ 'content-type': 'application/json' }),
    body: JSON.stringify({ text: input, voice: voice.checked })
  });
  const j = await r.json();
  add(`<b>Stickbot:</b> ${escapeHtml(j.text || j.error)}${j.audioUrl ? `<audio controls autoplay src="${j.audioUrl}"></audio>` : ''}${j.audioError ? `<br><span class="muted">Voice: ${escapeHtml(j.audioError)}</span>` : ''}`);
};

let rec;
let chunks = [];
document.getElementById('mic').onclick = async () => {
  if (rec && rec.state === 'recording') {
    rec.stop();
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  chunks = [];
  rec = new MediaRecorder(stream, { mimeType: 'audio/webm' });
  rec.ondataavailable = (e) => chunks.push(e.data);
  rec.onstop = async () => {
    stream.getTracks().forEach((t) => t.stop());
    const blob = new Blob(chunks, { type: 'audio/webm' });
    const r = await fetch('/api/stt', {
      method: 'POST',
      credentials: 'same-origin',
      headers: await csrfHeaders({ 'content-type': 'audio/webm' }),
      body: blob
    });
    const j = await r.json();
    add(`<b>Mic capture:</b> saved locally<br><span class="muted">${escapeHtml(j.error || JSON.stringify(j))}</span>`);
  };
  rec.start();
  add('<b>Mic:</b> recording... click again to stop');
};

ensureSession().catch((e) => add(`<span class="muted">Session setup failed: ${escapeHtml(e.message)}</span>`));
