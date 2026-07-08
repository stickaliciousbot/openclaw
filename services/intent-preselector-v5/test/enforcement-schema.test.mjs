import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const schema = JSON.parse(readFileSync(new URL('../config/enforcement.schema.json', import.meta.url), 'utf8'));

assert.equal(schema.$id, 'stickbot.context_plus_semantic_preselector.production_control_surface.v1');
assert.equal(schema.properties.schema.const, 'stickbot.context_plus_semantic_preselector.production_control_surface.v1');
assert.equal(schema.properties.subject.const, 'CONTEXT_PLUS_SEMANTIC_PRESELECTOR');
assert.equal(schema.properties.authority.const, 'lane_selection_only');
assert.equal(schema.properties.traffic_scope.const, 'owner_operator_live_turns_only');
assert.equal(schema.properties.operator_allowlist.contains.const, 'telegram:8495203551');
assert.ok(schema.required.includes('kill_switch'));
assert.ok(schema.properties.m6_evidence.required.includes('comparator_classification'));
assert.equal(schema.properties.m6_evidence.properties.comparator_classification.const, 'PASS_FALSE_POSITIVE_BASELINE_IMPROVED');
assert.equal(schema.properties.guards.properties.context_may_replace_prompt.const, false);
assert.equal(schema.properties.guards.properties.cache_allowed.const, false);
assert.equal(schema.properties.guards.properties.artifact_memory_promotion_allowed.const, false);
assert.equal(schema.properties.guards.properties.default_model_change_allowed.const, false);
assert.equal(schema.properties.guards.properties.provider_model_change_allowed.const, false);
assert.equal(schema.allOf[0].then.properties.enabled.const, true);
assert.equal(schema.allOf[0].then.properties.kill_switch.const, false);

console.log(JSON.stringify({ ok: true, name: 'intent-preselector-v5-enforcement-schema', assertions: 16, provider_calls: 0 }));
