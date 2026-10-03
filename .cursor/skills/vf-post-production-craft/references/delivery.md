# Delivery QA

1. Resolve destination requirements: container, codec, resolution, aspect ratio, frame rate, color/output space, audio layout and any caption/subtitle requirement.
2. Render from the known-good master/timeline using an explicit preset or recorded settings.
3. Inspect metadata with ffprobe or an equivalent deterministic inspector.
4. Confirm duration, video/audio stream count, frame rate, resolution and codec match the intended delivery.
5. Visually inspect opening, closing, representative midpoints and high-risk transitions/effects; for short pieces, review the whole artifact when practical.
6. Listen to the delivered audio for clipping, dropouts, sync and processing artifacts.
7. Confirm no unintended letterbox/crop, missing fonts, offline media, placeholder frames or watermarks.
8. Keep render receipt/QC evidence separate from publish receipt.

A successful Media Encoder/Resolve/ffmpeg exit is only execution evidence, not quality evidence.