# Excalidraw Patterns (VF copy)

Source: openclaw/diagram-maker `references/excalidraw-patterns.md` (2026-09-05).  
Optional local whiteboard only. Cloud Agent default = SVG HTML via `diagram-svg-template.html`.

Envelope:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "vfbriefux/diagram-maker",
  "elements": [],
  "appState": { "viewBackgroundColor": "#f7f3eb" }
}
```

Labeled rounded rectangle:

```json
{
  "type": "rectangle",
  "id": "svc",
  "x": 100,
  "y": 100,
  "width": 180,
  "height": 72,
  "roundness": { "type": 3 },
  "backgroundColor": "#d8e4f8",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeColor": "#caa96b",
  "roughness": 1,
  "opacity": 100,
  "boundElements": [{ "id": "svc_text", "type": "text" }]
}
```

Bound text:

```json
{
  "type": "text",
  "id": "svc_text",
  "x": 112,
  "y": 124,
  "width": 156,
  "height": 24,
  "text": "פנייה",
  "originalText": "פנייה",
  "fontSize": 20,
  "fontFamily": 1,
  "strokeColor": "#101a35",
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": "svc",
  "autoResize": true
}
```

Bound arrow:

```json
{
  "type": "arrow",
  "id": "a1",
  "x": 280,
  "y": 136,
  "width": 140,
  "height": 0,
  "points": [
    [0, 0],
    [140, 0]
  ],
  "endArrowhead": "arrow",
  "startBinding": { "elementId": "svc", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "db", "fixedPoint": [0, 0.5] }
}
```

VF palette (maps to DESIGN.md — not upstream rainbow):

- Input / start: `#d8e4f8`
- Process: `#e8e0c8`
- Success / pickup: `#d8ead8`
- Storage / queue: `#c3fae8` → prefer `#d8ead8` on cream
- External / hold: `#f0e4c0`
- Risk / blocked: `#f0d8d8`
- Note / decision: `#fff3bf`

Laws: no invented ₪ in labels; CTA stays WhatsApp / איסוף שדרות when present.
