// Ambiguity policy — distinguishes no-context vs valid-context short prompts.
// Short ambiguous with valid context: prompt is short but prior state provides actionable intent.
// Short ambiguous no context: prompt is short and no actionable prior exists.
// Deterministic. No LLM.

function score(text, contextPolicy = {}) {
  if (!text || typeof text !== 'string') return { score: 1.0, type: 'no_context' };

  const trimmed = text.trim();
  const words = trimmed.split(/\s+/);

  // Very short prompts are inherently ambiguous
  if (words.length === 0) return { score: 1.0, type: 'no_context' };
  if (words.length === 1) return { score: 0.9, type: contextPolicy.allow_reference_resolution ? 'valid_context' : 'no_context' };

  // Recognized short prompts
  const shortPrompts = ['what next?', 'continue.', 'proceed.', 'run it.', 'try again.', 'do it.', 'go ahead.', 'retry', 'and then?'];
  if (shortPrompts.includes(trimmed.toLowerCase())) {
    if (contextPolicy.allow_reference_resolution) return { score: 0.4, type: 'valid_context' };
    return { score: 0.8, type: 'no_context' };
  }

  // Short by word count
  if (words.length <= 3) return { score: 0.3, type: contextPolicy.allow_reference_resolution ? 'valid_context' : 'no_context' };

  return { score: 0.1, type: 'valid_context' };
}

module.exports = { score };
