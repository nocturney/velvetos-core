# Windows speech fallback integration — 2026-09-13

This implementation extends the already-canonical `sderot-windows` fallback rather than creating a second Windows host.

- Added VoiceStudio 0.5.2 TTS/STT backend contract and cross-platform adapter.
- Added Windows VoiceStudio bootstrap with real Hebrew TTS + back-transcription QA smoke.
- Added `bootstrap-media-host-windows.ps1` as the combined compatibility entrypoint over the existing render bootstrap plus speech bootstrap.
- Preserved `bootstrap-edge-host-windows.ps1` as the canonical HyperFrames render bootstrap contract.
- Bound Mac preferred → Windows fallback speech routing with sticky-per-job failover and unchanged QA thresholds.
- Windows AMD speech compute is CPU-backed because VoiceStudio ROCm support is Linux-only.
- Runtime remains commissioning until Remote Desktop Commander sees the physical Windows PC online and the local render/speech receipts pass.
