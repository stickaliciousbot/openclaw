export const TARS_PROSODY_PROFILE = Object.freeze({
  id: 'tars-inspired-local-v1',
  goal: 'voice_likeness_only_canonical_text_unchanged',
  engineHints: Object.freeze({
    current: 'xttsv2',
    piperReference: Object.freeze({
      sampleRateHz: 22050,
      inference: Object.freeze({ noiseScale: 0.667, lengthScale: 1.0, noiseW: 0.8 })
    })
  }),
  delivery: Object.freeze({
    normalRate: 0.96,
    statusRate: 1.05,
    warningRate: 0.88,
    pitchShiftSemitones: -3,
    pitchVariance: 0.12,
    energy: 0.62,
    breathiness: 0.05,
    expressiveness: 0.22,
    maxEmphasisPerSentence: 1,
    sentenceChunking: true
  }),
  pausesMs: Object.freeze({
    comma: 120,
    period: 220,
    status: 200,
    punchline: 360,
    warningAfterLabel: 400
  }),
  salienceWeights: Object.freeze({
    statusToken: 1.0,
    number: 0.85,
    warning: 1.0,
    operatorInstruction: 0.9,
    missionState: 0.8,
    joke: 0.65,
    ordinaryText: 0.35
  })
});

export function loadTarsProsodyProfile() {
  return TARS_PROSODY_PROFILE;
}
