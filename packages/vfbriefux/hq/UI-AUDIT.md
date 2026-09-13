# UI audit — Hallmark + Taste pattern embed

Sources: `Nutlope/hallmark` (audit pattern) and `Leonxlnx/taste-skill` (optional creative divergence). No vendor runtime is installed.

## Default: audit-only

After a UI candidate exists, inspect it for common AI-generated interface failure modes:

- generic hero/dashboard composition with no task-specific hierarchy;
- excessive cards, pills, gradients, glow, glass, shadows, or decorative charts;
- every section using the same visual weight;
- fake metrics, invented trends, decorative graphs, or placeholder KPIs presented as real;
- weak empty/loading/error/blocked states;
- duplicated labels, verbose helper text, and obvious AI filler;
- inconsistent spacing/radius/type scale;
- poor RTL mirroring or mixed-direction breakage;
- inaccessible contrast/focus/interaction states;
- novelty that conflicts with Velvet brand continuity.

Verdict: `PASS`, `REPAIR`, or `REJECT`. Each non-pass finding names the exact component and a repair.

## Optional creative-spike mode (Taste pattern)

Use only when the explicit goal is exploration, redesign, or escaping a generic default. Produce up to three materially different directions. They are proposals, not brand truth. Every direction must then pass `UI-SYSTEM.md`, Brand Guardian where relevant, RTL/a11y checks, and this audit.

Do not let creative-spike mode silently alter production tokens or become the default implementation style.
