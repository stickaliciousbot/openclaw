import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

export function publicProsodyTrace(score = {}) {
  return {
    schema: 'stickbot.tars.prosody-score.trace.v1',
    classification: score.classification,
    turnId: score.turnId || null,
    moodId: score.moodId,
    voicePersona: score.voicePersona,
    chunkCount: score.chunkCount,
    canonicalTextSha256: score.canonicalTextSha256,
    utteranceXttsParams: score.utteranceXttsParams,
    chunks: (score.chunks || []).map((chunk) => ({
      chunkId: chunk.chunkId,
      textSha256: chunk.textSha256,
      phraseRole: chunk.phraseRole,
      features: chunk.features,
      baseXtts: chunk.baseXtts,
      deltas: chunk.deltas,
      roleDeltas: chunk.roleDeltas,
      featureDeltas: chunk.featureDeltas,
      userTuningDeltas: chunk.userTuningDeltas,
      effectiveXtts: chunk.effectiveXtts,
      effectivePauses: chunk.effectivePauses,
      clampEvents: chunk.clampEvents,
      generationArtifact: chunk.generationArtifact || null
    })),
    boundaries: score.boundaries
  };
}

export async function writeProsodyTrace(rootDir, score, { filename = 'prosody-score-trace.json' } = {}) {
  const trace = publicProsodyTrace(score);
  await mkdir(rootDir, { recursive: true });
  const out = path.join(rootDir, filename);
  await writeFile(out, `${JSON.stringify(trace, null, 2)}\n`, 'utf8');
  return { path: out, trace };
}
