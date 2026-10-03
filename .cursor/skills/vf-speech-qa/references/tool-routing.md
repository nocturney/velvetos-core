# Speech tool routing

- VoiceStudio / OmniVoice: local generation/voice workflows when the accepted local service is available; keep output in files mode when that is the approved path.
- faster-whisper: local transcription/back-check, timestamps and VAD-assisted segmentation.
- ffmpeg/ffprobe: deterministic media inspection, trims/concats/transcodes and metadata checks when needed.
- Do not add a hosted speech API as an automatic fallback and do not claim the local service is connected unless runtime health is actually verified.
