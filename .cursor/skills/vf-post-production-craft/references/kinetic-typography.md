# Kinetic typography

Use when text itself is animated: title cards, captions, lower-thirds, callouts, word reveals and motion headlines.

- Readability comes first. Budget a fully readable hold before deciding entrance/exit animation; if the slot is too short, shorten the copy before shortening the readable hold.
- Treat entrance, readable hold and exit as three separate intervals. Do not count partially animated text as fully readable time.
- Use reading-speed numbers only as starting heuristics. Adjust for language, unfamiliar names/numbers, platform, font, size and actual playback review.
- Animate one primary property per line by default; two only with a clear reason. Opacity plus a small transform is often enough.
- Avoid animating layout properties that make glyphs reflow or jitter. Prefer transforms, masks/clips and opacity over live font-size/width changes.
- Build hierarchy through entrance order, size, weight, placement and hold time so all signals point to the same primary message.
- Use word-by-word animation only for short emphasis lines; dense captions should remain stable and easy to scan.
- Accent weight/scale once, then hold. Repeating pulses, bounces or perpetual motion compete with reading.
- Match the text exit to the edit: a hard cut may need no animated exit; a dissolve may justify a fade.
- For Hebrew/RTL, preserve exact word order, punctuation, numerals, direction and final rendered readability; never let an animation system reorder text.
