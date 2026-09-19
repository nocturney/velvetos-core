const ALLOWED_RECIPIENT = 'nocturney@gmail.com';
const SECRET_PROPERTY = 'VF_GMAIL_BRIEF_SHARED_SECRET';
const MAX_SKEW_SECONDS = 300;

function jsonResponse_(status, body) {
  const out = ContentService.createTextOutput(JSON.stringify(body));
  out.setMimeType(ContentService.MimeType.JSON);
  return out;
}

function hex_(bytes) {
  return bytes.map(function (b) {
    const v = (b < 0 ? b + 256 : b).toString(16);
    return v.length === 1 ? '0' + v : v;
  }).join('');
}

function sha256Hex_(text) {
  return hex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    text,
    Utilities.Charset.UTF_8
  ));
}

function hmacHex_(secret, text) {
  return hex_(Utilities.computeHmacSha256Signature(
    text,
    secret,
    Utilities.Charset.UTF_8
  ));
}

function constantTimeEqual_(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) {
    return false;
  }
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function decodeRawMessage_(raw) {
  const bytes = Utilities.base64DecodeWebSafe(raw);
  return Utilities.newBlob(bytes).getDataAsString('UTF-8');
}

function extractTo_(mime) {
  const match = mime.match(/^To:\s*([^\r\n]+)$/mi);
  return match ? match[1].trim().toLowerCase() : '';
}

function doGet() {
  return jsonResponse_(200, {ok: true, service: 'velvet-gmail-brief-bridge', version: 1});
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      throw new Error('missing request body');
    }

    const body = JSON.parse(e.postData.contents);
    const requestId = String(body.requestId || '').trim();
    const issuedAt = Number(body.issuedAt || 0);
    const to = String(body.to || '').trim().toLowerCase();
    const raw = String(body.raw || '').trim();
    const signature = String(body.signature || '').trim().toLowerCase();

    if (!requestId || !issuedAt || !raw || !signature) {
      throw new Error('missing signed request fields');
    }
    if (to !== ALLOWED_RECIPIENT) {
      throw new Error('recipient is not owner-allowed');
    }

    const now = Math.floor(Date.now() / 1000);
    if (Math.abs(now - issuedAt) > MAX_SKEW_SECONDS) {
      throw new Error('request timestamp outside allowed window');
    }

    const secret = PropertiesService.getScriptProperties().getProperty(SECRET_PROPERTY);
    if (!secret) {
      throw new Error('bridge shared secret is not configured');
    }

    const rawSha = sha256Hex_(raw);
    const canonical = requestId + '\n' + issuedAt + '\n' + to + '\n' + rawSha;
    const expected = hmacHex_(secret, canonical);
    if (!constantTimeEqual_(signature, expected)) {
      throw new Error('invalid request signature');
    }

    const mime = decodeRawMessage_(raw);
    if (extractTo_(mime) !== ALLOWED_RECIPIENT) {
      throw new Error('MIME recipient does not match owner lock');
    }

    const lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try {
      const props = PropertiesService.getScriptProperties();
      const lastId = props.getProperty('LAST_SUCCESS_REQUEST_ID');
      if (lastId === requestId) {
        throw new Error('duplicate requestId');
      }

      const response = UrlFetchApp.fetch(
        'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
        {
          method: 'post',
          contentType: 'application/json',
          headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()},
          payload: JSON.stringify({raw: raw}),
          muteHttpExceptions: true
        }
      );

      const code = response.getResponseCode();
      const text = response.getContentText();
      let result = {};
      try {
        result = JSON.parse(text);
      } catch (parseErr) {
        throw new Error('Gmail API returned non-JSON HTTP ' + code);
      }

      if (code < 200 || code >= 300) {
        const message = result && result.error && result.error.message
          ? result.error.message
          : 'Gmail API error';
        throw new Error('Gmail API HTTP ' + code + ': ' + message);
      }

      const messageId = String(result.id || '').trim();
      if (!messageId) {
        throw new Error('Gmail API returned no message id');
      }

      props.setProperty('LAST_SUCCESS_REQUEST_ID', requestId);
      props.setProperty('LAST_SUCCESS_MESSAGE_ID', messageId);
      props.setProperty('LAST_SUCCESS_AT', new Date().toISOString());

      return jsonResponse_(200, {
        ok: true,
        messageId: messageId,
        threadId: String(result.threadId || '')
      });
    } finally {
      lock.releaseLock();
    }
  } catch (err) {
    return jsonResponse_(400, {
      ok: false,
      error: String(err && err.message ? err.message : err)
    });
  }
}
