#!/usr/bin/env bash
# the-council installer. Idempotent, backs up settings.json, prints what it did.
set -euo pipefail
H="${HOME}/.claude"; SRC="$(cd "$(dirname "$0")" && pwd)"
echo "the-council → $H"
mkdir -p "$H/hooks" "$H/council"
cp "$SRC"/install/council-{retrieve.py,render.py,statusline.sh,query.py} "$H/hooks/"
chmod +x "$H/hooks"/council-*
cp "$SRC/corpus.json" "$H/council/corpus.json"
echo "  ✓ hooks + corpus installed"
S="$H/settings.json"; [ -f "$S" ] || echo '{}' > "$S"
cp "$S" "$S.bak-$(date +%Y%m%d-%H%M%S)"
python3 - "$S" <<'PY'
import json,sys
p=sys.argv[1]; s=json.load(open(p))
base=s.get("statusLine",{}).get("command","")
if "council-statusline" not in base:
    if base: open(f"{p}.prev-statusline","w").write(base)
    s["statusLine"]={"type":"command","command":'bash "$HOME/.claude/hooks/council-statusline.sh"'}
g={"matcher":"","hooks":[{"type":"command","command":'python3 "$HOME/.claude/hooks/council-retrieve.py"',"timeout":10}]}
if not any("council-retrieve" in h.get("command","") for grp in s.get("hooks",{}).get("Stop",[]) for h in grp.get("hooks",[])):
    s.setdefault("hooks",{}).setdefault("Stop",[]).append(g)
json.dump(s,open(p,"w"),indent=2); open(p,"a").write("\n")
print("  ✓ settings.json wired (backup written)")
PY
echo
echo "Done. Start a new session — a passage surfaces under your status line when one applies."
echo "Silence is the common case and is correct. Mute: touch ~/.claude/council-muted"
