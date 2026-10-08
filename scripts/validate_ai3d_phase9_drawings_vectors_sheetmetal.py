#!/usr/bin/env python3
"""Validate Phase 9 drawings, vectors, and sheet-metal capabilities."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CONFIG = BASE / "drawings-vectors-sheetmetal-v1.json"
DEFAULT_EVIDENCE = BASE / "evidence" / "phase9-drawings-vectors-sheetmetal-acceptance-20261007.json"

sys.path.insert(0, str(ROOT / "scripts"))
import ai3d_drawings_vectors_sheetmetal as phase9  # noqa: E402
import vf_cad_stack  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    assert isinstance(value, dict)
    return value


def close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(float(actual) - float(expected)) <= tolerance


def assert_vector(
    actual: list[float],
    expected: list[float],
    tolerance: float,
    label: str,
) -> None:
    assert len(actual) == len(expected), label
    for got, want in zip(actual, expected):
        assert close(got, want, tolerance), (label, actual, expected, tolerance)


def canonical_has_draftwright() -> bool:
    runtime = vf_cad_stack.runtime_paths()["build123d"]
    proc = subprocess.run(
        [
            str(runtime),
            "-c",
            "import importlib.util;print(bool(importlib.util.find_spec('draftwright')))",
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip().splitlines()[-1] == "True"


def sheetmetal_checkout_metadata(config: dict[str, Any]) -> dict[str, Any]:
    runtime = Path(config["runtime_truth"]["sheetmetal"]["runtime"])
    proc = subprocess.run(
        ["git", "-C", str(runtime), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    commit = proc.stdout.strip()
    package_xml = ET.parse(runtime / "package.xml").getroot()
    namespace = {"fc": "https://wiki.freecad.org/Package_Metadata"}
    version = package_xml.findtext("fc:version", namespaces=namespace)
    license_text = package_xml.findtext("fc:license", namespaces=namespace)
    return {
        "path": str(runtime),
        "commit": commit,
        "version": version,
        "license": license_text,
    }


def portable_suite_evidence(suite: dict[str, Any]) -> dict[str, Any]:
    """Remove ephemeral temp-root paths while retaining artifact names/hashes/bytes."""
    value = json.loads(json.dumps(suite))
    for section_name in ("techdraw", "sheetmetal", "text_vector"):
        section = value[section_name]
        for receipt in section.get("artifacts", {}).values():
            receipt["path"] = Path(receipt["path"]).name
    for sample in value["text_vector"]["samples"].values():
        sample["dxf"] = Path(sample["dxf"]).name
        sample["svg"] = Path(sample["svg"]).name
    return value


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()

    config = load(CONFIG)
    assert config["schema"] == "velvetos.ai3d.drawings-vectors-sheetmetal.v1"
    assert config["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
    safety = config["safety"]
    assert safety["printer_actions_allowed"] is False
    assert safety["machine_control_allowed"] is False
    assert safety["invent_k_factor"] is False
    assert safety["invent_material_thickness"] is False
    assert safety["accept_unparseable_dxf"] is False
    assert safety["copy_or_bundle_font_files"] is False
    assert safety["draftwright_in_canonical_runtime"] is False

    checkout = sheetmetal_checkout_metadata(config)
    sheet_cfg = config["runtime_truth"]["sheetmetal"]
    assert checkout["commit"] == sheet_cfg["commit"]
    assert checkout["version"] == sheet_cfg["version"]
    assert checkout["license"] == sheet_cfg["license"]

    with tempfile.TemporaryDirectory(prefix="ai3d-phase9-") as tmp:
        temp = Path(tmp)
        suite = phase9.all_fixtures(temp)

        assert suite["schema"] == "velvetos.ai3d.phase9-fixture-suite.v1"
        assert suite["status"] == "PASS"
        assert suite["authority"] == config["authority"]

        techdraw = suite["techdraw"]
        assert techdraw["status"] == "PASS"
        assert techdraw["freecad_version"] == "1.1.3"
        assert techdraw["page_type"] == "TechDraw::DrawPage"
        assert techdraw["view_type"] == "TechDraw::DrawViewPart"
        assert techdraw["visible_edges"] == 5
        assert techdraw["dxf_page_probe"]["entity_count"] == 5
        assert techdraw["dxf_view_probe"]["entity_count"] == 5
        assert techdraw["dxf_page_probe"]["build123d_shape_count"] == 5
        assert_vector(
            techdraw["dxf_view_probe"]["build123d_bbox_size"],
            [80.0, 60.0, 0.0],
            1e-6,
            "techdraw dxf bbox",
        )

        sheet = suite["sheetmetal"]
        assert sheet["status"] == "PASS"
        assert sheet["sheetmetal_version"] == "0.8.24"
        assert sheet["networkx_version"] == "3.5"
        assert sheet["thickness_mm"] == 1.0
        assert sheet["bend_radius_mm"] == 1.0
        assert sheet["k_factor"] == 0.38
        assert sheet["k_factor_standard"] == "ANSI"
        assert sheet["bend_count"] == 1
        assert_vector(sheet["root_normal"], [0.0, 0.0, 1.0], 1e-9, "sheet root normal")
        assert close(sheet["bend_angles_deg"][0], 90.0, 1e-9)
        assert close(sheet["bend_radii_mm"][0], 1.0, 1e-9)
        assert_vector(
            sheet["unfold_bbox_mm"],
            [60.0, 48.167698930976954, 1.0],
            1e-6,
            "sheet unfold bbox",
        )
        assert sheet["dxf_probe"]["entity_count"] == 8
        assert sheet["dxf_probe"]["entity_types"] == ["LINE"]
        assert sheet["dxf_probe"]["build123d_shape_count"] == 8
        assert_vector(
            sheet["dxf_probe"]["build123d_bbox_size"],
            [60.0, 48.167698930976954, 0.0],
            1e-6,
            "sheet dxf bbox",
        )

        text_vector = suite["text_vector"]
        assert text_vector["status"] == "PASS"
        assert text_vector["font_files_copied"] is False
        assert set(text_vector["samples"]) == {"latin", "hebrew"}
        for sample_id, sample in text_vector["samples"].items():
            assert sample["font"] == "Arial"
            assert sample["source_faces"] > 0, sample_id
            assert sample["dxf_shapes"] > 0, sample_id
            assert sample["svg_shapes"] > 0, sample_id
            assert_vector(
                sample["dxf_bbox_mm"],
                sample["source_bbox_mm"],
                1e-6,
                f"{sample_id} dxf roundtrip",
            )
            assert_vector(
                sample["svg_bbox_mm"],
                sample["source_bbox_mm"],
                0.001,
                f"{sample_id} svg roundtrip",
            )
        assert any(ord(char) > 127 for char in text_vector["samples"]["hebrew"]["text"])

        draftwright = suite["draftwright"]
        assert draftwright["status"] == "CANDIDATE_ISOLATED_EVAL"
        assert draftwright["installed"] is True
        assert draftwright["metadata"]["draftwright_version"] == "0.4.34"
        assert draftwright["metadata"]["license"] == "AGPL-3.0"
        assert draftwright["metadata"]["build123d_version"] == "0.10.0"
        assert draftwright["canonical_build123d_version"] == "0.11.1"
        assert draftwright["admission"] == "BLOCKED_FROM_CANONICAL_RUNTIME"
        assert canonical_has_draftwright() is False

        negative_controls: dict[str, str] = {}

        try:
            phase9.sheetmetal_fixture(
                temp / "invalid-kfactor",
                k_factor=0.0,
                k_factor_standard="ansi",
            )
        except ValueError:
            negative_controls["missing_or_invalid_k_factor"] = "BLOCKED"
        else:
            raise AssertionError("invalid k-factor was not blocked")

        try:
            phase9.sheetmetal_fixture(
                temp / "invalid-standard",
                k_factor=0.38,
                k_factor_standard="unknown",
            )
        except ValueError:
            negative_controls["invalid_k_factor_standard"] = "BLOCKED"
        else:
            raise AssertionError("invalid k-factor standard was not blocked")

        invalid_dxf = temp / "not-a-dxf.dxf"
        invalid_dxf.write_text("NOT_A_DXF_FILE\n", encoding="utf-8")
        try:
            phase9.dxf_probe(invalid_dxf)
        except RuntimeError:
            negative_controls["unparseable_dxf"] = "BLOCKED"
        else:
            raise AssertionError("unparseable DXF was not blocked")

        evidence = {
            "schema": "velvetos.ai3d.phase9-drawings-vectors-sheetmetal-acceptance.v1",
            "status": "PASS",
            "authority": config["authority"],
            "sheetmetal_checkout": checkout,
            "suite": portable_suite_evidence(suite),
            "artifact_retention": (
                "Fixture files are ephemeral validation artifacts; evidence retains "
                "artifact names, SHA-256 hashes, byte counts and geometry metrics."
            ),
            "negative_controls": negative_controls,
            "license_lanes": {
                "build123d": "Apache-2.0 / commercial-clean",
                "ezdxf": "MIT / commercial-clean",
                "svgwrite": "MIT / commercial-clean",
                "networkx": "BSD / commercial-clean",
                "sheetmetal": "LGPL-2.1-or-later / commercial-clean",
                "draftwright": "AGPL-3.0 / candidate isolated evaluation only",
            },
        }

    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    with args.evidence_out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(evidence, indent=2, ensure_ascii=True) + "\n")

    print(
        "validate_ai3d_phase9_drawings_vectors_sheetmetal: PASS "
        "techdraw=page+dxf sheetmetal=unfold+dxf "
        "text=latin+hebrew dxf+svg draftwright=CANDIDATE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
