import { isLoopbackHost } from './network-policy.js';

export class OriginPolicyError extends Error {
  constructor(message) {
    super(message);
    this.name = 'OriginPolicyError';
    this.statusCode = 403;
    this.publicMessage = 'origin rejected';
    this.classification = 'ORIGIN_REJECTED';
  }
}

function normalizePort(protocol, port) {
  if (port) return Number(port);
  return protocol === 'https:' ? 443 : 80;
}

export function isAllowedLoopbackOrigin(origin, { port }) {
  let u;
  try { u = new URL(origin); } catch { return false; }
  if (!['http:', 'https:'].includes(u.protocol)) return false;
  if (!isLoopbackHost(u.hostname)) return false;
  return normalizePort(u.protocol, u.port) === Number(port);
}

function hostHeaderHostname(req) {
  const host = req.headers?.host;
  if (!host) return null;
  try {
    return new URL(`http://${host}`).hostname.toLowerCase();
  } catch {
    return null;
  }
}

export function isAllowedLanOrigin(origin, req, { port, allowLan = false }) {
  if (!allowLan) return false;
  let u;
  try { u = new URL(origin); } catch { return false; }
  if (!['http:', 'https:'].includes(u.protocol)) return false;
  if (normalizePort(u.protocol, u.port) !== Number(port)) return false;
  const requestHost = hostHeaderHostname(req);
  if (!requestHost) return false;
  return u.hostname.toLowerCase() === requestHost;
}

export function assertPostOriginAllowed(req, config) {
  if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method || '')) return true;
  const origin = req.headers?.origin;
  // Local CLI/no-Origin allowance: requests without Origin still require CSRF for mutating browser/API routes.
  if (!origin) return true;
  if (!isAllowedLoopbackOrigin(origin, { port: config.port }) && !isAllowedLanOrigin(origin, req, config)) {
    throw new OriginPolicyError(`Unexpected Origin: ${origin}`);
  }
  return true;
}
