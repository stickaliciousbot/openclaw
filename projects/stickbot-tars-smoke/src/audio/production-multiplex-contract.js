export const PRODUCTION_MULTIPLEX_CONTRACT_SCHEMA = 'stickbot.tars.production-multiplex-turn-contract.v1';
export const PRODUCTION_MULTIPLEX_EVENT_SCHEMA = 'stickbot.tars.production-multiplex-event.v1';

const CHANNELS = Object.freeze({
  TEXT: 'canonical_text',
  AUDIO: 'audio_pcm_stream',
  PROSODY: 'prosody_metadata',
  CONTROL: 'control_events',
  AUDIT: 'audit_trace'
});

function boundaryDefaults() {
  return {
    localOnly: true,
    audioFirst: true,
    canonicalTextAuthoritative: true,
    textRewriteAllowed: false,
    audioInterruptionMutatesText: false,
    rawTranscriptDurableStorage: false,
    rawAudioCloudUploadAllowed: false,
    cloudSpeechApiAllowed: false,
    browserWebSpeechApiAllowed: false,
    gatewayMutationAllowed: false,
    openClawRoutingMutationAllowed: false,
    port8787Allowed: false
  };
}

function assertHash(name, value) {
  if (!/^[a-f0-9]{64}$/i.test(String(value || ''))) {
    const e = new Error(`${name} must be a 64-character sha256 hex digest`);
    e.classification = 'STICKBOT_TARS_PRODUCTION_MULTIPLEX_INVALID_HASH_FAIL';
    throw e;
  }
}

function textLane({ turnId, canonicalTextSha256, textCharCount = null }) {
  return {
    channel: CHANNELS.TEXT,
    turnId,
    canonicalTextSha256,
    charCount: textCharCount,
    authoritative: true,
    interruptible: false,
    mutableByAudioBargeIn: false,
    storesRawTranscript: false,
    textRewriteAllowed: false
  };
}

function audioLane({ turnId, canonicalTextSha256, realtimeManifest = {} }) {
  const frames = (realtimeManifest.frames || [])
    .filter((frame) => frame.type === 'audio_chunk_ready')
    .map((frame, index) => ({
      seq: frame.seq,
      streamIndex: index,
      chunkId: frame.payload?.chunkId || null,
      chunkIndex: frame.payload?.chunkIndex ?? index,
      textSha256: frame.payload?.textSha256 || null,
      audioSha256: frame.payload?.audioSha256 || null,
      fileBasename: frame.payload?.mastering?.outputFileBasename || frame.payload?.fileBasename || null,
      container: 'wav_or_pcm_frame',
      targetCodec: 'pcm_s16le',
      targetSampleRate: frame.payload?.mastering?.profile?.output?.sampleRate || 48000,
      channels: frame.payload?.mastering?.profile?.output?.channels || 1,
      pauseAfterMs: frame.timing?.pauseAfterMs || 0,
      durationMs: frame.timing?.durationMs || null,
      interruptible: true,
      canonicalTextSha256
    }));
  return {
    channel: CHANNELS.AUDIO,
    turnId,
    canonicalTextSha256,
    primaryRealtimeOutput: true,
    streamMode: 'audio_first_direct_wav_pcm_frames',
    fallbackFinalWavAllowed: true,
    frameCount: frames.length,
    frames,
    transport: realtimeManifest.transport || null,
    interruptible: true,
    cancellationPolicy: 'stop_audio_frames_preserve_text_lane'
  };
}

function prosodyLane({ turnId, canonicalTextSha256, liveProsodyCueLayer = null, prosodyScore = null }) {
  return {
    channel: CHANNELS.PROSODY,
    turnId,
    canonicalTextSha256,
    cueLayerSchema: liveProsodyCueLayer?.schema || null,
    cueLayerClassification: liveProsodyCueLayer?.classification || null,
    moodScore: liveProsodyCueLayer?.moodScore || null,
    emotionalSheetMusic: liveProsodyCueLayer?.emotionalSheetMusic || [],
    prosodyScoreClassification: prosodyScore?.classification || null,
    exposesRawText: false,
    deliveryMetadataOnly: true,
    textRewriteAllowed: false
  };
}

function controlLane({ turnId }) {
  return {
    channel: CHANNELS.CONTROL,
    turnId,
    stateMachine: 'full_duplex_audio_channel_owns_barge_in',
    events: [
      'turn_start',
      'audio_frame_ready',
      'audio_frame_playing',
      'barge_in',
      'audio_cancelled',
      'resume_listening',
      'turn_complete'
    ],
    bargeInPolicy: {
      ownerChannel: CHANNELS.AUDIO,
      stopActiveAudioFrames: true,
      preserveCanonicalTextLane: true,
      emitSupersededMarkerOnlyIfHigherLevelPolicyRequires: true,
      returnToLocalListening: true
    }
  };
}

function auditLane({ turnId, canonicalTextSha256, realtimeManifest = {}, liveProsodyCueLayer = null }) {
  return {
    channel: CHANNELS.AUDIT,
    turnId,
    canonicalTextSha256,
    records: {
      textHash: true,
      audioFrameHashes: true,
      prosodyCueHashes: true,
      interruptionMarkers: true,
      rawTranscriptText: false,
      rawAudioCloudPath: false
    },
    sourceSchemas: {
      realtimeManifest: realtimeManifest.schema || null,
      cueLayer: liveProsodyCueLayer?.schema || null
    }
  };
}

export function buildProductionMultiplexTurnContract({
  turnId,
  canonicalTextSha256,
  textCharCount = null,
  realtimeManifest = {},
  liveProsodyCueLayer = null,
  prosodyScore = null
} = {}) {
  if (!turnId) {
    const e = new Error('turnId is required');
    e.classification = 'STICKBOT_TARS_PRODUCTION_MULTIPLEX_MISSING_TURN_ID_FAIL';
    throw e;
  }
  assertHash('canonicalTextSha256', canonicalTextSha256);
  if (liveProsodyCueLayer?.canonicalTextSha256 && liveProsodyCueLayer.canonicalTextSha256 !== canonicalTextSha256) {
    const e = new Error('live prosody cue layer canonical hash does not match text lane');
    e.classification = 'STICKBOT_TARS_PRODUCTION_MULTIPLEX_HASH_MISMATCH_FAIL';
    throw e;
  }

  const lanes = [
    textLane({ turnId, canonicalTextSha256, textCharCount }),
    audioLane({ turnId, canonicalTextSha256, realtimeManifest }),
    prosodyLane({ turnId, canonicalTextSha256, liveProsodyCueLayer, prosodyScore }),
    controlLane({ turnId }),
    auditLane({ turnId, canonicalTextSha256, realtimeManifest, liveProsodyCueLayer })
  ];

  return {
    schema: PRODUCTION_MULTIPLEX_CONTRACT_SCHEMA,
    classification: 'STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_READY',
    turnId,
    canonicalTextSha256,
    channelOrder: lanes.map((lane) => lane.channel),
    lanes,
    invariants: {
      canonicalTextHashSharedByAllLanes: lanes.every((lane) => lane.canonicalTextSha256 === canonicalTextSha256 || lane.channel === CHANNELS.CONTROL),
      audioLaneOwnsBargeIn: true,
      audioCancellationPreservesTextLane: true,
      prosodyMetadataCannotRewriteText: true,
      auditUsesHashesNotRawText: true
    },
    boundaries: boundaryDefaults()
  };
}

export function reduceProductionMultiplexEvent(contract = {}, event = {}, { at = new Date() } = {}) {
  const type = event.type;
  const payload = event.payload || {};
  const record = {
    schema: PRODUCTION_MULTIPLEX_EVENT_SCHEMA,
    at: at.toISOString(),
    turnId: contract.turnId || null,
    type,
    payload: type === 'barge_in'
      ? { reason: payload.reason || 'user_started_speaking', rawTranscriptStored: false }
      : { ...payload },
    effects: []
  };

  if (type === 'barge_in') {
    record.effects.push({ lane: CHANNELS.AUDIO, action: 'cancel_active_audio_frames', preserveCanonicalText: true });
    record.effects.push({ lane: CHANNELS.CONTROL, action: 'return_to_local_listening', durableRawTranscript: false });
    record.effects.push({ lane: CHANNELS.AUDIT, action: 'record_interruption_marker', rawTranscriptStored: false });
    return record;
  }

  if (type === 'turn_complete') {
    record.effects.push({ lane: CHANNELS.AUDIO, action: 'finish_or_keep_replay_artifact_local_only' });
    record.effects.push({ lane: CHANNELS.TEXT, action: 'retain_canonical_text_hash_for_audit' });
    return record;
  }

  record.effects.push({ lane: CHANNELS.CONTROL, action: 'ignore_or_route_by_runtime_policy' });
  return record;
}

export function publicProductionMultiplexTurnContract(contract = {}) {
  return {
    schema: contract.schema || PRODUCTION_MULTIPLEX_CONTRACT_SCHEMA,
    classification: contract.classification,
    turnId: contract.turnId || null,
    canonicalTextSha256: contract.canonicalTextSha256 || null,
    channelOrder: contract.channelOrder || [],
    lanes: (contract.lanes || []).map((lane) => ({ ...lane })),
    invariants: contract.invariants || {},
    boundaries: contract.boundaries || boundaryDefaults()
  };
}
