#!/usr/bin/env python3
"""Validate global human-visible AI text gating across VelvetOS surfaces.

Static wiring sensor only. It proves the rules/routes/gate executable are present; it
must never be presented as proof that a particular future candidate actually ran.
Per-candidate execution evidence belongs in the relevant artifact/preflight/digest.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE6A_REPORT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6a-visible-text-tiers.json"
STAGE6A_GENERATOR = ROOT / "scripts" / "generate-stage6a-visible-text-tiers-report.py"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def require(rel: str, needles: tuple[str, ...]) -> None:
    body = text(rel)
    for needle in needles:
        if needle not in body:
            fail(f"{rel} missing {needle!r}")


def main() -> None:
    require(
        "constitution/VISIBLE_TEXT.md",
        ("כל טקסט", "כריסטיאן", "לקוח", "reader-first-he.md", "velvet-hebrew-copy", "ai-tells-he.md", "approved_static_copy", "visible_text_gate: PASS", "UNPROVEN", "DRAFT_INTERNAL", "FINAL_INTERNAL", "EXTERNAL_COMMITMENT", "PUBLIC_PUBLISH", "Tier downgrade is fail-closed"),
    )
    require("constitution/CONSTITUTION.md", ("Visible Text Gate", "VISIBLE_TEXT.md", "packages/vfcopy", "אין `PASS` בלי ביצוע בפועל"))
    require(
        "AGENTS.md",
        ("Visible Text Gate is global", "constitution/VISIBLE_TEXT.md", "customer-message", "owner-brief", "human-document", "ui-microcopy", "UNPROVEN", "scripts/check-visible-text-gate.py"),
    )
    require(
        "packages/vfharness/SKILL.md",
        ("Human-visible output", "constitution/VISIBLE_TEXT.md", "visible_text_gate: PASS", "UNPROVEN", "EXECUTION_PROVEN", "checkpoint / execution_state"),
    )
    rule = text(".cursor/rules/visible-text-gate.mdc")
    if "alwaysApply: true" not in rule:
        fail(".cursor/rules/visible-text-gate.mdc must be alwaysApply: true")
    for needle in ("constitution/VISIBLE_TEXT.md", "owner-facing", "customer", "reader-first-he.md", "vf-hebrew-copy", "Humanizer", "UNPROVEN", "DRAFT_INTERNAL", "FINAL_INTERNAL", "EXTERNAL_COMMITMENT", "PUBLIC_PUBLISH", "exact body/hash binding"):
        if needle not in rule:
            fail(f"always-on visible-text rule missing {needle!r}")

    require(
        "packages/vfcopy/SOFT-TOOLS-CONTRACT.md",
        ("human-visible AI text", "public-social", "customer-message", "sales-proposal", "owner-brief", "human-document", "ui-microcopy", "scripts/vf_visible_text.py", "text_sha256", "DRAFT_INTERNAL", "FINAL_INTERNAL", "EXTERNAL_COMMITMENT", "PUBLIC_PUBLISH", "no longer a universal full-chain checklist"),
    )
    require(
        "packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md",
        ("לכל טקסט אנושי נראה", "customer-message", "sales-proposal", "owner-brief", "human-document", "ui-microcopy", "reader-first-he.md", "ai-tells-he.md", "visible_text_gate", "DRAFT_INTERNAL", "FINAL_INTERNAL", "EXTERNAL_COMMITMENT", "PUBLIC_PUBLISH"),
    )
    require(
        "packages/vfcopy/skills/velvet-hebrew-copy/PIPELINE.md",
        ("PIPELINE — Visible Text Gate", "public-social", "visual-microcopy", "customer-message", "sales-proposal", "owner-brief", "human-document", "ui-microcopy", "UNPROVEN", "Stage 6 tier selector", "required_evidence", "approved_static_copy"),
    )
    require(
        ".cursor/skills/vf-hebrew-copy/SKILL.md",
        ("human-visible", "owner-brief", "customer-message", "sales-proposal", "human-document", "ui-microcopy", "visible_text_gate: PASS", "DRAFT_INTERNAL", "FINAL_INTERNAL", "EXTERNAL_COMMITMENT", "PUBLIC_PUBLISH"),
    )

    require(".cursor/skills/vf-inquiry-chain/SKILL.md", ("VISIBLE_TEXT.md", "customer-message", "sales-proposal", "visible_text_gate: PASS"))
    require("packages/vfe2b/crews/inquiry.md", ("VISIBLE_TEXT.md", "customer-message", "ai-tells-he.md", "visible_text_gate: PASS"))
    require("packages/vfconvert/WHATSAPP.md", ("VISIBLE_TEXT.md", "customer-message", "surface-aware lint", "visible_text_gate: PASS"))
    require("packages/vfsales/QUOTE.md", ("VISIBLE_TEXT.md", "sales-proposal", "reader-first-he.md", "ai-tells-he.md", "visible_text_gate: PASS"))
    require(".cursor/skills/vf-morning-brief/SKILL.md", ("VISIBLE_TEXT.md", "owner-brief", "reader-first-he.md", "visible_text_gate: PASS"))
    require("packages/vfe2b/crews/morning-brief.md", ("VISIBLE_TEXT.md", "owner-brief", "ai-tells-he.md", "visible_text_gate: PASS"))

    require(
        "constitution/SEND.md",
        ("VISIBLE_TEXT.md", "Transport readiness ≠ text readiness", "customer-message", "owner-brief", "public-social", "visual-microcopy", "visible_text_gate: PASS"),
    )
    require("packages/vfgrowth/PREFLIGHT.md", ("VISIBLE_TEXT.md", "visible_text_gate: PASS", "text_sha256", "visual-microcopy", "UNPROVEN", "הודעת Instagram"))
    require(
        "packages/vfgrowth/preflight/TEMPLATE.md",
        ("visible_text_gate: FAIL", "visible_text_surface: public-social", "text_sha256", "humanizer_ai_tells", "visual_text_gate", "הודעה באינסטגרם", "PUBLIC_CURRENT_CTA"),
    )

    gate = text("scripts/vf_visible_text.py")
    for needle in ("public-social", "visual-microcopy", "customer-message", "sales-proposal", "owner-brief", "human-document", "ui-microcopy", "text_sha256", "visible_text_gate", "UNPROVEN", "--gate", "detect_ai_slop", "anti_slop", "DRAFT_INTERNAL", "FINAL_INTERNAL", "EXTERNAL_COMMITMENT", "PUBLIC_PUBLISH", "required_evidence", "approved_static_sha256", "exact_body_bound"):
        if needle not in gate:
            fail(f"scripts/vf_visible_text.py missing {needle!r}")
    if "surface not in PUBLIC_SURFACES" not in gate:
        fail("surface-aware gate must distinguish public-only lint rules")

    # Behavioral proof: the exact visible-text gate must reject named slop patterns,
    # while a concrete clean owner-brief can still PASS with all stage evidence.
    sys.path.insert(0, str(ROOT / "scripts"))
    from vf_visible_text import evaluate  # noqa: PLC0415

    common = dict(
        file=None,
        surface="owner-brief",
        language="he",
        context_json=None,
        domain_tool=["vfops"],
        marketing_aids=None,
        truth_checked=True,
        reader_first=True,
        copy_authority=True,
        surface_qa=True,
        no_text_compared=False,
        rewrite=False,
        gate=True,
    )
    bad = evaluate(Namespace(text="הנה העניין: הכול השתנה. העתיד כבר כאן.", **common))
    findings = (bad.get("anti_slop") or {}).get("findings") or []
    if bad.get("visible_text_gate") != "FAIL" or not findings:
        fail("visible-text gate must FAIL on named anti-slop findings")

    clean = evaluate(
        Namespace(
            text="שלושה קבצים נבדקו. שני כשלים עדיין פתוחים ודורשים תיקון.",
            **common,
        )
    )
    if clean.get("visible_text_gate") != "PASS":
        fail(f"clean owner-brief should PASS the exact gate, got {clean!r}")

    # Stage 6A tier proof: internal drafts/finals reduce ceremony without allowing
    # an external/public request to downgrade itself into an internal tier.
    draft = evaluate(
        Namespace(
            text="הנה העניין: הכול השתנה. העתיד כבר כאן.",
            file=None,
            surface="desk",
            tier="DRAFT_INTERNAL",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=False,
            copy_authority=False,
            surface_qa=False,
            sensitive=False,
            exact_body_bound=False,
            approved_static_sha256=None,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if draft.get("visible_text_gate") != "PASS" or draft.get("required_evidence") != ["truth_checked"]:
        fail(f"DRAFT_INTERNAL should require truth/basic-safety only, got {draft!r}")
    if not (draft.get("anti_slop") or {}).get("findings") or (draft.get("anti_slop") or {}).get("blocking_for_tier") is not False:
        fail("DRAFT_INTERNAL anti-slop findings must remain diagnostic, not ceremony blockers")

    draft_fact = evaluate(
        Namespace(
            text="המחיר הוא 120 ₪.",
            file=None,
            surface="desk",
            tier="DRAFT_INTERNAL",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=False,
            copy_authority=False,
            surface_qa=False,
            sensitive=False,
            exact_body_bound=False,
            approved_static_sha256=None,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if draft_fact.get("visible_text_gate") != "FAIL":
        fail("DRAFT_INTERNAL must still fail closed on unverified price/fact text")

    final_internal = evaluate(
        Namespace(
            text="שלושה קבצים נבדקו. שני כשלים עדיין פתוחים ודורשים תיקון.",
            file=None,
            surface="owner-brief",
            tier="FINAL_INTERNAL",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=False,
            copy_authority=False,
            surface_qa=True,
            sensitive=False,
            exact_body_bound=False,
            approved_static_sha256=None,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if final_internal.get("visible_text_gate") != "PASS":
        fail(f"routine FINAL_INTERNAL should PASS without heavy copy ceremony, got {final_internal!r}")
    if final_internal.get("heavy_tools_required") is not False:
        fail("routine FINAL_INTERNAL must not require heavy copy tools")

    sensitive_internal = evaluate(
        Namespace(
            text="שלושה קבצים נבדקו. שני כשלים עדיין פתוחים ודורשים תיקון.",
            file=None,
            surface="owner-brief",
            tier="FINAL_INTERNAL",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=False,
            copy_authority=False,
            surface_qa=True,
            sensitive=True,
            exact_body_bound=False,
            approved_static_sha256=None,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if sensitive_internal.get("visible_text_gate") != "UNPROVEN":
        fail("sensitive FINAL_INTERNAL must require the heavier reader/copy path")
    if not {"reader_first", "copy_authority"} <= set(sensitive_internal.get("missing_evidence") or []):
        fail("sensitive FINAL_INTERNAL missing heavy-tool evidence must be explicit")

    commitment = evaluate(
        Namespace(
            text="תודה, קיבלתי את הפרטים.",
            file=None,
            surface="customer-message",
            tier="EXTERNAL_COMMITMENT",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=True,
            copy_authority=False,
            surface_qa=True,
            sensitive=False,
            exact_body_bound=False,
            approved_static_sha256=None,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if commitment.get("visible_text_gate") != "UNPROVEN" or "exact_body_bound" not in (commitment.get("missing_evidence") or []):
        fail("EXTERNAL_COMMITMENT must require exact-body binding")
    commitment_bound = evaluate(
        Namespace(
            text="תודה, קיבלתי את הפרטים.",
            file=None,
            surface="customer-message",
            tier="EXTERNAL_COMMITMENT",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=True,
            copy_authority=False,
            surface_qa=True,
            sensitive=False,
            exact_body_bound=True,
            approved_static_sha256=None,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if commitment_bound.get("visible_text_gate") != "PASS":
        fail(f"bound EXTERNAL_COMMITMENT should PASS, got {commitment_bound!r}")

    try:
        evaluate(
            Namespace(
                text="פוסט",
                file=None,
                surface="public-social",
                tier="DRAFT_INTERNAL",
                language="he",
                context_json=None,
                domain_tool=[],
                marketing_aids=None,
                truth_checked=True,
                reader_first=False,
                copy_authority=False,
                surface_qa=False,
                sensitive=False,
                exact_body_bound=False,
                approved_static_sha256=None,
                no_text_compared=False,
                rewrite=False,
                gate=True,
            )
        )
    except ValueError:
        pass
    else:
        fail("public surfaces must not downgrade to an internal Visible Text tier")

    static_sha = final_internal["text_sha256"]
    static_reuse = evaluate(
        Namespace(
            text="שלושה קבצים נבדקו. שני כשלים עדיין פתוחים ודורשים תיקון.",
            file=None,
            surface="owner-brief",
            tier="FINAL_INTERNAL",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=False,
            copy_authority=False,
            surface_qa=False,
            sensitive=False,
            exact_body_bound=False,
            approved_static_sha256=static_sha,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if static_reuse.get("visible_text_gate") != "PASS" or not (static_reuse.get("approved_static_copy") or {}).get("reuse_allowed"):
        fail("exact approved_static_copy should reuse prior copy work after fact recheck")
    static_changed = evaluate(
        Namespace(
            text="שלושה קבצים נבדקו. כשל אחד עדיין פתוח.",
            file=None,
            surface="owner-brief",
            tier="FINAL_INTERNAL",
            language="he",
            context_json=None,
            domain_tool=[],
            marketing_aids=None,
            truth_checked=True,
            reader_first=False,
            copy_authority=False,
            surface_qa=False,
            sensitive=False,
            exact_body_bound=False,
            approved_static_sha256=static_sha,
            no_text_compared=False,
            rewrite=False,
            gate=True,
        )
    )
    if static_changed.get("visible_text_gate") != "FAIL" or static_changed.get("failure_reason") != "approved_static_hash_mismatch":
        fail("changed approved_static_copy must fail exact-hash reuse")

    if not STAGE6A_REPORT.is_file() or not STAGE6A_GENERATOR.is_file():
        fail("Stage 6A report/generator missing")
    stage6a = json.loads(STAGE6A_REPORT.read_text(encoding="utf-8"))
    if stage6a.get("schema") != "velvetos.stage6a-visible-text-tiers.v1" or stage6a.get("stage") != "6A":
        fail("Stage 6A Visible Text receipt schema/stage mismatch")
    if stage6a.get("behavior_change") is not True:
        fail("Stage 6A must record the tier routing behavior change")
    if stage6a.get("prepared_against_main_sha") != "c1959a6c663d8d363545b5bc9ed8f30a1758941a":
        fail("Stage 6A base main SHA drift")
    if stage6a.get("repository_acceptance") != "PASS":
        fail("Stage 6A repository acceptance is not PASS")
    before6a = stage6a.get("before") or {}
    after6a = stage6a.get("after") or {}
    if before6a.get("model") != "UNIVERSAL_FULL_CHAIN" or before6a.get("universal_required_count") != 6:
        fail("Stage 6A pre-change Visible Text baseline drift")
    if before6a.get("source_sha256") != "65bc8ccde1e49c00cf33d611fdbaf4d04bdcf03ae086a2f3485ee6965019496f":
        fail("Stage 6A pre-change executable hash drift")
    current_visible_hash = hashlib.sha256((ROOT / "scripts/vf_visible_text.py").read_bytes()).hexdigest()
    if after6a.get("source_sha256") != current_visible_hash:
        fail("Stage 6A current executable hash does not match the acceptance receipt")
    if after6a.get("model") != "RISK_AND_SURFACE_TIERS" or after6a.get("tier_contract_version") != 1:
        fail("Stage 6A tier contract drift")
    expected_defaults6a = {
        "public-social": "PUBLIC_PUBLISH",
        "visual-microcopy": "PUBLIC_PUBLISH",
        "customer-message": "EXTERNAL_COMMITMENT",
        "sales-proposal": "EXTERNAL_COMMITMENT",
        "owner-brief": "FINAL_INTERNAL",
        "human-document": "FINAL_INTERNAL",
        "ui-microcopy": "FINAL_INTERNAL",
        "desk": "FINAL_INTERNAL",
    }
    if after6a.get("safe_default_by_surface") != expected_defaults6a:
        fail("Stage 6A safe surface defaults drift")
    expected_counts6a = {
        "DRAFT_INTERNAL": 1,
        "FINAL_INTERNAL_routine": 2,
        "FINAL_INTERNAL_sensitive": 5,
        "EXTERNAL_COMMITMENT": 4,
        "PUBLIC_PUBLISH": 6,
    }
    if after6a.get("tier_required_evidence_counts") != expected_counts6a:
        fail("Stage 6A tier evidence counts drift")
    expected_reduction6a = {
        "DRAFT_INTERNAL": 83.3,
        "FINAL_INTERNAL_routine": 66.7,
        "FINAL_INTERNAL_sensitive": 16.7,
        "EXTERNAL_COMMITMENT": 33.3,
        "PUBLIC_PUBLISH": 0.0,
    }
    if after6a.get("ceremony_reduction_percent_vs_before") != expected_reduction6a:
        fail("Stage 6A ceremony-reduction snapshot drift")
    if after6a.get("heavy_internal_length_threshold_chars") != 800:
        fail("Stage 6A internal heavy-tool threshold drift")
    if after6a.get("approved_static_requires_exact_sha") is not True or after6a.get("tier_downgrade_fail_closed") is not True:
        fail("Stage 6A approved-static/downgrade contract drift")
    vectors6a = stage6a.get("behavior_vectors") or {}
    if len(vectors6a) != 9 or not all((row or {}).get("pass") is True for row in vectors6a.values()):
        fail("Stage 6A behavioral vectors drift/fail")
    auth6a = stage6a.get("authorization_semantics") or {}
    if auth6a.get("external_effect_policy_registry_unchanged") is not True or auth6a.get("visible_text_is_effect_authority") is not False:
        fail("Stage 6A authorization boundary drift")
    acceptance6a = stage6a.get("acceptance") or {}
    if len(acceptance6a) != 10 or not all(value is True for value in acceptance6a.values()):
        fail("Stage 6A acceptance criteria drift/fail")
    workflow6a = stage6a.get("workflow_binding") or {}
    if workflow6a.get("explicit_tier") != "FINAL_INTERNAL" or workflow6a.get("pass") is not True:
        fail("Stage 6A owner-brief workflow binding drift")
    with tempfile.TemporaryDirectory(prefix="stage6a-visible-text-") as td:
        regenerated6a = Path(td) / "stage6a.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(STAGE6A_GENERATOR),
                "--prepared-against", stage6a["prepared_against_main_sha"],
                "--captured-at", stage6a["captured_at"],
                "--output", str(regenerated6a),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        if proc.returncode != 0:
            fail("Stage 6A report regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
        if regenerated6a.read_bytes() != STAGE6A_REPORT.read_bytes():
            fail("Stage 6A Visible Text report is not reproducible")

    require("packages/vfom/FOUNDRY.json", ("visualCopyPolicy", "noTextBaselineRequired", "vf-hebrew-copy", "ai-tells-he.md"))
    require(".cursor/skills/velvet-creative-director/SKILL.md", ("NO_TEXT", "velvet-hebrew-copy"))
    require(".cursor/skills/velvet-brand-guardian/SKILL.md", ("NO_TEXT", "velvet-hebrew-copy", "ai-tells-he.md"))

    print("OK visible-text-gate routes + surface-aware executable + anti-slop behavioral gate bound")


if __name__ == "__main__":
    main()
