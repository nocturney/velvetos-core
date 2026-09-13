# AI-tells gap audit — avoid-ai-writing

Source reviewed: `conorbronsdon/avoid-ai-writing`. This is a selective pattern import into the existing Hebrew Humanizer model; the external skill is not installed.

## Missing / under-explicit patterns to apply

- **Chatbot artifacts:** “שאלה מצוינת”, “מקווה שזה עוזר”, “אשמח לעזור” when they are not natural conversation.
- **Vague attribution:** “מומחים אומרים/מאמינים”, “מחקרים מראים” without an identifiable source.
- **Formulaic transitions:** “בואו נצלול”, “בואו נבחן”, “ראוי לציין” instead of starting from the point.
- **Hedge stacking:** “יכול אולי”, “עשוי אולי”, “ייתכן שאולי”; keep one uncertainty level.
- **Generic future closers:** “העתיד נראה מבטיח”, “עוד נראה לאן זה יוביל” without a concrete decision/fact.
- **Synonym cycling:** repeatedly changing the same term merely to avoid repetition; prefer stable terminology.
- **Bare-noun bullet stacks:** 5+ short noun-only bullets can indicate a template instead of decisions/actions.
- **Mechanical uniformity:** equal paragraph lengths, forced rule-of-three, copula avoidance, and polished-but-empty symmetry.

These are writing-quality signals, not proof of AI authorship. `hq/ai-tells-he.md`, `reader-first-he.md`, the Hebrew copy skill, factual gates, and the Visible Text Gate remain authoritative.
