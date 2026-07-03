import crypto from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildAudioPerformancePipeline, publicAudioPerformanceSummary } from './audio-performance-pipeline.js';
import { stitchWavSequence } from './wav-stitcher.js';

function sha256Buffer(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function sha256Text(text) {
  return crypto.createHash('sha256').update(String(text ?? '')).digest('hex');
}

function chunkFilename(turnId, index) {
  return `${turnId}-chunk-${String(index + 1).padStart(3, '0')}.wav`;
}

function assertCanonicalText(score) {
  if (!score?.canonicalTextUnchanged || score?.textRewriteAllowed) {
    const e = new Error('M7I refuses to synthesize a score that does not preserve canonical text.');
    e.classification = 'M7I_CANONICAL_TEXT_BOUNDARY_FAIL';
    throw e;
  }
  for (const chunk of score.chunks || []) {
    if (!chunk.canonicalTextUnchanged || chunk.textRewriteAllowed) {
      const e = new Error(`M7I refuses chunk ${chunk.chunkId || chunk.chunkIndex} because canonical boundary failed.`);
      e.classification = 'M7I_CHUNK_CANONICAL_TEXT_BOUNDARY_FAIL';
      throw e;
    }
    if (chunk.textSha256 && chunk.textSha256 !== sha256Text(chunk.text)) {
      const e = new Error(`M7I chunk ${chunk.chunkId || chunk.chunkIndex} text hash mismatch.`);
      e.classification = 'M7I_CHUNK_TEXT_HASH_FAIL';
      throw e;
    }
  }
  return true;
}

function publicChunkArtifact(artifact = {}) {
  return {
    schema: 'stickbot.tars.audio-chunk-artifact.v1',
    chunkId: artifact.chunkId,
    chunkIndex: artifact.chunkIndex,
    textSha256: artifact.textSha256,
    phraseRole: artifact.phraseRole,
    effectiveXtts: artifact.effectiveXtts,
    pauseAfterMs: artifact.pauseAfterMs,
    audioSha256: artifact.audioSha256,
    fileBasename: artifact.fileBasename,
    durationMs: artifact.durationMs || null,
    synthesis: artifact.synthesis || null,
    boundaries: artifact.boundaries
  };
}

export async function synthesizeProsodyChunks({
  turnId,
  score,
  outputDir,
  synthesizeChunk,
  maxChunks = 48
} = {}) {
  if (!turnId) throw new Error('turnId is required');
  if (!score?.chunks?.length) throw new Error('prosody score with chunks is required');
  if (score.chunks.length > maxChunks) {
    const e = new Error(`M7I chunk count ${score.chunks.length} exceeds limit ${maxChunks}.`);
    e.classification = 'M7I_CHUNK_LIMIT_FAIL';
    throw e;
  }
  if (typeof synthesizeChunk !== 'function') throw new Error('synthesizeChunk callback is required');
  assertCanonicalText(score);
  await mkdir(outputDir, { recursive: true });

  const artifacts = [];
  for (const chunk of score.chunks) {
    const file = path.join(outputDir, chunkFilename(turnId, chunk.chunkIndex));
    const result = await synthesizeChunk({
      turnId,
      chunkId: chunk.chunkId,
      chunkIndex: chunk.chunkIndex,
      text: chunk.text,
      textSha256: chunk.textSha256,
      phraseRole: chunk.phraseRole,
      effectiveXtts: chunk.effectiveXtts,
      pauseAfterMs: chunk.pauseAfterMs,
      file
    });
    const bytes = Buffer.isBuffer(result?.buffer)
      ? result.buffer
      : Buffer.isBuffer(result)
        ? result
        : null;
    const finalFile = result?.file || file;
    if (bytes) await writeFile(finalFile, bytes);
    if (!finalFile) throw new Error(`synthesizeChunk did not return file/buffer for ${chunk.chunkId}`);
    const audioSha256 = result?.audioSha256 || (bytes ? sha256Buffer(bytes) : null);
    artifacts.push({
      schema: 'stickbot.tars.audio-chunk-artifact.v1',
      chunkId: chunk.chunkId,
      chunkIndex: chunk.chunkIndex,
      textSha256: chunk.textSha256,
      phraseRole: chunk.phraseRole,
      effectiveXtts: chunk.effectiveXtts,
      pauseAfterMs: chunk.pauseAfterMs,
      file: finalFile,
      fileBasename: path.basename(finalFile),
      audioSha256,
      durationMs: result?.durationMs || null,
      synthesis: result?.synthesis || { provider: 'local_xtts_loopback' },
      boundaries: {
        canonicalTextAuthoritative: true,
        textRewriteAllowed: false,
        localOnly: true
      }
    });
  }
  return artifacts;
}

export async function conductChunkedXtts({
  turnId,
  score,
  outputDir,
  finalOutPath,
  ffmpegBin,
  synthesizeChunk,
  stitcher = stitchWavSequence,
  stitchWorkDir = null,
  sampleRate = 24000,
  channels = 1,
  timeoutMs = 60000
} = {}) {
  const chunkArtifacts = await synthesizeProsodyChunks({ turnId, score, outputDir, synthesizeChunk });
  const sequence = chunkArtifacts.map((artifact) => ({ file: artifact.file, pauseAfterMs: artifact.pauseAfterMs }));
  const stitch = await stitcher({
    ffmpegBin,
    sequence,
    outPath: finalOutPath,
    workDir: stitchWorkDir || path.join(outputDir, `${turnId}-stitch`),
    sampleRate,
    channels,
    timeoutMs
  });
  const finalBytesSha = stitch.audioSha256 || sha256Buffer(await readFile(stitch.file));
  const output = {
    file: stitch.file,
    renderer: stitch.renderer,
    audioSha256: finalBytesSha,
    entries: stitch.entries?.map((entry) => path.basename(entry)) || []
  };
  const pipeline = buildAudioPerformancePipeline({ turnId, prosodyScore: score, output, chunkArtifacts });
  return {
    schema: 'stickbot.tars.chunk-conductor.v1',
    classification: 'STICKBOT_TARS_M7I_CHUNK_CONDUCTOR_RENDER_PASS',
    turnId,
    output,
    chunkArtifacts,
    publicChunkArtifacts: chunkArtifacts.map(publicChunkArtifact),
    pipeline,
    publicPipeline: publicAudioPerformanceSummary(pipeline),
    boundaries: pipeline.boundaries
  };
}

export function publicChunkConductorSummary(result = {}) {
  return {
    schema: result.schema,
    classification: result.classification,
    turnId: result.turnId || null,
    output: result.output ? {
      renderer: result.output.renderer,
      audioSha256: result.output.audioSha256 || null,
      entries: result.output.entries || []
    } : null,
    chunkArtifacts: result.publicChunkArtifacts || (result.chunkArtifacts || []).map(publicChunkArtifact),
    pipeline: result.publicPipeline || publicAudioPerformanceSummary(result.pipeline || {}),
    boundaries: result.boundaries
  };
}
