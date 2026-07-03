import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { buildProsodyScore } from '../src/prosody/prosody-score-engine.js';
import { conductChunkedXtts, publicChunkConductorSummary, synthesizeProsodyChunks } from '../src/audio/xtts-chunk-conductor.js';
import { loadTarsProsodyProfile } from '../src/voice/tars-prosody-profile.js';
import { sanitizeTarsTuning } from '../src/voice/tars-prosody-tuning.js';

const profile = loadTarsProsodyProfile();

async function tmpRoot() {
  return mkdtemp(path.join(os.tmpdir(), 'stickbot-tars-m7i-'));
}

test('STICKBOT_TARS_M7I_CHUNK_SYNTH_USES_PER_CHUNK_EFFECTIVE_XTTS_PASS', async () => {
  const root = await tmpRoot();
  const score = buildProsodyScore('PASS. No model load occurred. Naturally, the robot waits.', {
    profile,
    tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }),
    maxChars: 32
  });
  const calls = [];
  const artifacts = await synthesizeProsodyChunks({
    turnId: 'turn-test',
    score,
    outputDir: root,
    synthesizeChunk: async (frame) => {
      calls.push(frame);
      return { buffer: Buffer.from(`chunk:${frame.chunkId}:${frame.effectiveXtts.temperature}`), synthesis: { provider: 'fake_xtts' } };
    }
  });
  assert.equal(calls.length, score.chunks.length);
  assert.equal(artifacts.length, score.chunks.length);
  for (const [index, call] of calls.entries()) {
    assert.equal(call.text, score.chunks[index].text);
    assert.deepEqual(call.effectiveXtts, score.chunks[index].effectiveXtts);
    assert.equal(call.pauseAfterMs, score.chunks[index].pauseAfterMs);
    assert.equal(call.textSha256, score.chunks[index].textSha256);
    assert.ok(artifacts[index].audioSha256?.length === 64);
  }
});

test('STICKBOT_TARS_M7I_CONDUCTOR_STITCHES_AND_EXPOSES_PUBLIC_MESH_SUMMARY_PASS', async () => {
  const root = await tmpRoot();
  const score = buildProsodyScore('PASS. No model load occurred. Naturally, the robot waits.', {
    profile,
    tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }),
    maxChars: 32
  });
  const finalOutPath = path.join(root, 'turn-test.wav');
  const result = await conductChunkedXtts({
    turnId: 'turn-test',
    score,
    outputDir: path.join(root, 'chunks'),
    finalOutPath,
    ffmpegBin: '/usr/bin/ffmpeg',
    synthesizeChunk: async (frame) => ({ buffer: Buffer.from(`fake-wav-${frame.chunkId}`), synthesis: { provider: 'fake_xtts' } }),
    stitcher: async ({ sequence, outPath }) => {
      await writeFile(outPath, Buffer.concat(await Promise.all(sequence.map((entry) => readFile(entry.file)))));
      return { file: outPath, renderer: 'fake_test_stitcher', entries: sequence.map((entry) => entry.file) };
    }
  });
  assert.equal(result.classification, 'STICKBOT_TARS_M7I_CHUNK_CONDUCTOR_RENDER_PASS');
  assert.equal(result.chunkArtifacts.length, score.chunks.length);
  assert.equal(result.output.renderer, 'fake_test_stitcher');
  assert.ok(result.output.audioSha256.length === 64);
  assert.equal(result.pipeline.stages.dsp.interfaceReserved, true);
  assert.equal(result.pipeline.stages.realtime.target, 'streaming_full_duplex_mesh');

  const pub = publicChunkConductorSummary(result);
  assert.equal(pub.chunkArtifacts[0].text, undefined, 'public conductor summary must not expose raw chunk text');
  assert.equal(pub.chunkArtifacts[0].textSha256.length, 64);
  assert.equal(pub.pipeline.stages.chunkSynthesis.frames.length, score.chunks.length);
  assert.equal(pub.boundaries.textRewriteAllowed, false);
});

test('STICKBOT_TARS_M7I_CANONICAL_BOUNDARY_FAILS_CLOSED_PASS', async () => {
  const root = await tmpRoot();
  const score = buildProsodyScore('PASS. Canonical text remains unchanged.', { profile, tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }) });
  score.chunks[0].text = 'PASS. Mutated text.';
  await assert.rejects(
    () => synthesizeProsodyChunks({ turnId: 'turn-test', score, outputDir: root, synthesizeChunk: async () => Buffer.from('x') }),
    /text hash mismatch/
  );
});
