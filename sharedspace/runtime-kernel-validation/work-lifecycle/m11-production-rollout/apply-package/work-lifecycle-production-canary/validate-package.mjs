import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import plugin, {
  CANARY_MARKER,
  DEFAULT_CONFIG,
  evaluateBeforeAgentReplyCanary,
  validateConfig
} from './index.mjs';

const ROOT = new URL('.', import.meta.url);
const requiredFiles = ['package.json', 'openclaw.plugin.json', 'index.mjs', 'validate-package.mjs', 'post-apply-smoke.mjs', 'closeout-delivery-validation.mjs'];
const hashes = {};
for (const file of requiredFiles) {
  const bytes = await readFile(new URL(file, ROOT));
  hashes[file] = createHash('sha256').update(bytes).digest('hex');
  const text = bytes.toString('utf8');
  assert.equal(/(?<![A-Za-z0-9:_-])\d{10,12}(?![A-Za-z0-9:_-])/.test(text), false, `${file} contains raw Telegram-id-shaped numeric identifier`);
  const deniedSentinels = [
    ['bot', 'Token'].join(''),
    ['Authorization', ':', ' Bearer'].join(''),
    ['OPENAI', '_API', '_KEY'].join('')
  ];
  for (const denied of deniedSentinels) {
    assert.equal(text.includes(denied), false, `${file} contains denied secret sentinel ${denied}`);
  }
}

assert.equal(plugin.id, 'work-lifecycle-production-canary');
assert.equal(validateConfig(DEFAULT_CONFIG).ok, true);
assert.equal(evaluateBeforeAgentReplyCanary({ cleanedBody: CANARY_MARKER }, { trigger: 'user' }, { ...DEFAULT_CONFIG, enabled: true }).handled, false);
assert.equal(evaluateBeforeAgentReplyCanary({ cleanedBody: 'normal user turn' }, { trigger: 'user' }, { ...DEFAULT_CONFIG, enabled: true }).reason, 'WORK_LIFECYCLE_M11E_OUTSIDE_CANARY_MARKER_NOOP');
assert.equal(evaluateBeforeAgentReplyCanary({ cleanedBody: CANARY_MARKER }, { trigger: 'heartbeat' }, { ...DEFAULT_CONFIG, enabled: true }).reason, 'WORK_LIFECYCLE_M11E_HEARTBEAT_IGNORED');
assert.equal(validateConfig({ ...DEFAULT_CONFIG, productionPromotion: true }).ok, false);
assert.equal(validateConfig({ ...DEFAULT_CONFIG, allowRuntimeSend: true }).ok, false);
assert.equal(validateConfig({ ...DEFAULT_CONFIG, allowSyntheticReply: true }).ok, false);

console.log(JSON.stringify({ ok: true, marker: 'M11E_PACKAGE_VALIDATION_PASS', pluginId: plugin.id, canaryMarker: CANARY_MARKER, hashes }, null, 2));
