// Trace writer — records decision traces for audit and turn contract integration.
// Writes local trace only; does NOT mutate context bridge or memory.
// Deterministic. No LLM.

const fs = require('fs');
const path = require('path');

const TRACE_DIR = process.env.TRACE_DIR || path.join(__dirname, '..', 'traces');

function writeTrace(decision) {
  const timestamp = new Date().toISOString();
  const trace = {
    timestamp,
    service: 'common-reasoner-vmesh',
    decision_schema: 'common-reasoner-decision.v1',
    mode: 'decision_only',
    turn_id: decision.turn_id,
    intent_family: decision.intent_family,
    obligation: decision.obligation,
    minimum_lane_class: decision.minimum_lane_class,
    rendering_allowed: false,
    tool_execution_allowed: false,
    memory_write_allowed: false,
    context_write_allowed: false
  };

  // Only write local trace file — does NOT touch shared state
  try {
    if (!fs.existsSync(TRACE_DIR)) fs.mkdirSync(TRACE_DIR, { recursive: true });
    const filename = `${timestamp.replace(/[:.]/g, '-')}-${decision.turn_id || 'unknown'}.json`;
    fs.writeFileSync(path.join(TRACE_DIR, filename), JSON.stringify(trace, null, 2), 'utf8');
  } catch (_) {
    // Trace writing failure is non-blocking
  }

  return trace;
}

module.exports = { writeTrace };
