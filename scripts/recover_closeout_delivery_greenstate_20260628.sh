#!/usr/bin/env bash
set -euo pipefail

# Recover Stickbot/OpenClaw closeout-delivery greenstate captured on 2026-06-28.
# Usage:
#   scripts/recover_closeout_delivery_greenstate_20260628.sh /path/to/stickbot-greenstate-closeout-*.tar.gz
# Optional env:
#   WORKSPACE=/home/stickai/.openclaw/workspace
#   OPENCLAW_PREFIX=/home/stickai/.npm-global
#   GITHUB_REPO_URL=https://github.com/stickaliciousbot/webworkspace.git
#   GITHUB_BRANCH=stickbot/v3-selected-model-persona-injection
#   SKIP_GATEWAY_RESTART=1   # restore files/install artifact but do not restart gateway

BUNDLE_PATH="${1:-${DR_BUNDLE:-}}"
WORKSPACE="${WORKSPACE:-/home/stickai/.openclaw/workspace}"
OPENCLAW_PREFIX="${OPENCLAW_PREFIX:-/home/stickai/.npm-global}"
GITHUB_REPO_URL="${GITHUB_REPO_URL:-https://github.com/stickaliciousbot/webworkspace.git}"
GITHUB_BRANCH="${GITHUB_BRANCH:-stickbot/v3-selected-model-persona-injection}"
EXPECTED_ARTIFACT_SHA="9ffa4cafda8b1185b09cebb7905a063c3851d8f83d74abfee9017dcf18a1e616"
EXPECTED_VERSION="OpenClaw 2026.5.7 (5c3a327)"
RUN_ID="greenstate-restore-$(date -u +%Y%m%dT%H%M%SZ)"
TMPDIR="$(mktemp -d)"
REPORT_DIR="$WORKSPACE/sharedspace/disaster-recovery/restore-reports"
REPORT_PATH="$REPORT_DIR/${RUN_ID}.log"

cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$REPORT_PATH"
}

fail() {
  log "FAIL: $*"
  exit 1
}

mkdir -p "$REPORT_DIR"
log "Starting closeout greenstate restore"
log "WORKSPACE=$WORKSPACE"
log "OPENCLAW_PREFIX=$OPENCLAW_PREFIX"

if [[ -z "$BUNDLE_PATH" ]]; then
  fail "Bundle path required as argv[1] or DR_BUNDLE"
fi
if [[ ! -f "$BUNDLE_PATH" ]]; then
  fail "Bundle not found: $BUNDLE_PATH"
fi

tar -xzf "$BUNDLE_PATH" -C "$TMPDIR"
BUNDLE_ROOT="$(find "$TMPDIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
[[ -n "$BUNDLE_ROOT" ]] || fail "Could not find extracted bundle root"
log "Extracted bundle root: $BUNDLE_ROOT"

ARTIFACT="$BUNDLE_ROOT/payload/artifacts/openclaw-2026.5.7.tgz"
[[ -f "$ARTIFACT" ]] || fail "Artifact missing from bundle: $ARTIFACT"
ACTUAL_ARTIFACT_SHA="$(sha256sum "$ARTIFACT" | awk '{print $1}')"
[[ "$ACTUAL_ARTIFACT_SHA" == "$EXPECTED_ARTIFACT_SHA" ]] || fail "Artifact SHA mismatch: $ACTUAL_ARTIFACT_SHA"
log "Artifact SHA verified: $ACTUAL_ARTIFACT_SHA"

mkdir -p "$WORKSPACE"
if [[ -d "$WORKSPACE/.git" ]]; then
  log "Workspace git repo exists; fetching/pulling $GITHUB_BRANCH"
  git -C "$WORKSPACE" fetch origin "$GITHUB_BRANCH" || log "WARN: git fetch failed; continuing with bundle overlay"
  git -C "$WORKSPACE" checkout "$GITHUB_BRANCH" || log "WARN: git checkout failed; continuing with current checkout"
  git -C "$WORKSPACE" pull --ff-only origin "$GITHUB_BRANCH" || log "WARN: git pull failed; continuing with bundle overlay"
elif command -v git >/dev/null 2>&1; then
  log "Workspace git repo missing; cloning $GITHUB_REPO_URL branch $GITHUB_BRANCH"
  rm -rf "$WORKSPACE"
  git clone --branch "$GITHUB_BRANCH" "$GITHUB_REPO_URL" "$WORKSPACE" || fail "git clone failed"
else
  log "WARN: git unavailable; using bundle overlay only"
fi

OVERLAY="$BUNDLE_ROOT/payload/workspace-overlay"
[[ -d "$OVERLAY" ]] || fail "Workspace overlay missing: $OVERLAY"
log "Restoring workspace overlay"
cp -a "$OVERLAY/." "$WORKSPACE/"

SYSTEMD_OVERLAY="$BUNDLE_ROOT/payload/systemd-user"
if [[ -d "$SYSTEMD_OVERLAY" ]]; then
  log "Restoring user systemd files"
  mkdir -p "$HOME/.config/systemd/user"
  cp -a "$SYSTEMD_OVERLAY/." "$HOME/.config/systemd/user/"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload || log "WARN: systemctl --user daemon-reload failed"
    systemctl --user enable --now openclaw-gateway-self-heal-watchdog.timer || log "WARN: enable watchdog timer failed"
  fi
fi

log "Installing OpenClaw closeout-delivery artifact"
npm install -g --ignore-scripts --prefix "$OPENCLAW_PREFIX" "$ARTIFACT" | tee -a "$REPORT_PATH"

OPENCLAW_BIN="$OPENCLAW_PREFIX/bin/openclaw"
[[ -x "$OPENCLAW_BIN" ]] || fail "OpenClaw CLI missing/not executable: $OPENCLAW_BIN"
VERSION="$($OPENCLAW_BIN --version)"
log "OpenClaw version after install: $VERSION"
[[ "$VERSION" == "$EXPECTED_VERSION" ]] || fail "OpenClaw version mismatch; expected '$EXPECTED_VERSION'"

if [[ "${SKIP_GATEWAY_RESTART:-0}" == "1" ]]; then
  log "SKIP_GATEWAY_RESTART=1; not restarting Gateway"
else
  OLD_PID="$(pgrep -f 'openclaw/dist/index.js gateway' | head -n 1 || true)"
  log "Gateway old PID: ${OLD_PID:-none}"
  set +e
  "$OPENCLAW_BIN" gateway restart >>"$REPORT_PATH" 2>&1
  RESTART_CODE=$?
  set -e
  log "Gateway restart command exit code: $RESTART_CODE (health gates decide final state)"
  sleep 5
fi

log "Gateway health status"
set +e
"$OPENCLAW_BIN" gateway status | tee -a "$REPORT_PATH"
STATUS_CODE=${PIPESTATUS[0]}
set -e
[[ "$STATUS_CODE" -eq 0 ]] || fail "openclaw gateway status failed"

if "$OPENCLAW_BIN" gateway status | grep -q 'Connectivity probe: ok' && "$OPENCLAW_BIN" gateway status | grep -q 'Capability: admin-capable'; then
  log "PASS: Gateway connectivity/admin health gates passed"
else
  fail "Gateway connectivity/admin health gates did not pass"
fi

log "PASS: closeout delivery greenstate restored"
log "Report: $REPORT_PATH"
