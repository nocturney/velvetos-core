# Speech generation

- Lock the final text before expensive voice generation when possible.
- Normalize punctuation, numbers, dates, units and abbreviations only when the intended spoken form is known.
- Maintain a pronunciation list for proper nouns and technical terms.
- Generate short test passages before long renders when voice/model/settings changed.
- Compare pacing, stress, pronunciation, pauses and emotional direction against the brief.
- Preserve a text-to-audio mapping so later copy changes invalidate the corresponding generated audio.
- Do not hide synthesis artifacts with excessive processing; fix generation settings/text first when feasible.