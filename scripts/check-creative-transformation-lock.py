#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
POLICY='packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md'
SURFACES=[
'AGENTS.md',
'.cursor/skills/velvet-brand-guardian/SKILL.md',
'.cursor/skills/velvet-creative-director/SKILL.md',
'.cursor/skills/vf-canva-instagram/SKILL.md',
'.cursor/skills/vf-content-sprint/SKILL.md',
'instances/velvet-factory/AGENTS.md',
'instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc',
'packages/vfcanva/WORKFLOW.md',
'packages/vfcovers/SKILL.md',
'packages/vfgrowth/GATE.md',
'packages/vfgrowth/PREFLIGHT.md',
'packages/vfgrowth/SKILL.md',
'packages/vfigos/SEND.md',
'packages/vfom/CREATIVE-AUTOPILOT.md',
'packages/vfom/SKILL.md']

def fail(msg):
    print('FAIL creative-transformation-lock:',msg,file=sys.stderr); raise SystemExit(1)
def text(rel):
    p=ROOT/rel
    if not p.is_file(): fail(f'missing {rel}')
    return p.read_text(encoding='utf-8')

policy=text(POLICY)
for needle in ('Preserve the product; redesign the presentation.','raw_passthrough: false','SOURCE_IMAGE_EDIT','Multiple source photos do not imply a carousel','NO LOGO, NO WORDMARK, NO PHONE NUMBER'):
    if needle not in policy: fail(f'policy missing {needle}')
for rel in SURFACES:
    body=text(rel)
    if POLICY not in body or 'raw_passthrough' not in body or 'fully treated hero' not in body:
        fail(f'{rel} missing transformation lock binding')
runtime=text('scripts/vf_send_preflight.py')
for needle in ('"creative_delta_gate": "PASS"','raw_passthrough must be false','source_edit_mode must prove source-grounded edit/composite','hero_transformation_evidence must identify the final hero'):
    if needle not in runtime: fail(f'runtime missing {needle}')
template=text('packages/vfgrowth/preflight/TEMPLATE.md')
for needle in ('creative_delta_gate: FAIL','raw_passthrough: true','source_edit_mode:','hero_transformation_evidence:'):
    if needle not in template: fail(f'template missing {needle}')
fixture=text('packages/vfom/tests/publication-prep-coldstart.json')
for needle in ('perform_meaningful_presentation_transform','avoid_raw_passthrough','do_not_default_to_raw_carousel'):
    if needle not in fixture: fail(f'fixture missing {needle}')
print(f'OK creative-transformation-lock surfaces={len(SURFACES)} raw_passthrough=forbidden source_edit=required')
