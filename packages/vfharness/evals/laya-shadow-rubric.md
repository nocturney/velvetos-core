# Laya Shadow Evaluation Rubric

Role: **classification evidence only**. Laya never authorizes or executes an action.

## Domain labels

- `office`: calendar, mail, orders, CRM/admin and ordinary business operations.
- `velvet-factory`: physical products, CAD/3D printing, slicers/printers and Velvet Factory product/social workflows.
- `development`: source code, Git, tests, CI, developer documentation and software engineering.
- `media`: images/video/assets, metadata, transcoding, media storage and asset integrity.
- `system`: host/OS/services, backups, infrastructure, security/runtime and platform operations.
- `unknown`: outside the known VelvetOS domains or too underspecified to route safely.

## Action labels

- `read`: retrieve or inspect without interpretation-heavy analysis or mutation.
- `analyse`: compare, diagnose, evaluate or explain existing information without making the primary artifact/change.
- `generate`: create a new draft/content/code/model/plan, without persisting or executing it as the requested end action.
- `write`: persist/edit a file, record, config or status without running an operational job or public publication.
- `execute`: run a command/job/tool/control action; excludes public content publication.
- `publish`: release or schedule content to a public/external publication channel.

## Escalation labels

Escalation is a **capability recommendation, not a permission decision**.

- `no-model`: deterministic lookup, exact state mutation, known command, sensor or rules-engine path; no generative reasoning is needed.
- `local/small`: bounded summarization, classification, drafting or transformation that a small local model can reasonably handle.
- `reasoning/frontier capability`: multi-source diagnosis, architecture, ambiguous planning, complex tradeoffs or novel reasoning.

A request can be authorization-sensitive while still being `no-model`. Example: “publish the already-approved post unchanged” needs no reasoning model, but VelvetOS publication authorization still applies independently.

## Dataset design

The corpus is synthetic/non-sensitive but uses real VelvetOS task shapes. Hebrew is deliberately dominant; English cases are retained to expose language-specific failures. It includes ambiguous instructions, untrusted-content/prompt-injection shapes and operations whose authorization must remain outside the classifier.

No promotion threshold is declared here. Measure first, then document an evidence-based criterion from observed failures and calibration.
