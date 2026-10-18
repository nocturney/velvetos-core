# Office v2 — Speech/TTS provider comparison: KittenTTS vs existing VoiceStudio

**Owner request:** 2026-10-13. **Status:** `SP-0 RESEARCH_ACTIVE / SP-1 FIXTURE_PREPARED / SP-2 LIVE_BASELINE_PARTIAL / SP-3 LAB_NOT_RUN / PRODUCTION_UNCHANGED`.
**Canonical candidate:** `candidate-kittenml-kittentts` in [Phase 2 Candidate Registry](candidate-registry-v0.json).
**Evaluation lane:** `speech-tts-local` (P1 bounded speech capability study; **not** a new P0 core-bake-off lane).
**Decision owner:** existing Office v2 [candidate intake #595](https://github.com/nocturney/velvetos-core/issues/595).
**Execution route:** existing Phase 4 Integration Factory / Phase 6 Creative Craft speech + media workflows; do not create another orchestrator, scheduler, writing authority, or speech gateway.

## Why this is scheduled

The owner submitted [KittenML/KittenTTS](https://github.com/KittenML/KittenTTS). The initial assistant analysis incorrectly overlooked the existing installed VoiceStudio/OmniVoice route. Historical evidence is in [the 2026-10-09 VoiceStudio intake](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6079970652) and [the 2026-10-13 omission correction](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6146293572).

This plan **preserves both incumbent awareness and open competition**: no incumbent-based veto, no assumption a new engine wins, and no automatic production duplication.

### Existing baseline — evidence is dated

- Existing [`packages/vfom/SPEECH-BACKEND.json`](../../../../packages/vfom/SPEECH-BACKEND.json) routes `speech-provider-v1` through VoiceStudio >=0.5.2 with `vf_speech.py`, OmniVoice / MOSS-TTS-Nano and alternatives, Faster-Whisper/MLX Whisper and back-transcription QA.
- Chris Windows VoiceStudio 0.5.2 installation and Hebrew TTS/ASR QA PASS were documented in early October. The 2026-10-09 intake reported no running VoiceStudio process/`:3900` listener. **No live status is asserted for 2026-10-13**; obtain fresh readback before claiming incumbent runtime success or failure.
- KittenTTS 2 claims a 1.7B CPU-capable multilingual speech model, expression controls, voice cloning, and 47 voices. Lighter ONNX 15M–80M models are also offered. Upstream claims of Hebrew require direct testing; do not assume the old ONNX models have identical language support. Library code Apache-2.0 **does not cover model weights**; check the actual Stellon Labs Community License for selected models.

## Queue and trigger — real next actions, no duplicate watchdog

| Gate | Responsible existing owner | Timing / dependency | Evidence for completion |
| --- | --- | --- | --- |
| SP-0 Intake, source and license review | #595 Phase 2 research | **NOW; parallel read-only** with #612 P0 | Candidate registry entry, upstream/version/model-weight refs, rights matrix, VoiceStudio known-baseline read |
| SP-1 Contract/fixture definition | #595 + Creative Craft | **NOW; no GPU claim or new installation** | Exact Hebrew/mixed-language test strings, ASR QA protocol, speed/resource metrics and preset/model matrix |
| SP-2 Incumbent live readback + compute admission | Existing speech operator / #604 resource evidence when relevant | First available authorized host; can run concurrently if independent resources | Fresh VoiceStudio doctor/service port, machine CPU/GPU/RAM, storage, lease and recovery/rollback record |
| SP-3 Isolated CPU-first KittenTTS benchmark | Phase 4 Integration Factory / Phase 6 Creative Craft | First independently verified idle host and admitted no-spend LAB; otherwise **after #612 P0 resource gate** | Pinned deps/weights/license, speech WAVs, measurements, cleanup + no incumbent regression |
| SP-4 Compare and decide | Phase 2 candidate review + Creative Craft | After SP-3 data | Same-fixture scorecard: keep VoiceStudio only / add Kitten engine within existing interface / alternative speech route; record evidence and follow-up stage |

Do not treat these gates as clock-time reminders or claim SP-3 was run because it is scheduled. If host access or rights evidence is absent, record `needs_sync` / `NOT_RUN` and the precise dependency rather than silently dropping the candidate.

## 2026-10-13 fresh read-only operator observations

**Chris Windows (Remote Desktop Commander readback):** The previously documented VoiceStudio executable and VelvetOS `speech-host.json` both **exist**. No running `omnivoice-studio` process or TCP listener on port `3900` was observed during this read; no service start or smoke was attempted. This means prior Hebrew QA remains historical, and **SP-2 is PARTIAL**, not passed. Do not infer active service availability from installation alone.

**Chris-Mini-PC (independent host readback):** Intel Core i5-14500, ~15.7 GiB total RAM, ~8.3 GiB free physical RAM, ~1,853 GiB free on D:; selected high-load process-name scan did not show a Python/Ollama/VoiceStudio/Grok process. Snapshot is momentary and is **not** a verified resource lease or proof of host-wide idle state. It is a CPU-first LAB *candidate*, not an authorized install target yet; validate ownership, background jobs, current free RAM and model requirements at execution time. Chris main is already running local AI and must not be preempted.

**SP-1 fixture:** [speech-tts-hebrew-fixtures-v0.json](speech-tts-hebrew-fixtures-v0.json) contains 12 synthetic Hebrew, mixed-language and English control scripts plus capture requirements and a minimum ASR similarity reference. This is a *prepared unexecuted input fixture*, not proof of speech quality or admission. No cloned voice or customer recording is used.

## Same-input, same-output evaluation matrix

1. **Hebrew correctness:** short instructions, RTL punctuation, acronyms, NIS prices, dates, numbers, names, mixed Hebrew/English, and a longer multi-paragraph narration. Score word errors/CER, back-transcription similarity against the existing QA threshold, intelligibility, stability and clipped/repeated speech.
2. **Naturalness and control:** blind human ratings, prosody, accent, emphasis and expressive controls on equivalent scripts. For voice-cloning tests only consented source recordings are acceptable; may skip cloning while testing standard voices.
3. **Latency and resources:** cold/warm synthesis, output duration, RTF/first-chunk delay (chunk streaming vs continuous), CPU/RAM/GPU/VRAM, disk/model downloads, crash/timeout behavior, reproducibility/version pins.
4. **Comparable providers:** VoiceStudio OmniVoice (verified historical Hebrew baseline), other currently supported VoiceStudio engines that actually run on the tested host, KittenTTS 2 and suitable legacy ONNX models **only if their specific language compatibility is verified**. Compare provider engines under the **existing speech contract**, not marketing claims or a single benchmark anecdote.
5. **Deployment and rights:** selected model licenses and commercial permissions, privacy/local processing, maintenance burden, source/release health, plugin/adapter effort, output artifacts and rollback.

## Operational boundaries

- Protect #612 P0 real coding-worker proof, #604 Fleet resource leases and the currently functioning speech/creative jobs. Research without GPU contention may proceed in parallel.
- No new recurring cost, paid API, public model hosting, production secret, recording collection, background watcher, new speech authority or source-of-truth change.
- Only change `packages/vfom/SPEECH-BACKEND.json` / `speech-provider-v1` implementation after typed-adapter, QA, policy, deployment/rollback and explicit promotion checks. Existing ASR/transcription is not displaced by a TTS-only challenger.
- An incumbent's temporary service downtime is not proof the newcomer is better. A loss of production capability does not auto-grant production rights to Kitten.
- Track evaluated and queued challengers even when existing solutions win, preserving later reopen rights under material evidence.

**Acceptance:** one traceable canonical candidate + Phase 2/Phase 4/6 ownership, one reproducible real speech fixture, comparable evidence-backed verdict, and no forgotten link or hidden product-veto. This document is a scoped plan, not a claim that software has been installed or tests completed.
