from production_sentinel_comparator import compare_production_sentinels

def production_sentinel_caused_deltas(prod_pre, prod_post):
    comparison = compare_production_sentinels(prod_pre, prod_post)
    return 0 if comparison.protected_match else {
        'classification': 'protected_semantic_or_identity_drift',
        'changes': comparison.changes,
        'authoritative_digest_pre': comparison.authoritative_digest_pre,
        'authoritative_digest_post': comparison.authoritative_digest_post,
    }
