#!/usr/bin/env python3
"""Real media privacy regressions. Generated fixtures are not product evidence."""
from __future__ import annotations
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import vf_video_normalization as video

MARKER = b'PRIVATE_TEST_METADATA_4f219'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, args)],
                   check=True, timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
                        '-show_streams', '-show_chapters', '-of', 'json', str(path)], timeout=20))


class VideoNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            raise RuntimeError('Video privacy regressions require real ffmpeg and ffprobe')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.master = self.root / 'master.mp4'
        self.output = self.root / 'normalized.mp4'

    def make_source(self, audio=False, secret=False):
        args = ['-f', 'lavfi', '-i', 'testsrc2=s=120x150:r=10:d=0.4']
        if audio:
            args += ['-f', 'lavfi', '-i', 'sine=frequency=600:duration=0.4', '-c:a', 'aac']
        args += ['-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p']
        if secret:
            args += ['-metadata:s:v:0', 'handler_name=' + MARKER.decode(),
                     '-metadata', 'comment=' + MARKER.decode(),
                     '-bsf:v', 'h264_metadata=sei_user_data=0123456789abcdef0123456789abcdef+' + MARKER.decode()]
        ffmpeg(*args, self.master)
        if secret:
            payload = bytes(range(16)) + MARKER
            with self.master.open('ab') as out:
                out.write(struct.pack('>I4s', len(payload) + 8, b'uuid') + payload)
        return self.master

    def test_private_container_and_bitstream_metadata_removed(self):
        self.make_source(secret=True)
        self.assertIn(MARKER, self.master.read_bytes())
        original = sha(self.master)
        video.normalize_video(self.master, self.output)
        self.assertFalse(MARKER in self.output.read_bytes(), 'private metadata survived normalization')
        self.assertEqual(sha(self.master), original)
        streams = probe(self.output)['streams']
        self.assertEqual([x['codec_type'] for x in streams], ['video'])

    def test_subtitles_chapters_and_extra_tracks_removed(self):
        subtitle = self.root / 'private.srt'
        subtitle.write_text('1\n00:00:00,000 --> 00:00:00,400\n' + MARKER.decode() + '\n', encoding='utf-8')
        chapters = self.root / 'chapters.txt'
        chapters.write_text(';FFMETADATA1\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=400\ntitle=' + MARKER.decode() + '\n', encoding='utf-8')
        ffmpeg('-f','lavfi','-i','testsrc2=s=120x150:r=10:d=0.4',
               '-f','lavfi','-i','sine=duration=0.4', '-f','srt','-i',subtitle,
               '-f','ffmetadata','-i',chapters,
               '-map','0:v:0','-map','1:a:0','-map','1:a:0','-map','2:s:0',
               '-map_chapters','3','-c:v','libx264','-threads','1','-c:a','aac','-c:s','mov_text', self.master)
        video.normalize_video(self.master, self.output)
        data = probe(self.output)
        self.assertEqual([s['codec_type'] for s in data['streams']], ['video', 'audio'])
        self.assertEqual(data['chapters'], [])
        self.assertFalse(MARKER in self.output.read_bytes(), 'private metadata survived normalization')

    def test_silent_output_reproduces_exact_bytes(self):
        self.make_source()
        video.normalize_video(self.master, self.output)
        video.verify_video_normalization(self.master, sha(self.master), sha(self.output),
                                         {'videoNormalization': {'maxBytes': video.MAX_OUTPUT_BYTES}})

    def test_audio_output_reproduces_exact_bytes(self):
        self.make_source(audio=True, secret=True)
        video.normalize_video(self.master, self.output)
        second = self.root / 'second.mp4'
        video.normalize_video(self.master, second)
        self.assertEqual(sha(second), sha(self.output))
        self.assertFalse(MARKER in self.output.read_bytes())
        self.assertEqual([x['codec_type'] for x in probe(second)['streams']], ['video', 'audio'])

    def test_edited_master_hash_mismatch_blocks(self):
        self.make_source()
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            video.normalize_video(self.master, self.output, expected_source_sha256='0' * 64)
        self.assertFalse(self.output.exists())

    def test_tampered_public_video_cannot_self_certify(self):
        self.make_source(secret=True)
        with self.assertRaisesRegex(ValueError, 'not the exact canonical'):
            video.verify_video_normalization(self.master, sha(self.master), sha(self.master),
                                             {'videoNormalization': {'maxBytes': video.MAX_OUTPUT_BYTES}})

    def test_metadata_change_after_review_invalidates_proof(self):
        self.make_source()
        video.normalize_video(self.master, self.output)
        payload = bytes(range(16)) + MARKER
        with self.output.open('ab') as out:
            out.write(struct.pack('>I4s', len(payload) + 8, b'uuid') + payload)
        with self.assertRaisesRegex(ValueError, 'not the exact canonical'):
            video.verify_video_normalization(self.master, sha(self.master), sha(self.output),
                                             {'videoNormalization': {'maxBytes': video.MAX_OUTPUT_BYTES}})

    def test_existing_files_are_never_overwritten(self):
        self.make_source()
        original = sha(self.master)
        with self.assertRaisesRegex(ValueError, 'must not overwrite'):
            video.normalize_video(self.master, self.master)
        self.output.write_bytes(b'existing review artifact')
        with self.assertRaisesRegex(ValueError, 'must not overwrite'):
            video.normalize_video(self.master, self.output)
        self.assertEqual(sha(self.master), original)
        self.assertEqual(self.output.read_bytes(), b'existing review artifact')

    def test_missing_decoder_fails_closed(self):
        self.make_source()
        with patch.object(video.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'requires ffmpeg and ffprobe'):
                video.normalize_video(self.master, self.output)
        self.assertFalse(self.output.exists())

    def test_output_budget_fails_instead_of_approving_truncation(self):
        self.make_source()
        with self.assertRaisesRegex(ValueError, 'output byte budget exceeded'):
            video.normalize_video(self.master, self.output, max_bytes=1024)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
