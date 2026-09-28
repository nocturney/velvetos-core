#!/usr/bin/env python3
"""Guard the shared brand tokens and the 2026-09-28 rich-editorial owner amendment.

Checks (read-only):
1. packages/vfbrand/brand-tokens.json exists and has the required keys.
2. Accent samples are labelled as approximate samples from published posts.
3. fonts/logo are either real committed (git-tracked) files or explicitly 'missing: owner to supply'
   with null values; a font family or logo path is never guessed. Logo may also be
   'supplied_raster_non_transparent' (committed rasters + a note that transparent PNG/SVG is wanted).
4. The layout limits match VISUAL-DNA.json typography (single source of numbers).
5. The grid standard carries the 2026-09-28 amendment, marks the old minimal-typography
   rule and the text-heavy hard reject as SUPERSEDED (history kept), and still keeps the
   Product Truth anchors and the non-text rejects.
6. The brand doc, VISUAL-DNA and HyperFrames frame contract no longer state the old
   defaults as active rules (NO_TEXT preferred, orange default accent, engineering-lab look).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "packages" / "vfbrand" / "brand-tokens.json"
TOKENS_README = ROOT / "packages" / "vfbrand" / "README.md"
DNA = ROOT / "packages" / "vfom" / "VISUAL-DNA.json"
STD = ROOT / "packages" / "vfom" / "OWNER-APPROVED-GRID-STANDARD-2026-09-14.md"
BRAND = ROOT / "packages" / "vfbrand" / "BRAND-SOURCE-OF-TRUTH.md"
FRAME = ROOT / "packages" / "vfom" / "HYPERFRAMES-FRAME.md"
MISSING = "missing: owner to supply"
# Supplied states: files must be real, git-tracked repo files.
SUPPLIED_STATUSES = {"fonts": ("committed",), "logo": ("committed", "supplied_raster_non_transparent")}
PROVENANCE = "sampled from published posts 2026-09-28, approximate"
CTA = "לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם"
HEX = re.compile(r"^#[0-9a-f]{6}$")
REQUIRED_TOP = ("schema", "brand", "updated", "authority", "accents", "brandMark", "scene", "layout", "reel", "fonts", "logo")
REQUIRED_LAYOUT = ("headline", "accentRule", "subhead", "chips", "insets", "mobileReadability", "product")
EXPECTED_ACCENTS = {"copper": "#a86838", "antique_gold": "#a87838", "light_gold": "#f8c888", "amber": "#f8a848"}

problems: list[str] = []


def require(cond: bool, message: str) -> None:
    if not cond:
        problems.append(message)


def load(path: Path) -> dict:
    if not path.is_file():
        print(f"FAIL brand-tokens: missing {path.relative_to(ROOT)}", file=sys.stderr)
        raise SystemExit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL brand-tokens: invalid JSON {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(data, dict):
        print(f"FAIL brand-tokens: {path.relative_to(ROOT)} must be an object", file=sys.stderr)
        raise SystemExit(1)
    return data


def committed_file(rel: object) -> bool:
    if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return False
    if not (ROOT / rel).is_file():
        return False
    try:
        proc = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT,
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return True  # no git available: the on-disk file is the best evidence
    return proc.returncode == 0


def check_asset_block(name: str, block: object, value_keys: tuple[str, ...]) -> None:
    require(isinstance(block, dict), f"{name} must be an object")
    if not isinstance(block, dict):
        return
    status = block.get("status")
    files = block.get("files")
    require(isinstance(files, list), f"{name}.files must be a list")
    files = files if isinstance(files, list) else []
    if status == MISSING:
        require(not files, f"{name} is '{MISSING}' but lists files")
        for key in value_keys:
            require(block.get(key) is None, f"{name}.{key} must be null while {name} is missing (never guess)")
    elif status in SUPPLIED_STATUSES.get(name, ("committed",)):
        require(bool(files), f"{name} status {status} but no files listed")
        for rel in files:
            require(committed_file(rel), f"{name} file is not a committed repo file: {rel}")
        for key in value_keys:
            require(block.get(key) is not None, f"{name}.{key} must be set once {name} is committed")
        if status == "supplied_raster_non_transparent":
            require(bool(str(block.get("stillWanted", "")).strip()), f"{name}: non-transparent rasters need a stillWanted note (transparent PNG/SVG)")
        variants = block.get("variants")
        if variants is not None:
            require(isinstance(variants, list), f"{name}.variants must be a list")
            vpaths = [v.get("path") for v in variants if isinstance(v, dict)] if isinstance(variants, list) else []
            require(sorted(vpaths) == sorted(files), f"{name}.variants paths must match {name}.files")
            for v in variants if isinstance(variants, list) else []:
                if isinstance(v, dict) and committed_file(v.get("path")) and v.get("sha256"):
                    digest = hashlib.sha256((ROOT / v["path"]).read_bytes()).hexdigest()
                    require(digest == v["sha256"], f"{name} variant sha256 mismatch: {v['path']}")
    else:
        allowed = (MISSING,) + SUPPLIED_STATUSES.get(name, ("committed",))
        problems.append(f"{name}.status must be one of {allowed}, got {status!r}")


SVG_FILL = re.compile(r'fill="(#[0-9a-fA-F]{6})"')
TRACED_PROVENANCE = "traced from owner JPG, owner-approved 2026-09-28"


def check_fonts(block: object, ty: dict) -> None:
    """Fonts are either explicitly missing (nothing guessed) or committed OFL files with roles."""
    require(isinstance(block, dict), "fonts must be an object")
    if not isinstance(block, dict):
        return
    status = block.get("status")
    if status == MISSING:
        require(not block.get("files") and not block.get("families") and not block.get("roles"),
                "fonts are missing but list files/families/roles (never guess)")
        for key in ("headline", "body"):
            require(block.get(key) is None, f"fonts.{key} must be null while fonts are missing")
        return
    require(status == "committed", f"fonts.status must be '{MISSING}' or 'committed', got {status!r}")
    families = block.get("families") or []
    names = [f.get("family") for f in families if isinstance(f, dict)]
    max_fonts = ty.get("maxFonts")
    require(bool(names) and len(set(names)) == len(names), "fonts.families must list unique families")
    require(isinstance(max_fonts, int) and len(names) <= max_fonts, f"fonts: {len(names)} families exceed VISUAL-DNA maxFonts {max_fonts}")
    require(sorted(block.get("files") or []) == sorted(f.get("file") for f in families if isinstance(f, dict)), "fonts.files must match families[].file")
    for fam in families:
        if not isinstance(fam, dict):
            continue
        for key in ("file", "licenceFile"):
            rel = fam.get(key)
            require(committed_file(rel), f"font {fam.get('family')}: {key} is not a committed repo file: {rel}")
            sha_key = "sha256" if key == "file" else "licenceSha256"
            if committed_file(rel):
                require(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == fam.get(sha_key), f"font {fam.get('family')}: {sha_key} mismatch")
        if committed_file(fam.get("licenceFile")):
            require("SIL Open Font License" in (ROOT / fam["licenceFile"]).read_text(encoding="utf-8", errors="replace"), f"font {fam.get('family')}: licence file is not OFL")
    roles = block.get("roles") or {}
    for role in ("headline", "subhead"):
        r = roles.get(role) or {}
        require(r.get("family") in names and isinstance(r.get("weight"), int), f"fonts.roles.{role} must name a committed family and a numeric weight")
    for role, r in roles.items():
        require(isinstance(r, dict) and r.get("family") in names, f"fonts.roles.{role} uses a family that is not committed")
    dna_fonts = ty.get("verifiedBrandFonts")
    require(isinstance(dna_fonts, list) and sorted(dna_fonts) == sorted(names), "VISUAL-DNA typography.verifiedBrandFonts must match brand-tokens fonts.families")


def check_logo_vectors(block: object, gold_hex: object) -> None:
    if not isinstance(block, dict):
        return
    for v in block.get("variants") or []:
        if not isinstance(v, dict) or v.get("format") != "svg" or not committed_file(v.get("path")):
            continue
        svg = (ROOT / v["path"]).read_text(encoding="utf-8", errors="replace")
        fills = {f.lower() for f in SVG_FILL.findall(svg)}
        require(fills == {str(gold_hex).lower()}, f"logo SVG must use a single brand-gold fill {gold_hex}: {v['path']} has {sorted(fills)}")
        require(v.get("fill", "").lower() == str(gold_hex).lower(), f"logo SVG variant fill must equal brand gold: {v['path']}")
        require("<image" not in svg and "<text" not in svg, f"logo SVG must be pure vector paths (no embedded raster/text): {v['path']}")
        if v.get("provenance", "").startswith("traced"):
            require(v.get("provenance") == TRACED_PROVENANCE, f"traced logo SVG provenance must read '{TRACED_PROVENANCE}': {v['path']}")
            require(committed_file(str(v.get("tracedFrom", "")).split(" ")[0]), f"traced logo SVG must name its committed source raster: {v['path']}")


def check_tokens(tokens: dict, dna: dict) -> None:
    for key in REQUIRED_TOP:
        require(key in tokens, f"brand-tokens missing key {key}")
    accents = tokens.get("accents") or {}
    require(accents.get("provenance") == PROVENANCE, f"accents.provenance must be '{PROVENANCE}'")
    samples = accents.get("samples") or []
    got = {s.get("id"): s for s in samples if isinstance(s, dict)}
    for sid, hexval in EXPECTED_ACCENTS.items():
        s = got.get(sid)
        require(s is not None, f"accent sample {sid} missing")
        if s:
            require(isinstance(s.get("hex"), str) and bool(HEX.match(s["hex"])), f"accent {sid} hex malformed")
            require(s.get("hex") == hexval, f"accent {sid} hex drifted from the recorded sample {hexval}")
            require(s.get("status") == "sampled_approximate", f"accent {sid} must be labelled sampled_approximate")
    layout = tokens.get("layout") or {}
    for key in REQUIRED_LAYOUT:
        require(key in layout, f"layout missing {key}")
    head = layout.get("headline") or {}
    ty = dna.get("typography") or {}
    pairs = [
        (head.get("linesMin"), ty.get("headlineLinesMin"), "headline lines min"),
        (head.get("linesMax"), ty.get("headlineLinesMax"), "headline lines max"),
        (head.get("wordsMin"), ty.get("headlineWordsMin"), "headline words min"),
        (head.get("wordsMax"), ty.get("headlineWordsMax"), "headline words max"),
        (head.get("wordsMin"), ty.get("coverWordsMin"), "Reel cover words min"),
        (head.get("wordsMax"), ty.get("coverWordsMax"), "Reel cover words max"),
        ((layout.get("subhead") or {}).get("lines"), ty.get("subheadLines"), "subhead lines"),
        ((layout.get("subhead") or {}).get("wordsMax"), ty.get("subheadWordsMax"), "subhead words max"),
        ((layout.get("chips") or {}).get("max"), ty.get("chipsMax"), "chips max"),
        ((layout.get("insets") or {}).get("max"), ty.get("insetsMax"), "insets max"),
    ]
    for tok_val, dna_val, label in pairs:
        require(isinstance(tok_val, int) and tok_val == dna_val, f"{label}: brand-tokens {tok_val!r} != VISUAL-DNA {dna_val!r}")
    require((layout.get("chips") or {}).get("max") == 3, "chips max must stay 3 (owner amendment)")
    require((layout.get("insets") or {}).get("max") == 3, "insets max must stay 3 (owner amendment)")
    require((layout.get("subhead") or {}).get("lines") == 1, "subhead must be one line (owner amendment)")
    require((layout.get("product") or {}).get("textOverProduct") is False, "layout.product.textOverProduct must be false")
    require(ty.get("textOverProduct") is False, "VISUAL-DNA typography.textOverProduct must be false")
    require(ty.get("inventFont") is False, "VISUAL-DNA typography.inventFont must stay false")
    require((tokens.get("reel") or {}).get("endCardCta") == CTA, "reel.endCardCta drifted from the owner CTA")
    check_fonts(tokens.get("fonts"), ty)
    check_asset_block("logo", tokens.get("logo"), ())
    check_logo_vectors(tokens.get("logo"), ((tokens.get("brandMark") or {}).get("gold") or {}).get("hex"))
    mark = tokens.get("brandMark") or {}
    gold = mark.get("gold") or {}
    require(isinstance(gold.get("hex"), str) and bool(HEX.match(gold.get("hex", ""))), "brandMark.gold.hex malformed")
    require("approximate" in str(gold.get("provenance", "")) and gold.get("status") == "sampled_approximate", "brandMark.gold must be labelled as an approximate sample")
    logo_files = (tokens.get("logo") or {}).get("files") or []
    require(any(f in str(gold.get("provenance", "")) for f in logo_files) or (tokens.get("logo") or {}).get("status") == MISSING,
            "brandMark.gold provenance must name the committed logo file it was sampled from")
    if mark.get("navyHex") is None:
        require(str(mark.get("navyHexStatus", "")).startswith(MISSING), "brandMark.navyHex null requires navyHexStatus 'missing: owner to supply …'")
    require(TOKENS_README.is_file(), "packages/vfbrand/README.md missing")


def check_docs(dna: dict) -> None:
    std = STD.read_text(encoding="utf-8")
    require("## Owner amendment · rich editorial layout · 2026-09-28" in std, "grid standard lacks the 2026-09-28 owner amendment")
    for line in std.splitlines():
        if "Minimal typography" in line or "text-heavy template cards" in line or "Prefer `NO_TEXT`" in line:
            if "## Owner amendment" in line:
                continue
            if "supersedes" in line:
                continue
            require("SUPERSEDED" in line, f"old rule still active (not marked SUPERSEDED): {line.strip()[:90]}")
    require("Minimal typography" in std, "history lost: superseded 'Minimal typography' text was deleted")
    require("text-heavy template cards" in std, "history lost: superseded text-heavy reject was deleted")
    for needle in ("Retouch the photo, not the product", "DAHUaelaug0", "synthetic replacement of a real product",
                   "SAME_FRAME_CROP", "ALTERNATE_VERIFIED_SOURCE", "brand-tokens.json",
                   "text, chips or inset cards that cover the product or overpower it"):
        require(needle in std, f"grid standard lost {needle}")
    for num in ("2–4 lines", "3–7 words", "at most 12 words", "at most 3 chips", "at most 3 inset cards"):
        require(num in std, f"grid standard amendment lost limit '{num}'")

    brand = BRAND.read_text(encoding="utf-8")
    require("## Owner reconciliation · 2026-09-28" in brand, "brand doc lacks the 2026-09-28 reconciliation")
    require("Accent follows the product" in brand, "brand doc lacks 'accent follows the product'")
    require("logo and brand-mark identity" in brand, "brand doc must record navy/gold/ivory as logo and brand-mark identity")
    for line in brand.splitlines():
        if "orange as a default brand accent" in line:
            require("SUPERSEDED" in line, "brand doc still states the old orange rule as active")
    require("## Product Truth — non-negotiable" in brand, "brand doc lost Product Truth")

    frame = FRAME.read_text(encoding="utf-8")
    require("## Reel structure (default)" in frame, "HyperFrames frame contract lacks the Reel structure")
    require(CTA in frame, "HyperFrames frame contract lacks the owner end-card CTA")
    require("warm, real-feeling interior" in frame, "HyperFrames default look is not the warm-interior editorial look")
    for line in frame.splitlines():
        if "tactile engineering lab" in line:
            require("SUPERSEDED" in line, "HyperFrames still states the engineering-lab look as the active default")

    ty = dna.get("typography") or {}
    require("NO_TEXT is preferred" not in str(ty.get("ownerApprovedDirection", "")), "VISUAL-DNA still prefers NO_TEXT")
    require("orange" not in str((dna.get("colorPolicy") or {}).get("ownerApprovedDirection", "")).lower(), "VISUAL-DNA colour direction still names orange")
    archetype = dna.get("visualArchetype") or []
    require(bool(archetype) and "warm real-feeling interior" in str(archetype[0]), "VISUAL-DNA default archetype must be the warm interior")
    std_block = dna.get("ownerApprovedVisualStandard") or {}
    require("text_heavy_template_card_overpowering_product" not in (std_block.get("hardRejects") or []), "VISUAL-DNA still lists the superseded text-heavy reject")
    require("rejected_g004_canva_DAHUaelaug0" in (std_block.get("hardRejects") or []), "VISUAL-DNA lost the G004 reject")
    amendments = std_block.get("ownerAmendments") or []
    require(any(isinstance(a, dict) and a.get("date") == "2026-09-28" for a in amendments), "VISUAL-DNA lacks the 2026-09-28 amendment record")


def main() -> int:
    tokens = load(TOKENS)
    dna = load(DNA)
    check_tokens(tokens, dna)
    check_docs(dna)
    if problems:
        for p in problems:
            print(f"FAIL brand-tokens: {p}", file=sys.stderr)
        return 1
    print("OK brand-tokens: tokens complete, fonts/logo explicit, layout limits match VISUAL-DNA, 2026-09-28 amendment active with history kept")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
