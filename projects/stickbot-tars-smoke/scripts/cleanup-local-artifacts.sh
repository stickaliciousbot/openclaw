#!/usr/bin/env bash
set -euo pipefail

# Cleanup local Stickbot-TARS operational artifacts.
# Usage:
#   RETENTION_DAYS=7 bash projects/stickbot-tars-smoke/scripts/cleanup-local-artifacts.sh
#
# This script intentionally targets only project-local runtime artifact directories.
# It must never delete model/source/config files outside this project data tree.

RETENTION_DAYS="${RETENTION_DAYS:-7}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

case "$RETENTION_DAYS" in
  ''|*[!0-9]*)
    echo "RETENTION_DAYS must be a non-negative integer" >&2
    exit 2
    ;;
esac

if [ ! -d "$DATA_DIR" ]; then
  echo "No data directory found: $DATA_DIR"
  exit 0
fi

# Delete generated/captured/temp audio older than N days.
for dir in \
  "$DATA_DIR/audio" \
  "$DATA_DIR/audio/input" \
  "$DATA_DIR/audio/output" \
  "$DATA_DIR/captured" \
  "$DATA_DIR/generated" \
  "$DATA_DIR/tmp"; do
  if [ -d "$dir" ]; then
    find "$dir" -type f -mtime +"$RETENTION_DAYS" \
      \( -name '*.wav' -o -name '*.webm' -o -name '*.ogg' -o -name '*.opus' -o -name '*.mp3' -o -name '*.flac' -o -name '*.tmp' \) \
      -print -delete
  fi
done

# Compact/archive traces older than N days by gzip-compressing JSONL traces in-place.
TRACE_DIR="$DATA_DIR/traces"
if [ -d "$TRACE_DIR" ]; then
  find "$TRACE_DIR" -type f -mtime +"$RETENTION_DAYS" -name '*.jsonl' -print -exec gzip -n {} \;
fi

echo "cleanup complete: data=$DATA_DIR retention_days=$RETENTION_DAYS"
