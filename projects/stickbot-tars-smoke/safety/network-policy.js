const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '::1', '[::1]']);

export class NetworkPolicyError extends Error {
  constructor(classification, message) {
    super(message);
    this.name = 'NetworkPolicyError';
    this.classification = classification;
  }
}

export function boolEnv(value) {
  return String(value || '').toLowerCase() === 'true';
}

export function normalizeHost(host) {
  return String(host || '').trim().toLowerCase().replace(/^\[|\]$/g, '');
}

export function isLoopbackHost(host) {
  const h = normalizeHost(host);
  return h === 'localhost' || h === '::1' || /^127(?:\.\d{1,3}){3}$/.test(h);
}

export function isAnyAddress(host) {
  const h = normalizeHost(host);
  return h === '0.0.0.0' || h === '::' || h === '';
}

export function assertPortAllowed(port) {
  if (Number(port) === 8787) {
    throw new NetworkPolicyError('BLOCKED_RESERVED_PORT', 'Port 8787 is reserved for NOA and must not be used by Stickbot-TARS.');
  }
}

export function assertHostAllowed(host, { allowLan = false } = {}) {
  if (isAnyAddress(host) && !allowLan) {
    throw new NetworkPolicyError('BLOCKED_UNSAFE_CONFIG', 'HOST binds all interfaces; set VOICE_DEMO_ALLOW_LAN=true only for an explicitly approved LAN exposure.');
  }
  if (!isLoopbackHost(host) && !isAnyAddress(host) && !allowLan) {
    throw new NetworkPolicyError('BLOCKED_NON_LOOPBACK_HOST', `HOST ${host} is non-loopback; default Stickbot-TARS startup is loopback-only.`);
  }
}

export function urlHost(urlValue) {
  try {
    return new URL(urlValue).hostname;
  } catch {
    throw new NetworkPolicyError('BLOCKED_UNSAFE_CONFIG', `Invalid URL: ${urlValue}`);
  }
}

export function assertXttsUrlAllowed(xttsUrl, { allowRemoteXtts = false, allowLan = false } = {}) {
  const host = urlHost(xttsUrl);
  if (!isLoopbackHost(host) && !(allowRemoteXtts || allowLan)) {
    throw new NetworkPolicyError('BLOCKED_NON_LOOPBACK_XTTS', `XTTS_URL host ${host} is non-loopback; remote XTTS requires explicit approval.`);
  }
}

export function validateNetworkConfig({ host, port, xttsUrl, allowLan = false, allowRemoteXtts = false }) {
  assertPortAllowed(port);
  assertHostAllowed(host, { allowLan });
  assertXttsUrlAllowed(xttsUrl, { allowLan, allowRemoteXtts });
  return true;
}
