#!/usr/bin/env bash
# Vendor a curated subset of Corey Haines marketing skills into packages/vfmskill/.
# Does not dump the SaaS CMO roster into .cursor/skills/.
# Does not send Instagram. Does not invent prices.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_REPO="${MARKETING_SKILLS_REPO:-https://github.com/coreyhaines31/marketingskills.git}"
WORKDIR="${TMPDIR:-/tmp}/vf-hq-marketingskills-$$"
DEST="$ROOT/packages/vfmskill/vendor"
CATALOG="$ROOT/packages/vfmskill/catalog.json"

# Skills that help a pickup-only 3D-print studio. SaaS / ads / send stay out.
EMBED_SKILLS=(
  product-marketing
  copywriting
  copy-editing
  social
  customer-research
  offers
  marketing-psychology
  sales-enablement
  content-strategy
  image
  video
  competitor-profiling
  marketing-ideas
  marketing-plan
  launch
)

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

echo "=== copy ${#EMBED_SKILLS[@]} embed skills -> $DEST ==="
rm -rf "$DEST"
mkdir -p "$DEST"
for skill in "${EMBED_SKILLS[@]}"; do
  src="$WORKDIR/src/skills/$skill"
  if [[ ! -d "$src" ]]; then
    echo "missing skill in source: $skill" >&2
    exit 1
  fi
  mkdir -p "$DEST/$skill"
  # Skip evals — they are the upstream test harness, not studio procedure.
  cp -a "$src/." "$DEST/$skill/"
  rm -rf "$DEST/$skill/evals"
  echo "  $skill"
done

if [[ -f "$WORKDIR/src/LICENSE" ]]; then
  cp "$WORKDIR/src/LICENSE" "$DEST/LICENSE"
fi

python3 - "$ROOT" "$SHA" "$SHA_SHORT" "$SRC_DATE" "${EMBED_SKILLS[@]}" <<'PY'
import json, sys
from datetime import date
from pathlib import Path

root = Path(sys.argv[1])
sha, sha_short, src_date = sys.argv[2], sys.argv[3], sys.argv[4]
embed = list(sys.argv[5:])
catalog_path = root / "packages" / "vfmskill" / "catalog.json"
catalog = json.loads(catalog_path.read_text())
catalog["source"]["commit"] = sha
catalog["source"]["commitShort"] = sha_short
catalog["source"]["sourceDate"] = src_date
catalog["source"]["vendoredAt"] = date.today().isoformat()
catalog["source"]["vendorPath"] = "packages/vfmskill/vendor"
catalog["embedCount"] = len(embed)
catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")

vendor_md = root / "packages" / "vfmskill" / "VENDOR.md"
vendor_md.write_text(
    "\n".join(
        [
            "# vfmskill vendor pin",
            "",
            f"Source: [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) @ `{sha_short}`",
            "",
            f"- Full SHA: `{sha}`",
            f"- Upstream date: {src_date}",
            f"- Vendored: {date.today().isoformat()}",
            f"- License: MIT (see `vendor/LICENSE`)",
            f"- Skills copied: {len(embed)} (evals skipped)",
            "",
            "Refresh:",
            "",
            "```bash",
            "./scripts/install-marketing-skills.sh",
            "python3 scripts/check-vfmskill.py",
            "```",
            "",
            "Do not dump the full 50-skill SaaS CMO set into `.cursor/skills/`.",
            "HQ overlay and desk laws win over upstream playbooks.",
            "This HQ does not send Instagram. Do not invent ₪ or Insights.",
            "",
        ]
    )
    + "\n"
)
print(f"catalog pinned @ {sha_short}; embed={len(embed)}")
PY

echo
echo "Vendored ${#EMBED_SKILLS[@]} skills from $SRC_REPO @ $SHA_SHORT"
echo "Tree:    packages/vfmskill/vendor/"
echo "Pin:     packages/vfmskill/VENDOR.md"
echo "Catalog: packages/vfmskill/catalog.json"
