# VoiceStudio Speech Backend

VoiceStudio is the local TTS/STT provider inside the existing Velvet Visual Foundry pipeline. It is not a second orchestrator, content authority, publish path or copy source.

Canonical provider contract: `packages/vfom/SPEECH-BACKEND.json`.

Routing is `sderot-mac` first, then the already-canonical `sderot-windows` fallback. Failover is allowed only for host/route/provider availability failures. It is sticky per job and may not bypass copy, rights, consent or QA failures.

For public content, the spoken script is authored through the existing vfcopy authority; it is not an automatic read-aloud of the caption. Commercial publishing must not use the OmniVoice model path. Voice cloning requires consent.

Every production speech asset requires a speech receipt. When configured for narration, the generated audio is back-transcribed and must pass the configured similarity threshold before it can be handed to HyperFrames for subtitle/audio composition. A speech receipt is evidence of speech generation/QA only; it never authorizes publication.

Windows commissioning is performed through `scripts/bootstrap-media-host-windows.ps1`, which reuses the existing Windows Edge bootstrap and Remote Desktop Commander route. The canonical Windows fallback is an NVIDIA RTX 4080 SUPER host. VoiceStudio on Windows uses NVIDIA/CUDA automatically when available, with CPU fallback supported; the bundled Windows install does not require a separate CUDA Toolkit.
