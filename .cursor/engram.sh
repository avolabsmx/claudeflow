#!/usr/bin/env bash
# Runs engram pinned to this repo's Engram project (AC-1128).
# ENGRAM_CLOUD_SERVER and ENGRAM_CLOUD_TOKEN come from Cursor secrets; never commit them.
set -euo pipefail
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export ENGRAM_PROJECT="claudeflow"
export ENGRAM_CLOUD_AUTOSYNC="${ENGRAM_CLOUD_AUTOSYNC:-1}"

case "${1:-}" in
  # Local-only, idempotent: marks the project for replication to the Engram server.
  enroll) exec engram cloud enroll "$ENGRAM_PROJECT" ;;
  # Pushes pending memories before the VM goes away; autosync alone polls every ~30s.
  flush) exec engram sync --cloud --project "$ENGRAM_PROJECT" ;;
  *) exec engram "$@" ;;
esac
