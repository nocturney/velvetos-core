#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = "packages/vfom/PUBLICATION-PREP-EXECUTION.md"
FAILURE = "visual_execution_unavailable"

SURFACES = [
    'AGENTS.md',
    '.cursor/skills/vf-canva-instagram/SKILL.md',
    '.cursor/skills/vf-content-sprint/SKILL.md',
    '.cursor/skills/velvet-creative-director/SKILL.md',
    '.cursor/skills/velvet-brand-guardian/SKILL.md',
    '.cursor/skills/vf-marketing-skills/SKILL.md',
    '.cursor/skills/vf-organic-growth/SKILL.md',
    'packages/vfgrowth/SKILL.md',
    'packages/vfgrowth/PREFLIGHT.md',
    'packages/vfgrowth/GATE.md',
    'packages/vfcovers/SKILL.md',
    'packages/vfcanva/WORKFLOW.md',
    'packages/vfom/CREATIVE-AUTOPILOT.md',
    'packages/vfom/SKILL.md',
    'packages/vfigos/SEND.md',
    'instances/velvet-factory/AGENTS.md',
    'instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc',
]

def fail(msg: str) -> None:
    print(f"FAIL publication-prep execution: {msg}", file=sys.stderr)
    raise SystemExit(1)

def text(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file(): fail(f"missing {rel}")
    return p.read_text(encoding='utf-8')

if not (ROOT / POLICY).is_file():
    fail(f"missing {POLICY}")
for rel in SURFACES:
    body = text(rel)
    for needle in (POLICY, FAILURE, 'selection/caption/planning alone is incomplete'):
        if needle not in body:
            fail(f"{rel} missing {needle}")
runtime = text('scripts/vf_send_preflight.py')
for needle in (
    '"visual_edit_performed": "PASS"',
    '"exact_final_visual_qa": "PASS"',
    '"public_cta_gate": "PASS"',
    'visual_output_evidence must identify the real edited visual artifact',
):
    if needle not in runtime:
        fail(f"runtime publish gate missing {needle}")

template = text('packages/vfgrowth/preflight/TEMPLATE.md')
for needle in ('visual_edit_performed: FAIL', 'visual_output_evidence:', 'exact_final_visual_qa: FAIL', 'public_cta_gate: FAIL'):
    if needle not in template:
        fail(f"preflight template missing {needle}")

print(f"OK publication-prep structural wiring verified surfaces={len(SURFACES)}")
fixture = text('packages/vfom/tests/publication-prep-coldstart.json')
for needle in (
    'פרסום פוטנציאלי, תכין את זה לפרסום בבקשה כדי שנבחן',
    'produce_visual_artifact_for_review',
    'finish_with_caption_only',
    'hardcode_business_whatsapp_as_public_cta',
):
    if needle not in fixture:
        fail(f"cold-start regression fixture missing {needle}")
