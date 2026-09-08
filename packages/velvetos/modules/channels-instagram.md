# Instagram channels

Module id: `channels-instagram`

## Provides
- \`channels.instagram[]\` with \`id\`, \`handle\`, \`purpose\`, \`primary\`
- Exactly one primary when the list is non-empty
- Dual-brand isolation: content for channel A does not cross to B without lead seat
- Public CTA from tenant \`PUBLIC_CURRENT_CTA\` (Instagram message / Hebrew «שלחו לנו הודעה…») — never auto-dm / \`send_dm\`
- Never invent WhatsApp phone as public CTA; \`BUSINESS_CONTACT_RECORD\` stays in desk/integration only

## Packs
\`vfigos\`, \`vfcanva\`, \`vfcovers\`

Always present in core. An instance enables it via `modulesEnabled` — this is not an on/off goal toggle in a shared tenant list.
