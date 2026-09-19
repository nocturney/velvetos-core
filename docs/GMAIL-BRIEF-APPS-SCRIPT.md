# Gmail Brief Apps Script Bridge · production owner setup

This is the canonical Velvet Factory owner-email transport.

The repo keeps the exact final HTML/MIME build, owner lock, Visible Text Gate/hash,
CID embedding and one-shot request. Google Apps Script only owns authentication
to the owner's Gmail account and forwards the exact RFC822 message to Gmail API.

## Security model

- Recipient is locked to `nocturney@gmail.com` in both GitHub and Apps Script.
- Enabled sends require the exact `owner-brief` Visible Text Gate receipt/hash.
- GitHub signs every bridge request with HMAC-SHA256 using a shared secret.
- The bridge rejects requests older than 5 minutes.
- Successful `requestId` values are deduplicated.
- Apps Script requests only:
  - `https://www.googleapis.com/auth/gmail.send`
  - `https://www.googleapis.com/auth/script.external_request`
- The bridge returns the real Gmail API `messageId`.
- No Gmail read/search/modify scope is requested.
- No OAuth client secret or refresh token is stored in the repository.

## Repo files

- `packages/vfops/apps_script_gmail_bridge/Code.gs`
- `packages/vfops/apps_script_gmail_bridge/appsscript.json`
- `packages/vfops/gmail_apps_script_request.py`
- `packages/vfops/out/gmail-send-request.json`
- `.github/workflows/gmail-brief-send.yml`

## One-time Apps Script deployment

Create a standalone Apps Script project owned by `nocturney@gmail.com`, push the
two files under `packages/vfops/apps_script_gmail_bridge/`, then deploy as a Web app:

- Execute as: Me
- Who has access: Anyone

The endpoint itself is public, but it cannot send without a valid HMAC signature
created with the private shared secret. The bridge independently verifies the MIME
recipient is the owner address.

In Apps Script Project Settings add Script property:

- Key: `VF_GMAIL_BRIEF_SHARED_SECRET`
- Value: a randomly generated 256-bit secret

In GitHub Actions repository secrets add:

- `GMAIL_APPS_SCRIPT_URL` = deployed `https://script.google.com/.../exec` URL
- `GMAIL_APPS_SCRIPT_SECRET` = the same shared secret

The legacy `GMAIL_OAUTH_JSON` secret is not used by the canonical workflow.

## Authorization

The owner authorizes the Apps Script project once. Because the script runs as the
owner and explicitly requests `gmail.send`, there is no seven-day Testing refresh
token lifecycle in the production sender.

## Delivery truth

Never claim delivery until all are true:

1. workflow success;
2. exact Visible Text Gate PASS/hash;
3. Apps Script bridge returns a non-empty Gmail message ID;
4. Gmail presence is confirmed when a readable Gmail connector is available;
5. the one-shot request is restored to `enabled:false`.

No interactive Gmail plugin fallback is allowed for the canonical brief.
