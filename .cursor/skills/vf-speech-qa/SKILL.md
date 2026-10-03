---
name: vf-speech-qa
description: Apply local-first speech generation, transcription and audio QA across VoiceStudio, OmniVoice, faster-whisper and deterministic audio tools. Use for TTS/voiceover preparation, pronunciation and number/date normalization, ASR transcript validation, timing/VAD review, clipping/dropout/noise checks and speech-model/license review. Preserve consent, identity and model-license boundaries; this skill does not authorize voice cloning, impersonation, publishing, paid cloud fallback or claims of transcript accuracy without checking the produced audio/transcript.
---

# Velvet Speech QA

Treat speech generation and speech recognition as evidence-producing pipelines that require an independent check.

## Workflow

1. Resolve language, speaker/voice source, intended wording, destination format and whether identity/consent is involved.
2. Read references/generation.md for TTS/voiceover preparation.
3. Read references/transcription.md for transcription or back-checking generated speech.
4. Read references/audio-qa.md for exact-file audio inspection.
5. Read references/licensing-consent.md before using a new model/voice or identity-sensitive source.
6. Read references/tool-routing.md only for the engine involved.
7. Verify the exact output audio and transcript before handoff.

## Core rules

- Normalize ambiguous numbers, dates, units, acronyms and names before generation when pronunciation matters.
- Keep a pronunciation/wording source for names and product terms that must be exact.
- Use ASR as a back-check, not as proof by itself; listen to critical regions.
- Resolve loudness/peak/sample requirements from the destination rather than one universal value.
- Keep generated voice assets and transcripts tied to their source text/model/voice metadata.

## Hard stops

- Do not clone or imitate a real person's voice without the required consent/authorization.
- Do not infer that a model's code license also grants rights to every bundled/upstream voice model.
- Do not use paid/cloud speech services automatically.
- Do not publish or send audio from this skill.
- Do not claim an exact transcript when names, numbers or low-confidence/unclear regions remain unresolved.

## Completion evidence

Report text_normalized, voice_model_rights_checked, audio_generated_or_received, asr_backcheck_done, critical_listen_passed, audio_qc_passed and transcript_verified separately.
