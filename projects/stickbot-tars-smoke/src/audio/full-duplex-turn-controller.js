export const FULL_DUPLEX_CONTROLLER_SCHEMA = 'stickbot.tars.full-duplex-turn-controller.v1';

const STATES = Object.freeze({
  IDLE: 'idle',
  LISTENING: 'listening',
  THINKING: 'thinking',
  SPEAKING: 'speaking',
  INTERRUPTED: 'interrupted',
  COMPLETE: 'complete',
  FAILED: 'failed'
});

function eventRecord(type, payload = {}, at = new Date()) {
  return {
    type,
    at: at.toISOString(),
    payload: redactPayload(type, payload)
  };
}

function redactPayload(type, payload = {}) {
  if (type === 'partial_transcript' || type === 'final_transcript') {
    return {
      textSha256: payload.textSha256 || null,
      charCount: Number(payload.charCount || 0),
      confidence: payload.confidence ?? null,
      durableRawTextStored: false
    };
  }
  return { ...payload };
}

function action(type, payload = {}) {
  return { type, payload };
}

export function createFullDuplexTurnController({ turnId, now = new Date() } = {}) {
  return {
    schema: FULL_DUPLEX_CONTROLLER_SCHEMA,
    classification: 'STICKBOT_TARS_M7L_FULL_DUPLEX_TURN_CONTROLLER_READY',
    turnId: turnId || null,
    state: STATES.IDLE,
    startedAt: now.toISOString(),
    events: [],
    actions: [],
    activeOutputSeq: null,
    boundaries: {
      localOnly: true,
      rawTranscriptDurableStorage: false,
      cloudSpeechApiAllowed: false,
      browserWebSpeechApiAllowed: false,
      textRewriteAllowed: false,
      gatewayMutationAllowed: false,
      openClawRoutingMutationAllowed: false
    }
  };
}

export function reduceFullDuplexEvent(controller, input = {}, { now = new Date() } = {}) {
  const c = {
    ...controller,
    events: [...(controller.events || [])],
    actions: [...(controller.actions || [])]
  };
  const type = input.type;
  const payload = input.payload || {};
  c.events.push(eventRecord(type, payload, now));

  if (type === 'listen_start' && c.state === STATES.IDLE) {
    c.state = STATES.LISTENING;
    c.actions.push(action('capture_audio_local_only', { durableRawTranscript: false }));
    return c;
  }

  if (type === 'partial_transcript' && c.state === STATES.LISTENING) {
    c.actions.push(action('update_partial_transcript_hash', {
      textSha256: payload.textSha256 || null,
      charCount: payload.charCount || 0,
      durableRawTranscript: false
    }));
    return c;
  }

  if (type === 'final_transcript' && c.state === STATES.LISTENING) {
    c.state = STATES.THINKING;
    c.actions.push(action('submit_final_transcript_to_turn_engine', {
      textSha256: payload.textSha256 || null,
      charCount: payload.charCount || 0,
      durableRawTranscript: false
    }));
    return c;
  }

  if (type === 'assistant_text_ready' && c.state === STATES.THINKING) {
    c.actions.push(action('build_prosody_score', {
      canonicalTextSha256: payload.canonicalTextSha256 || null
    }));
    c.actions.push(action('start_chunk_audio_pipeline', {
      streamingPreferred: true,
      fallbackFinalWav: true
    }));
    return c;
  }

  if (type === 'audio_frame_ready' && (c.state === STATES.THINKING || c.state === STATES.SPEAKING)) {
    c.state = STATES.SPEAKING;
    c.activeOutputSeq = payload.seq ?? c.activeOutputSeq;
    c.actions.push(action('emit_audio_frame', {
      seq: payload.seq ?? null,
      frameType: payload.frameType || 'audio_chunk_ready',
      interruptible: true
    }));
    return c;
  }

  if (type === 'barge_in' && c.state === STATES.SPEAKING) {
    c.state = STATES.INTERRUPTED;
    c.actions.push(action('stop_audio_output', {
      reason: 'barge_in',
      activeOutputSeq: c.activeOutputSeq
    }));
    c.actions.push(action('return_to_local_listening', {
      durableRawTranscript: false
    }));
    return c;
  }

  if (type === 'resume_listening' && c.state === STATES.INTERRUPTED) {
    c.state = STATES.LISTENING;
    c.activeOutputSeq = null;
    c.actions.push(action('capture_audio_local_only', { durableRawTranscript: false }));
    return c;
  }

  if (type === 'turn_complete' && (c.state === STATES.SPEAKING || c.state === STATES.THINKING)) {
    c.state = STATES.COMPLETE;
    c.actions.push(action('finalize_turn', {
      retainRawTranscript: false,
      retainAudioArtifactsLocalOnly: true
    }));
    return c;
  }

  if (type === 'error') {
    c.state = STATES.FAILED;
    c.actions.push(action('fail_closed', {
      classification: payload.classification || 'M7L_FULL_DUPLEX_CONTROLLER_ERROR',
      safeTextFallback: true
    }));
    return c;
  }

  c.actions.push(action('ignore_invalid_or_out_of_order_event', {
    eventType: type,
    state: c.state
  }));
  return c;
}

export function runFullDuplexScenario(events = [], options = {}) {
  let controller = createFullDuplexTurnController(options);
  for (const item of events) controller = reduceFullDuplexEvent(controller, item, options);
  return controller;
}

export function publicFullDuplexControllerSummary(controller = {}) {
  return {
    schema: controller.schema || FULL_DUPLEX_CONTROLLER_SCHEMA,
    classification: controller.classification,
    turnId: controller.turnId || null,
    state: controller.state,
    eventCount: (controller.events || []).length,
    actionCount: (controller.actions || []).length,
    events: controller.events || [],
    actions: controller.actions || [],
    boundaries: controller.boundaries
  };
}
