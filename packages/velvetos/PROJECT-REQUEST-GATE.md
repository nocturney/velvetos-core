# VelvetOS — Project Request Gate

Machine authority: `policy_id: project.request.preflight`

Status: **MANDATORY ROUTER · SCOPE-AWARE PREFLIGHT · FAIL-CLOSED ON TRUE BLOCKERS**

This is the single front door for any Velvet Factory / VelvetOS request. It does not replace the Constitution, packs, skills or tools; it forces the request to be routed through them before work begins.

## Core law

**No substantive work starts before `project_preflight: PASS`.**

The preflight is not permission to dump the whole warehouse into context. It is a dispatcher with two execution modes:

1. classify the request and its action scope;
2. use `FAST_PATH` for a known read-only, local routine or internal-mutation flow with no full-preflight trigger;
3. use `FULL` for external mutation, unknown domain, creative/publication, commercial/spend, rights/privacy, destructive/permission, physical-print or authority-conflict cases;
4. load only the baseline + domain authorities required by that mode;
5. verify the applicable constraints and current evidence;
6. only then execute;
7. run exact-final / action postflight before claiming completion.

If a mandatory authority is unavailable, stale, contradictory or cannot be verified, the branch is `BLOCKED` / `needs_sync`; never silently fall back to model defaults.

## ChatGPT Project bundle fallback

When live GitHub/repository access or the repository executable preflight is unavailable inside a ChatGPT Project, a hash-verified Project bundle at **Contract 6 / Revision 6.6.4 or newer** may satisfy the baseline authority and creative/public-copy routing for `creative_publication` only. Record `repo_state=UNAVAILABLE_PROJECT_BUNDLE_FALLBACK` and the exact bundle ID/hashes. Do not claim repository synchronization, deployment or a repository preflight PASS.

This fallback does **not** authorize stale operational truth. Operations, finance, production status, catalog status, Instagram action and any branch that depends on live external state remain fail-closed or limited to the evidence actually available. If GitHub becomes available, resolve current `main` and apply newer scoped owner corrections before continuing.

## Preflight sequence

### 1. Baseline authority

Always resolve the authority manifest: `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json`.

The manifest now owns two baseline shapes. `FAST_PATH` resolves only the minimal universal authority declared under `fastPath.baselineAuthorities` plus the selected domain profile. `FULL` keeps the complete baseline for sensitive or ambiguous work. Task-local preference can never override either baseline.

### 2. Classify the request

Choose one or more domains from the manifest. Do not guess a new pack or invent a parallel workflow. If classification is uncertain, use the office graph / router (`vfmem`) and Living Studio registry before choosing handlers.

### 3. Choose `FAST_PATH` or `FULL`

`FAST_PATH` is allowed only when all selected domains have an explicit fast-path profile and the request scope is `read_only`, `local_routine` or `internal_mutation`. It is not a bypass: it still produces a complete internal receipt, validates every selected authority path and preserves downstream postflight.

`FULL` is required when any configured full-preflight trigger applies. A routine Gmail/Drive write is therefore still `FULL` at Stage 4B because it is an external mutation, while owner-brief preparation, internal status, research, bounded DCC work and CAD inspection/build can use `FAST_PATH` when no other trigger applies.

### 4. Load only relevant authorities

For every selected domain, load the named pack instructions, relevant skills and canonical Sources of Truth required by the chosen mode before drafting or acting. A tool being available does not make it authoritative; the manifest and Constitution decide whether it may be used.

### 5. Build an internal preflight receipt

Before execution, resolve these fields internally:
- `request_domain`
- `request_scope`
- `preflight_mode: FAST_PATH|FULL`
- `full_preflight_triggers`
- `owner_surface`
- `authority_manifest_version`
- `baseline_authority: PASS|FAIL`
- `routed_packs`
- `required_skills`
- `required_sources`
- `required_tools`
- `hard_gates`
- `current_evidence_state`
- `project_preflight: PASS|BLOCKED`

Keep this receipt internal by default. Do not turn routine PASS receipts, retries, fallbacks, compatibility checks or evidence repair into owner prompts. Surface only a genuine blocker/decision or the receipt when explicitly requested. But do not proceed when the applicable receipt is incomplete.

### 6. Execute through the real pipeline

Execution must use the routed skills/tools rather than reproducing their intended behavior from memory. When a matching specialist, lint, editor, source or provider exists, actually use it when the task requires it.

Source-ingest evidence preparation for current-chat attachments is allowed before creative authorization; it may only copy/hash/inspect source bytes and must not create a preview. In `CHAT_LOCAL_ATTACHMENT` mode, when the repo executor and attachment bytes live on different filesystems, `scripts/vf_chat_cold_start_preflight.py` is the canonical pre-tool creative gate: it validates the hash-verified current Project bundle, exact source-ingest receipts and inspected creative plan, may return `creative_execution_authorized: true`, and can never authorize publication. Do not send chat-local source paths to a remote repo preflight that cannot read them. For other creative_publication execution, no image-generation, image-editing, design/composition or public-copy production tool may be called until the executable preflight receipt for the exact Creative Manifest/content ID says both project_preflight: PASS and creative_execution_authorized: true. File existence, CI, remembered rules or a planned future QA do not authorize the call. If the receipt cannot be produced or is BLOCKED, stop before tool invocation; diagnostics may repair the evidence, but no creative preview is a valid fallback.

### 7. Postflight

Before claiming `done`, `ready`, `prepared`, `published`, `synced`, `sent`, or equivalent, run the domain's output/action gates on the exact final artifact or provider result. Evidence beats intention.
## Mandatory creative/publication path

Any request involving product media, social content, copy, image/video editing, post/carousel/Story/Reel/cover/grid or `prepare for publication` must route through the complete creative stack named in the authority manifest.

This path is especially fail-closed because observed failures came from skipping layers:
- visual language / owner-approved reference;
- Product Truth / source-subject lock;
- publication-prep execution contract;
- meaningful creative transformation (no raw-photo fallback);
- Brand Asset + Public CTA lock;
- copy/voice + Visible Text gate;
- exact-final visual QA / publish preflight.

A beautiful artifact that violates Product Truth, branding, CTA or facts fails. A truthful raw photo carousel that skipped meaningful treatment also fails when the request was publication prep.

**Reference-role separation:** Product Truth QA images are not aesthetic references. For creative/publication work, style/atmosphere/composition come only from explicitly approved aesthetic references. Product Truth comes from the actual product source pixels plus the text fidelity guide. A Product Truth teaching/QA board must never be sent to an image-generation or style-conditioning tool.

## Conflict order

When authorities disagree, resolve in this order:

`system / safety / rights` → `Constitution + Product Truth + verified facts` → `tenant/instance policy` → `domain authority / pack` → `owner-approved visual/copy standards` → `local creative preference`.

Never use memory of an old chat to override a newer canonical authority.
## ChatGPT Project binding

For a ChatGPT Project, this gate must be named directly in **Project Instructions** and stored as a Project Source (or otherwise supplied in project context). Project Instructions must say that every request first performs this preflight and that missing authority fails closed.

Project memory is helpful context, not governance. Do not rely on a previous chat to remember the pipeline. The always-on Project Instructions are the bootstrap; this gate + manifest are the router; domain files/skills are the authority.

## What this gate is not

- not a second runtime;
- not a new office or pack;
- not permission to load all 273 specialists every turn;
- not a replacement for provider receipts, file evidence or current operational Sources of Truth;
- not a promise that a tool exists when the current environment does not expose it.

The desired behavior is simple: **route first, verify authority, execute, verify the exact result.**
## Creative evidence phase

`vf_project_preflight.py --domain creative_publication` defaults to pre-production evidence. For review delivery, specify `--phase delivery`. The `instagram_action` domain always requires delivery evidence and rejects `--phase production`; a completed nine-stage manifest must not be checked as a five-stage production manifest. Transport diagnostics never authorize creative production or publication.
