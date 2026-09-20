from __future__ import annotations
import argparse, json, sqlite3

DB='file:/var/lib/openpost/db/openpost.db?mode=ro'
ACTIVE_JOBS={'pending','processing'}
AMBIGUOUS_DELIVERY={'submitted','processing','provider_scheduled','ambiguous','manual_resolution','live','queued'}

def rowdict(row): return dict(row) if row is not None else None

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--publication-id',required=True)
    ap.add_argument('--rendition-id',required=True)
    a=ap.parse_args()
    c=sqlite3.connect(DB,uri=True); c.row_factory=sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    pub=c.execute('select id,status,failure_dismissed_at,revision from publications where id=?',(a.publication_id,)).fetchone()
    ren=c.execute('select id,status,error_kind,error_retryable,error_code,error_http_status from renditions where id=? and publication_id=?',(a.rendition_id,a.publication_id)).fetchone()
    job=c.execute('select id,status,type,run_at,locked_at,locked_by,attempts,max_attempts from jobs where scope_id=? order by run_at desc limit 1',(a.publication_id,)).fetchone()
    delivery=c.execute('select state,retry_safety,safe_error_class,safe_error_code,error_http_status,external_id from provider_deliveries where publication_id=? and rendition_id=? order by updated_at desc limit 1',(a.publication_id,a.rendition_id)).fetchone()
    attempt=c.execute('select status,submission_state,retry_safety,safe_error_class,safe_error_code,error_http_status,external_id from provider_write_attempts where publication_id=? and rendition_id=? order by attempt_number desc limit 1',(a.publication_id,a.rendition_id)).fetchone()
    if pub is None or ren is None:
        print(json.dumps({'ok':False,'safe_to_failover':False,'reason':'publication_or_rendition_not_found'})); return 0
    active_job=job is not None and job['status'] in ACTIVE_JOBS
    safe=False; reason='primary_not_definitively_failed'
    if active_job:
        reason='primary_job_still_active'
    elif pub['status']!='failed' or ren['status']!='failed':
        reason='primary_not_failed'
    elif delivery is not None and (delivery['state'] in AMBIGUOUS_DELIVERY or delivery['retry_safety']=='reconcile_only'):
        reason='provider_outcome_requires_reconciliation'
    elif delivery is not None and delivery['state']=='rejected' and delivery['retry_safety'] in ('safe','idempotent'):
        safe=True; reason='provider_definitely_rejected_retry_safe'
    elif attempt is not None and attempt['status']=='definite_failure' and attempt['submission_state'] in ('not_sent','rejected') and attempt['retry_safety'] in ('safe','idempotent'):
        safe=True; reason='provider_attempt_definite_failure_retry_safe'
    elif attempt is None and delivery is None and job is not None and job['status'] in ('completed','failed'):
        safe=True; reason='failed_before_provider_write'
    else:
        reason='provider_outcome_not_proven_safe'
    out={
      'ok':True,
      'safe_to_failover':safe,
      'reason':reason,
      'publication':{'status':pub['status'],'failure_dismissed':pub['failure_dismissed_at'] is not None,'revision':pub['revision']},
      'rendition':{'status':ren['status'],'error_kind':ren['error_kind'],'error_retryable':bool(ren['error_retryable']),'error_code':ren['error_code'],'http_status':ren['error_http_status']},
      'job':None if job is None else {'status':job['status'],'type':job['type'],'run_at':job['run_at'],'locked':bool(job['locked_at'] or job['locked_by']),'attempts':job['attempts'],'max_attempts':job['max_attempts']},
      'delivery':None if delivery is None else {'state':delivery['state'],'retry_safety':delivery['retry_safety'],'error_class':delivery['safe_error_class'],'error_code':delivery['safe_error_code'],'http_status':delivery['error_http_status'],'has_external_id':bool(delivery['external_id'])},
      'attempt':None if attempt is None else {'status':attempt['status'],'submission_state':attempt['submission_state'],'retry_safety':attempt['retry_safety'],'error_class':attempt['safe_error_class'],'error_code':attempt['safe_error_code'],'http_status':attempt['error_http_status'],'has_external_id':bool(attempt['external_id'])},
    }
    print(json.dumps(out,ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())