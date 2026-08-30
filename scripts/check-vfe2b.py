#!/usr/bin/env python3
"""Check vfe2b catalog against HQ packs and crew files. No network. No send."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
CATALOG = ROOT / "packages" / "vfe2b" / "catalog.json"
CREWS = ROOT / "packages" / "vfe2b" / "crews"
RUN_CARDS = ROOT / "packages" / "vfe2b" / "fixtures" / "run-cards.json"
RUN_SKILL = ROOT / ".cursor" / "skills" / "vf-run" / "SKILL.md"
STATE_LINE = re.compile(r"^מצב:\s*(\S+)\s*$", re.MULTILINE)
VERDICTS = {"embed", "later", "skip"}
REQUIRED_CREWS = {
    "crews/morning-brief.md",
    "crews/research.md",
    "crews/inquiry.md",
    "crews/content.md",
    "crews/books-data.md",
    "crews/run.md",
}
RUN_OUTCOMES = ("worker_done", "escalation", "decision_gate")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_run_card(card: str) -> str:
    """Return the single run outcome, or raise ValueError."""
    found = STATE_LINE.findall(card)
    if len(found) != 1:
        raise ValueError("exactly-one-state")
    state = found[0]
    if state not in RUN_OUTCOMES:
        raise ValueError("unknown-state")
    return state


def check_run_card_fixtures() -> int:
    if not RUN_CARDS.is_file():
        fail(f"missing {RUN_CARDS}")
    fixtures = json.loads(RUN_CARDS.read_text())
    ok_rows = fixtures.get("ok") or []
    fail_rows = fixtures.get("fail") or []
    if len(ok_rows) < 3 or len(fail_rows) < 2:
        fail("run-cards fixture too small")
    for row in ok_rows:
        name = row.get("name") or "?"
        try:
            state = parse_run_card(row["card"])
        except ValueError as exc:
            fail(f"ok card {name}: {exc}")
        if state != row.get("expect"):
            fail(f"ok card {name}: got {state} want {row.get('expect')}")
    for row in fail_rows:
        name = row.get("name") or "?"
        want = row.get("reason")
        try:
            parse_run_card(row["card"])
        except ValueError as exc:
            if str(exc) != want:
                fail(f"fail card {name}: {exc} want {want}")
            continue
        fail(f"fail card {name}: expected to reject")
    return len(ok_rows) + len(fail_rows)


def main() -> None:
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST}")
    if not CATALOG.is_file():
        fail(f"missing {CATALOG}")

    manifest = json.loads(MANIFEST.read_text())
    catalog = json.loads(CATALOG.read_text())
    pack_names = {p["name"] for p in manifest["packs"]}

    if catalog.get("name") != "vfe2b":
        fail("catalog name must be vfe2b")
    listed = catalog.get("source", {}).get("listedCount")
    if listed != 209:
        fail(f"listedCount expected 209, got {listed}")

    picks = catalog.get("picks") or []
    if len(picks) < 20:
        fail(f"expected at least 20 picks, got {len(picks)}")

    crew_refs: set[str] = set()
    embed_count = 0
    for i, pick in enumerate(picks):
        name = pick.get("name") or f"#{i}"
        verdict = pick.get("verdict")
        if verdict not in VERDICTS:
            fail(f"{name}: verdict {verdict!r} not in {sorted(VERDICTS)}")
        if verdict == "embed":
            embed_count += 1
        packs = pick.get("packs") or []
        if not packs:
            fail(f"{name}: no packs")
        for p in packs:
            if p not in pack_names:
                fail(f"{name}: unknown pack {p!r}")
        crew = pick.get("crew")
        if not crew:
            fail(f"{name}: missing crew")
        crew_refs.add(crew)
        crew_path = ROOT / "packages" / "vfe2b" / crew
        if not crew_path.is_file():
            fail(f"{name}: crew file missing {crew}")

    if embed_count < 10:
        fail(f"expected at least 10 embed picks, got {embed_count}")
    missing_crews = REQUIRED_CREWS - crew_refs
    if missing_crews:
        fail(f"crews not referenced: {sorted(missing_crews)}")

    on_disk = {f"crews/{p.name}" for p in CREWS.glob("*.md")}
    extra = on_disk - REQUIRED_CREWS
    if extra:
        fail(f"unexpected crew files: {sorted(extra)}")
    if not on_disk == REQUIRED_CREWS:
        fail(f"crew files mismatch disk={sorted(on_disk)}")

    locks = set(catalog.get("locks") or [])
    for need in (
        "no-send-instagram",
        "no-send-gmail",
        "no-invented-prices",
        "no-invented-insights",
        "no-second-ade",
    ):
        if need not in locks:
            fail(f"missing lock {need}")

    run_text = (CREWS / "run.md").read_text()
    for token in RUN_OUTCOMES:
        if token not in run_text:
            fail(f"crews/run.md missing outcome {token}")
    if "stablyai/orca" not in run_text and "github.com/stablyai/orca" not in run_text:
        fail("crews/run.md must cite stablyai/orca")

    orca = next((p for p in picks if p.get("name") == "Orca"), None)
    if not orca:
        fail("catalog missing Orca pick")
    if orca.get("crew") != "crews/run.md":
        fail("Orca pick must use crews/run.md")
    if orca.get("verdict") != "embed":
        fail("Orca pick must be embed (pattern), not an ADE install")

    if "vfe2b" not in pack_names:
        fail("vfe2b missing from packages/manifest.json")

    if not RUN_SKILL.is_file():
        fail(f"missing {RUN_SKILL}")
    skill_text = RUN_SKILL.read_text()
    for token in RUN_OUTCOMES:
        if token not in skill_text:
            fail(f"vf-run skill missing outcome {token}")
    if "Do not install Orca" not in skill_text:
        fail("vf-run skill must refuse an Orca install")

    cards = check_run_card_fixtures()

    print(
        f"OK picks={len(picks)} embed={embed_count} "
        f"crews={len(REQUIRED_CREWS)} packs={len(pack_names)} "
        f"listed={listed} run_cards={cards}"
    )


if __name__ == "__main__":
    main()
