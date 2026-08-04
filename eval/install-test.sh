#!/usr/bin/env bash
# Clean-room install eval. Binary assertions, no judgment, no rubric.
#
# Everything the DX review scored 8/10 was ASSERTED, not measured. This is the
# measurement: a throwaway HOME with no ~/.claude, run install.sh, and check that
# what the README promises actually happens. Exits non-zero on any failure.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
ok(){ printf '  \033[32m✓\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
no(){ printf '  \033[31m✗\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
chk(){ if eval "$2" >/dev/null 2>&1; then ok "$1"; else no "$1"; fi; }

SANDBOX=$(mktemp -d); trap 'rm -rf "$SANDBOX"' EXIT
echo "clean-room: $SANDBOX"

# ── case 1: virgin machine, no ~/.claude at all ─────────────────────────────
echo; echo "case 1 — no ~/.claude"
H1="$SANDBOX/virgin"; mkdir -p "$H1"
HOME="$H1" bash "$REPO/install.sh" >"$SANDBOX/c1.log" 2>&1 || no "install.sh exited non-zero"
chk "hooks dir created"            "[ -d '$H1/.claude/hooks' ]"
for f in council-retrieve.py council-render.py council-statusline.sh council-query.py; do
  chk "shipped $f"                 "[ -f '$H1/.claude/hooks/$f' ]"
done
chk "hooks are executable"         "[ -x '$H1/.claude/hooks/council-statusline.sh' ]"
chk "corpus installed"             "[ -f '$H1/.claude/council/corpus.json' ]"
chk "settings.json is valid JSON"  "python3 -c \"import json;json.load(open('$H1/.claude/settings.json'))\""
chk "statusLine wired"             "python3 -c \"import json;s=json.load(open('$H1/.claude/settings.json'));raise SystemExit(0 if 'council-statusline' in s['statusLine']['command'] else 1)\""
chk "Stop hook wired"              "python3 -c \"import json;s=json.load(open('$H1/.claude/settings.json'));raise SystemExit(0 if any('council-retrieve' in h['command'] for g in s['hooks']['Stop'] for h in g['hooks']) else 1)\""

# ── case 2: the promise in the README — a query returns a passage ───────────
echo; echo "case 2 — README hello world"
OUT=$(COUNCIL_CORPUS="$H1/.claude/council/corpus.json" HOME="$H1" \
      python3 "$H1/.claude/hooks/council-query.py" "should we build the team plan before launch" 2>&1)
chk "query runs from the installed location" "[ \$? -eq 0 ]"
chk "query returns a scored pattern"         "printf '%s' \"\$OUT\" | grep -qE '^ *1\. *\[ *[0-9]+\.[0-9]+\]'"
chk "query reports corpus size"              "printf '%s' \"\$OUT\" | grep -q 'corpus: 107 patterns'"

# ── case 3: an existing statusLine must be preserved, not clobbered ─────────
echo; echo "case 3 — existing statusLine"
H3="$SANDBOX/existing"; mkdir -p "$H3/.claude"
printf '{"statusLine":{"type":"command","command":"my-own-bar"},"outputStyle":"Direct"}\n' > "$H3/.claude/settings.json"
HOME="$H3" bash "$REPO/install.sh" >/dev/null 2>&1
chk "prior statusLine saved for rollback" "[ -f '$H3/.claude/settings.json.prev-statusline' ] && grep -q 'my-own-bar' '$H3/.claude/settings.json.prev-statusline'"
chk "unrelated settings preserved"        "python3 -c \"import json;s=json.load(open('$H3/.claude/settings.json'));raise SystemExit(0 if s.get('outputStyle')=='Direct' else 1)\""
chk "a backup was written"                "ls '$H3/.claude/settings.json.bak-'* >/dev/null 2>&1"

# ── case 4: idempotence — running twice must not double-wire ────────────────
echo; echo "case 4 — run twice"
HOME="$H1" bash "$REPO/install.sh" >/dev/null 2>&1
N=$(python3 -c "import json;s=json.load(open('$H1/.claude/settings.json'));print(sum('council-retrieve' in h['command'] for g in s['hooks']['Stop'] for h in g['hooks']))")
chk "Stop hook wired exactly once (got $N)" "[ '$N' = '1' ]"

# ── case 5: the status line must never go dark ──────────────────────────────
echo; echo "case 5 — status line degradation"
EV='{"session_id":"eval-probe","model":{"display_name":"Opus"},"workspace":{"current_dir":"/tmp"}}'
chk "renders with no cache"      "HOME='$H1' COLUMNS=100 bash '$H1/.claude/hooks/council-statusline.sh' <<<'$EV'"
chk "renders when muted"         "touch '$H1/.claude/council-muted'; HOME='$H1' bash '$H1/.claude/hooks/council-statusline.sh' <<<'$EV'; rm -f '$H1/.claude/council-muted'"
chk "survives garbage stdin"     "HOME='$H1' bash '$H1/.claude/hooks/council-statusline.sh' <<<'not json'"
chk "survives a corrupt cache"   "echo xx > \"\${TMPDIR:-/tmp}/council-\$(python3 -c \"import hashlib;print(hashlib.sha1(b'eval-probe').hexdigest()[:16])\").json\"; HOME='$H1' bash '$H1/.claude/hooks/council-statusline.sh' <<<'$EV'"

echo; printf 'PASS %d · FAIL %d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
