#!/usr/bin/env python3
"""Behavioral regressions for VF evidence integrity; fixtures are NOT real QA."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
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
    guide = write(evidence.PRODUCT_TRUTH_GUIDE, b'Test-only Product Truth guide.')
    refs = [dict(image(f'refs/{i}.png', (12, 12), (i * 50, 15, 20)), role='STYLE_ONLY') for i in range(1, 4)]
    style_roles = sorted(evidence.STYLE_REFERENCE_ROLES)
    asset_rows = [
        {'filename': 'Velvet-Factory-Project-Authority-v6.txt', 'sha256': authority['sha256'],
         'required_for': 'all_requests', 'role': 'authority'},
        *[{'sha256': x['sha256'], 'required_for': 'visual_work', 'role': style_roles[i]}
          for i, x in enumerate(refs)],
        {'filename': 'Velvet-Factory-PRODUCT-TRUTH-GUIDE-v1.txt', 'sha256': guide['sha256'],
         'required_for': 'visual_work', 'role': 'text_only_product_truth_fidelity_qa_not_style'},
    ]
    assets = write(evidence.ASSETS, {'contract_version': evidence.PROJECT_CONTRACT_VERSION,
        'revision': evidence.PROJECT_REVISION, 'bundle_id': evidence.PROJECT_BUNDLE_ID,
        'assets': asset_rows})
    source = dict(image('source.png', (60, 75), (100, 80, 25)), role='PRODUCT_SOURCE')
    import vf_publish_bridge as bridge
    master = image('master.png', (120, 150), (40, 80, 25))
    bridge.normalize_image(root/'master.png', root/'final.jpg', int(bridge.load_config()['imageNormalization']['quality']))
    output = dict(path='final.jpg', sha256=evidence.digest(root/'final.jpg'), role='FINAL_VISUAL', normalization_source=master)
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
        guide = evidence.canonical_text_digest(self.root / evidence.PRODUCT_TRUTH_GUIDE)
        for name, value in [('AUTHORITY_SHA', authority), ('ASSETS_SHA', assets),
                            ('PRODUCT_TRUTH_GUIDE_SHA', guide)]:
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
        (self.root / 'final.jpg').unlink()
        self.assertFalse(self.result()['ok'])
    def test_changed_bytes(self):
        (self.root / 'final.jpg').write_bytes(b'changed')
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


    def _rebind_test_visual(self, path, payload, full_alias=None):
        visual = dict(self.write(path, payload), role='FINAL_VISUAL')
        if 'normalization_source' in self.ev['outputs'][0]:
            visual['normalization_source'] = self.ev['outputs'][0]['normalization_source']
        self.ev['outputs'][0] = visual
        self.ev['package_sha256'] = evidence.package_digest(self.ev['outputs'])
        review = json.loads((self.root / 'review.json').read_text())
        review['package_sha256'] = self.ev['package_sha256']
        full = self.write(full_alias, payload) if full_alias else visual
        review['views'][0].update(artifact_sha256=visual['sha256'], full=full)
        self.ev['review'] = self.write('review.json', review)

    def test_text_is_not_product_source(self):
        self.ev['sources'] = [dict(self.write('source.txt', b'not pixels'), role='PRODUCT_SOURCE')]
        self.ev['stages'] = self.ev['stages'][:5]
        self.assertFalse(self.result('production')['ok'])

    def test_corrupt_image_is_not_product_source(self):
        self.ev['sources'] = [dict(self.write('source.png', b'not pixels'), role='PRODUCT_SOURCE')]
        self.ev['stages'] = self.ev['stages'][:5]
        self.assertFalse(self.result('production')['ok'])

    def test_corrupt_final_with_full_alias_is_blocked(self):
        self._rebind_test_visual('final.jpg', b'not pixels', 'full.bin')
        self._write_bound_approval()
        self.assertFalse(self.result()['ok'])
        self.assertFalse(self._approved_result()['ok'])

    def test_corrupt_video_with_valid_hash_is_blocked(self):
        self._rebind_test_visual('final.mp4', b'not video')
        self.assertFalse(self.result()['ok'])

    def test_valid_image_full_alias_cannot_skip_mobile_decode(self):
        self._rebind_test_visual('final.jpg', (self.root/'final.jpg').read_bytes(), 'full.bin')
        self.assertTrue(self.result()['ok'])
        review = json.loads((self.root/'review.json').read_text())
        review['views'][0]['mobile'] = self.write('mobile.png', b'not pixels')
        self.ev['review'] = self.write('review.json', review)
        self.assertFalse(self.result()['ok'])

    def test_image_cannot_be_final_mp4(self):
        self._rebind_test_visual('final.mp4', (self.root/'final.jpg').read_bytes())
        self.assertFalse(self.result()['ok'])

    def test_production_video_requires_real_decode(self):
        self.ev['sources'] = [dict(self.write('source.mp4', b'not video'), role='PRODUCT_SOURCE')]
        self.ev['stages'] = self.ev['stages'][:5]
        self.assertFalse(self.result('production')['ok'])

    def test_valid_mp4_delivery_decodes(self):
        import shutil, subprocess
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('real video smoke needs ffmpeg/ffprobe; runtime blocks without them')
        video = self.root/'smoke.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=s=120x150:d=0.1:r=10', '-c:v', 'mpeg4',
                        '-pix_fmt', 'yuv420p', str(video)], check=True, timeout=20)
        self._rebind_test_visual('final.mp4', video.read_bytes())
        self.manifest['format'] = 'reel'
        self.assertTrue(self.result()['ok'])

    def test_public_mp4_requires_hash_bound_normalization(self):
        import shutil, subprocess, struct
        import vf_publish_bridge as bridge
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.fail('Public video proof requires real ffmpeg and ffprobe')
        master = self.root/'edited-master.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=s=120x150:d=0.1:r=10', '-c:v', 'mpeg4',
                        '-pix_fmt', 'yuv420p', str(master)], check=True, timeout=20)
        normalized = self.root/'normalized.mp4'
        bridge.normalize_video(master, normalized)
        self._rebind_test_visual('final.mp4', normalized.read_bytes())
        self.manifest['format'] = 'reel'
        out = self.ev['outputs'][0]
        out.pop('normalization_source', None)
        def public_result():
            self.write('manifest.json', self.manifest)
            return evidence.validate(self.root, 'manifest.json', 'TEST', require_staging=True)
        self.assertTrue(self.result()['ok'], 'Private review remains possible')
        self.assertFalse(public_result()['ok'], 'Public MP4 requires normalization source')
        out['normalization_source'] = {'path': 'edited-master.mp4', 'sha256': '0'*64}
        self.assertFalse(public_result()['ok'], 'Master hash must match')
        out['normalization_source']['sha256'] = evidence.digest(master)
        verdict = public_result()
        self.assertTrue(verdict['ok'], verdict)
        payload = bytes(range(16)) + b'PRIVATE_TEST_METADATA'
        altered = normalized.read_bytes() + struct.pack('>I4s', len(payload)+8, b'uuid') + payload
        self._rebind_test_visual('final.mp4', altered)
        self.assertTrue(self.result()['ok'], 'Metadata is invisible to image review')
        self.assertFalse(public_result()['ok'], 'Rebinding QA cannot approve a tampered container')

    def test_review_png_requires_normalization_before_publication(self):
        path = self.root/'review.png'
        Image.new('RGB',(120,150),(4,90,20)).save(path)
        self._rebind_test_visual('review.png',path.read_bytes())
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'], 'PNG remains valid for owner review')
        self.assertFalse(self._approved_result()['ok'], 'Publication must use reviewed normalized bytes')

    def test_review_webp_requires_normalization_before_publication(self):
        path = self.root/'review.webp'
        Image.new('RGB',(120,150),(4,90,20)).save(path)
        self._rebind_test_visual('review.webp',path.read_bytes())
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'])
        self.assertFalse(self._approved_result()['ok'])

    def test_progressive_jpeg_is_not_publication_ready(self):
        path = self.root/'progressive.jpg'
        Image.new('RGB',(120,150),(4,90,20)).save(path,progressive=True)
        self._rebind_test_visual('progressive.jpg',path.read_bytes())
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'])
        self.assertFalse(self._approved_result()['ok'])

    def test_huge_video_rejected_before_decoder(self):
        import vf_media_integrity as media
        path=self.root/'oversized.mp4'; path.write_bytes(b'Test fixture')
        data={'format':{'format_name':'mov','duration':'1'},'streams':[
            {'codec_type':'video','width':1000000,'height':1000000,'avg_frame_rate':'30/1'}]}
        with patch.object(media.shutil,'which',side_effect=lambda x:x), patch.object(media,'run_bounded',return_value=json.dumps(data).encode()) as runner:
            with self.assertRaisesRegex(ValueError,'pixel budget'):
                media.inspect_media(path,'test')
            self.assertEqual(runner.call_count,1, 'Decode must not start')

    def test_long_video_rejected_before_decoder(self):
        import vf_media_integrity as media
        path=self.root/'too-long.mp4'; path.write_bytes(b'Test fixture')
        data={'format':{'format_name':'mov','duration':'86400'},'streams':[
            {'codec_type':'video','width':120,'height':150,'avg_frame_rate':'30/1'}]}
        with patch.object(media.shutil,'which',side_effect=lambda x:x), patch.object(media,'run_bounded',return_value=json.dumps(data).encode()) as runner:
            with self.assertRaisesRegex(ValueError,'duration/stream budget'):
                media.inspect_media(path,'test')
            self.assertEqual(runner.call_count,1)

    def test_nonfinite_video_budget_rejected(self):
        import vf_media_integrity as media
        for duration in ('NaN','inf','0'):
            with self.assertRaises(ValueError):
                media._video_budget({'format':{'duration':duration},'streams':[{}]})

    def test_decoder_memory_limit_is_real(self):
        from vf_media_limits import run_bounded
        with self.assertRaises(ValueError):
            run_bounded([sys.executable,'-c','x=bytearray(512*1024*1024)'],memory_bytes=128*1024*1024)

    def test_decoder_stdout_is_bounded(self):
        from vf_media_limits import run_bounded, OUTPUT_BYTES
        with self.assertRaises(ValueError):
            run_bounded([sys.executable,'-c',f'print("x"*{OUTPUT_BYTES+100})'],capture=True)

    def test_decoder_stderr_is_not_buffered(self):
        from vf_media_limits import run_bounded
        result=run_bounded([sys.executable,'-c','import sys; sys.stderr.write("x"*1000000); print("ok")'],capture=True)
        self.assertEqual(result.strip(),b'ok')

    def test_decoder_time_is_bounded(self):
        from vf_media_limits import run_bounded
        with self.assertRaises(ValueError):
            run_bounded([sys.executable,'-c','import time; time.sleep(20)'],timeout=1)

    def _assert_private_jpeg_metadata_blocked(self, payload, marker=None):
        original=(self.root/'final.jpg').read_bytes()
        data=original+payload if marker is None else original[:2]+b'\xff'+bytes([marker])+(len(payload)+2).to_bytes(2,'big')+payload+original[2:]
        self._rebind_test_visual('private.jpg',data)
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'], 'Private owner review can inspect the image')
        self.assertFalse(self._approved_result()['ok'], 'Private JPEG metadata must never be published')

    def test_xmp_metadata_blocks_publication(self):
        self._assert_private_jpeg_metadata_blocked(b'http://ns.adobe.com/xap/1.0/\0<fixture>private-test</fixture>',0xe1)

    def test_iptc_metadata_blocks_publication(self):
        self._assert_private_jpeg_metadata_blocked(b'Photoshop 3.0\0'+b'8BIM\x04\x04\0\0\0\0\0\x0cprivate-test',0xed)

    def test_unknown_app_metadata_blocks_publication(self):
        self._assert_private_jpeg_metadata_blocked(b'private-test',0xec)

    def test_trailing_jpeg_payload_blocks_publication(self):
        self._assert_private_jpeg_metadata_blocked(b'private-test')

    def test_hidden_entropy_payload_cannot_receive_publication_approval(self):
        original=(self.root/'final.jpg').read_bytes()
        self._rebind_test_visual('hidden.jpg',original[:-2]+b'XMP_PRIVATE_payload_without_ff'+original[-2:])
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'])
        self.assertFalse(self._approved_result()['ok'], 'Entropy padding must not be published')

    def test_duplicate_jfif_cannot_receive_publication_approval(self):
        original=(self.root/'final.jpg').read_bytes()
        self.assertEqual(original[2:4],b'\xff\xe0')
        end=4+int.from_bytes(original[4:6],'big')
        self._rebind_test_visual('duplicates.jpg',original[:end]+original[2:end]*100+original[end:])
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'])
        self.assertFalse(self._approved_result()['ok'], 'Duplicate JFIF payload must not be published')

    def test_public_jpeg_requires_normalization_source(self):
        self.ev['outputs'][0].pop('normalization_source')
        self._write_bound_approval()
        self.assertTrue(self.result()['ok'])
        self.assertFalse(self._approved_result()['ok'])

    def test_normalization_source_hash_is_checked(self):
        self.ev['outputs'][0]['normalization_source']['sha256']='0'*64
        self._write_bound_approval()
        self.assertFalse(self._approved_result()['ok'])

    def test_tampered_final_cannot_self_certify_normalization(self):
        original=(self.root/'final.jpg').read_bytes()
        payload=original[:-2]+b'XMP_PRIVATE_payload_without_ff'+original[-2:]
        self._rebind_test_visual('self.jpg',payload)
        out=self.ev['outputs'][0]
        out['normalization_source']={'path':'self.jpg','sha256':out['sha256']}
        self._write_bound_approval()
        self.assertFalse(self._approved_result()['ok'])

    def _write_bound_approval(self, include_digest=True):
        self.write('manifest.json', self.manifest)
        folder = self.root / 'packages/vfgrowth/preflight'
        folder.mkdir(parents=True, exist_ok=True)
        body = legacy_text().replace('a' * 64, self.ev['outputs'][0]['sha256']).replace('b' * 64, self.ev['package_sha256'])
        body = body.replace(': FAIL', ': PASS').replace('synthetic_subject_change: PRESENT', 'synthetic_subject_change: NONE')
        body += '\ncreative_manifest_ref: manifest.json\nreference_match_gate: PASS\ncreative_director_lock: PASS'
        if include_digest:
            body += '\ncreative_manifest_sha256: ' + evidence.digest(self.root / 'manifest.json')
        (folder / 'TEST.md').write_text(body, encoding='utf-8')
        return folder

    def _approved_result(self):
        folder = self.root / 'packages/vfgrowth/preflight'
        with patch.object(send, 'ROOT', self.root), patch.object(send, 'PREFLIGHT_ROOT', folder):
            return send.validate_publication_approval('packages/vfgrowth/preflight/TEST.md', 'TEST', 'post', self.ev['package_sha256'])

    def test_approval_requires_manifest_digest(self):
        self._write_bound_approval(include_digest=False)
        result = self._approved_result()
        self.assertFalse(result['ok'], result)
        self.assertIn('creative_manifest_sha256', ' '.join(result['problems']))

    def test_rebound_evidence_invalidates_old_approval(self):
        self._write_bound_approval()
        self.assertTrue(self._approved_result()['ok'])
        decomposition = json.loads((self.root / 'decomposition.json').read_text())
        decomposition['light'] = 'A different lighting judgment after approval'
        self.ev['reference_decomposition'] = self.write('decomposition.json', decomposition)
        self.write('manifest.json', self.manifest)
        self.assertTrue(self.result()['ok'], 'Changed evidence remains internally consistent')
        changed = self._approved_result()
        self.assertFalse(changed['ok'], 'Old approval must not authorize rebound evidence')
        self.assertIn('manifest', ' '.join(changed['problems']).lower())
        self._write_bound_approval()
        self.assertTrue(self._approved_result()['ok'], 'Explicit fresh binding must work')

    def _project_result(self, domain, *extra, env_extra=None):
        import io
        from contextlib import redirect_stdout
        import vf_project_preflight as project
        self.write('manifest.json', self.manifest)
        route = {'schemaVersion': 1, 'baselineAuthorities': [], 'domains': {
            'creative_publication': {'packs': ['vfom']},
            'instagram_action': {'packs': ['vfigos']}}}
        args = ['vf_project_preflight.py', '--domain', domain, '--manifest', 'manifest.json', '--content-id', 'TEST', *extra]
        out = io.StringIO()
        env_patch = {}
        if env_extra:
            env_patch = env_extra
        with patch.object(project, 'ROOT', self.root), patch.object(project, 'load_manifest', return_value=route), patch.object(sys, 'argv', args), redirect_stdout(out):
            if env_patch:
                with patch.dict(os.environ, env_patch, clear=False):
                    code = project.main()
            else:
                code = project.main()
        return code, json.loads(out.getvalue())

    def _mint_delivery_approval(self, *, mutation_tool='publish_image'):
        """Ephemeral Ed25519 receipt for tests — never production keys."""
        import base64
        import hashlib
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'packages'))
        from vfigos.approval.issuer.signing import issue_approval
        from vfigos.approval.keys_registry import KeyRegistry
        priv = Ed25519PrivateKey.generate()
        key_id = 'test-pub-evidence'
        registry = KeyRegistry.from_ephemeral(key_id, priv.public_key())
        digest = self.ev['package_sha256']
        media_bytes = b'publication-evidence-fixture-bytes'
        media_dig = hashlib.sha256(media_bytes).hexdigest()
        media_url = f'https://cas.example.test/sha256/{media_dig}/fixture.jpg'
        issued = issue_approval(
            private_key=priv,
            key_id=key_id,
            content_id='TEST',
            package_sha256=digest,
            mutation_tool=mutation_tool,
            mutation_payload={
                'image_url': media_url,
                'caption': 'fixture',
                'account': 'velvets_cloud',
            } if mutation_tool == 'publish_image' else {},
            media_artifacts=[{'bytes_b64': base64.b64encode(media_bytes).decode('ascii')}]
            if mutation_tool == 'publish_image'
            else None,
            media_byte_fetcher={media_url: media_bytes}.get,
            ttl_seconds=600,
        )
        self.assertTrue(issued['ok'], issued)
        receipt_path = self.root / 'delivery-approval.json'
        receipt_path.write_text(json.dumps(issued['receipt']), encoding='utf-8')
        reg_path = self.root / 'approval-registry.json'
        reg_path.write_text(json.dumps({
            'keys': [{
                'key_id': key_id,
                'algorithm': 'Ed25519',
                'public_key_b64': base64.b64encode(priv.public_key().public_bytes_raw()).decode('ascii'),
            }]
        }), encoding='utf-8')
        return receipt_path, reg_path, digest

    def test_instagram_action_uses_delivery_evidence(self):
        # Evidence alone is necessary but not sufficient — missing signed approval ⇒ BLOCKED.
        code, result = self._project_result('instagram_action')
        self.assertNotEqual(code, 0, result)
        self.assertEqual(result['publication_evidence_phase'], 'delivery')
        self.assertTrue(result['production_evidence']['ok'], result)
        self.assertFalse(result.get('delivery_authorized'))
        self.assertEqual(result['project_preflight'], 'BLOCKED')
        # With ephemeral signed approval bound to the package ⇒ PASS (advisory).
        receipt_path, reg_path, digest = self._mint_delivery_approval()
        code2, result2 = self._project_result(
            'instagram_action',
            '--delivery-approval', str(receipt_path),
            '--mutation-tool', 'publish_image',
            '--package-sha256', digest,
            env_extra={'VELVET_DELIVERY_APPROVAL_REGISTRY': str(reg_path)},
        )
        self.assertEqual(code2, 0, result2)
        self.assertTrue(result2.get('delivery_authorized'), result2)
        self.assertEqual(result2['publication_evidence_phase'], 'delivery')

    def test_explicit_review_delivery_accepts_complete_manifest(self):
        # Explicit --phase delivery also requires signed approval now.
        code, result = self._project_result('creative_publication', '--phase', 'delivery')
        self.assertNotEqual(code, 0, result)
        self.assertEqual(result['publication_evidence_phase'], 'delivery')
        self.assertTrue(result['production_evidence']['ok'], result)
        receipt_path, reg_path, digest = self._mint_delivery_approval()
        code2, result2 = self._project_result(
            'creative_publication',
            '--phase', 'delivery',
            '--delivery-approval', str(receipt_path),
            '--mutation-tool', 'publish_image',
            '--package-sha256', digest,
            env_extra={'VELVET_DELIVERY_APPROVAL_REGISTRY': str(reg_path)},
        )
        self.assertEqual(code2, 0, result2)
        self.assertEqual(result2['publication_evidence_phase'], 'delivery')
        self.assertTrue(result2.get('delivery_authorized'), result2)

    def test_instagram_action_cannot_downgrade_to_production(self):
        self.ev['stages'] = self.ev['stages'][:5]
        code, result = self._project_result('instagram_action', '--phase', 'production')
        self.assertNotEqual(code, 0, result)
        self.assertEqual(result['project_preflight'], 'BLOCKED')

    def test_creation_retains_production_phase(self):
        self.ev['stages'] = self.ev['stages'][:5]
        code, result = self._project_result('creative_publication')
        self.assertEqual(code, 0, result)
        self.assertEqual(result['publication_evidence_phase'], 'production')
        self.assertFalse(result['production_evidence']['publishAuthorized'])

    def test_generic_canva_transport_diagnostic_unchanged(self):
        report = {'channels': {'canva': {'ready': True}}}
        self.assertEqual(send.gate_channel(report, 'canva'), 0)

    def test_final_mov_requires_normalization(self):
        (self.root / 'final.jpg').rename(self.root / 'final.mov')
        self.ev['outputs'][0]['path'] = 'final.mov'
        review = json.loads((self.root / 'review.json').read_text())
        review['views'][0]['full']['path'] = 'final.mov'
        self.ev['review'] = self.write('review.json', review)
        self.assertFalse(self.result()['ok'], 'MOV cannot be labeled as reviewed MP4')

    def test_staging_mov_rejected_before_probe_or_network(self):
        import vf_publish_bridge as bridge
        path = self.root / 'reviewed.mov'
        path.write_bytes(b'Unnormalized MOV fixture')
        with patch.object(bridge.shutil, 'which', side_effect=AssertionError('MOV must be rejected before probing')):
            with self.assertRaisesRegex(ValueError, 'MOV.*MP4'):
                bridge.inspect_reviewed_asset(path, bridge.load_config())


    def test_actual_package_passes_combined_gate(self):
        folder = self.root / 'packages/vfgrowth/preflight'
        folder.mkdir(parents=True)
        text = legacy_text().replace('a' * 64, self.ev['outputs'][0]['sha256']).replace('b' * 64, self.ev['package_sha256'])
        text = text.replace(': FAIL', ': PASS').replace('synthetic_subject_change: PRESENT', 'synthetic_subject_change: NONE')
        text += '\ncreative_manifest_ref: manifest.json\nreference_match_gate: PASS\ncreative_director_lock: PASS'
        text += '\ncreative_manifest_sha256: ' + evidence.digest(self.root / 'manifest.json')
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
       'hero_transformation_evidence': 'missing-final.jpg', 'visual_output_evidence': 'missing-final.jpg',
       'creative_edit_evidence': 'missing-final.jpg', 'creative_treatment_categories': 'composition,lighting,background',
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
