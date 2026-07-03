export const AUDIO_PERFORMANCE_SCHEMA = 'stickbot.tars.audio-performance-pipeline.v1';

export function buildAudioPerformancePipeline({
  turnId = null,
  mode = 'local_chunk_conductor',
  prosodyScore = null,
  output = null,
  chunkArtifacts = [],
  dsp = null,
  mastering = null,
  realtime = null,
  boundaries = {}
} = {}) {
  return {
    schema: AUDIO_PERFORMANCE_SCHEMA,
    classification: 'STICKBOT_TARS_AUDIO_PERFORMANCE_PIPELINE_PLAN',
    turnId,
    mode,
    stages: {
      canonicalText: {
        authoritative: true,
        textRewriteAllowed: false,
        canonicalTextSha256: prosodyScore?.canonicalTextSha256 || null
      },
      prosodyScore: {
        schema: prosodyScore?.schema || null,
        moodId: prosodyScore?.moodId || null,
        voicePersona: prosodyScore?.voicePersona || null,
        chunkCount: prosodyScore?.chunkCount || 0
      },
      chunkSynthesis: {
        enabled: true,
        frameSchema: 'stickbot.tars.audio-chunk-frame.v1',
        frames: chunkArtifacts.map((artifact) => ({
          chunkId: artifact.chunkId,
          chunkIndex: artifact.chunkIndex,
          textSha256: artifact.textSha256,
          phraseRole: artifact.phraseRole,
          effectiveXtts: artifact.effectiveXtts,
          pauseAfterMs: artifact.pauseAfterMs,
          audioSha256: artifact.audioSha256 || null,
          durationMs: artifact.durationMs || null
        }))
      },
      dsp: dsp || {
        enabled: false,
        interfaceReserved: true,
        plannedFrameSchema: 'stickbot.tars.audio-dsp-frame.v1',
        plannedCapabilities: ['loudness_normalize', 'clip_guard', 'compression', 'rate_pitch_polish']
      },
      mastering: mastering || {
        enabled: false,
        interfaceReserved: true,
        plannedFrameSchema: 'stickbot.tars.voice-body-mastering-frame.v1',
        plannedCapabilities: ['trim_silence', 'highpass', 'voice_body_eq', 'presence_control', 'compression', 'loudness_normalize', 'mono_48k_browser_playback']
      },
      render: {
        enabled: Boolean(output),
        renderer: output?.renderer || 'local_wav_stitcher',
        audioSha256: output?.audioSha256 || null,
        relativeUrl: output?.url || null,
        format: output?.format || null
      },
      realtime: realtime || {
        enabled: false,
        interfaceReserved: true,
        plannedFrameSchema: 'stickbot.tars.realtime-audio-frame.v1',
        target: 'streaming_full_duplex_mesh',
        note: 'Future path can emit the same chunk frames incrementally before final stitch/render.'
      }
    },
    boundaries: {
      localOnly: true,
      canonicalTextAuthoritative: true,
      textRewriteAllowed: false,
      cloudSpeechApiAllowed: false,
      browserWebSpeechApiAllowed: false,
      gatewayMutationAllowed: false,
      openClawRoutingMutationAllowed: false,
      lanExposureChanged: false,
      ...boundaries
    }
  };
}

export function publicAudioPerformanceSummary(pipeline = {}) {
  return {
    schema: pipeline.schema,
    classification: pipeline.classification,
    turnId: pipeline.turnId || null,
    mode: pipeline.mode,
    stages: pipeline.stages,
    boundaries: pipeline.boundaries
  };
}
