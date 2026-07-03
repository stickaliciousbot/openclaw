export const REALTIME_FRAME_SCHEMA = 'stickbot.tars.realtime-audio-frame.v1';
export const LOW_LATENCY_TRANSPORT_SCHEMA = 'stickbot.tars.low-latency-transport.v1';

function frame({ turnId, seq, type, payload = {}, timing = {}, boundaries = {} }) {
  return {
    schema: REALTIME_FRAME_SCHEMA,
    turnId,
    seq,
    type,
    payload,
    timing,
    boundaries: {
      localOnly: true,
      textRewriteAllowed: false,
      rawTranscriptDurableStorage: false,
      cloudSpeechApiAllowed: false,
      browserWebSpeechApiAllowed: false,
      ...boundaries
    }
  };
}

export function buildLowLatencyTransportPlan({
  frames = [],
  targetQueueDepth = 2,
  firstAudioTargetMs = 1200,
  interChunkGapTargetMs = 120,
  preloadTimeoutMs = 1200
} = {}) {
  const audioFrames = (frames || []).filter((item) => item.type === 'audio_chunk_ready');
  let relativeOffsetMs = 0;
  const schedule = audioFrames.map((item, index) => {
    const planned = {
      seq: item.seq,
      chunkId: item.payload?.chunkId || null,
      chunkIndex: item.payload?.chunkIndex ?? index,
      preloadPriority: index < targetQueueDepth ? 'eager' : 'rolling',
      plannedRelativeOffsetMs: relativeOffsetMs,
      pauseAfterMs: item.timing?.pauseAfterMs || 0,
      durationMs: item.timing?.durationMs || null
    };
    relativeOffsetMs += item.timing?.pauseAfterMs || 0;
    return planned;
  });
  return {
    schema: LOW_LATENCY_TRANSPORT_SCHEMA,
    classification: 'STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_READY',
    enabled: audioFrames.length > 0,
    mode: 'browser_preload_queue_then_serial_playback',
    queueDepthTarget: targetQueueDepth,
    firstAudioTargetMs,
    interChunkGapTargetMs,
    preloadTimeoutMs,
    audioFrameCount: audioFrames.length,
    schedule,
    telemetryContract: {
      clientMayReport: true,
      fields: [
        'queueBuiltMs',
        'firstFrameCanPlayMs',
        'firstAudioPlayMs',
        'maxInterChunkGapMs',
        'playedFrameCount',
        'cancelled'
      ],
      rawAudioStored: false,
      rawTranscriptDurableStorage: false
    },
    boundaries: {
      localOnly: true,
      textRewriteAllowed: false,
      rawTranscriptDurableStorage: false,
      cloudSpeechApiAllowed: false,
      browserWebSpeechApiAllowed: false,
      gatewayMutationAllowed: false,
      openClawRoutingMutationAllowed: false
    }
  };
}

export function buildRealtimeFrameManifest({ turnId, score = {}, chunkArtifacts = [], dspStage = null, masteringStage = null, output = null } = {}) {
  let seq = 0;
  const frames = [];
  frames.push(frame({
    turnId,
    seq: seq++,
    type: 'turn_start',
    payload: {
      canonicalTextSha256: score.canonicalTextSha256 || null,
      moodId: score.moodId || null,
      voicePersona: score.voicePersona || null,
      chunkCount: chunkArtifacts.length
    }
  }));

  for (const artifact of chunkArtifacts) {
    const dspFrame = (dspStage?.frames || []).find((candidate) => candidate.chunkId === artifact.chunkId) || null;
    const masteringFrame = (masteringStage?.frames || []).find((candidate) => candidate.chunkId === artifact.chunkId) || null;
    frames.push(frame({
      turnId,
      seq: seq++,
      type: 'audio_chunk_ready',
      payload: {
        chunkId: artifact.chunkId,
        chunkIndex: artifact.chunkIndex,
        textSha256: artifact.textSha256,
        phraseRole: artifact.phraseRole,
        effectiveXtts: artifact.effectiveXtts,
        audioSha256: artifact.audioSha256 || null,
        fileBasename: artifact.fileBasename || null,
        dsp: dspFrame ? {
          schema: dspFrame.schema,
          classification: dspFrame.classification,
          outputFileBasename: dspFrame.outputFileBasename,
          profile: dspFrame.profile
        } : null,
        mastering: masteringFrame ? {
          schema: masteringFrame.schema,
          classification: masteringFrame.classification,
          outputFileBasename: masteringFrame.outputFileBasename,
          profile: masteringFrame.profile
        } : null
      },
      timing: {
        pauseAfterMs: artifact.pauseAfterMs || 0,
        durationMs: artifact.durationMs || null
      }
    }));
    if (artifact.pauseAfterMs > 0) {
      frames.push(frame({
        turnId,
        seq: seq++,
        type: 'pause',
        payload: {
          afterChunkId: artifact.chunkId,
          reason: 'prosody_score_rest'
        },
        timing: { durationMs: artifact.pauseAfterMs }
      }));
    }
  }

  frames.push(frame({
    turnId,
    seq: seq++,
    type: 'turn_end',
    payload: {
      renderer: output?.renderer || null,
      audioSha256: output?.audioSha256 || null
    }
  }));

  const transport = buildLowLatencyTransportPlan({ frames });
  return {
    schema: 'stickbot.tars.realtime-frame-manifest.v1',
    classification: 'STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS',
    turnId,
    frameSchema: REALTIME_FRAME_SCHEMA,
    target: 'streaming_full_duplex_mesh',
    enabled: true,
    frameCount: frames.length,
    frames,
    transport,
    boundaries: {
      localOnly: true,
      textRewriteAllowed: false,
      rawTranscriptDurableStorage: false,
      cloudSpeechApiAllowed: false,
      browserWebSpeechApiAllowed: false
    }
  };
}

export async function* iterateRealtimeFrames(manifest = {}) {
  for (const item of manifest.frames || []) yield item;
}

export function publicRealtimeFrameManifest(manifest = {}) {
  return {
    schema: manifest.schema,
    classification: manifest.classification,
    turnId: manifest.turnId || null,
    frameSchema: manifest.frameSchema || REALTIME_FRAME_SCHEMA,
    target: manifest.target || 'streaming_full_duplex_mesh',
    enabled: manifest.enabled !== false,
    frameCount: manifest.frameCount || 0,
    frames: (manifest.frames || []).map((item) => ({
      schema: item.schema,
      turnId: item.turnId,
      seq: item.seq,
      type: item.type,
      payload: item.payload,
      timing: item.timing,
      boundaries: item.boundaries
    })),
    transport: manifest.transport || buildLowLatencyTransportPlan({ frames: manifest.frames || [] }),
    boundaries: manifest.boundaries
  };
}
