#!/usr/bin/env bash
# Install The Agency (msitarzewski/agency-agents) as Cursor project rules.
# Does not send Instagram. Does not invent prices.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_REPO="${AGENCY_AGENTS_REPO:-https://github.com/msitarzewski/agency-agents.git}"
WORKDIR="${TMPDIR:-/tmp}/vf-hq-agency-agents-$$"
DEST="$ROOT/.cursor/rules"
DESK_RULE="$DEST/velvet-factory-desk.mdc"

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

if ! command -v git >/dev/null 2>&1; then
  echo "need git" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "need python3" >&2
  exit 1
fi

mkdir -p "$WORKDIR"
echo "=== clone $SRC_REPO ==="
git clone --depth 1 --single-branch "$SRC_REPO" "$WORKDIR/src"
SHA="$(git -C "$WORKDIR/src" rev-parse HEAD)"
SHA_SHORT="$(git -C "$WORKDIR/src" rev-parse --short HEAD)"
SRC_DATE="$(git -C "$WORKDIR/src" log -1 --format='%cs')"

echo "=== convert --tool cursor @ $SHA_SHORT ==="
"$WORKDIR/src/scripts/convert.sh" --tool cursor --parallel

desk_preserve=""
if [[ -f "$DESK_RULE" ]]; then
  desk_preserve="$WORKDIR/velvet-factory-desk.mdc"
  cp "$DESK_RULE" "$desk_preserve"
fi

echo "=== install Cursor rules -> $DEST ==="
(
  cd "$ROOT"
  "$WORKDIR/src/scripts/install.sh" --tool cursor --no-interactive
)

if [[ -n "$desk_preserve" ]]; then
  cp "$desk_preserve" "$DESK_RULE"
  echo "Preserved VF desk rule: $DESK_RULE"
fi

python3 - "$ROOT" "$WORKDIR/src" "$SHA" "$SHA_SHORT" "$SRC_DATE" <<'PY'
import json, re, sys
from datetime import date
from pathlib import Path

root = Path(sys.argv[1])
src = Path(sys.argv[2])
sha, sha_short, src_date = sys.argv[3], sys.argv[4], sys.argv[5]
rules = root / ".cursor" / "rules"
divs = json.loads((src / "divisions.json").read_text())["divisions"]

def is_agent(p: Path) -> bool:
    try:
        return p.read_text(encoding="utf-8", errors="replace").startswith("---")
    except OSError:
        return False

def field(text: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.*)$", text, re.M)
    if not m:
        return ""
    v = m.group(1).strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]
    return v

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

agents = []
for div in sorted(divs):
    d = src / div
    if not d.is_dir():
        continue
    for f in sorted(d.rglob("*.md")):
        if not is_agent(f):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        name = field(text, "name")
        desc = field(text, "description")
        if not name:
            continue
        slug = slugify(name)
        dest = rules / f"{slug}.mdc"
        if not dest.is_file():
            continue
        agents.append({
            "slug": slug,
            "name": name,
            "description": desc,
            "division": div,
            "divisionLabel": divs[div]["label"],
            "sourcePath": str(f.relative_to(src)),
            "ruleFile": f".cursor/rules/{slug}.mdc",
            "installed": True,
        })

catalog = {
    "name": "agency-agents",
    "title": "The Agency — Cursor rules",
    "source": "https://github.com/msitarzewski/agency-agents",
    "sourceCommit": sha,
    "sourceCommitShort": sha_short,
    "sourceDate": src_date,
    "installedAt": date.today().isoformat(),
    "tool": "cursor",
    "installPath": ".cursor/rules",
    "alwaysApply": False,
    "agentCount": len(agents),
    "divisionCounts": {k: sum(1 for a in agents if a["division"] == k) for k in sorted(divs)},
    "agents": agents,
}
(root / ".cursor" / "agency-agents.json").write_text(
    json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
)

lines = [
    "# The Agency — installed Cursor rules",
    "",
    f"Source: [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) @ `{sha_short}`",
    "",
    f"**{len(agents)} agents** installed as project rules in `.cursor/rules/`.",
    "Each Agency rule has `alwaysApply: false` — mention it with `@slug` when you need that specialist.",
    "",
    "Velvet Factory **desk** (packs + live tools): [`docs/AGENCY-TOOLS.md`](AGENCY-TOOLS.md), [`.cursor/vf-desk.json`](../.cursor/vf-desk.json).",
    "Always-on router: `.cursor/rules/velvet-factory-desk.mdc`. Warehouse specialists stay off a print job unless asked.",
    "",
    "This HQ still does not send Instagram. Live send stays on Grok Bot.",
    "Do not invent prices or Insights.",
    "",
    "Refresh:",
    "",
    "```bash",
    "./scripts/install-agency-agents.sh",
    "```",
    "",
]
for div in sorted(divs):
    group = [a for a in agents if a["division"] == div]
    if not group:
        continue
    lines.append(f"## {divs[div]['label']} ({len(group)})")
    lines.append("")
    lines.append("| Agent | Slug | Specialty |")
    lines.append("|---|---|---|")
    for a in group:
        desc = a["description"].replace("|", "\\|")
        lines.append(f"| {a['name']} | `@{a['slug']}` | {desc} |")
    lines.append("")

(root / "docs" / "AGENCY-AGENTS.md").write_text("\n".join(lines) + "\n")
print(f"catalog: {len(agents)} agents @ {sha_short}")
PY

count="$(find "$DEST" -maxdepth 1 -name '*.mdc' | wc -l | tr -d ' ')"
echo
echo "Installed $count Cursor rules from $SRC_REPO @ $SHA_SHORT"
echo "Catalog: .cursor/agency-agents.json"
echo "Roster:  docs/AGENCY-AGENTS.md"
