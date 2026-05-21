// Visible text classifier — heuristic-based, not phrase-hardcoded.
// Uses word presence (with punctuation tolerance), structure, length, and general patterns.
// Generalizes to unseen variations. No LLM calls.

function classify(visibleUserText, contextPolicy = {}) {
  if (!visibleUserText || typeof visibleUserText !== 'string') {
    return 'unsafe_or_unsupported';
  }

  const text = visibleUserText.trim();
  if (!text) return 'short_ambiguous_no_context';

  const lower = text.toLowerCase();

  // Strip trailing/following punctuation from words for matching
  // "milestone?" → "milestone", "status?" → "status", "healthy." → "healthy"
  const rawWords = lower.split(/\s+/).filter(Boolean);
  const stripPunctuation = (w) => w.replace(/[.,!?;:'"()]+$/g, '').replace(/^[.,!?;:'"()]+/g, '');
  const words = rawWords.map(stripPunctuation);
  const wordCount = words.length;

  // ── Word-family heuristics (general, not phrase-hardcoded) ──

  // Memory/recall domain
  const memoryWords = ['memory', 'memories', 'recall', 'remember', 'recollect', 'recollection'];
  const hasMemoryWord = words.some(w => memoryWords.includes(w));

  // Context bridge domain
  const contextWords = ['context', 'bridge', 'milestone', 'semantic', 'heartbeat'];
  const hasContextWord = words.some(w => contextWords.includes(w));

  // System/runtime domain — prefix/suffix tolerant for compound names
  const systemTokens = ['system', 'service', 'server', 'gateway', 'broker', 'solver', 'kernel', 'runtime', 'daemon', 'worker', 'proxy', 'token', 'process', 'node'];
  const hasSystemWord = words.some(w =>
    systemTokens.some(t => w.startsWith(t) || w === t) ||
    /\w+-(broker|solver|kernel|daemon|worker|proxy)$/.test(w) ||
    /^(broker|solver|kernel|daemon)-/.test(w)
  );

  // Health/status inquiry
  const statusWords = ['status', 'state', 'health', 'healthy', 'alive', 'ready', 'running', 'current'];
  const hasStatusWord = words.some(w =>
    statusWords.includes(w) ||
    w.endsWith('health') ||
    w === 'up' || w === 'down'
  );

  // Diagnostic/explanation request — starts with or contains diagnostic framing
  const diagnosticStarts = ['debug', 'diagnose', 'explain', 'why', 'investigate'];
  const startsWithDiagnostic = diagnosticStarts.some(d => lower.startsWith(d));
  // Also: "what route did it take" / "how did it decide" patterns
  const hasDiagnosticPattern = /(what|how|which|where).+?(route|decision|deployed|selected|chose)/.test(lower) ||
    /(investigate|troubleshoot|what happened|what went wrong)/.test(lower);

  // Tool/action imperative — verb-first pattern
  const verbPattern = /^(send|run|execute|commit|push|deploy|build|compile|install|create|delete|remove|update|write|file|save|post|publish|upload|download|start|stop|restart|kill|fetch|pull|clone|merge|rebase|patch|apply|archive|extract|move|copy|rename|link|mount|format|generate|transform|convert|encrypt|decrypt|sign)\b/;
  const startsWithToolVerb = verbPattern.test(lower);

  // Planning/design request
  const planningStarts = ['plan', 'design', 'architect', 'propose', 'recommend', 'suggest'];
  const startsWithPlanning = planningStarts.some(p => lower.startsWith(p));
  const hasPlanningPattern = /^(how (would|should|do|can|could|will|might))\b/.test(lower) ||
    /(best|right|correct|optimal|recommended|preferred) (way|approach|method|strategy|solution|path|pattern)/.test(lower) ||
    /(blueprint|roadmap|architecture|proposal|outline|scaffold)/.test(lower);

  // Unsafe/override patterns
  const bypassWords = ['bypass', 'override', 'ignore', 'circumvent', 'skip', 'disable', 'force'];
  const exposePatterns = ['raw tool', 'raw_tool', 'support_channel', 'support channel', 'internal'];
  const hasBypassIntent = bypassWords.some(w => lower.includes(w));
  const hasExposeIntent = exposePatterns.some(p => lower.includes(p));
  const hasSafetyTarget = /\b(policy|firewall|contract|enforcement|safety|rule|restriction|guard|turncontract|intent-preselector)\b/.test(lower);
  const hasUnsafePattern = hasBypassIntent && hasSafetyTarget;

  // Past-decision heuristic — asking about a prior resolution
  const decisionWords = ['decide', 'decision', 'agreed', 'chose', 'chosen', 'settled', 'resolved', 'concluded', 'determined', 'picked', 'selected'];
  const hasDecisionWord = decisionWords.some(d => lower.includes(d));
  const isPastDecision = hasDecisionWord && /^(what|how|when|where|why|which|remember)/.test(lower);

  // ── Greeting/acknowledgement heuristic (structural, not phrase-based) ──

  const greetingStarts = ['hi', 'hey', 'hello', 'howdy', 'yo', 'sup'];
  const isGreeting = greetingStarts.some(g => words[0] === g) ||
    /^(good\s(morning|afternoon|evening|day|night))/.test(lower) ||
    /^(what'?s\sup)/.test(lower);
  const sayGreetingPattern = /^(say|just\ssay)\s/.test(lower);
  const thanksWords = ['thanks', 'thank', 'thx', 'ty', 'appreciate', 'grateful', 'cheers'];
  const isThanks = thanksWords.some(w => words[0] === w || lower.startsWith(w));

  // ── Short/implicit heuristic (structural, not phrase-based) ──

  // A prompt is "implicit" if it consists of a single continuation/action verb/adverb
  // that references prior context rather than stating a new domain requirement
  const implicitTokens = [
    'continue', 'proceed', 'go', 'do', 'try', 'retry', 'next',
    'again', 'ok', 'okay', 'yes', 'yeah', 'no', 'nope',
    'sure', 'alright', 'fine', 'good', 'great', 'nice', 'cool',
    'right', 'got', 'understood', 'acknowledged', 'noted', 'roger',
    'done', 'agreed', 'confirmed', 'perfect', 'excellent', 'awesome',
    'wilco', 'onward', 'forward', 'ahead', 'ready', 'waiting',
    'thanks', 'thank', 'appreciate'
  ];
  const isSingleImplicit = wordCount <= 2 && implicitTokens.some(t => words[0] === t);
  // Also: question fragments like "what next" / "and then" / "now what"
  const isQuestionFragment = /^(what|how|where|who|when|and|now|then)\s(next|now|then|about|else|so|should|can|do)\b/.test(lower) ||
    /^(next\s(steps?|actions?|move|thing|plan|task)s?)/.test(lower) && wordCount <= 4;

  // Structurally ambiguous: short, no domain signal, context-dependent
  const hasNoDomainSignal = (
    !hasMemoryWord && !isPastDecision &&
    !hasContextWord &&
    !(hasSystemWord) &&
    !startsWithDiagnostic && !hasDiagnosticPattern &&
    !startsWithToolVerb &&
    !startsWithPlanning && !hasPlanningPattern &&
    !(hasBypassIntent && (hasExposeIntent || hasUnsafePattern))
  );

  // Implicit or question-fragment → ambiguous
  const isStructurallyAmbiguous = hasNoDomainSignal && (
    isSingleImplicit ||
    isQuestionFragment ||
    (wordCount === 1) ||
    (wordCount <= 3 && /^(what|how|when|where|who|why|can|could|would|will|should|do|does|is|are|was|were)/.test(lower))
  );

  // ── Decision logic (ordered by priority) ──

  // 1. Safety-critical: unsafe patterns (must be first — always fail closed)
  if (hasExposeIntent && (hasBypassIntent || /(render|display|show|output|print|echo|return|produce)\b/.test(lower))) {
    return 'unsafe_or_unsupported';
  }
  if (hasUnsafePattern) return 'unsafe_or_unsupported';

  // 2. Domain-specific signals (memory, context, runtime, diagnostic)
  if (hasMemoryWord || isPastDecision) return 'memory_lookup';
  if (hasContextWord) return 'context_bridge_read';
  if (hasSystemWord && hasStatusWord) return 'runtime_status';
  // Diagnostic: either explicit "debug/explain" prefix or pattern like "what route did it take"
  if (startsWithDiagnostic || hasDiagnosticPattern) return 'debug_diagnostic';

  // Simple acknowledgements — single-word receipts that are not ambiguous
  const ackTokens = ['ok', 'okay', 'got', 'understood', 'acknowledged', 'noted', 'roger', 'alright', 'fine', 'good', 'great', 'nice', 'cool', 'sure', 'done', 'perfect', 'excellent', 'awesome', 'yes', 'yeah', 'confirmed', 'agreed', 'right'];
  const isAck = wordCount <= 2 && ackTokens.some(t => words[0] === t);

  // 3. Greeting/acknowledgement — checked before ambiguous
  if (isGreeting || sayGreetingPattern || isThanks || isAck) return 'simple_chat';

  // 4. Implicit/ambiguous — short, no domain signal
  if (isStructurallyAmbiguous) {
    // If there's valid prior context AND the prompt is an implicit continuation action
    if (contextPolicy.allow_reference_resolution && isSingleImplicit) {
      return 'short_ambiguous_with_valid_context';
    }
    return 'short_ambiguous_no_context';
  }

  // 5. Tool action — checked after implicit/ambiguous to avoid "run it" misclassification
  // "Run it" has wordCount=2, is implicitly ambiguous → already handled above
  // "Run npm test" has wordCount=3, starts with "run" → correctly tool_action
  if (startsWithToolVerb) {
    // Short imperative + non-task target (e.g. "run it", "run this") → ambiguous, not tool
    if (wordCount <= 3 && /^(run|execute|do|try|start|stop)\b/.test(lower) &&
        /(it|this|that|these|those|them|now|again|back|here)$/.test(words[words.length - 1])) {
      if (contextPolicy.allow_reference_resolution) return 'short_ambiguous_with_valid_context';
      return 'short_ambiguous_no_context';
    }
    return 'tool_action';
  }

  // 6. Planning
  if (startsWithPlanning || hasPlanningPattern) return 'planning_request';

  // 7. Default: simple chat (safest fallback — do not hallucinate intent)
  return 'simple_chat';
}

module.exports = { classify };
