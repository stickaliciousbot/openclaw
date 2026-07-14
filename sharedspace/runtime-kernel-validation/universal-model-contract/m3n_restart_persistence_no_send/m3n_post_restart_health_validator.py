#!/usr/bin/env python3
"""M3N post-restart health scanner/liveness validator. Evidence-only helper.
No sends, no config writes, no provider calls.
"""
import json, re
BAD_TERMS = ["ERR_MODULE_NOT_FOUND","missing pi-embedded","missing Zalo","missing Zalouser","channels.telegram: unknown channel id"]
LIVENESS_TERMS = ["liveness warning","channels.telegram.start-account","fetch timeout reached","getMe","event-loop starvation","gateway timeout","context overflow detected"]
TRANSCRIPT_PATH_MARKERS = ["/agents/main/sessions/", ".trajectory.jsonl", "session transcript", "assistant/user transcript"]
def classify(path, message, after_restart):
    text = f"{path} {message}"
    if any(m in text for m in TRANSCRIPT_PATH_MARKERS) or "/sessions/" in path:
        return "TRANSCRIPT_FALSE_POSITIVE"
    if not after_restart:
        return "STALE_PRE_RESTART_LOG_SIGNAL"
    if any(t in message for t in BAD_TERMS + LIVENESS_TERMS):
        return "REAL_GATEWAY_LOG_SIGNAL"
    return "UNCLASSIFIED_SIGNAL"
def scan_records(records):
    seen=set(); out=[]; after_restart=False
    for idx, rec in enumerate(records):
        path=rec.get("path","runtime.log"); msg=rec.get("message","")
        if rec.get("restart_marker") or "SIGUSR1 received" in msg or "received SIGUSR1; restarting" in msg:
            after_restart=True
        terms=[t for t in BAD_TERMS + LIVENESS_TERMS if t in msg]
        if not terms: continue
        cls=classify(path,msg,after_restart)
        norm=re.sub(r"\d+ms|id=[a-z0-9-]+|conn=[^ ]+","<var>",msg)
        key=(cls, tuple(terms), norm)
        if key in seen: continue
        seen.add(key)
        out.append({"classification":cls,"terms":terms,"path":path,"line_index":idx,"message":msg})
    return out
def health_decision(gateway_rpc_ok, telegram_readback_ok, signals, stabilization_clean):
    real=[s for s in signals if s["classification"]=="REAL_GATEWAY_LOG_SIGNAL"]
    if not gateway_rpc_ok: return "FAIL_GATEWAY_RPC"
    if not telegram_readback_ok: return "FAIL_TELEGRAM_READBACK"
    if real and not stabilization_clean: return "FAIL_REAL_LIVENESS_SIGNAL"
    return "PASS_HEALTH"
