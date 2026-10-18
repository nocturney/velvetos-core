#!/usr/bin/env python3
"""Self-test (run by check-office-v2-phase2.py) for durable Office v2 repo-link intake (#595 AC5/AC6). Offline; temp copies only."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
REGISTRY = P2 / "candidate-registry-v0.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    li = _load("vf_link_intake_under_test", ROOT / "scripts" / "vf_office_v2_link_intake.py")
    p2 = _load("check_phase2_under_test", ROOT / "scripts" / "check-office-v2-phase2.py")
    real_before = REGISTRY.read_bytes()
    lanes = json.loads((P2 / "p0-shortlists-v0.json").read_text(encoding="utf-8-sig")).get("lanes", [])

    with tempfile.TemporaryDirectory(prefix="vf-link-intake-") as tmp:
        reg = Path(tmp) / "registry.json"
        rcpt = Path(tmp) / "receipts"
        shutil.copyfile(REGISTRY, reg)
        orig = json.loads(reg.read_text(encoding="utf-8"))
        orig_items = orig["items"]
        n0 = len(orig_items)

        # Round-trip: the committed registry formatting must be reproducible, or intake must refuse.
        if li.dump_registry(orig) != reg.read_text(encoding="utf-8"):
            fail("registry formatting does not round-trip")

        # Normalization.
        for raw in ("https://github.com/Example-Org/Some.Repo", "https://github.com/example-org/some.repo.git",
                    "github.com/EXAMPLE-ORG/some.repo/", "http://www.github.com/example-org/Some.Repo/tree/main/x",
                    " https://github.com/example-org/some.repo.git/ "):
            if li.parse_repo(raw) != ("example-org", "some.repo"):
                fail(f"normalization failed for {raw!r}")

        # 1. Unregistered credible link cannot silently disappear.
        url = "https://github.com/QA-Fixture-Org/Unregistered-Tool"
        r1 = li.intake(url, registry_path=reg, receipt_dir=rcpt, requested_by="https://github.com/nocturney/velvetos-core/issues/612")
        if r1["status"] != "REGISTERED" or not r1.get("receipt_path"):
            fail(f"unregistered link not registered with receipt: {r1}")
        after = json.loads(reg.read_text(encoding="utf-8"))
        if len(after["items"]) != n0 + 1 or after["candidate_count"] != n0 + 1:
            fail("candidate not appended or candidate_count not updated")
        entry = after["items"][-1]
        if entry["candidate_id"] != r1["candidate_ids"][0] or "https://github.com/qa-fixture-org/unregistered-tool" not in entry["evidence_refs"]:
            fail("receipt does not point to the appended candidate")
        schema = json.loads((P2 / "candidate-registry.schema.json").read_text(encoding="utf-8"))
        problems = li.validate_entry(entry, schema)
        if problems:
            fail(f"new entry violates registry schema: {problems}")
        if entry["lifecycle_state"] != "DISCOVERED" or entry["authority_role"] != "NONE" or entry["runtime_verification"] != "NOT_RUN":
            fail("intake must not promote or grant authority")
        if p2.evaluation_route_issues(after["items"], lanes):
            fail(f"phase2 evaluation_route rules rejected intake entry: {p2.evaluation_route_issues(after['items'], lanes)}")
        if not Path(r1["receipt_path"]).is_file() and not (ROOT / r1["receipt_path"]).is_file():
            fail("receipt file missing")

        # 2. Duplicates (case, .git, trailing slash, sub-path) add nothing.
        for dup in ("https://github.com/qa-fixture-org/unregistered-tool.git", "https://GITHUB.com/QA-FIXTURE-ORG/UNREGISTERED-TOOL/",
                    "https://github.com/qa-fixture-org/unregistered-tool/blob/main/README.md"):
            rd = li.intake(dup, registry_path=reg, receipt_dir=rcpt)
            if rd["status"] != "DUPLICATE" or rd.get("candidate_ids") != [entry["candidate_id"]]:
                fail(f"duplicate not detected for {dup}: {rd}")
        # A pre-existing historical candidate is also detected as a duplicate.
        hist = next(i for i in orig_items for ref in i["evidence_refs"]
                    if li.parse_repo(ref) and li.parse_repo(ref) not in li.SELF_REPOS)
        hist_url = next(r for r in hist["evidence_refs"] if li.parse_repo(r) and li.parse_repo(r) not in li.SELF_REPOS)
        hk = li.parse_repo(hist_url)
        rh = li.intake(f"https://github.com/{hk[0].upper()}/{hk[1]}.git/", registry_path=reg, receipt_dir=rcpt)
        if rh["status"] != "DUPLICATE" or hist["candidate_id"] not in rh["candidate_ids"]:
            fail(f"historical duplicate not detected: {rh}")
        if len(json.loads(reg.read_text(encoding="utf-8"))["items"]) != n0 + 1:
            fail("duplicate intake changed candidate count")

        # 3. Historical rows stay unchanged.
        final = json.loads(reg.read_text(encoding="utf-8"))
        if final["items"][:n0] != orig_items:
            fail("historical registry rows changed")
        for k in orig:
            if k not in {"items", "candidate_count", "updated_at"} and final[k] != orig[k]:
                fail(f"registry header field changed: {k}")

        # 4. Invalid input and write failure are explicit, never silent.
        bad = li.intake("https://gitlab.com/x/y", registry_path=reg, receipt_dir=rcpt)
        if bad["status"] != "INVALID_INPUT" or not bad.get("receipt_path"):
            fail("invalid input not receipted")
        selfref = li.intake("https://github.com/nocturney/velvetos-core/issues/595", registry_path=reg, receipt_dir=rcpt)
        if selfref["status"] != "INVALID_INPUT":
            fail("self-repo link must not become a candidate")
        broken = Path(tmp) / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        rb = li.intake("https://github.com/qa-fixture-org/other-tool", registry_path=broken, receipt_dir=rcpt)
        if rb["status"] != "NEEDS_SYNC" or not rb.get("receipt_path") or broken.read_text(encoding="utf-8") != "{not json":
            fail("unreadable registry must yield NEEDS_SYNC receipt without writing")
        reformatted = Path(tmp) / "reformatted.json"
        reformatted.write_text(json.dumps(orig, indent=4), encoding="utf-8")
        before_bytes = reformatted.read_bytes()
        rf = li.intake("https://github.com/qa-fixture-org/third-tool", registry_path=reformatted, receipt_dir=rcpt)
        if rf["status"] != "NEEDS_SYNC" or reformatted.read_bytes() != before_bytes:
            fail("non-round-tripping registry must not be rewritten")

        # 5. Dry run writes nothing.
        snap = reg.read_bytes()
        rdry = li.intake("https://github.com/qa-fixture-org/dry-tool", registry_path=reg, receipt_dir=rcpt, dry_run=True)
        if rdry["status"] != "REGISTERED" or reg.read_bytes() != snap or "receipt_path" in rdry:
            fail("dry run must not write registry or receipt")

        receipts = sorted(rcpt.glob("*.json"))
        if len(receipts) != 9:
            fail(f"expected 9 receipts, found {len(receipts)}")

    if REGISTRY.read_bytes() != real_before:
        fail("check mutated the committed registry")
    print("OK office-v2 link-intake registered=1 duplicates=4 invalid=2 needs_sync=2 dry_run=1 historical_rows=unchanged network=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
