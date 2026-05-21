// Common Reasoner vMesh — native decision-policy service
// M25A: decision-only. No rendering, no tool execution, no memory writes.

const http = require('http');
const { buildDecision } = require('./src/decisionBuilder');
const { validateDecision } = require('./src/decisionSchema');
const { compareDecision } = require('./src/comparePolicy');
const { safetyGuard } = require('./src/safetyGuards');

const PORT = parseInt(process.env.PORT || '18860', 10);
const SERVICE_NAME = 'common-reasoner-vmesh';
const VERSION = 'common-reasoner-vmesh.m25a';

function json(res, code, body) {
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body) + '\n');
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (chunk) => { data += chunk; });
    req.on('end', () => {
      try { resolve(JSON.parse(data)); }
      catch (_) { resolve(null); }
    });
  });
}

// ── Health ──
function healthLive() {
  return { ok: true, service: SERVICE_NAME, version: VERSION, status: 'live' };
}

function healthReady() {
  return {
    ok: true, service: SERVICE_NAME, status: 'ready',
    mode: 'decision_only',
    rendering_allowed: false,
    tool_execution_allowed: false,
    memory_write_allowed: false,
    context_write_allowed: false
  };
}

function capabilities() {
  return {
    ok: true, service: SERVICE_NAME,
    mode: 'decision_only',
    intent_families: [
      'simple_chat', 'short_ambiguous_no_context', 'short_ambiguous_with_valid_context',
      'memory_lookup', 'context_bridge_read', 'runtime_status', 'debug_diagnostic',
      'tool_action', 'planning_request', 'unsafe_or_unsupported'
    ],
    obligation_classes: [
      'answer_only', 'clarify', 'memory_required', 'context_required',
      'runtime_tool_required', 'tool_required', 'high_reasoning_required', 'fail_closed'
    ],
    lane_classes: [
      'cheap_chat', 'continuity_capable', 'memory_capable', 'context_capable',
      'tool_capable', 'high_reasoning_tool', 'fail_closed'
    ],
    rendering_allowed: false,
    tool_execution_allowed: false,
    memory_write_allowed: false,
    context_write_allowed: false
  };
}

// ── Server ──
const server = http.createServer(async (req, res) => {
  const { method, url } = req;

  try {
    // GET endpoints
    if (method === 'GET') {
      if (url === '/health/live') return json(res, 200, healthLive());
      if (url === '/health/ready') return json(res, 200, healthReady());
      if (url === '/v1/capabilities') return json(res, 200, capabilities());
      if (url === '/v1/schema') {
        const schema = require('./schemas/common-reasoner-decision.v1.schema.json');
        return json(res, 200, { ok: true, schema });
      }
      if (url === '/v1/version') return json(res, 200, { ok: true, service: SERVICE_NAME, version: VERSION });
    }

    // POST endpoints
    if (method === 'POST') {
      const body = await readBody(req);
      if (!body) return json(res, 400, { ok: false, error: 'invalid_json' });

      if (url === '/v1/decide') {
        const decision = buildDecision(body);
        const valid = validateDecision(decision);
        const guarded = safetyGuard(decision);
        return json(res, 200, { ok: true, ...guarded });
      }

      if (url === '/v1/explain') {
        const decision = buildDecision(body);
        const valid = validateDecision(decision);
        const guarded = safetyGuard(decision);
        const explain = {
          ok: true,
          decision: guarded,
          policy_trace: guarded.trace || [],
          schema_valid: valid.ok,
          schema_version: 'common-reasoner-decision.v1'
        };
        return json(res, 200, explain);
      }

      if (url === '/v1/compare') {
        const result = compareDecision(body);
        return json(res, 200, result);
      }
    }

    json(res, 404, { ok: false, error: 'not_found' });
  } catch (e) {
    json(res, 500, { ok: false, error: 'internal_error', detail: e.message });
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`${SERVICE_NAME} ${VERSION} listening on 127.0.0.1:${PORT}`);
});
