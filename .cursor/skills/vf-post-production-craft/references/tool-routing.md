# Post tool routing

Do not replace accepted adapters; choose tools by craft requirement.

- DaVinci Resolve Studio: preferred when edit, color, Fairlight audio and/or Fusion page integration benefits from one timeline/project. Use Blackmagic's official editor/color/Fairlight/VFX training patterns as craft authority.
- Fusion Studio standalone: use for node-graph compositing/VFX work that benefits from a dedicated Fusion host; treat it as first-class craft, with execution dependent on the accepted integration available at runtime.
- Premiere Pro: use the existing first-party bridge for timeline/edit operations that belong in Premiere projects.
- After Effects: use the existing functional bridge for layer/composition/motion work. Borrow craft patterns from external agent skills, not their macOS-specific runtimes.
- Media Encoder: use for managed exports/transcodes where the Adobe route is already authoritative.
- ffmpeg/ffprobe: use for deterministic transforms, metadata inspection and lightweight delivery QA. Favor probe -> transform -> probe -> visual/audio review.
- HyperFrames: remain the deterministic render backend inside the existing Velvet content pipeline; it is not a creative authority.
- Topaz Video: use only for justified restoration/upscale/denoise/interpolation tasks and compare against source for artifacts or invented detail.
- Speech/TTS/ASR: route generation, transcription, pronunciation and back-check work through `.cursor/skills/vf-speech-qa/SKILL.md` before audio finishing. That skill never grants content or publish authority.