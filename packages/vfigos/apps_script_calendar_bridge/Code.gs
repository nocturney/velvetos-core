const CALENDAR_NAME = 'אינסטגרם';
const PUBLISHER_BASE = 'https://velvetos-instagram-publisher.velvetos-vf.workers.dev';
const PUBLISHER_TOKEN_PROPERTY = 'VF_PUBLISHER_CONTROL_TOKEN';
const CALENDAR_ID_PROPERTY = 'VF_INSTAGRAM_CALENDAR_ID';
const LAST_SYNC_PROPERTY = 'VF_INSTAGRAM_LAST_SYNC';
const EXPECTED_PUBLISHER_TOKEN_SHA256 = '94b39e445255a43d83f4a8847b24bb7eeffd9b13f1219047aa5cdbc95a6c9507';
const ACTIVE_STATUSES = ['scheduled','retry','publishing','reconcile_required','published_verified','dead_letter'];
const REQUIRED_SCOPES = [
  'https://www.googleapis.com/auth/calendar',
  'https://www.googleapis.com/auth/script.external_request',
  'https://www.googleapis.com/auth/script.scriptapp'
];

function jsonResponse_(body) {
  return ContentService.createTextOutput(JSON.stringify(body)).setMimeType(ContentService.MimeType.JSON);
}

function hex_(bytes) {
  return bytes.map(function(b) { const v=b<0?b+256:b; return ('0'+v.toString(16)).slice(-2); }).join('');
}

function sha256Hex_(text) {
  return hex_(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, text, Utilities.Charset.UTF_8));
}

function authorizeCalendarBridge() {
  ScriptApp.requireScopes(ScriptApp.AuthMode.FULL, REQUIRED_SCOPES);
  const cal = ensureInstagramCalendar_();
  return {ok:true, calendarId:cal.getId(), calendarName:cal.getName(), auth:authState_()};
}

function authState_() {
  const info = ScriptApp.getAuthorizationInfo(ScriptApp.AuthMode.FULL, REQUIRED_SCOPES);
  return {
    status: String(info.getAuthorizationStatus()),
    authorizationUrl: info.getAuthorizationUrl() || ''
  };
}

function syncTriggerCount_() {
  return ScriptApp.getProjectTriggers().filter(function(t) {
    return t.getHandlerFunction() === 'syncPublisherCalendar';
  }).length;
}

function doGet(e) {
  const action = String((e && e.parameter && e.parameter.action) || 'health');
  if (action === 'auth') return jsonResponse_({ok:true, service:'velvet-instagram-calendar-bridge', auth:authState_()});
  const props = PropertiesService.getScriptProperties();
  return jsonResponse_({
    ok:true,
    service:'velvet-instagram-calendar-bridge',
    calendarName:CALENDAR_NAME,
    calendarId:props.getProperty(CALENDAR_ID_PROPERTY) || '',
    lastSync:props.getProperty(LAST_SYNC_PROPERTY) || '',
    syncTriggerCount:syncTriggerCount_(),
    auth:authState_()
  });
}

function doPost(e) {
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (String(body.action || '') !== 'bootstrap') throw new Error('unsupported action');
    const publisherToken = String(body.publisherToken || '').trim();
    if (publisherToken.length < 32) throw new Error('publisher token missing');
    if (sha256Hex_(publisherToken) !== EXPECTED_PUBLISHER_TOKEN_SHA256) throw new Error('publisher token mismatch');
    const result = bootstrapCalendarBridge_(publisherToken);
    return jsonResponse_({ok:true, result:result});
  } catch (err) {
    return jsonResponse_({ok:false, error:String(err && err.message ? err.message : err)});
  }
}

function bootstrapCalendarBridge_(publisherToken) {
  const props = PropertiesService.getScriptProperties();
  props.setProperty(PUBLISHER_TOKEN_PROPERTY, publisherToken);
  const cal = ensureInstagramCalendar_();
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (t.getHandlerFunction() === 'syncPublisherCalendar') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('syncPublisherCalendar').timeBased().everyMinutes(5).create();
  const sync = syncPublisherCalendar();
  return {calendarId:cal.getId(), calendarName:cal.getName(), sync:sync};
}

function ensureInstagramCalendar_() {
  const props = PropertiesService.getScriptProperties();
  const stored = String(props.getProperty(CALENDAR_ID_PROPERTY) || '').trim();
  if (stored) {
    const existing = CalendarApp.getCalendarById(stored);
    if (existing) return existing;
  }
  const matches = CalendarApp.getCalendarsByName(CALENDAR_NAME);
  let cal = matches && matches.length ? matches[0] : null;
  if (!cal) {
    cal = CalendarApp.createCalendar(CALENDAR_NAME, {
      description:'מראה חד-כיוונית של תזמוני Instagram מ-VelvetOS Publisher. עריכה ביומן אינה משנה את הפרסום.',
      timeZone:'Asia/Jerusalem'
    });
  }
  props.setProperty(CALENDAR_ID_PROPERTY, cal.getId());
  return cal;
}

function publisherJson_(path) {
  const token = String(PropertiesService.getScriptProperties().getProperty(PUBLISHER_TOKEN_PROPERTY) || '').trim();
  if (!token) throw new Error('publisher token not configured');
  const response = UrlFetchApp.fetch(PUBLISHER_BASE + path, {
    method:'get',
    headers:{Authorization:'Bearer ' + token, Accept:'application/json'},
    muteHttpExceptions:true
  });
  if (response.getResponseCode() !== 200) throw new Error('publisher HTTP ' + response.getResponseCode());
  return JSON.parse(response.getContentText());
}

function eventKey_(jobId) {
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, jobId, Utilities.Charset.UTF_8);
  return 'VF_IG_EVENT_' + digest.slice(0,12).map(function(b){const v=b<0?b+256:b;return ('0'+v.toString(16)).slice(-2);}).join('');
}

function statusLabel_(status) {
  const labels = {scheduled:'מתוזמן',retry:'ניסיון חוזר',publishing:'מפרסם',reconcile_required:'דורש בדיקה',published_verified:'פורסם',dead_letter:'כשל'};
  return labels[status] || status;
}

function titleFor_(job) {
  const kind = job.kind === 'carousel' ? 'קרוסלה' : (job.kind === 'image' ? 'פוסט' : String(job.kind || 'פוסט'));
  return 'Instagram · ' + String(job.content_id || job.id) + ' · ' + kind + ' · ' + statusLabel_(job.status);
}

function descriptionFor_(job) {
  return [
    'VelvetOS Publisher',
    'סטטוס: ' + statusLabel_(job.status),
    'job_id: ' + job.id,
    'content_id: ' + String(job.content_id || ''),
    'סוג: ' + String(job.kind || ''),
    job.permalink ? ('Instagram: ' + job.permalink) : '',
    '',
    'מקור האמת לתזמון הוא Cloudflare Publisher.',
    'עריכה ידנית ביומן אינה משנה את מועד הפרסום.'
  ].filter(function(x){return x !== '';}).join('\n');
}

function upsertEvent_(cal, job) {
  const props = PropertiesService.getScriptProperties();
  const key = eventKey_(job.id);
  let eventId = String(props.getProperty(key) || '').trim();
  let ev = eventId ? cal.getEventById(eventId) : null;
  const start = new Date(Number(job.scheduled_at) * 1000);
  const end = new Date(start.getTime() + 30 * 60 * 1000);
  if (!ev) {
    ev = cal.createEvent(titleFor_(job), start, end, {description:descriptionFor_(job)});
    props.setProperty(key, ev.getId());
  } else {
    ev.setTitle(titleFor_(job));
    ev.setTime(start, end);
    ev.setDescription(descriptionFor_(job));
  }
  try { ev.removeAllReminders(); } catch (_) {}
  try { ev.setTransparency(CalendarApp.EventTransparency.TRANSPARENT); } catch (_) {}
  return {jobId:job.id, eventId:ev.getId(), status:job.status};
}

function deleteEvent_(cal, jobId) {
  const props = PropertiesService.getScriptProperties();
  const key = eventKey_(jobId);
  const eventId = String(props.getProperty(key) || '').trim();
  if (eventId) {
    const ev = cal.getEventById(eventId);
    if (ev) ev.deleteEvent();
    props.deleteProperty(key);
  }
}

function syncPublisherCalendar() {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const cal = ensureInstagramCalendar_();
    const listing = publisherJson_('/v1/jobs');
    const jobs = listing.jobs || [];
    const results = [];
    jobs.forEach(function(summary) {
      const status = String(summary.status || '');
      if (status === 'cancelled') { deleteEvent_(cal, summary.id); return; }
      if (ACTIVE_STATUSES.indexOf(status) < 0) return;
      const full = publisherJson_('/v1/jobs/' + encodeURIComponent(summary.id)).job || summary;
      results.push(upsertEvent_(cal, full));
    });
    PropertiesService.getScriptProperties().setProperty(LAST_SYNC_PROPERTY, new Date().toISOString());
    return {calendarId:cal.getId(), count:results.length, events:results};
  } finally {
    lock.releaseLock();
  }
}
