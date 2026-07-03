const ROLE_CUES = Object.freeze({
  status: { glyph: '✅', dynamic: 'mf', contour: 'flat-positive', tempo: 'steady', emotionalColor: 'controlled_success', intensity: 0.58 },
  instruction: { glyph: '🛰️', dynamic: 'mf', contour: 'mission-brief', tempo: 'brisk', emotionalColor: 'operator_precision', intensity: 0.62 },
  warning: { glyph: '⚠️', dynamic: 'f', contour: 'clipped-command', tempo: 'fast', emotionalColor: 'urgent_control', intensity: 0.9 },
  blocker: { glyph: '⛔', dynamic: 'f', contour: 'fail-closed', tempo: 'slow-firm', emotionalColor: 'hard_boundary', intensity: 0.84 },
  evidence: { glyph: '🔎', dynamic: 'mp', contour: 'measured-analysis', tempo: 'steady', emotionalColor: 'diagnostic_focus', intensity: 0.48 },
  aside: { glyph: '😐', dynamic: 'p', contour: 'delayed-deadpan', tempo: 'dry-pause', emotionalColor: 'dry_restraint', intensity: 0.42 },
  punchline: { glyph: '😐', dynamic: 'p', contour: 'delayed-deadpan', tempo: 'dry-pause', emotionalColor: 'dry_wit', intensity: 0.45 },
  confirmation: { glyph: '☑️', dynamic: 'mp', contour: 'quiet-confirmation', tempo: 'steady', emotionalColor: 'quiet_confidence', intensity: 0.44 },
  uncertainty: { glyph: '🤔', dynamic: 'mp', contour: 'careful-uncertain', tempo: 'slow-careful', emotionalColor: 'bounded_uncertainty', intensity: 0.5 },
  recovery: { glyph: '🛠️', dynamic: 'mf', contour: 'calm-recovery', tempo: 'steady', emotionalColor: 'repair_focus', intensity: 0.56 },
  question: { glyph: '❓', dynamic: 'mp', contour: 'measured-question', tempo: 'steady-rise', emotionalColor: 'curious_diagnostic', intensity: 0.46 },
  closeout: { glyph: '🏁', dynamic: 'mf', contour: 'flat-closeout', tempo: 'steady', emotionalColor: 'completion_control', intensity: 0.64 }
});

function clamp01(n) {
  return Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));
}

function round2(n) {
  return Number(clamp01(n).toFixed(2));
}

function cueForChunk(chunk = {}) {
  const base = ROLE_CUES[chunk.phraseRole] || ROLE_CUES.evidence;
  const features = chunk.features || {};
  const technicalBoost = clamp01(features.technicalDensity || 0) * 0.16;
  const punctuationBoost = clamp01(features.punctuationDensity || 0) * 0.08;
  const markerBoost = (features.warningMarker || features.blockerMarker || features.failMarker) ? 0.12 : 0;
  const questionLift = features.question ? 0.04 : 0;
  const pause = chunk.effectivePauses || {};
  const pauseAfterMs = Number(chunk.pauseAfterMs ?? pause.postPauseMs ?? 0);
  const restGlyph = pauseAfterMs >= 300 ? '𝄽' : pauseAfterMs >= 180 ? '𝄾' : '·';
  const intensity = round2(base.intensity + technicalBoost + punctuationBoost + markerBoost + questionLift);
  const tempo = pauseAfterMs >= 300 ? `${base.tempo}+held` : base.tempo;
  return {
    chunkId: chunk.chunkId,
    chunkIndex: chunk.chunkIndex,
    textSha256: chunk.textSha256,
    phraseRole: chunk.phraseRole,
    deliveryLabel: chunk.deliveryLabel,
    cueGlyph: base.glyph,
    restGlyph,
    dynamic: base.dynamic,
    contour: base.contour,
    tempo,
    emotionalColor: base.emotionalColor,
    intensity,
    pauseAfterMs,
    sheetToken: `${base.glyph}${base.dynamic}/${restGlyph}`,
    canonicalTextUnchanged: true,
    textRewriteAllowed: false
  };
}

function aggregateMoodScore(score = {}, cues = []) {
  const averageIntensity = cues.length
    ? cues.reduce((sum, cue) => sum + cue.intensity, 0) / cues.length
    : 0;
  const dominant = [...cues].sort((a, b) => b.intensity - a.intensity)[0] || null;
  const sequence = cues.map((cue) => cue.sheetToken).join(' ');
  return {
    moodId: score.moodId,
    moodLabel: score.moodLabel,
    expressionToken: score.expressionToken,
    voicePersona: score.voicePersona,
    averageIntensity: round2(averageIntensity),
    dominantCue: dominant ? {
      chunkId: dominant.chunkId,
      cueGlyph: dominant.cueGlyph,
      phraseRole: dominant.phraseRole,
      emotionalColor: dominant.emotionalColor,
      intensity: dominant.intensity
    } : null,
    cueSequence: sequence,
    chunkCount: cues.length
  };
}

export function buildLiveProsodyCueLayer(score = {}, { generatedBy = 'stickbot-local-deterministic-cue-engine' } = {}) {
  const cues = (score.chunks || []).map(cueForChunk);
  const moodScore = aggregateMoodScore(score, cues);
  return {
    schema: 'stickbot.tars.live-prosody-cue-layer.v1',
    classification: 'STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_READY',
    generatedBy,
    generatedAt: score.generatedAt || null,
    canonicalTextSha256: score.canonicalTextSha256,
    canonicalTextUnchanged: score.canonicalTextUnchanged === true,
    textRewriteAllowed: false,
    moodScore,
    emotionalSheetMusic: cues,
    boundaries: {
      canonicalTextAuthoritative: true,
      textRewriteAllowed: false,
      deliveryMetadataOnly: true,
      exposesRawText: false,
      localOnly: true,
      cloudSpeechAllowed: false,
      browserWebSpeechApiAllowed: false,
      gatewayMutationAllowed: false,
      openClawRoutingMutationAllowed: false
    }
  };
}

export function publicLiveProsodyCueLayer(layer = {}) {
  return {
    schema: layer.schema,
    classification: layer.classification,
    generatedBy: layer.generatedBy,
    generatedAt: layer.generatedAt,
    canonicalTextSha256: layer.canonicalTextSha256,
    canonicalTextUnchanged: layer.canonicalTextUnchanged,
    textRewriteAllowed: layer.textRewriteAllowed,
    moodScore: layer.moodScore,
    emotionalSheetMusic: (layer.emotionalSheetMusic || []).map((cue) => ({
      chunkId: cue.chunkId,
      chunkIndex: cue.chunkIndex,
      textSha256: cue.textSha256,
      phraseRole: cue.phraseRole,
      deliveryLabel: cue.deliveryLabel,
      cueGlyph: cue.cueGlyph,
      restGlyph: cue.restGlyph,
      dynamic: cue.dynamic,
      contour: cue.contour,
      tempo: cue.tempo,
      emotionalColor: cue.emotionalColor,
      intensity: cue.intensity,
      pauseAfterMs: cue.pauseAfterMs,
      sheetToken: cue.sheetToken,
      canonicalTextUnchanged: cue.canonicalTextUnchanged,
      textRewriteAllowed: cue.textRewriteAllowed
    })),
    boundaries: layer.boundaries
  };
}
