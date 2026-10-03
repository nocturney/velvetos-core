# Corel Craft Spec

Store specs under `D:\Velvet\Tmp\creative-craft`. The adapter creates a new document only and refuses a pre-existing Corel user session.

## Shape schema

Top level:

```json
{
  "job_id": "example-001",
  "page": {"width_mm": 210, "height_mm": 148},
  "objects": [],
  "outputs": ["cdr", "pdf"]
}
```

Supported object types:

- Rectangle: rect with x/y/width/height/radius in mm and optional RGB fill.
- Ellipse: ellipse with center/radii in mm and optional RGB fill.
- Line: line with two endpoints in mm and RGB stroke.
- Text: artistic text with position, font, size, weight, and RGB fill.
- Image: a file under `D:\Velvet` with target position and size in mm.

## Constraints

- `job_id` must contain only letters, digits, underscore, or hyphen and be at most 64 characters.
- Inputs and outputs stay under `D:\Velvet`.
- The adapter accepts at most 200 objects per job.
- RGB channels are integers 0–255.
- Output is non-overwriting.
- Supported final outputs are CDR and PDF.
- Never add a raw COM operation to a spec.
