# Velvet UI System — UI/UX Pro Max pattern embed

Source pattern: `nextlevelbuilder/ui-ux-pro-max-skill`. Use its breadth as design intelligence, not as an authority over Velvet brand, Hebrew, RTL, truth, or product scope.

## Order of authority

1. Existing Velvet product/brand rules and actual product requirements.
2. Hebrew + RTL semantics.
3. Accessibility and responsive behavior.
4. Information hierarchy and task completion.
5. Pattern/library inspiration.

## Required design contract

- **RTL first:** layout direction, icon directionality, numeric islands, punctuation, tables, timelines, charts, and mixed Hebrew/English strings must be tested explicitly.
- **Hebrew readability:** no compressed type, faux-small-caps, letter spacing hacks, or Latin-centric line-height assumptions.
- **Accessible:** keyboard path, visible focus, semantic labels, contrast, reduced-motion fallback, target size, and non-color status cues.
- **Responsive:** owner console must work at narrow laptop widths before ornamental density is added.
- **Data truth:** charts and KPIs only from measured sources; `אין ספירה` beats invented numbers.
- **Design tokens:** spacing, radius, type scale, elevation, status semantics, and component states are centralized instead of one-off styling.
- **No public-marketing creep:** this system applies to internal office surfaces and approved artifacts; it does not unlock a public marketing site.

## Design pass

`task -> information architecture -> component choice -> RTL/a11y pass -> brand pass -> anti-slop audit -> implementation -> evidence`.

For a novel surface, generate 2–3 layout candidates, then choose against task completion and brand constraints rather than aesthetic novelty alone.
