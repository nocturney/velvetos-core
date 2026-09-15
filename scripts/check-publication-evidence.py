#!/usr/bin/env python3
"""Behavioral regressions for VF evidence integrity; fixtures are NOT real QA."""
from __future__ import annotations
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import vf_publication_evidence as evidence
import vf_send_preflight as send


def fixture(root):
    def write(path, body):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            target.write_bytes(body)
        else:
            target.write_text(json.dumps(body), encoding='utf-8')
        return {'path': path, 'sha256': evidence.digest(target)}
    def image(path, size, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', size, value).save(target)
        return {'path': path, 'sha256': evidence.digest(target)}
    policy = {'publicationRoute': {'version': 1, 'mode': 'fail_closed',
               'rejectedArtifactSha256': [], 'rejectedDirectionFamilies': ['rejected-family']}}
    write(evidence.POLICY, policy)
    authority = write(evidence.AUTHORITY, b'Test-only authority; not deployment or real creative evidence.')
    refs = [dict(image(f'refs/{i}.png', (12, 12), (i * 50, 15, 20)), role='STYLE_ONLY') for i in range(1, 4)]
    assets = write(evidence.ASSETS, {'contract_version': 6, 'revision': '6.2',
        'bundle_id': 'VF-PROJECT-6.2-DETAIL-TRUTH',
        'assets': [{'sha256': x['sha256'], 'required_for': 'visual_work'} for x in refs]})
    source = dict(image('source.png', (60, 75), (100, 80, 25)), role='PRODUCT_SOURCE')
    output = dict(image('final.png', (120, 150), (40, 80, 25)), role='FINAL_VISUAL')
    mobile = image('mobile.png', (40, 50), (40, 80, 25))
    text = dict(write('caption.txt', b'Test caption.'), role='FINAL_TEXT')
    lint = write('lint.json', {'visible_text_gate': 'PASS', 'lint': {'status': 'pass'},
        'surface': 'public-social', 'text_sha256': text['sha256']})
    report = write('workflow.txt', b'Test-only workflow attestation, not real execution.')
    decomposition = write('decomposition.json', {'reference_sha256': [x['sha256'] for x in refs],
        **{x: 'Specific test fixture observation' for x in evidence.AXES}})
    outputs = [output, text]
    package = evidence.package_digest(outputs)
    review = write('review.json', {'job_id': 'TEST', 'package_sha256': package,
        'source_sha256': [source['sha256']], 'reference_sha256': [x['sha256'] for x in refs],
        'checks': {x: 'PASS' for x in evidence.CHECKS}, 'synthetic_subject_change': 'NONE',
        'reviewer': 'TEST-ONLY', 'reference_match_observations': 'Test observations, not aesthetic validation.',
        'reviewed_at': '2026-01-01T00:00:00Z',
        'views': [{'artifact_sha256': output['sha256'], 'full': output, 'mobile': mobile}]})
    ev = {'version': 1, 'policy_sha256': evidence.digest(root / evidence.POLICY),
        'public_intent': 'showcase', 'direction': {'family_id': 'valid-family', 'status': 'LOCKED'},
        'direction_history': [], 'tools': ['source-compositor'], 'sources': [source], 'references': refs,
        'reference_decomposition': decomposition, 'product_protection': {'method': 'SOURCE_MASK_COMPOSITE',
            'evidence': report, 'protected_regions': ['whole-product', 'eyes']},
        'stages': [{'name': n, 'status': 'PASS', 'started_at': '2026-01-01T00:00:00Z',
                    'completed_at': '2026-01-01T00:00:00Z', 'evidence': [report]} for n in evidence.STAGES],
        'outputs': outputs, 'copy_receipts': [lint], 'package_sha256': package, 'review': review}
    manifest = {'jobId': 'TEST', 'format': 'post', 'publicationEvidence': ev}
    write('manifest.json', manifest)
    return manifest, write, authority['sha256'], assets['sha256']


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest, self.write, authority, assets = fixture(self.root)
        self.ev = self.manifest['publicationEvidence']
        for name, value in [('AUTHORITY_SHA', authority), ('ASSETS_SHA', assets)]:
            p = patch.object(evidence, name, value)
            p.start(); self.addCleanup(p.stop)
    def result(self, phase='delivery'):
        self.write('manifest.json', self.manifest)
        return evidence.validate(self.root, 'manifest.json', 'TEST', phase)
    def test_valid_fixture_integrity_not_publish(self):
        result = self.result()
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['publishAuthorized'])
    def test_canva_blocked(self):
        for tool in ['Canva.generate-design', 'vfcanva', 'CANVA.export']:
            self.ev['tools'] = [tool]
            self.assertFalse(self.result()['ok'])
    def test_missing_output(self):
        (self.root / 'final.png').unlink()
        self.assertFalse(self.result()['ok'])
    def test_changed_bytes(self):
        (self.root / 'final.png').write_bytes(b'changed')
        self.assertFalse(self.result()['ok'])
    def test_stale_policy(self):
        self.ev['policy_sha256'] = '0' * 64
        self.assertFalse(self.result()['ok'])
    def test_style_cannot_supply_product(self):
        self.ev['sources'] = [dict(self.ev['references'][0], role='PRODUCT_SOURCE')]
        self.assertFalse(self.result()['ok'])
    def test_unknown_reference_identity(self):
        self.ev['references'][0] = dict(self.ev['sources'][0], role='STYLE_ONLY')
        self.assertFalse(self.result()['ok'])
    def test_rejected_family_and_parent(self):
        self.ev['direction']['family_id'] = 'rejected-family'
        self.assertFalse(self.result()['ok'])
        self.ev['direction']['family_id'] = 'new-name'
        self.ev['direction']['derived_from_families'] = ['rejected-family']
        self.assertFalse(self.result()['ok'])
    def test_missing_early_stage(self):
        self.ev['stages'].pop(3)
        self.assertFalse(self.result()['ok'])
    def test_unproven_stage(self):
        self.ev['stages'][4]['status'] = 'UNPROVEN'
        self.assertFalse(self.result()['ok'])
    def test_wrong_order(self):
        self.ev['stages'][0], self.ev['stages'][1] = self.ev['stages'][1], self.ev['stages'][0]
        self.assertFalse(self.result()['ok'])
    def test_production_phase_not_approval(self):
        self.ev['stages'] = self.ev['stages'][:5]
        result = self.result('production')
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['publishAuthorized'])
    def test_reference_failure_in_review(self):
        review = json.loads((self.root / 'review.json').read_text())
        review['checks']['reference_match'] = 'FAIL'
        self.ev['review'] = self.write('review.json', review)
        self.assertFalse(self.result()['ok'])
    def test_changed_caption(self):
        self.ev['outputs'][1] = dict(self.write('caption.txt', b'Changed caption.'), role='FINAL_TEXT')
        self.assertFalse(self.result()['ok'])
    def test_missing_mobile(self):
        (self.root / 'mobile.png').unlink()
        self.assertFalse(self.result()['ok'])
    def test_fake_mobile_dimensions(self):
        Image.new('RGB', (240, 300), (1, 2, 3)).save(self.root / 'mobile.png')
        review = json.loads((self.root / 'review.json').read_text())
        review['views'][0]['mobile']['sha256'] = evidence.digest(self.root / 'mobile.png')
        self.ev['review'] = self.write('review.json', review)
        self.assertFalse(self.result()['ok'])
    def test_malformed_json_fails_closed(self):
        (self.root / 'manifest.json').write_text('{"jobId":"TEST","jobId":"other"}')
        self.assertFalse(evidence.validate(self.root, 'manifest.json', 'TEST')['ok'])
    def test_escape_path(self):
        self.ev['sources'][0]['path'] = '../secret.txt'
        self.assertFalse(self.result()['ok'])
    def test_raw_passthrough(self):
        self.ev['outputs'][0] = dict(self.ev['sources'][0], role='FINAL_VISUAL')
        self.assertFalse(self.result()['ok'])


    def test_actual_package_passes_combined_gate(self):
        folder = self.root / 'packages/vfgrowth/preflight'
        folder.mkdir(parents=True)
        text = legacy_text().replace('a' * 64, self.ev['outputs'][0]['sha256']).replace('b' * 64, self.ev['package_sha256'])
        text = text.replace(': FAIL', ': PASS').replace('synthetic_subject_change: PRESENT', 'synthetic_subject_change: NONE')
        text += '\ncreative_manifest_ref: manifest.json\nreference_match_gate: PASS\ncreative_director_lock: PASS'
        (folder / 'TEST.md').write_text(text, encoding='utf-8')
        with patch.object(send, 'ROOT', self.root), patch.object(send, 'PREFLIGHT_ROOT', folder):
            result = send.validate_publication_approval('packages/vfgrowth/preflight/TEST.md', 'TEST', 'post', self.ev['package_sha256'])
            self.assertTrue(result['ok'], result)
            mismatch = send.validate_publication_approval('packages/vfgrowth/preflight/TEST.md', 'TEST', 'reel', self.ev['package_sha256'])
            self.assertFalse(mismatch['ok'])

    def test_direct_bridge_write_requires_evidence(self):
        import vf_publish_bridge as bridge
        file = self.root / 'unapproved.jpg'
        Image.new('RGB', (120, 150), (40, 80, 25)).save(file)
        metadata = {'approvalRef':'missing.md', 'correlation':'TEST'}
        with patch.object(bridge, 'api_request', side_effect=AssertionError('NETWORK MUST NOT RUN')):
            with self.assertRaisesRegex(ValueError, 'format and --package-sha256'):
                bridge.stage_to_github(file, metadata, bridge.load_config())

    def test_register_boolean_cannot_mark_approved(self):
        import vf_publish_handoff as handoff
        file = self.root / 'unapproved.jpg'
        Image.new('RGB', (120, 150), (40, 80, 25)).save(file)
        with patch.object(handoff,'ROOT',self.root), patch.object(handoff,'HANDOFF_DIR',self.root/'handoff'), patch.object(handoff,'PUBLICATIONS_DIR',self.root/'publications'):
            with self.assertRaisesRegex(ValueError, 'format and --package-sha256'):
                handoff.register_local_export(correlation='TEST', file_path=file, approval_ref='missing.md', source_ref='source', frame_index=1, public_release_approved=True)
        self.assertFalse((self.root/'handoff/TEST.json').exists())

    def test_bridge_boolean_is_not_authorization(self):
        import argparse
        import vf_publish_bridge as bridge
        file = self.root / 'unapproved.jpg'
        Image.new('RGB', (120, 150), (40, 80, 25)).save(file)
        args = argparse.Namespace(file=str(file), correlation='TEST', approval_ref='missing.md', source_ref='source', public_release_approved=True)
        with patch.object(bridge, 'stage_to_github', side_effect=AssertionError('NETWORK MUST NOT RUN')):
            with self.assertRaisesRegex(ValueError, 'format and --package-sha256'):
                bridge.cmd_prepare(args, True)


def legacy_text():
    """An apparently approved v3 record with nonexistent files and failed truth."""
    fields = {'publish_gate_schema': '3', 'publish_gate': 'PASS', 'approval_invalidated': 'false',
       'visual_standard_canva_asset_id': send.VELVET_VISUAL_STANDARD_ASSET,
       'visual_standard_artifact_sha256': send.VELVET_VISUAL_STANDARD_SHA256,
       'visual_standard_document': send.VELVET_VISUAL_STANDARD_DOCUMENT,
       'product_truth_source_refs': 'missing-source.jpg', 'generated_brand_mark': 'NONE',
       'logo_usage': 'NONE', 'logo_source_ref': 'NONE', 'logo_render_method': 'NONE',
       'content_rubric_total': '23/25', 'artifact_digest': 'a' * 64,
       'qa_scope': 'exact-final-render', 'source_material_state': 'RAW',
       'qa_reviewed_at': '2026-01-01T00:00:00Z', 'final_package_sha256': 'b' * 64,
       'raw_passthrough': 'false', 'source_edit_mode': 'DETERMINISTIC_COMPOSITE',
       'hero_transformation_evidence': 'missing-final.png', 'visual_output_evidence': 'missing-final.png',
       'creative_edit_evidence': 'missing-final.png', 'creative_treatment_categories': 'composition,lighting,background',
       'audio_gate': 'N/A', 'product_truth_gate': 'FAIL', 'source_subject_match': 'FAIL',
       'subject_identity_integrity': 'FAIL', 'synthetic_subject_change': 'PRESENT'}
    keys = ('visual_standard_gate visible_text_gate fact_gate brand_guardian copy_qa readability contrast '
       'creative_treatment brand_treatment commercial_visual_qa scroll_stop_qa derivative_is_distinct_from_source '
       'visual_edit_performed creative_delta_gate exact_final_visual_qa public_cta_gate brand_asset_gate public_phone_absent')
    fields.update({x: 'PASS' for x in keys.split()})
    return '\n'.join(f'{k}: {v}' for k, v in fields.items())


class IntegrationTests(unittest.TestCase):
    def test_legacy_fake_approval_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / 'packages/vfgrowth/preflight'; folder.mkdir(parents=True)
            (folder / 'TEST.md').write_text(legacy_text(), encoding='utf-8')
            with patch.object(send, 'ROOT', root), patch.object(send, 'PREFLIGHT_ROOT', folder):
                result = send.validate_publication_approval('packages/vfgrowth/preflight/TEST.md', 'TEST', 'post', 'b' * 64)
            self.assertFalse(result['ok'], 'FALSE POSITIVE: missing files / failed Product Truth accepted')


if __name__ == '__main__':
    unittest.main(verbosity=2)
