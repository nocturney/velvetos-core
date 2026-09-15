---
name: canva-bulk-create
description: Bulk-create Canva designs from tabular data using a brand template with autofill fields, producing one design per row. Use when users say "bulk create designs from this CSV", "generate one design per row", "create a design for each product", "batch generate from a template", or "autofill a template from a spreadsheet". Accepts any tabular data source — uploaded files, pasted tables, JSON, or URLs.
---

# Canva Bulk Design Creation

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

> LEGACY / provenance only for VF publication; not a provider route: Create one Canva design per row of data by autofilling a brand template with data tags.

## Workflow

### Step 1: Get the Data

Accept data in any form the user provides and extract a list of rows with named columns:

- **Uploaded file**: read the file and extract headers and rows
- **Pasted data**: parse markdown tables, tab-separated values, or JSON arrays directly from the chat
- **URL**: fetch the resource and parse the response as tabular data

If no data has been provided, ask the user to share it in whatever format is convenient for them.

Once parsed, show the user:
- Column headers found
- Number of rows (= number of designs that will be created)
- A preview of the first few rows

### Step 2: Select the Brand Template

If the user hasn't specified a template, search for autofill-capable ones:

```
> LEGACY / provenance only for VF publication; not a provider route: Canva:search-brand-templates  dataset=non_empty
```

Show the results and ask the user to pick one. If they already named or described a template, search with that query.

### Step 3: Inspect the Template Schema

```
> LEGACY / provenance only for VF publication; not a provider route: Canva:get-brand-template-dataset  template_id=<selected_id>
```

This returns the field names and types (text, image, chart) that the template expects.

### Step 4: Map CSV Columns to Template Fields

Present a mapping table to the user:

| Template Field | Type | Matched CSV Column | Notes |
|---|---|---|---|
| `product_name` | text | `Product Name` | auto-matched |
| `price` | text | `Price` | auto-matched |
| `hero_image` | image | *(none)* | no match — image fields need asset IDs |

**Matching rules:**
- Do case-insensitive, fuzzy matching between CSV headers and template field names
- Text fields can be filled directly from CSV string values
> LEGACY / provenance only for VF publication; not a provider route: - Image fields require a Canva asset ID — see **Image Field Handling** below
- Chart fields require structured data — treat as advanced and ask the user for clarification

Confirm the mapping with the user before proceeding, especially if there are unmapped fields or ambiguous matches.

#### Image Field Handling

There are two ways a CSV can supply images for image-type template fields:

> LEGACY / provenance only for VF publication; not a provider route: **Pattern A — CSV has a Canva asset ID column** (e.g. `image_asset_id`):
Use the asset ID value directly in the `autofill-design` call:
```json
{ "image": { "type": "image", "asset_id": "<value from CSV column>" } }
```

**Pattern B — CSV has an image URL column** (e.g. `image_url`):
> LEGACY / provenance only for VF publication; not a provider route: URLs cannot be passed directly to `autofill-design`. Upload each URL to Canva first using `Canva:upload-asset-from-url`, capture the returned asset ID, then use it in the autofill call. Do the upload immediately before creating that row's design so failures stay localised.

**Pattern C — No image column in CSV:**
Ask the user whether to skip the image field (template default image stays) or abort. Skipping is safe — just omit the image key from the `data` payload entirely.

### Step 5: Bulk Create — One Design per Row

> LEGACY / provenance only for VF publication; not a provider route: Loop through every CSV row and call `Canva:autofill-design` for each one. Call them **sequentially**, not all at once — the API may have rate limits and sequential calls are easier to debug.

For each row:

> LEGACY / provenance only for VF publication; not a provider route: 1. If the row has an image URL column (Pattern B), first call `Canva:upload-asset-from-url` to get a Canva asset ID.
2. Build the `data` payload from the confirmed field mapping:

```json
{
  "text_field_name": { "type": "text", "text": "<value from CSV>" },
  "image_field_name": { "type": "image", "asset_id": "<asset ID>" }
}
```

> LEGACY / provenance only for VF publication; not a provider route: 3. Call `Canva:autofill-design` with the template ID, data payload, and a descriptive title using the row number or a meaningful column value (e.g. `"Bulk Design - Row 3 - <identifier>"`).

Track results as you go:

```
Row 1 / 50: Created — <design_url>
Row 2 / 50: Created — <design_url>
Row 3 / 50: Failed — <error>
```

### Step 6: Report Results

After all rows are processed, summarise:

- Total rows attempted
- Successes (with links)
- Failures (with row number and reason)

Offer to save a summary CSV with columns: `row`, `status`, `design_url`, `error`.

## Notes

> LEGACY / provenance only for VF publication; not a provider route: - Autofill requires a Canva Enterprise plan.
- For large CSVs (50+ rows), warn the user upfront that this will make N API calls and may take a while. Offer to do a test run on the first 3 rows before proceeding with the full batch.
- If some rows fail, continue with the rest — don't abort the whole batch.
- Skip rows where all mapped fields are empty and warn the user about them.
- If no CSV column matches a required template field, ask the user to confirm which column to use or whether to skip that field.
- Template field names are case-sensitive in the API — use the exact keys from `get-brand-template-dataset`.
- There is no "undo bulk create" — warn the user before starting large runs.
> LEGACY / provenance only for VF publication; not a provider route: - Designs created this way are full Canva designs the user can further edit in their account.

## Verification

Before claiming completion, verify the routed target state or run the existing package/route sensor. Configuration, a draft, a command exit, or an agent statement alone is not success. If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.

## Velvet Factory instance override — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: When the active job/instance is Velvet Factory or `@velvets_cloud`, do not operate this Canva skill in isolation. Before any create/edit/resize/feedback/brand-check/bulk action, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`, verify `MAHVL7PKpvE` / `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`, and require `visual_standard_gate=PASS`. If the binding cannot be verified, return `visual_standard_unavailable` instead of using generic Canva/template defaults. Product source media remains the sole authority for the physical product.
