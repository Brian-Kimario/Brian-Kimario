#!/usr/bin/env bash
# Regenerate every static panel. Stats are built by CI (they need a token).
set -euo pipefail
cd "$(dirname "$0")"

python3 gen_hero.py
python3 gen_panels.py

# Fail loudly on malformed XML rather than shipping a broken <img> to the README.
python3 - <<'PY'
import glob, sys, xml.dom.minidom
bad = []
for f in sorted(glob.glob("../assets/*.svg")):
    try:
        xml.dom.minidom.parse(f)
        print(f"  ok  {f}")
    except Exception as e:
        bad.append(f"{f}: {e}")
if bad:
    sys.exit("invalid SVG:\n  " + "\n  ".join(bad))
PY
