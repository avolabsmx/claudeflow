#!/usr/bin/env bash
# Cursor cloud agent boot step (AC-1128). Runs on every boot and must never block it.
bash "$(dirname "${BASH_SOURCE[0]}")/engram.sh" enroll || echo "[cursor-start] engram enroll failed" >&2
