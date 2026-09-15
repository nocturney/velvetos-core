"""Decode local publication media. No network, writes, approvals or provenance claims."""
from __future__ import annotations

import json
import shutil
import subprocess
import warnings
from pathlib import Path

FINAL_IMAGES = {'.png': {'PNG'}, '.jpg': {'JPEG'}, '.jpeg': {'JPEG'}, '.webp': {'WEBP'}}
SOURCE_IMAGES = {**FINAL_IMAGES, '.tif': {'TIFF'}, '.tiff': {'TIFF'}, '.bmp': {'BMP'},
                 '.gif': {'GIF'}, '.heic': {'HEIF', 'HEIC'}, '.heif': {'HEIF', 'HEIC'},
                 '.avif': {'AVIF'}}
SOURCE_VIDEO = {'.mp4': 'mov', '.mov': 'mov', '.m4v': 'mov', '.avi': 'avi',
                '.mkv': 'matroska,webm', '.webm': 'matroska,webm'}


def inspect_media(path: Path, label: str, *, source: bool = False) -> dict:
    """Require a supported extension AND actual decodable media; fail closed."""
    path = Path(path).resolve()
    suffix = path.suffix.lower()
    images = SOURCE_IMAGES if source else FINAL_IMAGES
    videos = SOURCE_VIDEO if source else {'.mp4': 'mov'}
    try:
        if suffix in images:
            from PIL import Image
            if suffix in {'.heic', '.heif'}:
                try:
                    import pillow_heif
                except ImportError as exc:
                    raise ValueError('HEIF decoder unavailable; use a verified decoded source') from exc
                pillow_heif.register_heif_opener()
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    actual = image.format
                    if actual not in images[suffix]:
                        raise ValueError('image bytes do not match the declared format')
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
                    frames = getattr(image, 'n_frames', 1)
                    if width <= 0 or height <= 0 or width * height * frames > 100_000_000:
                        raise ValueError('image dimensions/frame budget exceeded')
                    for frame in range(frames):
                        image.seek(frame)
                        image.load()
            return {'kind': 'image', 'width': width, 'height': height, 'format': actual}
        if suffix not in videos:
            raise ValueError('unsupported media extension')
        probe, decoder = shutil.which('ffprobe'), shutil.which('ffmpeg')
        if not probe or not decoder:
            raise ValueError('video decoding requires ffprobe and ffmpeg')
        # Restrict demuxers/protocols: disguised playlists must not fetch external media.
        restrictions = ['-protocol_whitelist', 'file,pipe', '-format_whitelist', videos[suffix]]
        run = subprocess.run([probe, '-v', 'error', *restrictions, '-show_entries',
                              'format=format_name:format_tags=major_brand:stream=index,codec_type,width,height',
                              '-of', 'json', str(path)], capture_output=True, text=True,
                             check=True, timeout=20)
        data = json.loads(run.stdout)
        streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
        if not streams or any(int(s.get('width', 0)) <= 0 or int(s.get('height', 0)) <= 0 for s in streams):
            raise ValueError('no valid video stream')
        width, height = int(streams[0]['width']), int(streams[0]['height'])
        fmt = data.get('format', {})
        names = set(fmt.get('format_name', '').split(','))
        if not names.intersection(videos[suffix].split(',')):
            raise ValueError('video container does not match declared format')
        if not source and str(fmt.get('tags', {}).get('major_brand', '')).strip() == 'qt':
            raise ValueError('QuickTime must be normalized to MP4 before final review')
        # Probe success alone is insufficient: fully decode video and optional audio.
        subprocess.run([decoder, '-v', 'error', '-xerror', '-nostdin', '-threads', '1',
                        *restrictions, '-i', str(path), '-map', '0:v', '-map', '0:a?',
                        '-f', 'null', '-'], capture_output=True, check=True, timeout=90)
        return {'kind': 'video', 'width': width, 'height': height, 'format': fmt['format_name']}
    except Exception as exc:
        # Decoder/parser failures must return a blocked verdict, never escape the gate.
        raise ValueError(f'{label}: media is not decodable ({type(exc).__name__}: {str(exc)[:500]})') from exc
