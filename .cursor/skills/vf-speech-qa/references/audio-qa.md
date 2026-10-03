# Speech audio QA

- Listen for clipping, dropouts, repeated phonemes, truncated words, metallic/warbling artifacts, abrupt silence and unnatural breath/pause behavior.
- Compare loudness and peak requirements against the destination specification rather than one universal target.
- Check beginning/end padding and whether fades truncate consonants or breaths.
- If denoise/EQ/compression is applied, compare before/after for intelligibility and artifact introduction.
- For synced video, verify lip/action alignment only where the source requires it; do not imply real lip sync for synthetic speech without evidence.