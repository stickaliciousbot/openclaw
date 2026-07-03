import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { buildProsodyScore } from '../src/prosody/prosody-score-engine.js';
import { buildDspFilterGraph, deriveDspProfileFromProsody, polishChunkArtifacts } from '../src/audio/dsp-polish-stage.js';
import { buildRealtimeFrameManifest, iterateRealtimeFrames } from '../src/audio/streaming-frame-interface.js';
import { createFullDuplexTurnController, publicFullDuplexControllerSummary, reduceFullDuplexEvent, runFullDuplexScenario } from '../src/audio/full-duplex-turn-controller.js';
import { conductChunkedXtts } from '../src/audio/xtts-chunk-conductor.js';
import { loadTarsProsodyProfile } from '../src/voice/tars-prosody-profile.js';
import { sanitizeTarsTuning } from '../src/voice/tars-prosody-tuning.js';

const profile = loadTarsProsodyProfile();

async function tmpRoot() {
  return mkdtemp(path.join(os.tmpdir(), 'stickbot-tars-m7jkl-'));
}

function sampleScore() {
  return buildProsodyScore('PASS. No model load occurred. Naturally, the robot waits.', {
    profile,
    tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }),
    maxChars: 32
  });
}

test('STICKBOT_TARS_M7J_DSP_PROFILE_AND_FILTER_GRAPH_PASS', () => {
  const warning = deriveDspProfileFromProsody({ phraseRole: 'warning', effectiveXtts: { speed: 1.2 }, voicePersona: 'TARS' });
  const aside = deriveDspProfileFromProsody({ phraseRole: 'aside', effectiveXtts: { speed: 0.9 }, voicePersona: 'CASE' });
  assert.equal(warning.mode, 'local_ffmpeg_light_polish');
  assert.ok(warning.atempo <= 1.08);
  assert.equal(aside.loudnessI, -18);
  const filter = buildDspFilterGraph(warning);
  assert.match(filter, /acompressor=/);
  assert.match(filter, /alimiter=/);
  assert.match(filter, /loudnorm=/);
  assert.match(filter, /atempo=/);
});

test('STICKBOT_TARS_M7J_DSP_STAGE_PROCESSES_CHUNK_ARTIFACTS_PASS', async () => {
  const root = await tmpRoot();
  const input = path.join(root, 'input.wav');
  await writeFile(input, Buffer.from('fake-wav'));
  const artifacts = [{
    chunkId: 'c001',
    chunkIndex: 0,
    textSha256: 'a'.repeat(64),
    phraseRole: 'warning',
    effectiveXtts: { speed: 1.03 },
    pauseAfterMs: 120,
    file: input,
    fileBasename: 'input.wav',
    audioSha256: 'b'.repeat(64)
  }];
  const stage = await polishChunkArtifacts({
    chunkArtifacts: artifacts,
    ffmpegBin: '/usr/bin/ffmpeg',
    outputDir: path.join(root, 'dsp'),
    processor: async ({ inputFile, outputFile, profile }) => {
      await writeFile(outputFile, await readFile(inputFile));
      return { outputFile, filter: 'fake_filter', profile, classification: 'STICKBOT_TARS_M7J_DSP_FRAME_POLISHED' };
    }
  });
  assert.equal(stage.classification, 'STICKBOT_TARS_M7J_DSP_STAGE_LOCAL_PASS');
  assert.equal(stage.enabled, true);
  assert.equal(stage.frames[0].schema, 'stickbot.tars.audio-dsp-frame.v1');
  assert.equal(stage.artifacts[0].preDspFile, input);
  assert.match(stage.artifacts[0].fileBasename, /\.dsp\.wav$/);
});

test('STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS', async () => {
  const score = sampleScore();
  const artifacts = score.chunks.map((chunk) => ({
    chunkId: chunk.chunkId,
    chunkIndex: chunk.chunkIndex,
    textSha256: chunk.textSha256,
    phraseRole: chunk.phraseRole,
    effectiveXtts: chunk.effectiveXtts,
    pauseAfterMs: chunk.pauseAfterMs,
    audioSha256: 'c'.repeat(64),
    fileBasename: `${chunk.chunkId}.wav`
  }));
  const manifest = buildRealtimeFrameManifest({ turnId: 'turn-stream', score, chunkArtifacts: artifacts, output: { renderer: 'fake', audioSha256: 'd'.repeat(64) } });
  assert.equal(manifest.classification, 'STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS');
  assert.equal(manifest.target, 'streaming_full_duplex_mesh');
  assert.equal(manifest.frames[0].type, 'turn_start');
  assert.ok(manifest.frames.some((frame) => frame.type === 'audio_chunk_ready'));
  assert.ok(manifest.frames.some((frame) => frame.type === 'pause'));
  assert.equal(manifest.frames.at(-1).type, 'turn_end');
  for await (const frame of iterateRealtimeFrames(manifest)) {
    assert.equal(frame.boundaries.cloudSpeechApiAllowed, false);
    assert.equal(frame.boundaries.rawTranscriptDurableStorage, false);
  }
});

test('STICKBOT_TARS_M7L_FULL_DUPLEX_TURN_CONTROLLER_BARGE_IN_PASS', () => {
  const controller = runFullDuplexScenario([
    { type: 'listen_start' },
    { type: 'partial_transcript', payload: { textSha256: 'a'.repeat(64), charCount: 12, confidence: 0.8 } },
    { type: 'final_transcript', payload: { textSha256: 'b'.repeat(64), charCount: 24 } },
    { type: 'assistant_text_ready', payload: { canonicalTextSha256: 'c'.repeat(64) } },
    { type: 'audio_frame_ready', payload: { seq: 1, frameType: 'audio_chunk_ready' } },
    { type: 'barge_in', payload: { reason: 'user_started_speaking' } },
    { type: 'resume_listening' }
  ], { turnId: 'turn-duplex' });
  const pub = publicFullDuplexControllerSummary(controller);
  assert.equal(pub.classification, 'STICKBOT_TARS_M7L_FULL_DUPLEX_TURN_CONTROLLER_READY');
  assert.equal(pub.state, 'listening');
  assert.ok(pub.actions.some((item) => item.type === 'stop_audio_output'));
  assert.ok(pub.actions.some((item) => item.type === 'return_to_local_listening'));
  assert.equal(pub.boundaries.rawTranscriptDurableStorage, false);
  assert.equal(pub.events.find((item) => item.type === 'partial_transcript').payload.durableRawTextStored, false);
});

test('STICKBOT_TARS_M7L_INVALID_EVENT_FAILS_SAFE_BY_IGNORING_PASS', () => {
  let controller = createFullDuplexTurnController({ turnId: 'turn-invalid' });
  controller = reduceFullDuplexEvent(controller, { type: 'audio_frame_ready', payload: { seq: 1 } });
  assert.equal(controller.state, 'idle');
  assert.equal(controller.actions.at(-1).type, 'ignore_invalid_or_out_of_order_event');
});

test('STICKBOT_TARS_M7JKL_PIPELINE_INTEGRATION_SUMMARY_PASS', async () => {
  const root = await tmpRoot();
  const score = sampleScore();
  const result = await conductChunkedXtts({
    turnId: 'turn-jkl',
    score,
    outputDir: path.join(root, 'chunks'),
    finalOutPath: path.join(root, 'final.wav'),
    ffmpegBin: '/usr/bin/ffmpeg',
    synthesizeChunk: async (frame) => ({ buffer: Buffer.from(`fake-wav-${frame.chunkId}`), synthesis: { provider: 'fake_xtts' } }),
    dspProcessor: async ({ chunkArtifacts, outputDir }) => polishChunkArtifacts({
      chunkArtifacts,
      ffmpegBin: '/usr/bin/ffmpeg',
      outputDir,
      processor: async ({ inputFile, outputFile, profile }) => {
        await writeFile(outputFile, await readFile(inputFile));
        return { outputFile, filter: 'fake_filter', profile, classification: 'STICKBOT_TARS_M7J_DSP_FRAME_POLISHED' };
      }
    }),
    stitcher: async ({ sequence, outPath }) => {
      await writeFile(outPath, Buffer.concat(await Promise.all(sequence.map((entry) => readFile(entry.file)))));
      return { file: outPath, renderer: 'fake_test_stitcher', entries: sequence.map((entry) => entry.file) };
    }
  });
  assert.equal(result.dspStage.classification, 'STICKBOT_TARS_M7J_DSP_STAGE_LOCAL_PASS');
  assert.equal(result.realtime.classification, 'STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS');
  assert.equal(result.pipeline.stages.dsp.enabled, true);
  assert.equal(result.pipeline.stages.realtime.target, 'streaming_full_duplex_mesh');
  assert.equal(result.pipeline.boundaries.textRewriteAllowed, false);
});
