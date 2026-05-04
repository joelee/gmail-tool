#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
REPO_ROOT="$(readlink -f "$SCRIPT_DIR/..")"

usage() {
  printf 'Usage: %s <coverage-json> [badge-json]\n' "$0"
  printf 'Example: %s coverage.json .github/badges/coverage.json\n' "$0"
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

COVERAGE_JSON="$1"
BADGE_JSON="${2:-$REPO_ROOT/.github/badges/coverage.json}"

[[ -f "$COVERAGE_JSON" ]] || fail "coverage JSON not found: $COVERAGE_JSON"

python - <<'PY' "$COVERAGE_JSON" "$BADGE_JSON"
import json
import math
import sys
from pathlib import Path

coverage_path = Path(sys.argv[1])
badge_path = Path(sys.argv[2])

coverage_data = json.loads(coverage_path.read_text(encoding="utf-8"))
percent = float(coverage_data["totals"]["percent_covered_display"])
rounded = int(math.floor(percent + 0.5))

if rounded >= 90:
    color = "brightgreen"
elif rounded >= 80:
    color = "green"
elif rounded >= 70:
    color = "yellowgreen"
elif rounded >= 60:
    color = "yellow"
else:
    color = "red"

badge = {
    "schemaVersion": 1,
    "label": "coverage",
    "message": f"{rounded}%",
    "color": color,
}

badge_path.parent.mkdir(parents=True, exist_ok=True)
badge_path.write_text(json.dumps(badge, indent=2) + "\n", encoding="utf-8")
PY

printf 'Updated %s\n' "$BADGE_JSON"
