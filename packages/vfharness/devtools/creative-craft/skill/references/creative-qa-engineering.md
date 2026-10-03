# Creative QA engineering

Use this protocol when quality must be proven across more than one specialist, tool, revision or export.

- Define the acceptance dimensions before production: truth/fidelity, function, form, readability, temporal behavior, output compliance and editability as applicable.
- Choose one or more references plus an anti-reference when style convergence is a risk. Record what each reference is authoritative for.
- Create a golden or accepted comparison state whenever repeatability matters. Never let a later render silently redefine the target.
- Use neutral test conditions before beauty conditions: clay/neutral material, neutral light, ungraded source, clean background or simple camera as appropriate.
- Capture evidence at meaningful milestones, not only at the end. Bind evidence to source revision, tool/version and output hash when available.
- Run perturbation tests on systems that claim resilience: change a key CAD parameter, swap a lighting condition, test another output transform, inspect stress frames or vary the target size.
- Compare outputs at the level where the defect appears: geometry, texture, color space, frame sequence, vector path, PDF separation or G-code preview.
- Prefer structured critique: observation -> likely cause -> corrective action -> verification. Avoid vague notes such as "make it better".
- For temporal media, inspect worst/stress frames and playback continuity. For static artifacts, inspect intended size plus at least one reduced/alternate view.
- Cross-tool parity means preserving intent and evidence, not forcing pixel-identical results when renderers or formats differ.
- A validator may prove only its declared field. Passing a technical check never proves beauty, usability, safety, manufacturability or publication approval.
- Record unresolved uncertainty explicitly and route it to the owning authority rather than filling it with a default.

Completion evidence should state what was checked, against which reference/fixture, what changed after critique, and what remains unproven.
## Eval split

The bundled `evals/run_creative_craft_evals.py` measures deterministic architecture/craft coverage against fixed fixtures and records baseline/candidate deltas. It does not impersonate perceptual review. Manual artifact criteria remain explicit in each case and must be recorded separately when a real render/model/shot/output is produced.
