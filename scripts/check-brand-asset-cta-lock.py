#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

SURFACES = [
    'AGENTS.md',
    '.cursor/skills/velvet-creative-director/SKILL.md',
    '.cursor/skills/velvet-brand-guardian/SKILL.md',
    '.cursor/skills/vf-content-sprint/SKILL.md',
    '.cursor/skills/vf-canva-instagram/SKILL.md',
    'packages/vfom/SKILL.md',
    'packages/vfom/CREATIVE-AUTOPILOT.md',
    'packages/vfcanva/WORKFLOW.md',
    'packages/vfcovers/SKILL.md',
    'packages/vfgrowth/SKILL.md',
    'packages/vfgrowth/PREFLIGHT.md',
    'packages/vfgrowth/GATE.md',
    'packages/vfigos/SEND.md',
    'instances/velvet-factory/AGENTS.md',
    'instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc',
]

def fail(msg: str) -> None:
    print(f'FAIL brand-asset-cta-lock: {msg}', file=sys.stderr)
    raise SystemExit(1)
policy = (ROOT / 'packages/vfom/BRAND-ASSET-LOCK.md').read_text(encoding='utf-8')
for needle in (
    'Never invent, redraw, approximate, stylize',
    'NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR',
    '050-2517000',
    'DETERMINISTIC_OVERLAY',
    'public_phone_absent: PASS',
):
    if needle not in policy:
        fail(f'policy missing {needle}')

for rel in SURFACES:
    text = (ROOT / rel).read_text(encoding='utf-8')
    if 'BRAND-ASSET-LOCK.md' not in text:
        fail(f'{rel} missing BRAND-ASSET-LOCK binding')

runtime = (ROOT / 'scripts/vf_send_preflight.py').read_text(encoding='utf-8')
for needle in (
    'brand_asset_gate must be PASS',
    'generated_brand_mark must be NONE',
    'public_phone_absent must be PASS',
    'DETERMINISTIC_OVERLAY',
):
    if needle not in runtime:
        fail(f'runtime missing {needle}')
template = (ROOT / 'packages/vfgrowth/preflight/TEMPLATE.md').read_text(encoding='utf-8')
for needle in (
    'brand_asset_gate: FAIL',
    'generated_brand_mark: PRESENT',
    'logo_usage: NONE',
    'logo_source_ref: NONE',
    'logo_render_method: NONE',
    'public_phone_absent: FAIL',
):
    if needle not in template:
        fail(f'preflight template missing {needle}')

fixture = (ROOT / 'packages/vfom/tests/publication-prep-coldstart.json').read_text(encoding='utf-8')
for needle in (
    'invent_or_redraw_logo_or_wordmark',
    'render_logo_with_generative_model',
    'include_business_phone_in_public_visual_or_caption',
):
    if needle not in fixture:
        fail(f'regression fixture missing {needle}')

print(f'OK brand-asset-cta-lock surfaces={len(SURFACES)} generated_logo=forbidden public_phone=forbidden')
