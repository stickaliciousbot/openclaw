import crypto from 'node:crypto';
import { selectRoute } from '../../intent-preselector-v5/src/index.js';
import { intentPreselectorV5RequestAllowed } from './intentPreselectorV5ControlSurface.js';

function sha256(text = '') {
  return crypto.createHash('sha256').update(String(text || ''), 'utf8').digest('hex');
}

function compactObligations(obligations = []) {
  return (Array.isArray(obligations) ? obligations : []).slice(0, 8).map((item) => ({
    type: item?.type || null,
    confidence: item?.confidence ?? null,
    evidence: Array.isArray(item?.evidence) ? item.evidence.slice(0, 4) : []
  }));
}

function compactContextFrames(frames = []) {
  return (Array.isArray(frames) ? frames : []).slice(0, 6).map((frame) => ({
    frame_id: frame?.frame_id || null,
    kind: frame?.kind || null,
    source: frame?.source || null,
    confidence: frame?.confidence ?? null,
    ttl_turns: frame?.ttl_turns ?? null,
    can_resolve_referents: Boolean(frame?.can_resolve_referents),
    can_increase_lane_strength: Boolean(frame?.can_increase_lane_strength),
    can_replace_user_prompt: false
  }));
}

function v5Mode(enforcement = {}) {
  return enforcement.enforced === true ? 'enforced_route_contract' : 'shadow_contract_only';
}

function compactDecision(decision, prompt, config = {}, enforcement = {}) {
  if (!decision || typeof decision !== 'object') return null;
  const enforced = enforcement.enforced === true;
  return {
    mode: v5Mode(enforcement),
    enforced,
    control_surface: enforcement.control_surface || null,
    route_contract_version: decision.route_contract?.route_contract_version || decision.route_contract_version || 'intent-preselector-v5.0',
    decision_id: decision.decision_id || decision.route_contract?.decision_id || null,
    schema: decision.route_contract?.schema || 'intent-preselector-v5.contract.v1',
    turn_id: decision.route_contract?.turn_id || decision.decision_id || null,
    selected_lane: decision.selected_lane || decision.route_contract?.selected_lane || null,
    fallback_lanes: decision.route_contract?.fallback_lanes || [],
    visible_user_text_hash: decision.route_contract?.visible_user_text_hash || `sha256:${sha256(prompt)}`,
    support_context_hash: decision.route_contract?.support_context_hash || null,
    contract_input_hash: decision.route_contract?.contract_input_hash || null,
    intent_family: decision.route_contract?.intent_family || null,
    ambiguity_score: decision.route_contract?.ambiguity_score ?? decision.ambiguity ?? null,
    minimum_lane_class: decision.route_contract?.minimum_lane_class || null,
    disallowed_lane_classes: decision.route_contract?.disallowed_lane_classes || [],
    safe_escalation_allowed: decision.route_contract?.safe_escalation_allowed !== false,
    fail_closed_if_unavailable: Boolean(decision.route_contract?.fail_closed_if_unavailable),
    confidence: decision.confidence ?? null,
    prompt_preserved: decision.prompt_preserved === true,
    user_prompt_hash: sha256(prompt),
    user_prompt_length: String(prompt || '').length,
    context_may_replace_prompt: false,
    answer_user_prompt: decision.route_contract?.answer_user_prompt !== false,
    requires: decision.route_contract?.requires || {},
    tool_policy: decision.route_contract?.tool_policy || null,
    write_policy: decision.route_contract?.write_policy || null,
    obligations: compactObligations(decision.obligations),
    must_not: Array.isArray(decision.must_not) ? decision.must_not.slice(0, 8) : [],
    required_capabilities: decision.required_capabilities || {},
    reason_codes: Array.isArray(decision.reason_codes) ? decision.reason_codes.slice(0, 16) : [],
    degraded: Boolean(decision.degraded),
    degraded_reason: decision.degraded_reason || null,
    context_frames: compactContextFrames(decision.context_frames)
  };
}

function conversationState({ previousState = null, routeScore = null } = {}) {
  const state = previousState && typeof previousState === 'object' ? previousState : {};
  const activeBits = [state.contextIntentLabel || state.intentLabel, state.contextLane || state.lane, state.hardGateReason].filter(Boolean);
  const scoreBits = [routeScore?.intent?.label, routeScore?.recommendedLane, routeScore?.hardGate?.reason].filter(Boolean);
  const bits = activeBits.length ? activeBits : scoreBits;
  return {
    active_topic: bits.length ? `intent=${bits[0]}; lane=${bits[1] || 'unknown'}; hard_gate=${bits[2] || 'none'}` : null,
    runtime_state_summary: 'token-solver-v4 shadow contract compile; user prompt must remain authoritative and context may resolve only; production enforcement requires protected control surface state.',
    turns_since_topic_shift: bits.length ? 1 : 999
  };
}

export async function buildV5ShadowContract({ prompt = '', selectedModel = null, rawBody = null, previousState = null, routeScore = null, path = null, sessionKey = null, config = {} } = {}) {
  if (config?.intentPreselectorV5ShadowEnabled === false) {
    return { mode: 'disabled', enforced: false, reason: 'config_disabled' };
  }

  const requestAllowance = intentPreselectorV5RequestAllowed({ controlSurface: config?.intentPreselectorV5ControlSurface, rawBody, sessionKey });
  const enforcement = {
    enforced: config?.intentPreselectorV5Enforced === true && requestAllowance.allowed === true,
    control_surface: {
      schema: config?.intentPreselectorV5ControlSurface?.schema || null,
      subject: config?.intentPreselectorV5ControlSurface?.subject || null,
      active: Boolean(config?.intentPreselectorV5ControlSurface?.active),
      request_allowed: Boolean(requestAllowance.allowed),
      reason: requestAllowance.reason,
      traffic_scope: config?.intentPreselectorV5ControlSurface?.trafficScope || null,
      authority: config?.intentPreselectorV5ControlSurface?.authority || null
    }
  };

  const userPrompt = String(prompt || '').trim();
  if (!userPrompt) {
    return { mode: v5Mode(enforcement), enforced: enforcement.enforced, control_surface: enforcement.control_surface, degraded: true, degraded_reason: 'missing_prompt', prompt_preserved: false };
  }

  try {
    const decision = await selectRoute({
      request_id: rawBody?.request_id || rawBody?.id || sessionKey || null,
      user_prompt: { raw: userPrompt },
      prompt: userPrompt,
      selected_model: selectedModel,
      conversation_state: conversationState({ previousState, routeScore }),
      runtime_state: {
        service: config?.serviceId || 'token-solver-v4',
        endpoint: path,
        selected_model: selectedModel,
        deterministic_score_lane: routeScore?.recommendedLane || null,
        tool_need_probability: routeScore?.toolNeedProbability ?? null
      },
      policy: {
        remote_llm_for_scoring_allowed: false,
        local_advisor_allowed: false,
        write_trace: config?.intentPreselectorV5TraceEnabled === true
      }
    }, { writeTrace: config?.intentPreselectorV5TraceEnabled === true });
    return compactDecision(decision, userPrompt, config, enforcement);
  } catch (err) {
    return {
      mode: v5Mode(enforcement),
      enforced: enforcement.enforced,
      control_surface: enforcement.control_surface,
      degraded: true,
      degraded_reason: `intent_preselector_v5_failed:${String(err?.message || err).slice(0, 160)}`,
      prompt_preserved: false,
      user_prompt_hash: sha256(userPrompt),
      user_prompt_length: userPrompt.length,
      context_may_replace_prompt: false
    };
  }
}
