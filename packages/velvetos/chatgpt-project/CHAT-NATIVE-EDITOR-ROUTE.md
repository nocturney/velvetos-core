# Velvet Factory — Chat-native image editor route

Status: **Project source extension for Revision 6.6.11**  
Base creative runtime: **Revision 6.6.9 / VF-PROJECT-6.6.9-NATIVE-PRODUCT-EDIT-ROUTING**.  
Reel/video extension: **Revision 6.6.10 / VF-PROJECT-6.6.10-REEL-VIDEO-ROUTE**.

## 1. Purpose

Restore the proven ChatGPT built-in image editor as the preferred execution route for still publication-prep when the host editor is available but its call is terminal and does not expose file-backed continuation.

This route does **not** weaken Product Truth and does **not** pretend that post-tool QA happened when the tool contract makes post-tool continuation impossible.

## 2. Route selection

For a still post/carousel/Story request with current-task product photos, resolve routes in this order:

1. **CHAT_NATIVE_TERMINAL** — preferred when the built-in ChatGPT image editor can edit the current product photo and return the edited image to the user, but the call is terminal or does not expose exact output bytes for continuation.
2. **FILE_BACKED_NATIVE_EDIT** — use the existing 6.6.9 Native Product Edit workflow when the actual editor accepts the current product photo, returns accessible bytes, and allows continuation to native-import, Identity Gate, Creative Gate, MASTER and deterministic finalization.
3. **SOURCE_COMPOSITE** — bounded 6.6.9 fallback when neither Native route is actually available.

Do not route to a paid external provider merely because CHAT_NATIVE_TERMINAL lacks file-backed continuation. Existing zero-new-recurring-cost policy remains in force.

## 3. Product identity lock

Before any Chat-native terminal edit:

- inspect the current-task source photos;
- select the hero source;
- lock silhouette, proportions, parts/openings, surface identity, base colour/finish and critical details;
- define allowed edit scope: scene/background, light, composition, depth of field, crop and placement;
- define explicit forbidden changes to product geometry and identity.

Only current-task product photo(s) may be image inputs to the edit. STYLE-POST references remain visual comparison only; approved logos and reference boards are not Native image-conditioning inputs.

## 4. Pre-terminal creative preparation

Because the built-in editor call is terminal, everything that would normally be prepared after a file-backed Native edit must be decided **before** the call:

- selected style reference and its role;
- scene, surface, light and composition target;
- exact Hebrew headline/subhead/chips if used;
- RTL wording and factual checks;
- safe negative space and product-protection zones;
- whether insets are omitted or source-backed;
- whether the optional logo is omitted.

The default is to omit the logo on this route unless an exact approved-logo placement can be performed without asking the image model to redraw or imitate it.

## 5. Terminal final composition exception

The 6.6.9 rule that final Hebrew/graphics are added only after MASTER applies to **FILE_BACKED_NATIVE_EDIT**.

For **CHAT_NATIVE_TERMINAL only**, the final terminal edit may include the already-validated Hebrew and editorial graphics in the same image-edit call, because there is no supported post-call continuation for deterministic overlay.

This exception is bounded:
- no invented facts, material, dimensions, durability, quality, stock, price or fit;
- no phone, WhatsApp or wa.me without exact current-task authorization;
- no synthetic alternate product view;
- no generated replacement logo;
- no style-reference product/text/claim/CTA copied into the output.

## 6. Evidence semantics

A successful CHAT_NATIVE_TERMINAL result is an **OWNER_REVIEW_CANDIDATE**.

Do not claim any of the following unless a later file-backed process actually proves them:
- native-import completed;
- Identity Gate PASS;
- Creative Gate PASS;
- MASTER selected;
- exact-final SHA-256 bound;
- publication-ready or publish-authorized.

The image itself is still a complete reviewable post candidate, which satisfies “תכין פוסט” / prepare-post intent. Preparation remains separate from publication.

## 7. Failure behaviour

Do not stop at a brief, raw source, diagnosis or “provider missing” message when CHAT_NATIVE_TERMINAL is available.

If the built-in image editor is unavailable, use the next valid route. If no route can produce a real review visual, report the narrow capability blocker; never present a weak raw-photo-plus-text fallback as finished.

## 8. Fresh-chat acceptance

Revision 6.6.11 is not accepted merely because repo CI passes.

The real acceptance test is:
1. fresh ChatGPT Project chat;
2. current product photos supplied;
3. owner message: **“תכין פוסט”**;
4. the Project selects CHAT_NATIVE_TERMINAL when the built-in editor is terminal-only;
5. one complete edited image with Hebrew/graphics is returned for owner review;
6. the response does not falsely claim file-backed gates or publication approval.

Record installation/provider/fresh-chat evidence separately from repository source state.
