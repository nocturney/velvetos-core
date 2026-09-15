---
name: canva-resize-for-social-media
description: Resize a Canva design into multiple social media formats (Facebook post, Facebook story, Instagram post, Instagram story, LinkedIn post). Use this skill when users want to resize Canva designs specifically for multiple social media platforms in one operation, rather than resizing to a single format manually.
---

# Canva Resize for Social Media

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

> LEGACY / provenance only for VF publication; not a provider route: Automatically resize a single Canva design into multiple social media formats.

## Overview

> LEGACY / provenance only for VF publication; not a provider route: This skill enables rapid multi-platform content distribution by taking a single Canva design and creating optimized versions for:
- Facebook post
- Facebook story
- Instagram post
- Instagram story
- LinkedIn post

> LEGACY / provenance only for VF publication; not a provider route: All resized versions are provided with Canva edit links so users can further edit or download them directly from Canva.

## Workflow

### Step 1: Identify the Source Design

> LEGACY / provenance only for VF publication; not a provider route: Determine which Canva design the user wants to resize. This can be provided in three ways:

1. **Direct design ID**: User provides a design ID (starts with "D")
   - Example: "resize design DABcd1234ef for all social media"
   - Use the design ID directly with `get-design` tool to retrieve design information
   
> LEGACY / provenance only for VF publication; not a provider route: 2. **Direct design URL**: User provides a Canva design link
> LEGACY / provenance only for VF publication; not a provider route:    - Example: "resize https://www.canva.com/design/DABcd1234ef/... for all social media"
   - Extract the design ID from the URL (the part after `/design/` and before the next `/` or query parameter)
   - Use the extracted design ID with `get-design` tool
   
3. **Search by design name**: Use `search-designs` tool with the design name as the query
   - Example: "resize my Demo Brand Template: Brix&Hart Flyer design for all social media"
   - Use the exact name/phrase the user provides as the search query
   - If multiple matches are found, present options and ask the user to select one
   
4. **Current context**: If the user just created or edited a design in the conversation, use that design ID

**Implementation note**: When searching by name, pass the design name directly to `search-designs` as the query parameter. The tool will find the best match based on the design title.

### Step 2: Retrieve Source Design Information

Use the `get-design` tool with the design ID to:
- Confirm the design exists and is accessible
- Get the design title (for naming resized versions)
- Verify design type compatibility

### Step 3: Ask Which Platforms and Formats

Present the available formats and ask which ones the user wants:

```
Which platforms and formats would you like to resize for?

- Facebook post (1200×630)
- Facebook story (1080×1920)
- Instagram post (1080×1080)
- Instagram story (1080×1920)
- LinkedIn post (1200×627)
```

If the user says "all" or "all social media", use all five. Otherwise, only resize for the ones they select.

### Step 4: Resize to Selected Formats

Execute the resize operations **in parallel** by calling the `resize-design` tool once for each selected format. Use these exact specifications:

**Available formats and dimensions:**

1. **Facebook Post**: 1200 × 630 pixels (custom)
   ```
   design_type: { type: "custom", width: 1200, height: 630 }
   ```

2. **Facebook Story**: 1080 × 1920 pixels (custom)
   ```
   design_type: { type: "custom", width: 1080, height: 1920 }
   ```

3. **Instagram Post**: 1080 × 1080 pixels (custom)
   ```
   design_type: { type: "custom", width: 1080, height: 1080 }
   ```

4. **Instagram Story**: 1080 × 1920 pixels (custom)
   ```
   design_type: { type: "custom", width: 1080, height: 1920 }
   ```

5. **LinkedIn Post**: 1200 × 627 pixels (custom)
   ```
   design_type: { type: "custom", width: 1200, height: 627 }
   ```

**Note**: Facebook Story and Instagram Story have identical dimensions. Create both versions but inform the user they're the same size.

**Error handling**: If a resize operation fails, continue with remaining formats and report which formats succeeded and which failed at the end.

### Step 5: Present Results with Edit Links

**Present comprehensive results to the user:**

Provide the user with a summary including:

1. **Summary**: Confirm which formats were created successfully
> LEGACY / provenance only for VF publication; not a provider route: 2. **Design edit links**: Canva editor URLs for each resized design so users can make further edits or download directly from Canva
3. **Note about duplicates**: Mention that Facebook Story and Instagram Story have identical dimensions

**Presentation format example:**
```
✅ Successfully resized your design for all social media platforms!

Edit Links:

**Facebook Post** (1200×630)
> LEGACY / provenance only for VF publication; not a provider route: - [Edit in Canva](edit_url)

**Facebook Story** (1080×1920)
> LEGACY / provenance only for VF publication; not a provider route: - [Edit in Canva](edit_url)

**Instagram Post** (1080×1080)
> LEGACY / provenance only for VF publication; not a provider route: - [Edit in Canva](edit_url)

**Instagram Story** (1080×1920)
> LEGACY / provenance only for VF publication; not a provider route: - [Edit in Canva](edit_url)

**LinkedIn Post** (1200×627)
> LEGACY / provenance only for VF publication; not a provider route: - [Edit in Canva](edit_url)

Note: Facebook Story and Instagram Story use the same dimensions (1080×1920).
```

**Implementation details**:
- Design edit links come from the `resize-design` tool response (use the `urls.edit_url` field from each resized design)
- Present links as clickable URLs, not just plain text
- Organize by platform for easy scanning

## Key Implementation Notes

> LEGACY / provenance only for VF publication; not a provider route: - **Compatibility**: Check if `resize-design` is available in the current MCP tools. If not, inform the user that this skill requires the Canva MCP resize tool in the current host
- **Parallel execution**: Resize operations should be performed in parallel for efficiency
- **Consistent naming**: Use the source design title with platform suffix for resized designs
- **Error resilience**: If any operation fails, complete the remaining operations and clearly report what succeeded/failed
- **User confirmation**: Do not require user approval between steps - execute the full workflow automatically unless errors occur
- **Format accuracy**: Always use the exact pixel dimensions specified above for each platform

## Velvet Factory instance override — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: When the active job/instance is Velvet Factory or `@velvets_cloud`, do not operate this Canva skill in isolation. Before any create/edit/resize/feedback/brand-check/bulk action, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`, verify `MAHVL7PKpvE` / `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`, and require `visual_standard_gate=PASS`. If the binding cannot be verified, return `visual_standard_unavailable` instead of using generic Canva/template defaults. Product source media remains the sole authority for the physical product.
