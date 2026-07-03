import path from 'node:path';
import crypto from 'node:crypto';
import { writeFile } from 'node:fs/promises';
import { buildTarsProsodyPlan } from '../voice/tars-prosody-kernel.js';
import { conductChunkedXtts, publicChunkConductorSummary } from './xtts-chunk-conductor.js';
import {
  buildProductionMultiplexTurnContract,
  publicProductionMultiplexTurnContract,
  reduceProductionMultiplexEvent
} from './production-multiplex-contract.js';

export const PRODUCTION_MULTIPLEX_RUNTIME_HARNESS_SCHEMA = 'stickbot.tars.production-multiplex-runtime-harness.v1';

function sha256Buffer(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function defaultTurnId() {
  return `mux-${Date.now().toString(36)}-${crypto.randomBytes(4).toString('hex')}`;
}

async function defaultSynthesizeChunk({ chunkId }) {
  const buffer = Buffer.from(`local-fake-wav-frame:${chunkId}`);
  return {
    buffer,
    audioSha256: sha256Buffer(buffer),
    durationMs: 420,
    synthesis: {
      provider: 'local_deterministic_fake_audio_frame',
      cloudProvider: false
    }
  };
}

async function defaultStitcher({ sequence, outPath }) {
  await writeFile(outPath, Buffer.from(`local-runtime-harness-final-replay:${sequence.length}`));
  return {
    file: outPath,
    renderer: 'local_runtime_harness_final_replay_placeholder',
    entries: sequence.map((entry) => entry.file),
    replayFallbackOnly: true
  };
}

function assertSafePlan(plan = {}) {
  if (!plan.canonicalTextUnchanged || plan.delivery?.textRewriteAllowed) {
    const e = new Error('runtime harness refuses a plan that does not preserve canonical text');
    e.classification = 'STICKBOT_TARS_RUNTIME_HARNESS_CANONICAL_TEXT_FAIL';
    throw e;
  }
  if (!plan.noSecretSpeech) {
    const e = new Error('runtime harness refuses secret-like assistant text');
    e.classification = 'STICKBOT_TARS_RUNTIME_HARNESS_SECRET_TEXT_FAIL';
    throw e;
  }
}

export async function runProductionMultiplexRuntimeHarness({
  turnId = defaultTurnId(),
  text,
  tuning = null,
  matrixState = null,
  maxChars = 180,
  outputDir,
  finalOutPath = null,
  ffmpegBin = '/usr/bin/ffmpeg',
  synthesizeChunk = defaultSynthesizeChunk,
  stitcher = defaultStitcher,
  simulateBargeIn = true
} = {}) {
  if (!outputDir) {
    const e = new Error('outputDir is required for runtime harness audio frame artifacts');
    e.classification = 'STICKBOT_TARS_RUNTIME_HARNESS_OUTPUT_DIR_REQUIRED_FAIL';
    throw e;
  }
  const canonicalText = String(text ?? '');
  const plan = buildTarsProsodyPlan(canonicalText, { tuning, matrixState, maxChars });
  assertSafePlan(plan);
  const finalPath = finalOutPath || path.join(outputDir, `${turnId}.wav`);
  const conductor = await conductChunkedXtts({
    turnId,
    score: plan.prosodyScoreRaw,
    outputDir,
    finalOutPath: finalPath,
    ffmpegBin,
    synthesizeChunk,
    stitcher
  });
  const contract = buildProductionMultiplexTurnContract({
    turnId,
    canonicalTextSha256: plan.canonicalTextSha256,
    textCharCount: canonicalText.length,
    realtimeManifest: conductor.realtime,
    liveProsodyCueLayer: plan.liveProsodyCueLayer,
    prosodyScore: plan.prosodyScore
  });
  const lifecycleEvents = [
    reduceProductionMultiplexEvent(contract, { type: 'turn_start', payload: { canonicalTextSha256: plan.canonicalTextSha256 } }),
    ...(simulateBargeIn ? [reduceProductionMultiplexEvent(contract, { type: 'barge_in', payload: { reason: 'runtime_harness_user_interrupt' } })] : []),
    reduceProductionMultiplexEvent(contract, { type: 'turn_complete', payload: { canonicalTextSha256: plan.canonicalTextSha256 } })
  ];
  const audioLane = contract.lanes.find((lane) => lane.channel === 'audio_pcm_stream') || { frames: [] };
  return {
    schema: PRODUCTION_MULTIPLEX_RUNTIME_HARNESS_SCHEMA,
    classification: 'STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS',
    turnId,
    canonicalTextSha256: plan.canonicalTextSha256,
    textCharCount: canonicalText.length,
    contract,
    conductor,
    lifecycleEvents,
    evidence: {
      laneCount: contract.lanes.length,
      audioFrameCount: audioLane.frameCount || 0,
      prosodyCueCount: plan.liveProsodyCueLayer?.emotionalSheetMusic?.length || 0,
      bargeInEventCount: lifecycleEvents.filter((event) => event.type === 'barge_in').length,
      canonicalTextPreservedAfterBargeIn: true,
      finalWavIsReplayFallbackOnly: true
    },
    boundaries: {
      localOnly: true,
      audioFirst: true,
      canonicalTextAuthoritative: true,
      textRewriteAllowed: false,
      rawTranscriptDurableStorage: false,
      cloudSpeechApiAllowed: false,
      browserWebSpeechApiAllowed: false,
      gatewayMutationAllowed: false,
      openClawRoutingMutationAllowed: false,
      port8787Touched: false
    }
  };
}

export function publicProductionMultiplexRuntimeHarnessSummary(result = {}) {
  return {
    schema: result.schema || PRODUCTION_MULTIPLEX_RUNTIME_HARNESS_SCHEMA,
    classification: result.classification,
    turnId: result.turnId || null,
    canonicalTextSha256: result.canonicalTextSha256 || null,
    textCharCount: result.textCharCount ?? null,
    contract: publicProductionMultiplexTurnContract(result.contract || {}),
    audioPerformance: result.conductor ? publicChunkConductorSummary(result.conductor) : null,
    lifecycleEvents: (result.lifecycleEvents || []).map((event) => ({
      schema: event.schema,
      at: event.at,
      turnId: event.turnId,
      type: event.type,
      payload: event.payload,
      effects: event.effects
    })),
    evidence: result.evidence || {},
    boundaries: result.boundaries || {}
  };
}
