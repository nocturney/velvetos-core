---
name: Velvet Factory Office
version: "1.0"
tokens:
  color:
    canvas: "#0b1224"
    surface-dark: "#101a35"
    surface-cream: "#f7f3eb"
    accent-gold: "#caa96b"
    text-on-dark: "#f4ead3"
    text-on-dark-muted: "#d8deeb"
    text-on-cream: "#101a35"
    text-muted: "#c9d0df"
    white: "#ffffff"
  typography:
    display: "Georgia, serif"
    body: "Arial, sans-serif"
    label-size: "11px"
    body-size: "14px"
    title-size: "28px"
    bottom-line-size: "17px"
  spacing:
    outer: "24px 12px"
    card-padding: "28px"
    section-gap: "20px"
    accent-border: "6px"
  layout:
    max-width: "640px"
    direction: rtl
  components:
    header-bar:
      backgroundColor: "{color.surface-dark}"
      borderRight: "{spacing.accent-border} solid {color.accent-gold}"
      padding: "{spacing.card-padding}"
    bottom-line-card:
      backgroundColor: "{color.surface-dark}"
      textColor: "{color.white}"
      labelColor: "{color.accent-gold}"
      padding: "16px"
    slot-body:
      backgroundColor: "{color.surface-cream}"
      textColor: "{color.text-on-cream}"
      padding: "{spacing.card-padding}"
    footer:
      backgroundColor: "{color.surface-dark}"
      textColor: "{color.text-muted}"
      fontSize: "12px"
      padding: "16px 28px"
---

# Velvet Factory — Office Visual Identity

## Design Philosophy

**Architectural warmth meets print-floor clarity.** The office UI reads like a morning brief from a small studio — not a SaaS dashboard. Dark navy grounds the eye; cream surfaces carry readable content; gold accents mark decisions and hierarchy. RTL-first. Pickup-only, human CTA.

Target audience: studio lead reading the 07:00 brief on phone. Emotional tone: calm authority, no urgency theater, no fake scarcity.

## Color

| Token | Hex | Use |
|---|---|---|
| canvas | `#0b1224` | Email outer background (תצוגה 3) |
| surface-dark | `#101a35` | Headers, decision cards, footer |
| surface-cream | `#f7f3eb` | Slot body, readable blocks |
| accent-gold | `#caa96b` | Labels, right border, emphasis |
| text-on-dark | `#f4ead3` | Subtitle on dark |
| text-muted | `#c9d0df` | Footer, secondary |

Do not introduce bright greens, purple gradients, or pure black `#000`. Do not use light gray `#f5f5f5` as primary surface — cream is the light surface.

## Typography

- **Labels** (e.g. «השורה התחתונה», slot numbers): Georgia 11px, gold, letter-spaced feel
- **Titles**: Arial 28px white on dark
- **Body / slots**: Arial 14px, line-height ~1.55
- **Bottom line**: Arial 17px white — one sentence max

Hebrew copy only in product-facing blocks. English OK in dev docs and token names.

## Layout & Spacing

- Max content width: **640px** centered on canvas
- Direction: **rtl** on all presentation tables and slot content
- Header: 6px solid gold border on the **right** (RTL accent)
- Section padding: 28px horizontal on cards; 20px between stacked blocks

## Components

### Morning brief envelope (MAIL.html)

Locked structure 01–07. Agent fills `{{SLOTS}}` only — never reorders slots. Header/footer tokens fixed. See `packages/vfops/hq/BRIEF-SLOTS.md`.

### Wireframe (brief-email.html)

Same tokens for Mobbin-blocked / effective-html reference. Not the live send path — `MAIL.html` + `render_mail.py` is production.

### Decision card (slot 01 pattern)

Dark surface, gold label, white action text. Yes / No / Defer — no fake countdown timers.

## Do's and Don'ts

**Do**

- Keep one CTA per customer-facing block: WhatsApp `050-2517000` or איסוף שדרות
- Use verified numbers only in slot 06 — write «אין ספירה» when missing
- Match Canva IG palette where brief covers appear in slot 07 (`#vfcovers`)

**Don't**

- «שלחו DM» or boost CTAs
- Invent ₪, Insights, or queue hours
- Swap תצוגה 3 structure for a «cleaner» single-column marketing layout
- Add stock photos of bedrooms, national shipping badges, or generic startup illustrations

## Breakpoints

Email target: mobile-first 320–640px. Tables use `role="presentation"` — no responsive framework required. Desktop: same 640px card centered on `#0b1224` canvas.

## Related files

| File | Role |
|---|---|
| `../MAIL.html` | Live brief template (תצוגה 3) |
| `brief-email.html` | Wireframe reference |
| `DESIGN-EMBED.md` | Source map (awesome-design-md) |
| `EFFECTIVE-HTML.md` | Slot → html-plan mapping |
| `packages/vfcanva/` | Instagram visuals — Canva brand kit is authoritative for feed |
