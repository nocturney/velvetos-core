#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INTAKE=ROOT/'packages'/'vfharness'/'devtools'/'repo-intake-2026-10-07.json'
EXEC=ROOT/'packages'/'vfharness'/'devtools'/'execution-providers.json'
CLI=ROOT/'packages'/'vfharness'/'devtools'/'approved-cli.json'
VTR=ROOT/'packages'/'vfharness'/'state'/'vtracer-pilot-2026-10-07.json'

def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def main() -> int:
    intake=load(INTAKE); providers=load(EXEC); cli=load(CLI); vtr=load(VTR)
    dashy=load(ROOT/'packages'/'vfharness'/'devtools'/'dashy-launchpad.json')
    ext=load(ROOT/'packages'/'vfharness'/'devtools'/'openclaw-candidate-audit.json')
    sources=intake.get('sources') or []
    assert len(sources)==17, f'expected 17 sources, got {len(sources)}'
    repos=[row['repo'] for row in sources]
    assert len(repos)==len(set(repos)), 'duplicate repo source'
    assert {row['priority'] for row in sources} <= {'P0','P1','P2','P3'}
    assert all(row.get('runtimeAuthority') is False for row in sources), 'repo intake granted runtime authority'
    rules=providers['rules']
    assert rules['printerMutationViaGenericGui'] is False
    assert rules['socialMutationViaGenericGui'] is False
    assert rules['customerSendViaGenericGui'] is False
    order=providers['selectionOrder']
    assert order == ['API_OR_MCP','CLI','DETERMINISTIC_DESKTOP_AUTOMATION','COMPUTER_USE','VISION_FALLBACK']
    p={row['id']:row for row in providers['providers']}
    assert p['cua']['state']=='STAGED_PILOT' and p['cua']['runtimeAuthority'] is False
    assert p['ufo']['state']=='RESEARCH_COMPARE_AFTER_CUA' and p['ufo']['runtimeAuthority'] is False
    audits={row['id']:row for row in intake['candidateAudits']}
    for forbidden in ('print-start','upload','heating','motion'):
        assert forbidden in audits['bambu-cli']['denied']
    assert 'raw-arbitrary-jsx-runtime' in audits['adobe-automator']['denied']
    assert audits['dashy']['decision']=='LAUNCHPAD_ONLY'
    assert audits['agent-passport']['decision']=='PATTERN_ONLY_PENDING_LICENSE_REVIEW'
    tool_ids=[row['id'] for row in cli['tools']]
    assert len(tool_ids)==len(set(tool_ids)), 'duplicate CLI tool'
    assert cli['hosts']['Chris']['observed']['gh'] is True
    assert cli['hosts']['MacMiniOffice.local']['observed']['jq'] is True
    assert dashy['role']=='READ_ONLY_LAUNCHPAD_NOT_CONTROL_PLANE' and dashy['state']=='BLOCKED_PREREQUISITE'
    assert dashy['observedHosts']['Chris']['docker'] is False and dashy['observedHosts']['MacMiniOffice.local']['docker'] is False
    assert ext['runtimeAuthorityGranted'] is False
    verdicts={row['id']:row['verdict'] for row in ext['candidates']}
    assert verdicts['bambu-cli']=='READ_ONLY_ADAPTER_AUDIT'
    assert verdicts['adobe-automator']=='COMPARE_ONLY'
    assert verdicts['agent-passport']=='PATTERN_ONLY_PENDING_LICENSE_REVIEW'
    assert (ROOT/'scripts'/'vf_skill_eval.py').is_file()
    assert vtr['status']=='PASS'
    assert vtr['test']['observed_color_count'] <= 4
    assert set(vtr['test']['observed_svg_colors']) <= set(vtr['test']['palette'])
    assert vtr['runtime_authority'] is False and vtr['printer_control'] is False
    assert vtr['promotion'].startswith('BLOCKED_')
    skill=(ROOT/'packages'/'vfharness'/'SKILL.md').read_text(encoding='utf-8')
    assert 'playbooks/skill-intake-evaluation.md' in skill
    assert 'playbooks/automation-standards.md' in skill
    print('OK repo-intake sources=17 authority=none vtracer=PASS palette<=4 cua=STAGED ufo=AFTER_CUA')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
