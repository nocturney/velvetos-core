"""Canonical public MP4 from decoded frames/audio, never source container bytes.

Run before exact-final review. Reproduction is intentionally tied to the local
FFmpeg build; a different result requires normalization and review again.
"""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from vf_media_integrity import SOURCE_VIDEO, inspect_media
from vf_media_limits import run_bounded

MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_OUTPUT_BYTES = 50 * 1024 * 1024


def _freeze(source: Path, target: Path) -> str:
    h = hashlib.sha256()
    count = 0
    with source.open('rb') as reader, target.open('xb') as writer:
        for block in iter(lambda: reader.read(1024 * 1024), b''):
            count += len(block)
            if count > MAX_INPUT_BYTES:
                raise ValueError('video normalization input byte budget exceeded')
            writer.write(block)
            h.update(block)
    return h.hexdigest()


def normalize_video(src: Path, dst: Path, *, expected_source_sha256: str | None = None,
                    max_bytes: int = MAX_OUTPUT_BYTES) -> None:
    """Create a new private MP4. Keep only primary picture and optional primary sound."""
    src, dst = Path(src).resolve(), Path(dst).absolute()
    if src.suffix.lower() not in SOURCE_VIDEO or dst.suffix.lower() != '.mp4':
        raise ValueError('video normalization requires supported video input and MP4 output')
    if dst.exists() or dst.is_symlink() or src == dst.resolve():
        raise ValueError('normalization must not overwrite a source or existing output')
    if not isinstance(max_bytes, int) or not (1024 <= max_bytes <= MAX_OUTPUT_BYTES):
        raise ValueError('invalid video normalization output byte budget')
    encoder = shutil.which('ffmpeg')
    if not encoder or not shutil.which('ffprobe'):
        raise ValueError('video normalization requires ffmpeg and ffprobe')
    with tempfile.TemporaryDirectory(prefix='vf-video-normalize-') as directory:
        frozen = Path(directory) / ('master' + src.suffix.lower())
        master_sha = _freeze(src, frozen)
        if expected_source_sha256 is not None and master_sha != expected_source_sha256:
            raise ValueError('video normalization source SHA-256 mismatch')
        inspect_media(frozen, 'video normalization source', source=True)
        encoded = Path(directory) / 'canonical.mp4'
        command = [
            encoder, '-v', 'error', '-xerror', '-nostdin', '-threads', '1',
            '-max_alloc', '67108864', '-protocol_whitelist', 'file,pipe',
            '-format_whitelist', SOURCE_VIDEO[src.suffix.lower()], '-i', str(frozen),
            '-map', '0:V:0', '-map', '0:a:0?', '-sn', '-dn',
            '-map_metadata', '-1', '-map_metadata:s', '-1', '-map_chapters', '-1',
            '-filter_threads', '1', '-vf', 'sidedata=mode=delete',
            '-af', 'asidedata=mode=delete', '-c:v', 'libx264', '-threads:v', '1',
            '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
            '-flags:v', '+bitexact', '-bsf:v', 'filter_units=remove_types=6',
            '-c:a', 'aac', '-threads:a', '1', '-b:a', '192k', '-flags:a', '+bitexact',
            '-fflags', '+bitexact', '-disposition:v:0', 'default',
            '-disposition:a:0', 'default', '-metadata', 'encoder=',
            '-metadata:s:v:0', 'encoder=', '-metadata:s:v:0', 'handler_name=VideoHandler',
            '-metadata:s:v:0', 'language=und', '-metadata:s:a:0', 'encoder=',
            '-metadata:s:a:0', 'handler_name=SoundHandler', '-metadata:s:a:0', 'language=und',
            '-movflags', '+faststart', '-fs', str(max_bytes + 1), '-f', 'mp4', str(encoded),
        ]
        run_bounded(command, timeout=90)
        if encoded.stat().st_size > max_bytes:
            raise ValueError('video normalization output byte budget exceeded')
        inspect_media(encoded, 'canonical video')
        # Copy only the completed, decoded encoder output. Exclusive create protects sources.
        with encoded.open('rb') as reader, dst.open('xb') as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)


def verify_video_normalization(master: Path, master_sha256: str, output_sha256: str,
                               cfg: dict) -> None:
    """Reproduce exact public bytes from a hash-bound master, not a tag allowlist."""
    with tempfile.TemporaryDirectory(prefix='vf-video-proof-') as directory:
        expected = Path(directory) / 'canonical.mp4'
        normalize_video(master, expected, expected_source_sha256=master_sha256,
                        max_bytes=int(cfg['videoNormalization']['maxBytes']))
        with expected.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != output_sha256:
            raise ValueError('final MP4 is not the exact canonical normalized output; normalize then repeat final QA')
