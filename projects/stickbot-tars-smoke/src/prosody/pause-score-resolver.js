function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value) || 0));
}

export function resolvePauseScore({ text = '', phraseRole = 'evidence', features = {}, baseDelivery = {}, voiceIdentity = {} } = {}) {
  const baseSentence = Number(baseDelivery.sentencePauseMs ?? 230);
  const baseComma = Number(baseDelivery.commaPauseMs ?? 90);
  const baseLine = Number(baseDelivery.lineBreakPauseMs ?? 320);
  let prePauseMs = 0;
  let postPauseMs = baseSentence;
  let commaPauseMs = baseComma;
  let semicolonPauseMs = Math.round(baseComma * 1.35);
  let colonPauseMs = Math.round(baseComma * 1.2);
  let lineBreakPauseMs = baseLine;

  if (phraseRole === 'status') postPauseMs = 190;
  if (phraseRole === 'blocker') postPauseMs = 260;
  if (phraseRole === 'instruction') postPauseMs = 160;
  if (phraseRole === 'evidence') postPauseMs = 230;
  if (phraseRole === 'aside' || phraseRole === 'punchline') {
    prePauseMs = 120;
    postPauseMs = 300;
  }
  if (phraseRole === 'warning') postPauseMs = 140;
  if (phraseRole === 'question') postPauseMs = 240;
  if (phraseRole === 'uncertainty') postPauseMs = 280;
  if (phraseRole === 'recovery') postPauseMs = 250;
  if (phraseRole === 'closeout') postPauseMs = 210;

  if (voiceIdentity.voicePersona === 'CASE') postPauseMs += 60;
  if (features.hasSemicolon) postPauseMs += 25;
  if (features.hasColon) postPauseMs += 15;
  if (features.hasLineBreak) postPauseMs = Math.max(postPauseMs, lineBreakPauseMs);
  if (/\.\.\./.test(text)) postPauseMs += 80;
  const delta = Number(voiceIdentity.allowedPauseDeltaMs ?? 160);
  return {
    prePauseMs: Math.round(clamp(prePauseMs, 0, delta)),
    postPauseMs: Math.round(clamp(postPauseMs, 45, Math.max(560, baseSentence + delta))),
    commaPauseMs: Math.round(clamp(commaPauseMs, 45, 560)),
    semicolonPauseMs: Math.round(clamp(semicolonPauseMs, 45, 650)),
    colonPauseMs: Math.round(clamp(colonPauseMs, 45, 650)),
    lineBreakPauseMs: Math.round(clamp(lineBreakPauseMs, 45, 760)),
    punctuationRests: {
      comma: commaPauseMs,
      semicolon: semicolonPauseMs,
      colon: colonPauseMs,
      lineBreak: lineBreakPauseMs
    }
  };
}
