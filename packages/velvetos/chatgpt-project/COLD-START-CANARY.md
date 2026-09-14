# ChatGPT Project Cold-Start Canary — Velvet Factory

Purpose: detect regression between repository policy and a brand-new ChatGPT Project chat.

## Preconditions
- Project Instructions contain the exact v6 bootstrap.
- Project Sources contain `Velvet-Factory-Project-Authority-v6.txt`.
- Project Sources contain `Velvet-Factory-APPROVED-Visual-Reference-v2.jpg`.
- Superseded v5 authority and old visual-reference sources are removed from Project Sources.

## Canary A — publication prep
Start a brand-new chat, attach real product photos, then send only:
`תכין פוסט לפרסום`

PASS requires all of the following behavior:
- treats the request as execution, not planning;
- uses real product source as physical truth;
- produces at least one genuinely edited visual artifact in the same task when editing capability exists;
- presentation shows meaningful creative transformation rather than raw/crop-only fallback;
- does not assume carousel from multiple photos;
- no invented logo/wordmark;
- no public phone/WhatsApp/contact bar;
- no generated Hebrew baked into the base image;
- caption/copy uses only supported facts and current CTA;
- does not claim ready before exact-final QA.

## Canary B — offering shape
Start a new chat and ask what Velvet Factory offers.
PASS: answer resolves to two public tracks only — ready products; custom 3D print/model work. Quantity/customer type may be described only as job attributes, never as a third service pillar.

## Canary C — missing authority
Temporarily remove or rename the v6 authority source, then ask for publication prep.
PASS: the chat reports a sync/authority blocker and does not silently continue from memory or generic defaults.

## Canary D — source conflict
If an old authority source is deliberately present beside v6, ask a request affected by a changed rule.
PASS: v6 wins. If version cannot be determined, fail closed rather than blend rules.

## Failure signature
Any of these is a regression: caption-only; image-ranking-only; raw carousel; generic template output; invented branding; phone/WhatsApp leakage; stale offering shape; no authority load; ready claim without artifact evidence.

## Evidence record
For each run record: date/time, chat URL/name, request, source set present, artifact screenshot/file, PASS/FAIL per criterion, and first failing layer. Repository sensors validate contract wiring; this canary validates actual ChatGPT Project behavior and therefore cannot be replaced by static source checks.
