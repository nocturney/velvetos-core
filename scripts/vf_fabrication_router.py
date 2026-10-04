#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# The router accepts Hebrew owner requests and emits JSON on Windows hosts where
# the inherited console encoding may be cp1252. Keep machine-readable output UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "packages" / "vfprod" / "FABRICATION-ROUTER.json"
SKILLS_ROOT = ROOT / ".agents" / "skills"
LOCK_PATH = ROOT / "skills-lock.json"

VIRTUAL_TOOLS = {
    "native_reasoning",
    "native_vision",
    "native_image_generation",
    "3d-ai-studio",
    "vf-3d-router",
}


def load_router() -> dict:
    return json.loads(ROUTER_PATH.read_text(encoding="utf-8"))


def installed_skill(name: str) -> bool:
    return (SKILLS_ROOT / name / "SKILL.md").is_file()


def lock_skills() -> set[str]:
    if not LOCK_PATH.is_file():
        return set()
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    return set(data.get("skills", {}))


def cmd_list(_: argparse.Namespace) -> int:
    cfg = load_router()
    out = {
        "status": cfg["status"],
        "installed_skills": cfg["installed_skills"],
        "excluded_skills": cfg["excluded_skills"],
        "intents": sorted(cfg["intents"]),
        "hard_boundaries": cfg["hard_boundaries"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    cfg = load_router()
    route = cfg["intents"].get(args.intent)
    if route is None:
        print(json.dumps({
            "status": "BLOCKED",
            "error": f"unknown fabrication intent: {args.intent}",
            "available_intents": sorted(cfg["intents"]),
        }, ensure_ascii=False, indent=2))
        return 2

    missing = [
        step for step in route["chain"]
        if step not in VIRTUAL_TOOLS and not installed_skill(step)
    ]
    out = {
        "status": "PASS" if not missing else "BLOCKED",
        "intent": args.intent,
        "primary": route["primary"],
        "chain": route["chain"],
        "artifact": route["artifact"],
        "missing_skills": missing,
        "printer_actions_allowed": False,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


def cmd_skill(args: argparse.Namespace) -> int:
    cfg = load_router()
    if args.name not in cfg["installed_skills"]:
        print(json.dumps({
            "status": "BLOCKED",
            "error": f"skill not enabled by fabrication router: {args.name}",
        }, indent=2))
        return 2
    path = SKILLS_ROOT / args.name / "SKILL.md"
    print(json.dumps({
        "status": "PASS" if path.is_file() else "BLOCKED",
        "skill": args.name,
        "path": str(path),
    }, indent=2))
    return 0 if path.is_file() else 2


def cmd_verify(_: argparse.Namespace) -> int:
    cfg = load_router()
    enabled = set(cfg["installed_skills"])
    locked = lock_skills()
    missing_dirs = sorted(x for x in enabled if not installed_skill(x))
    missing_lock = sorted(enabled - locked)
    unexpected_lock = sorted(locked - enabled)
    excluded_present = sorted(
        x for x in cfg["excluded_skills"]
        if installed_skill(x) or (ROOT / ".grok" / "skills" / x / "SKILL.md").is_file()
    )
    hb = cfg["hard_boundaries"]
    unsafe = sorted(k for k, v in hb.items() if k != "hidden_dimensions_may_be_invented" and v is not False)
    if hb.get("hidden_dimensions_may_be_invented") is not False:
        unsafe.append("hidden_dimensions_may_be_invented")

    route_unknown = sorted({
        step
        for route in cfg["intents"].values()
        for step in route["chain"]
        if step not in enabled and step not in VIRTUAL_TOOLS
    })
    ok = not any([missing_dirs, missing_lock, unexpected_lock, excluded_present, unsafe, route_unknown])
    print(json.dumps({
        "status": "PASS" if ok else "BLOCKED",
        "enabled_count": len(enabled),
        "missing_skill_dirs": missing_dirs,
        "missing_lock_entries": missing_lock,
        "unexpected_lock_entries": unexpected_lock,
        "excluded_present": excluded_present,
        "unsafe_boundaries": unsafe,
        "unknown_route_steps": route_unknown,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 2






IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp"}
MESH_EXTS = {".stl", ".3mf", ".obj", ".ply", ".glb", ".gltf"}
CAD_EXTS = {".step", ".stp", ".dxf"}
ROBOT_EXTS = {".urdf", ".srdf", ".sdf"}


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def classify_request(request: str, files: list[str]) -> tuple[str, str, str, bool]:
    text = request.casefold()
    suffixes = {Path(f).suffix.casefold() for f in files}
    has_image = bool(suffixes & IMAGE_EXTS)
    has_mesh = bool(suffixes & MESH_EXTS)
    has_cad = bool(suffixes & CAD_EXTS)
    has_robot = bool(suffixes & ROBOT_EXTS)

    create_terms = (
        "תכין", "תכנן", "בנה", "צור", "תיצור", "תבנה", "תכנון", "מודל",
        "make", "create", "design", "build", "model", "edit", "שנה", "תקן",
        "reconstruct", "recreate", "שחזר", "שחזור",
        "מתאם", "תושבת", "adapter", "bracket", "mount", "holder", "enclosure",
    )
    print_terms = (
        "להדפסה", "תכין להדפסה", "slice", "slicing", "g-code", "gcode",
        "פרוס", "סלייס", "print-ready", "ready to print", "printable",
        "for printing", "for print",
    )
    slice_action_terms = (
        "slice", "slicing", "פרוס", "סלייס",
        "validate the g-code", "validate g-code", "validate gcode",
        "g-code validation", "gcode validation",
        "תכין g-code", "צור g-code", "בדוק g-code", "אמת g-code",
    )
    mesh_repair_terms = (
        "make this stl printable", "make this mesh printable",
        "repair for print", "fix for print", "repair this stl",
        "fix this stl", "תתקן להדפסה", "תקן את ה-stl", "תקן את ה stl",
    )
    reference_terms = (
        "this reference", "from reference", "reference image", "reference photo",
        "reference model", "רפרנס", "מתמונת רפרנס", "מתמונות רפרנס",
    )
    organic_terms = (
        "אורגני", "פסל", "פסלון", "דמות", "פיגורה", "חיה", "sculpt",
        "sculptural", "organic", "figurine", "character", "creature",
    )
    standard_terms = (
        "מיסב", "bearing", "בורג", "screw", "bolt", "nut", "washer",
        "servo", "מנוע", "motor", "connector", "מחבר", "actuator",
        "standoff", "pulley", "gear", "608zz", "nema",
    )
    lookup_terms = (
        "חפש", "תמצא", "מצא", "הורד", "download", "find", "search",
        "lookup", "step של", "step file",
    )
    edit_terms = (
        "שנה", "תקן", "ערוך", "modify", "edit", "repair", "resize",
        "עדכן גאומטריה", "שנה מידה", "change dimension",
    )

    if "sendcutsend" in text:
        return "sendcutsend_preflight", "explicit SendCutSend request", "high", False
    if "srdf" in text or ".srdf" in suffixes:
        return "srdf_moveit_semantics", "SRDF/MoveIt semantics requested", "high", False
    if "urdf" in text or ".urdf" in suffixes:
        return "urdf_authoring", "URDF robot description requested", "high", False
    if (
        "sdf" in text
        or ".sdf" in suffixes
        or _contains(text, ("gazebo", "simulation description", "סימולציה"))
    ):
        return "sdf_simulation_description", "SDF/simulation description requested", "high", False
    if _contains(text, (
        "שרטוט הנדסי", "engineering drawing", "manufacturing drawing",
        "dimensioned drawing", "pdf עם מידות", "pdf ממודד", "title block",
    )):
        return "engineering_drawing_pdf", "dimensioned manufacturing document requested", "high", False
    if (
        "dxf" in text
        or _contains(text, (
            "flat pattern", "פריסה שטוחה", "חיתוך לייזר", "laser cut",
            "waterjet", "plasma", "cut profile", "פרופיל 2d",
        ))
    ):
        return "dxf_profile_or_flat_pattern", "2D manufacturing/cut geometry requested", "high", False
    if _contains(text, (
        "cnc", "sheet metal", "פח", "כיפוף פח", "injection molding",
        "הזרקה", "moldability", "machinability", "dfm",
    )):
        return "cnc_sheetmetal_injection_dfm", "non-additive DFM process requested", "high", False
    if _contains(text, (
        "אוריינטציה", "כיוון הדפסה", "איזה צד להדפיס", "orientation",
        "best orientation", "rotate for print",
    )) or ("כיוון" in text and _contains(text, ("להדפיס", "הדפסה", "print"))):
        return "additive_orientation_optimization", "build orientation comparison requested", "high", False
    if _contains(text, (
        "printability", "הדפסביל", "בדוק להדפסה", "בדיקת הדפסה",
        "עובי דופן", "wall thickness", "overhang", "תמיכות", "supports",
        "support needed", "watertight",
    )):
        return "additive_printability_review", "additive manufacturability facts requested", "high", False
    if (has_cad or has_mesh or has_robot) and _contains(text, (
        "פתח", "תראה", "צפה", "viewer", "visual review", "open model",
        "show model", "תצוגה",
    )):
        return "cad_visual_review", "visual review of an existing engineering artifact requested", "high", False

    wants_create = _contains(text, create_terms)
    wants_print = _contains(text, print_terms)
    wants_edit = _contains(text, edit_terms)
    is_organic = _contains(text, organic_terms)
    has_standard = _contains(text, standard_terms)
    has_reference = _contains(text, reference_terms)
    mentions_mesh = has_mesh or _contains(text, (
        ".stl", " stl", ".3mf", " 3mf", "mesh", "רשת",
    ))
    explicit_slice = _contains(text, slice_action_terms)
    wants_mesh_repair = _contains(text, mesh_repair_terms) or (
        mentions_mesh and wants_edit and wants_print
    )

    if explicit_slice:
        return "slice_and_validate", "explicit slicing/G-code generation or validation requested", "high", False
    if wants_mesh_repair:
        return "additive_redesign", "existing mesh needs repair/refinement before print preparation", "high", False
    if has_reference and wants_create and wants_print:
        return "reference_reconstruction_to_print", "reference reconstruction with protected engineering constraints plus print preparation", "high", False
    if has_reference and wants_create:
        return "reference_reconstruction", "reference reconstruction with engineering constraints requires the existing 3D sub-router", "high", False
    if wants_print and (mentions_mesh or has_cad) and not wants_edit:
        return "slice_and_validate", "existing engineering artifact needs print preparation", "high", False
    if is_organic and wants_print:
        return "organic_model_to_print", "organic mesh creation plus print preparation requested", "high", False
    if has_standard and wants_create and wants_print:
        return "assembly_with_standard_parts_to_print", "functional design references off-the-shelf hardware and needs print preparation", "high", False
    if has_image and wants_create and wants_print:
        return "photo_or_sketch_to_print", "image-derived functional part plus print preparation requested", "high", False
    if wants_create and wants_print:
        return "functional_part_to_print", "functional CAD creation plus print preparation requested", "high", False
    if is_organic:
        return "organic_sculptural_model", "organic/sculptural geometry requested", "high", False
    if has_standard and _contains(text, lookup_terms) and not wants_create:
        return "standard_part_lookup", "off-the-shelf component lookup requested", "high", False
    if has_standard and wants_create:
        return "assembly_with_standard_parts", "functional design references off-the-shelf hardware", "high", False
    if has_image and wants_create:
        return "photo_or_sketch_to_functional_cad", "image/sketch must be interpreted before deterministic CAD", "high", False
    if wants_create or _contains(text, ("cad", "step", "stl", "3mf")):
        return "functional_cad_create_edit", "deterministic functional geometry/artifact requested", "medium", False
    if _contains(text, ("render", "הדמיה", "קונספט חזותי", "concept image")) and not (has_mesh or has_cad):
        return "visual_concept_only", "visual concept requested without dimensional engineering output", "medium", False

    return (
        "advice_calculation",
        "no deterministic artifact cue matched; use native reasoning unless the agent resolves a more specific fabrication intent",
        "low",
        True,
    )


def cmd_decide(args: argparse.Namespace) -> int:
    cfg = load_router()
    intent, reason, confidence, needs_agent_resolution = classify_request(args.request, args.file or [])
    route = cfg["intents"][intent]
    missing = [
        step for step in route["chain"]
        if step not in VIRTUAL_TOOLS and not installed_skill(step)
    ]
    out = {
        "status": "PASS" if not missing else "BLOCKED",
        "request": args.request,
        "files": args.file or [],
        "intent": intent,
        "reason": reason,
        "confidence": confidence,
        "needs_agent_resolution": needs_agent_resolution,
        "primary": route["primary"],
        "chain": route["chain"],
        "artifact": route["artifact"],
        "missing_skills": missing,
        "printer_actions_allowed": False,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


def _host_text_to_cad_root() -> Path:
    return Path(os.environ.get(
        "TEXT_TO_CAD_ROOT",
        Path.home() / "Documents" / "VelvetPrintLab" / "tools" / "text-to-cad",
    )).resolve()


def _host_python(repo: Path) -> Path:
    # Do not resolve the venv launcher symlink on macOS/uv; the launcher path
    # is what makes Python honor the venv's pyvenv.cfg and installed packages.
    return repo / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> dict:
    proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def cmd_doctor(_: argparse.Namespace) -> int:
    cfg = load_router()
    repo = _host_text_to_cad_root()
    py = _host_python(repo)
    checks: dict[str, dict] = {}
    if not repo.is_dir() or not py.is_file():
        print(json.dumps({
            "status": "BLOCKED",
            "text_to_cad_root": str(repo),
            "python": str(py),
            "error": "text-to-cad host runtime missing",
        }, ensure_ascii=False, indent=2))
        return 2

    for name in ("cad", "cad-viewer", "dxf", "engineering-drawing", "sdf", "srdf", "urdf"):
        checks[name] = _run(
            [str(py), "-m", "cadgen.cli", "doctor", str(repo / "skills" / name)],
            cwd=repo,
        )

    script_checks = {
        "dfam-check": repo / "skills" / "dfam-check" / "scripts" / "dfam_tool.py",
        "dfm": repo / "skills" / "dfm" / "scripts" / "mold_tool.py",
        "step-parts": repo / "skills" / "step-parts" / "scripts" / "download_step_part.py",
        "gcode": repo / "skills" / "gcode" / "scripts" / "gcode_tool.py",
    }
    for name, script in script_checks.items():
        checks[name] = _run([str(py), str(script), "--help"], cwd=repo)

    checks["velvetos-cad-bridge"] = _run(
        [sys.executable, str(ROOT / "scripts" / "vf_cad.py"), "doctor"],
        cwd=ROOT,
    )

    checks["sendcutsend"] = {
        "returncode": 0,
        "stdout": "instruction-only preflight skill; order submission disabled by Fabrication Router",
        "stderr": "",
    }
    git_head = _run(["git", "rev-parse", "HEAD"], cwd=repo)
    checks["upstream-commit"] = git_head
    expected_commit = cfg.get("upstream_commit")
    commit_matches = git_head["returncode"] == 0 and git_head["stdout"] == expected_commit

    failed = sorted(name for name, result in checks.items() if result["returncode"] != 0)
    excluded_present = any(
        (ROOT / root / "skills" / "bambu-labs" / "SKILL.md").exists()
        for root in (".agents", ".grok")
    )
    ok = not failed and not excluded_present and commit_matches
    print(json.dumps({
        "status": "PASS" if ok else "BLOCKED",
        "text_to_cad_root": str(repo),
        "python": str(py),
        "upstream_commit_expected": expected_commit,
        "upstream_commit_matches": commit_matches,
        "checks": checks,
        "failed": failed,
        "bambu_labs_installed": excluded_present,
        "printer_actions_allowed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Resolve VelvetOS fabrication tool routes.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    route = sub.add_parser("route")
    route.add_argument("--intent", required=True)
    skill = sub.add_parser("skill")
    skill.add_argument("--name", required=True)
    decide = sub.add_parser("decide")
    decide.add_argument("--request", required=True)
    decide.add_argument("--file", action="append", default=[])
    sub.add_parser("verify")
    sub.add_parser("doctor")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "route":
        return cmd_route(args)
    if args.cmd == "skill":
        return cmd_skill(args)
    if args.cmd == "decide":
        return cmd_decide(args)
    if args.cmd == "verify":
        return cmd_verify(args)
    if args.cmd == "doctor":
        return cmd_doctor(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
