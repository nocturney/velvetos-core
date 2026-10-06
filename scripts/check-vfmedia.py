#!/usr/bin/env python3
"""Validate the locked VelvetOS shared media vault. No network. No Drive writes."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "MEDIA-VAULT.md"
SWC = ROOT / "docs" / "SHARED-WORK-COORDINATION.md"
PACK = ROOT / "packages" / "vfmedia"
CATALOG = PACK / "catalog.json"
SCHEMA = PACK / "catalog.schema.json"
FOLDERS = PACK / "FOLDERS.json"
CATALOG_MD = PACK / "CATALOG.md"
LOCK = PACK / "LOCK.md"
SKILL = PACK / "SKILL.md"
ORIGIN = PACK / "ORIGIN.md"
CLI = ROOT / "scripts" / "vfmedia.py"
INTAKE_MD = PACK / "INTAKE.md"
INTAKE_STATE = PACK / "state" / "intake-runner.json"
INTAKE_WORKFLOW = ROOT / ".github" / "workflows" / "vfmedia-intake.yml"
EVENTS_CATALOG = ROOT / "packages" / "velvetos" / "schema" / "events.catalog.json"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
MANIFEST = ROOT / "packages" / "manifest.json"
AGENTS = PACK / "AGENTS.md"
VELVETOS_PACK = ROOT / "packages" / "velvetos"
MEM = ROOT / "packages" / "vfmem" / "catalog.json"
SLOTS = ROOT / "packages" / "vfops" / "hq" / "BRIEF-SLOTS.md"

ROOT_ID = "1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv"
FOLDER_IDS = {
    "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
    "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6",
    "13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a",
    "1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib",
    "19A-_QOSvII-CvxjRMpQ2j5Z46UAjeNep",
}
NEEDLES_DOCS = (
    ROOT_ID,
    "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
    "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6",
    "13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a",
    "1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib",
    "19A-_QOSvII-CvxjRMpQ2j5Z46UAjeNep",
    "05 - פורסם",
    "קטלוג אחד",
    "תפעול",
    "העלאה ≠ אישור",
    "תיקיית «מאושר לפרסום» לבד ≠ הוכחת אישור",
    "לא ממציאים ₪",
    "אין שינוי הרשאות שיתוף",
    "GrokBot",
    "Cursor",
    "Drive MCP",
)
NEEDLES_SWC = (
    "vfmedia",
    "Drive MCP",
    "תפעול",
    "Cursor",
    "GrokBot",
)
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def assert_no_ils(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for m in ILS_NUMBER.finditer(text):
        snippet = text[max(0, m.start() - 20) : m.end() + 8]
        if "X ₪" in snippet:
            continue
        if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
            continue
        fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")


def canonical_tool_desk() -> Path:
    if str(VELVETOS_PACK) not in sys.path:
        sys.path.insert(0, str(VELVETOS_PACK))
    from instance_resolver import resolve_surface  # type: ignore
    try:
        return resolve_surface(ROOT, "toolDesk", instance_id="velvet-factory", env={})
    except Exception as exc:
        fail(f"cannot resolve canonical VF tool desk: {exc}")
    raise AssertionError("unreachable")


def main() -> None:
    desk_path = canonical_tool_desk()
    for path in (
        DOCS,
        SWC,
        CATALOG,
        SCHEMA,
        FOLDERS,
        CATALOG_MD,
        LOCK,
        SKILL,
        ORIGIN,
        CLI,
        INTAKE_MD,
        INTAKE_STATE,
        INTAKE_WORKFLOW,
        EVENTS_CATALOG,
        LOOP,
        MANIFEST,
        AGENTS,
        desk_path,
        MEM,
        SLOTS,
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    for path in (DOCS, CATALOG_MD, LOCK, SKILL, ORIGIN, CATALOG, FOLDERS, SWC, SLOTS):
        assert_no_ils(path)

    docs = DOCS.read_text(encoding="utf-8")
    for needle in NEEDLES_DOCS:
        if needle not in docs:
            fail(f"MEDIA-VAULT.md missing {needle!r}")
    if "מק״ט" not in docs and "SKU" not in docs:
        fail("MEDIA-VAULT.md must forbid invented SKUs")

    swc = SWC.read_text(encoding="utf-8")
    for needle in NEEDLES_SWC:
        if needle not in swc:
            fail(f"SHARED-WORK-COORDINATION.md missing {needle!r}")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("items") not in ([],):
        # Rows are allowed later; each must still pass vfmedia.py validate.
        pass
    if catalog.get("oneCatalog") is not True:
        fail("catalog.json must lock oneCatalog")
    blob = json.dumps(catalog, ensure_ascii=False)
    if re.search(r'"sku"', blob, re.I):
        fail("catalog.json must not invent SKU fields")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    item_req = ((schema.get("$defs") or {}).get("mediaItem") or {}).get("required") or []
    for field in (
        "sourceFile",
        "viewDescription",
        "uploadedAt",
        "productLink",
        "status",
        "assignee",
        "derivativeIds",
        "sourceLinks",
        "versionApproval",
    ):
        if field not in item_req:
            fail(f"catalog.schema.json mediaItem missing {field}")

    item_props = ((schema.get("$defs") or {}).get("mediaItem") or {}).get("properties") or {}
    if "truth" not in item_props:
        fail("catalog.schema.json mediaItem must expose optional truth metadata")
    if "publication" not in item_props:
        fail("catalog.schema.json mediaItem must expose publication evidence")
    status_enum = ((item_props.get("status") or {}).get("enum") or [])
    if "published" not in status_enum:
        fail("catalog.schema.json status must include published")
    truth_spec = ((schema.get("$defs") or {}).get("assetTruth") or {})
    if "truthLevel" not in (truth_spec.get("required") or []):
        fail("catalog.schema.json assetTruth must require truthLevel")

    vfmedia_spec = importlib.util.spec_from_file_location("vfmedia_sensor_target", CLI)
    if vfmedia_spec is None or vfmedia_spec.loader is None:
        fail("cannot load scripts/vfmedia.py for Asset Truth regression")
    vfmedia_module = importlib.util.module_from_spec(vfmedia_spec)
    vfmedia_spec.loader.exec_module(vfmedia_module)

    class TruthValidationError(Exception):
        pass

    vfmedia_module.fail = lambda message: (_ for _ in ()).throw(TruthValidationError(message))
    try:
        vfmedia_module.validate_truth_block(
            {"truth": {"truthLevel": "verified_real", "rightsStatus": "approved", "usableFor": ["hero"]}},
            0,
            schema,
        )
    except TruthValidationError as exc:
        fail(f"vfmedia Asset Truth regression rejected canonical metadata: {exc}")

    for invalid_truth in (
        {"truthLevel": "verified_real", "inventedField": "nope"},
        {"truthLevel": "not-a-canonical-level"},
    ):
        try:
            vfmedia_module.validate_truth_block({"truth": invalid_truth}, 0, schema)
        except TruthValidationError:
            pass
        else:
            fail(f"vfmedia Asset Truth regression accepted invalid metadata: {invalid_truth}")

    class PublicationValidationError(Exception):
        pass

    vfmedia_module.fail = lambda message: (_ for _ in ()).throw(PublicationValidationError(message))
    canonical_derivative = {
        "id": "drive-published-derivative",
        "url": "https://drive.google.com/file/d/drive-published-derivative/view",
    }
    canonical_published = {
        "status": "published",
        "derivativeIds": [canonical_derivative],
        "publication": {
            "state": "published_verified",
            "provider": "instagram",
            "mediaId": "17841400000000000",
            "permalink": "https://www.instagram.com/p/EXAMPLE/",
            "publishedAt": "2026-09-19T12:00:00Z",
            "verifiedAt": "2026-09-19T12:00:10Z",
            "publishedDerivative": canonical_derivative,
        },
    }
    try:
        vfmedia_module.validate_publication_block(canonical_published, 0)
    except PublicationValidationError as exc:
        fail(f"vfmedia published regression rejected canonical evidence: {exc}")

    invalid_publication_items = (
        {"status": "published", "derivativeIds": [], "publication": None},
        {
            "status": "published",
            "derivativeIds": [canonical_derivative],
            "publication": {
                **canonical_published["publication"],
                "state": "publish_pending_verification",
            },
        },
        {
            "status": "approved",
            "derivativeIds": [canonical_derivative],
            "publication": canonical_published["publication"],
        },
        {
            "status": "published",
            "derivativeIds": [],
            "publication": canonical_published["publication"],
        },
    )
    for invalid_item in invalid_publication_items:
        try:
            vfmedia_module.validate_publication_block(invalid_item, 0)
        except PublicationValidationError:
            pass
        else:
            fail(f"vfmedia published regression accepted invalid evidence: {invalid_item}")

    folders = json.loads(FOLDERS.read_text(encoding="utf-8"))
    if folders.get("sharePermissionChanges") != "forbidden":
        fail("FOLDERS.json must forbid share permission changes")
    if folders.get("deleteFiles") != "forbidden":
        fail("FOLDERS.json must forbid deletes")
    ids = {row["id"] for row in folders.get("stages") or []}
    if ids != FOLDER_IDS:
        fail(f"FOLDERS.json ids mismatch {ids}")

    lock = LOCK.read_text(encoding="utf-8")
    for needle in ("קטלוג אחד", "העלאה ≠ אישור", "לא ממציאים", "שיתוף"):
        if needle not in lock:
            fail(f"LOCK.md missing {needle!r}")

    origin = ORIGIN.read_text(encoding="utf-8")
    if "hq-native" not in origin:
        fail("ORIGIN.md must stay hq-native")
    if re.search(r"christian-velvet/tmp-", origin):
        fail("ORIGIN.md must not invent an Origin slug")

    loop = json.loads(LOOP.read_text(encoding="utf-8"))
    ids_loop = [p["id"] for p in loop.get("packs") or []]
    if "vfmedia" not in ids_loop:
        fail("LOOP.json must consume vfmedia")
    media = next(p for p in loop["packs"] if p["id"] == "vfmedia")
    if "vfmedia.py" not in (media.get("consume") or ""):
        fail("vfmedia consume must be vfmedia.py validate")

    packs = {p["name"] for p in json.loads(MANIFEST.read_text(encoding="utf-8")).get("packs") or []}
    if "vfmedia" not in packs:
        fail("vfmedia missing from packages/manifest.json")

    if "check-vfmedia.py" not in AGENTS.read_text(encoding="utf-8"):
        fail("AGENTS.md sensor table must list check-vfmedia.py")

    desk = json.loads(desk_path.read_text(encoding="utf-8"))
    ops = next((s for s in desk.get("seats") or [] if s.get("id") == "ops"), None)
    if not ops or "vfmedia" not in (ops.get("packs") or []):
        fail("desk ops seat must include vfmedia")
    drive = (desk.get("tools") or {}).get("drive") or {}
    if ROOT_ID not in json.dumps(drive, ensure_ascii=False):
        fail("desk drive tool must name the locked vault root id")

    mem = json.loads(MEM.read_text(encoding="utf-8"))
    if not any(r.get("pack") == "vfmedia" for r in mem.get("routes") or []):
        fail("vfmem catalog must route media vault to vfmedia")

    if "vfmedia" not in SLOTS.read_text(encoding="utf-8"):
        fail("BRIEF-SLOTS.md must mention vfmedia")
    slots = SLOTS.read_text(encoding="utf-8")
    if "intake" not in slots.lower() and "קליטה" not in slots:
        fail("BRIEF-SLOTS.md must mention media intake phases / intake")

    intake_md = INTAKE_MD.read_text(encoding="utf-8")
    for needle in (
        "registered",
        "verified",
        "validate",
        "לא מנגנון ניטור",
        "intake run",
        "activation",
    ):
        if needle not in intake_md:
            fail(f"INTAKE.md missing {needle!r}")

    events = json.loads(EVENTS_CATALOG.read_text(encoding="utf-8"))
    ev_ids = {e.get("id") for e in events.get("events") or []}
    for need in (
        "media.intake.registered",
        "media.intake.verified",
        "media.intake.failed",
    ):
        if need not in ev_ids:
            fail(f"events.catalog.json missing {need}")

    workflow = INTAKE_WORKFLOW.read_text(encoding="utf-8")
    if "cron:" not in workflow:
        fail("vfmedia-intake.yml must declare schedule cron")
    runner_src = (PACK / "intake" / "runner.py").read_text(encoding="utf-8")
    import re as _re
    wf_cron = _re.search(r'cron:\s*"([^"]+)"', workflow)
    rn_cron = _re.search(r'"githubActionsCron":\s*"([^"]+)"', runner_src)
    if not wf_cron or not rn_cron or wf_cron.group(1) != rn_cron.group(1):
        fail("vfmedia-intake.yml cron must equal runner.py schedule.githubActionsCron")
    if wf_cron.group(1).split()[0].startswith("*"):
        fail("vfmedia-intake.yml cron must use a fixed minute (GitHub under-delivers dense schedules)")
    if 'base["schedule"] = default_runner_state()["schedule"]' not in runner_src:
        fail("runner.py must refresh schedule config from code on load")
    if "concurrency:" not in workflow:
        fail("vfmedia-intake.yml must declare concurrency to prevent overlapping runners")
    if "git push ||" in workflow:
        fail("vfmedia-intake.yml must not swallow git push failures")
    if "|| echo" in workflow and "push" in workflow:
        fail("vfmedia-intake.yml must not swallow git push failures with || echo")
    if "credentials" not in workflow.lower() and "AUTH" not in workflow:
        fail("workflow must treat Drive credentials as required")
    if "intake run" not in workflow:
        fail("vfmedia-intake.yml must run intake")
    if "python3 scripts/check-vfmedia.py" not in workflow:
        fail("vfmedia-intake.yml must run the canonical media sensor")
    for duplicate in (
        "python3 packages/vfmedia/tests/test_intake_hardening.py",
        "python3 scripts/vfmedia.py intake selftest",
        "python3 scripts/vfmedia.py validate",
    ):
        if duplicate in workflow:
            fail(f"vfmedia-intake.yml duplicates offline proof already owned by check-vfmedia.py: {duplicate}")
    if "owned once by check-vfmedia.py" not in workflow:
        fail("workflow must document check-vfmedia.py as the offline validation owner")

    hardening = PACK / "tests" / "test_intake_hardening.py"
    if not hardening.is_file():
        fail("missing packages/vfmedia/tests/test_intake_hardening.py")

    other_catalogs = list((ROOT / "packages").glob("**/media-catalog.json"))
    if other_catalogs:
        fail(f"parallel media catalog files: {other_catalogs}")

    for legacy in ("constitution/MEDIA-VAULT.md", "scripts/check-media-vault.py"):
        if (ROOT / legacy).exists():
            fail(f"parallel media procedure/sensor: {legacy}")
    # The merge can be textually clean while routing tools to a second catalog.
    for relative in (
        "packages/vfmedia/AGENTS.md", "constitution/CONSTITUTION.md",
        "packages/vfigos/SKILL.md", "packages/vfigos/SEND.md",
        "packages/vfops/LOOP.json", "instances/velvet-factory/.cursor/vf-desk.json",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for legacy in ("constitution/MEDIA-VAULT.md", "media-catalog.json", "check-media-vault.py", "needs-appointment"):
            if legacy in text:
                fail(f"stale media vault reference in {relative}: {legacy}")
        if relative != "instances/velvet-factory/.cursor/vf-desk.json":
            for canonical in ("docs/MEDIA-VAULT.md", "packages/vfmedia/catalog.json"):
                if canonical not in text:
                    fail(f"missing canonical media vault reference in {relative}: {canonical}")

    # Load a fresh vfmedia module for the canonical validator instead of
    # spawning another Python process under check-all on Windows.
    validate_spec = importlib.util.spec_from_file_location("vfmedia_validate_target", CLI)
    if validate_spec is None or validate_spec.loader is None:
        fail("cannot load scripts/vfmedia.py for validate")
    validate_module = importlib.util.module_from_spec(validate_spec)
    validate_spec.loader.exec_module(validate_module)
    validate_rc = validate_module.cmd_validate(None)
    if validate_rc != 0:
        fail(f"vfmedia.py validate rc={validate_rc}")

    # Keep the offline intake proof and its hardening tests in-process.
    # Under check-all on Windows, nesting Python -> Python -> Python with
    # captured pipes can leak Ctrl+C to the parent process group.
    root_import = str(ROOT)
    added_root = root_import not in sys.path
    if added_root:
        sys.path.insert(0, root_import)
    try:
        from packages.vfmedia.intake import runner as intake_runner
    finally:
        if added_root:
            sys.path.remove(root_import)

    selftest_rc = intake_runner.run_selftest()
    if selftest_rc != 0:
        fail(f"vfmedia.py intake selftest rc={selftest_rc}")

    import io
    import unittest

    hardening_spec = importlib.util.spec_from_file_location("vfmedia_intake_hardening_tests", hardening)
    if hardening_spec is None or hardening_spec.loader is None:
        fail("could not load intake hardening tests")
    hardening_module = importlib.util.module_from_spec(hardening_spec)
    hardening_spec.loader.exec_module(hardening_module)
    hardening_suite = unittest.defaultTestLoader.loadTestsFromModule(hardening_module)
    hardening_out = io.StringIO()
    hardening_result = unittest.TextTestRunner(stream=hardening_out, verbosity=2).run(hardening_suite)
    if not hardening_result.wasSuccessful():
        fail(f"intake hardening tests: {hardening_out.getvalue()}")

    print("OK vfmedia vault+catalog+intake locked (validate≠monitor; one catalog)")


if __name__ == "__main__":
    main()
