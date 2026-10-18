#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT/'packages'/'vfharness'/'devtools'/'repo-intake-2026-10-07.json'
EXEC = ROOT/'packages'/'vfharness'/'devtools'/'execution-providers.json'
CLI = ROOT/'packages'/'vfharness'/'devtools'/'approved-cli.json'
VTR = ROOT/'packages'/'vfharness'/'state'/'vtracer-pilot-2026-10-07.json'
CUA = ROOT/'packages'/'vfharness'/'state'/'cua-pilot-complete-2026-10-08.json'
DASHY_RECEIPT = ROOT/'packages'/'vfharness'/'state'/'dashy-launchpad-smoke-2026-10-08.json'

def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def main() -> int:
    intake=load(INTAKE); providers=load(EXEC); cli=load(CLI); vtr=load(VTR)
    dashy=load(ROOT/'packages'/'vfharness'/'devtools'/'dashy-launchpad.json')
    cua_receipt=load(CUA); dashy_receipt=load(DASHY_RECEIPT)
    ext=load(ROOT/'packages'/'vfharness'/'devtools'/'openclaw-candidate-audit.json')
    sources=intake.get('sources') or []
    assert len(sources)==17, f'expected 17 sources, got {len(sources)}'
    repos=[row['repo'] for row in sources]
    assert len(repos)==len(set(repos)), 'duplicate repo source'
    assert {row['priority'] for row in sources} <= {'P0','P1','P2','P3'}
    assert all(row.get('runtimeAuthority') is False for row in sources), 'repo intake granted runtime authority'
    rules=providers['rules']
    # Capability engineering is allowed, but this registry cannot mint execution authority.
    assert rules['sensitiveCapabilityDevelopmentAllowed'] is True
    assert rules['capabilityDevelopmentDoesNotAuthorizeExecution'] is True
    assert rules['computerUseSensitiveExecutionRequiresOwnerDirectionOrExplicitApproval'] is True
    assert rules['computerUseCannotInheritOtherProviderAuthority'] is True
    assert rules['computerUseStillRequiresCanonicalEffectPolicy'] is True
    assert rules['printerMutationViaGenericGui'] is False
    assert rules['socialMutationViaGenericGui'] is False
    assert rules['customerSendViaGenericGui'] is False
    assert rules['credentialsMustUseExistingSecretBoundary'] is True
    order=providers['selectionOrder']
    assert order == ['API_OR_MCP','CLI','DETERMINISTIC_DESKTOP_AUTOMATION','COMPUTER_USE','VISION_FALLBACK']
    p={row['id']:row for row in providers['providers']}
    assert p['cua']['state']=='PILOT_VERIFIED_BOUNDED' and p['cua']['runtimeAuthority'] is False
    assert p['cua']['activationAllowed'] is False
    assert p['cua']['sensitiveCapabilityDevelopmentAllowed'] is True
    assert p['cua']['sensitiveExternalEffectExecutionAllowedNow'] is False
    assert p['cua']['authorizationModel']=='OWNER_DIRECTED_OR_EXPLICIT_BOUNDED_APPROVAL_PLUS_CANONICAL_EFFECT_GATE'
    constitution=(ROOT/'constitution'/'CONSTITUTION.md').read_text(encoding='utf-8')
    assert 'CAPABILITY_NOT_AUTHORITY_V1' in constitution
    assert 'runtimeAuthority=false, activationAllowed=false' in constitution
    assert 'policy_id: instagram.publish' in constitution
    assert 'policy_id: customer.whatsapp.send' in constitution
    assert 'CAPABILITY_NOT_AUTHORITY_V1' in (ROOT/'README.md').read_text(encoding='utf-8')
    assert p['ufo']['state']=='RESEARCH_PENDING_MATERIAL_CALCULATOR_GAP' and p['ufo']['runtimeAuthority'] is False
    assert p['ufo']['installed'] is False
    assert cua_receipt['promotion']=='BOUNDED_PILOT_VALIDATED_NOT_PRODUCTION_CONTROL'
    assert cua_receipt['runtimeAuthority'] is False and cua_receipt['boundary']['runtimeAuthority'] is False
    assert cua_receipt['officeGate']['verifiedAncestor'] is True and cua_receipt['officeGate']['status']=='PASS'
    assert cua_receipt['release']['standaloneZip']['verification']=='PASS'
    assert cua_receipt['release']['standaloneZip']['expectedSha256']==cua_receipt['release']['standaloneZip']['observedSha256']
    assert cua_receipt['guiSmoke']['status']=='PASS'
    assert cua_receipt['guiSmoke']['titleReadback'] is True and cua_receipt['guiSmoke']['textReadback'] is True
    assert cua_receipt['guiSmoke']['afterUiAText']=='Result: 42'
    assert cua_receipt['boundary']['desktopDisplay'] is False
    assert cua_receipt['boundary']['genericWindowEnumeration']=='REFUSED_OUTSIDE_MANIFEST'
    assert cua_receipt['ufo']['decision']=='RESEARCH_PENDING_MATERIAL_CALCULATOR_GAP'
    assert all(term in cua_receipt['boundary']['prohibited'] for term in (
        'printers','social-publishing','customer-sends','purchases','credential-entry'))
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
    assert dashy['role']=='READ_ONLY_LAUNCHPAD_NOT_CONTROL_PLANE'
    assert dashy['state']=='PILOT_DEPLOYED_READ_ONLY' and dashy['runtimeAuthority'] is False
    assert dashy['deployed']['runtimeAuthority'] is False and dashy['deployed']['managementApi'] is False
    assert dashy['deployed']['listenAddress']=='127.0.0.1' and dashy['deployed']['configReadOnly'] is True
    assert dashy['observedHosts']['Chris']['docker'] is False and dashy['observedHosts']['MacMiniOffice.local']['docker'] is False
    assert dashy_receipt['role']=='READ_ONLY_LAUNCHPAD_NOT_CONTROL_PLANE'
    assert dashy_receipt['status']=='PILOT_DEPLOYED_READ_ONLY' and dashy_receipt['runtimeAuthority'] is False
    assert dashy_receipt['deployment']['noRemoteBinding'] is True
    assert dashy_receipt['deployment']['disableConfiguration'] is True
    assert dashy_receipt['deployment']['preventWriteToDisk'] is True
    assert dashy_receipt['deployment']['preventLocalSave'] is True
    assert dashy_receipt['deployment']['managementApi'] is False and dashy_receipt['deployment']['controlPlane'] is False
    assert dashy_receipt['source']['expectedSha256']==dashy_receipt['source']['observedSha256']
    assert dashy_receipt['smoke']['status']=='PASS'
    assert dashy_receipt['smoke']['getIndex']==200 and dashy_receipt['smoke']['getConfig']==200
    assert dashy_receipt['smoke']['getApiConfig']==404 and dashy_receipt['smoke']['postConfig']==405
    assert dashy_receipt['smoke']['renderedVelvetOffice'] is True
    assert dashy_receipt['smoke']['renderedControlCenterLink'] is True
    assert dashy_receipt['smoke']['renderedApiHealthLink'] is True
    assert dashy_receipt['sourceOfTruth'] is False and dashy_receipt['ownsApprovals'] is False
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
    pilot_root=ROOT/'packages'/'vfharness'/'devtools'/'pilots'
    for rel in ('cua/README.md','cua/CuaSmokeFixture.cs','cua/pilot-capabilities.yaml','cua/Start-CuaPilot.ps1','cua/Run-CuaSmoke.ps1','dashy/README.md','dashy/serve-readonly.js','dashy/conf.yml','dashy/Run-DashyBrowserSmoke.ps1'):
        assert (pilot_root/rel).is_file(), f'missing pilot source: {rel}'
    assert '    display: false' in (pilot_root/'cua'/'pilot-capabilities.yaml').read_text(encoding='utf-8')
    server_source=(pilot_root/'dashy'/'serve-readonly.js').read_text(encoding='utf-8')
    assert "const host = '127.0.0.1'" in server_source
    assert "'No control APIs'" in server_source and "'Read-only launchpad'" in server_source
    config=(pilot_root/'dashy'/'conf.yml').read_text(encoding='utf-8')
    assert all(flag in config for flag in ('disableConfiguration: true','preventWriteToDisk: true','preventLocalSave: true'))
    print('OK repo-intake sources=17 authority=none vtracer=PASS cua=BOUNDED_SMOKE_PASS ufo=RESEARCH_PENDING dashy=READ_ONLY_SMOKE_PASS')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
