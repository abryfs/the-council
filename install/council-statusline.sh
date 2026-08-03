#!/usr/bin/env bash
# council-statusline — wraps the existing status line and appends <=2 council rows.
#
# Composition, not replacement: the existing statusline script owns rows 1..n and
# renders first. If ANY part of the council half fails, the existing rows still
# print unchanged. That property is the whole point — the status bar is the only
# status display on this machine and must never go dark for a nicety.
#
# This script does NO retrieval. council-retrieve.py wrote a cache at turn end;
# this only reads it. Budget is a few milliseconds.
set -uo pipefail

INPUT=$(cat)                       # stdin is consumed once, then replayed
BASE="$HOME/.claude/hooks/gsd-statusline.js"
CACHE_DIR="${TMPDIR:-/tmp}"
MUTE_FILE="$HOME/.claude/council-muted"
CACHE_TTL=5400                     # 90 min; matches council-retrieve.py

# ── row 1..n: the existing status line, unchanged ────────────────────────────
if [[ -x "$BASE" || -f "$BASE" ]]; then
    printf '%s' "$INPUT" | timeout 5 node "$BASE" 2>/dev/null || true
    printf '\n'   # base script emits no trailing newline; council rows must start clean
fi

# ── council rows: every failure path below ends in silence ───────────────────
[[ -f "$MUTE_FILE" ]] && exit 0
[[ -n "${COUNCIL_DISABLE:-}" ]] && exit 0

command -v python3 >/dev/null 2>&1 || exit 0

printf '%s' "$INPUT" | timeout 3 python3 "$HOME/.claude/hooks/council-render.py" "$CACHE_DIR" "$CACHE_TTL" 2>/dev/null
exit 0
