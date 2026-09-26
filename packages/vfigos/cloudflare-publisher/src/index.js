import {
  checkRecentFingerprint,
  publishFingerprint,
  recordFingerprint,
} from "./fingerprint.js";
const te=new TextEncoder();
const json=(v,s=200)=>new Response(JSON.stringify(v),{status:s,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
const now=()=>Math.floor(Date.now()/1000), sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
function hex(b){return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("")}
async function sha256(b){return hex(await crypto.subtle.digest("SHA-256",b))}
async function hmac(secret,text){const k=await crypto.subtle.importKey("raw",te.encode(secret),{name:"HMAC",hash:"SHA-256"},false,["sign"]);return hex(await crypto.subtle.sign("HMAC",k,te.encode(text)))}
function secureEq(a,b){if(typeof a!=="string"||typeof b!=="string"||a.length!==b.length)return false;let x=0;for(let i=0;i<a.length;i++)x|=a.charCodeAt(i)^b.charCodeAt(i);return x===0}
function canonicalJob(j){return JSON.stringify({id:j.id,content_id:j.content_id,package_sha256:j.package_sha256,kind:j.kind,scheduled_at:j.scheduled_at,caption:j.caption,media:j.media,authorization:j.authorization})}
async function requireAdmin(req,env){if(!(env.CONTROL_TOKEN||"").trim())return false;const a=req.headers.get("authorization")||"";const t=a.toLowerCase().startsWith("bearer ")?a.slice(7).trim():"";return secureEq(t,env.CONTROL_TOKEN)}
function validateJob(b){if(!b||typeof b!=="object")throw Error("body_object_required");if(!/^[A-Za-z0-9._-]{3,120}$/.test(b.content_id||""))throw Error("invalid_content_id");if(!/^[0-9a-f]{64}$/.test(b.package_sha256||""))throw Error("invalid_package_sha256");if(!["image","carousel"].includes(b.kind))throw Error("invalid_kind");const ts=Math.floor(Date.parse(b.scheduled_at)/1000);if(!Number.isFinite(ts))throw Error("invalid_scheduled_at");if(typeof b.caption!=="string"||b.caption.length>2200)throw Error("invalid_caption");if(!Array.isArray(b.media)||b.media.length<1||b.media.length>10)throw Error("invalid_media");if(b.kind==="image"&&b.media.length!==1)throw Error("image_requires_one_media");if(b.kind==="carousel"&&b.media.length<2)throw Error("carousel_requires_multiple_media");for(const m of b.media){if(typeof m.key!=="string"||!/^[A-Za-z0-9._-]{3,180}$/.test(m.key))throw Error("invalid_media_key");if(!/^[0-9a-f]{64}$/.test(m.sha256||""))throw Error("media_sha_required")}if(!b.authorization||typeof b.authorization!=="object"||typeof b.authorization.evidence!=="string"||b.authorization.evidence.length<8)throw Error("authorization_evidence_required");return ts}
async function event(env,id,name,detail={}){await env.DB.prepare("INSERT INTO events(job_id,event,detail_json,created_at) VALUES(?,?,?,?)").bind(id,name,JSON.stringify(detail),now()).run()}
async function graph(env,path,params={},method="POST"){if(!(env.META_ACCESS_TOKEN||"").trim()||!(env.IG_USER_ID||"").trim())throw new Error("meta_config_missing");const u=new URL("https://graph.facebook.com/"+(env.GRAPH_VERSION||"v21.0")+"/"+path.replace(/^\//,""));const q=new URLSearchParams({...params,access_token:env.META_ACCESS_TOKEN});let r;if(method==="GET"){u.search=q;r=await fetch(u,{headers:{"accept":"application/json"}})}else r=await fetch(u,{method,headers:{"content-type":"application/x-www-form-urlencoded","accept":"application/json"},body:q});const text=await r.text();let data;try{data=JSON.parse(text)}catch{data={raw:text.slice(0,500)}}if(!r.ok||data.error){const e=new Error("graph_error");e.graph=data;e.http=r.status;throw e}return data}
async function poll(env,id){for(let i=0;i<20;i++){const d=await graph(env,id,{fields:"status_code,status"},"GET");if(d.status_code==="FINISHED")return d;if(["ERROR","EXPIRED"].includes(d.status_code))throw Object.assign(new Error("container_failed"),{graph:d});await sleep(1500)}throw new Error("container_timeout")}
async function verifyMedia(env,media){for(const m of media){const got=await env.MEDIA.getWithMetadata(m.key,{type:"arrayBuffer"});if(!got.value)throw new Error("media_missing");if(got.value.byteLength>25*1024*1024)throw new Error("media_too_large");const h=await sha256(got.value);if(h!==m.sha256||got.metadata?.sha256!==m.sha256)throw new Error("media_sha_mismatch")}}
async function publishJob(env,j){await verifyMedia(env,j.media);const ids=[];if(j.kind==="carousel"){for(const m of j.media){const c=await graph(env,env.IG_USER_ID+"/media",{image_url:m.url,is_carousel_item:"true"});await poll(env,c.id);ids.push(c.id)}const p=await graph(env,env.IG_USER_ID+"/media",{media_type:"CAROUSEL",children:ids.join(","),caption:j.caption});await poll(env,p.id);return await mediaPublish(env,p.id)}const c=await graph(env,env.IG_USER_ID+"/media",{image_url:j.media[0].url,caption:j.caption});await poll(env,c.id);return await mediaPublish(env,c.id)}
async function mediaPublish(env,creationId){let out;try{out=await graph(env,env.IG_USER_ID+"/media_publish",{creation_id:creationId})}catch(e){e.afterPublishBoundary=true;throw e}if(!out.id){const e=new Error("publish_missing_media_id");e.afterPublishBoundary=true;throw e}let v;try{v=await graph(env,out.id,{fields:"id,media_type,permalink,timestamp"},"GET")}catch(e){e.afterPublishBoundary=true;throw e}if(v.id!==out.id||!v.permalink){const e=new Error("live_verification_failed");e.afterPublishBoundary=true;throw e}return v}
async function readJob(env,id){const r=await env.DB.prepare("SELECT * FROM jobs WHERE id=?").bind(id).first();if(!r)return null;return {...r,media:JSON.parse(r.media_json),authorization:JSON.parse(r.authorization_json)}}
async function claim(env,id,t){const lease=t+180;const q=await env.DB.prepare("UPDATE jobs SET status='publishing',lease_until=?,attempt_count=attempt_count+1,updated_at=? WHERE id=? AND status IN ('scheduled','retry') AND scheduled_at<=? AND COALESCE(next_attempt_at,scheduled_at)<=?").bind(lease,t,id,t,t).run();return (q.meta?.changes||0)===1}

async function handleOne(env,id){
  const t=now();
  if(!await claim(env,id,t))return;
  let j=await readJob(env,id);
  await event(env,id,"lease_acquired",{attempt:j.attempt_count});
  const expected=await hmac(env.SCHEDULE_HMAC_KEY,canonicalJob(j));
  if(!secureEq(expected,j.job_auth)){
    await env.DB.prepare("UPDATE jobs SET status='dead_letter',last_error_class='authorization',last_error='job_auth_mismatch',updated_at=? WHERE id=?").bind(now(),id).run();
    await event(env,id,"dead_letter",{reason:"job_auth_mismatch"});
    return;
  }
  let fingerprint=null;
  try{
    fingerprint=await publishFingerprint({
      igUserId:env.IG_USER_ID,
      mediaSha256s:j.media.map((m)=>m.sha256),
      caption:j.caption,
    });
    const fpCheck=await checkRecentFingerprint(env.DB,fingerprint,t);
    if(!fpCheck.ok){
      await env.DB.prepare("UPDATE jobs SET status='dead_letter',last_error_class='duplicate_publish',last_error=?,lease_until=NULL,updated_at=? WHERE id=?")
        .bind(fpCheck.status,now(),id).run();
      await event(env,id,"publish_fingerprint_blocked",{
        fingerprint,
        status:fpCheck.status,
        last_recorded_at:fpCheck.last_recorded_at??null,
      });
      return;
    }
    const live=await publishJob(env,j);
    const recordedAt=now();
    try{
      await recordFingerprint(env.DB,{
        fingerprint,
        jobId:id,
        recordedAt,
        outcome:"published_verified",
      });
      await event(env,id,"publish_fingerprint_recorded",{fingerprint,outcome:"published_verified",recorded_at:recordedAt});
      await env.DB.prepare("UPDATE jobs SET status='published_verified',meta_media_id=?,permalink=?,published_at=?,lease_until=NULL,updated_at=? WHERE id=?")
        .bind(live.id,live.permalink,recordedAt,recordedAt,id).run();
      await event(env,id,"published_verified",{media_id:live.id,permalink:live.permalink});
    }catch(e){
      e.afterPublishBoundary=true;
      throw e;
    }
  }catch(e){
    let msg=String(e?.message||e).slice(0,500);
    if(e?.afterPublishBoundary===true){
      if(fingerprint){
        try{
          const recordedAt=now();
          await recordFingerprint(env.DB,{
            fingerprint,
            jobId:id,
            recordedAt,
            outcome:"reconcile_required",
          });
          await event(env,id,"publish_fingerprint_recorded",{fingerprint,outcome:"reconcile_required",recorded_at:recordedAt});
        }catch(recordErr){
          msg=(msg+"; fingerprint_record_error="+String(recordErr?.message||recordErr)).slice(0,500);
        }
      }
      await env.DB.prepare("UPDATE jobs SET status='reconcile_required',last_error_class='ambiguous_after_publish_boundary',last_error=?,lease_until=NULL,updated_at=? WHERE id=?")
        .bind(msg,now(),id).run();
      await event(env,id,"reconcile_required",{error:msg});
    }else{
      j=await readJob(env,id);
      if(j.attempt_count>=Number(env.MAX_ATTEMPTS||3)){
        await env.DB.prepare("UPDATE jobs SET status='dead_letter',last_error_class='pre_publish',last_error=?,lease_until=NULL,updated_at=? WHERE id=?")
          .bind(msg,now(),id).run();
        await event(env,id,"dead_letter",{error:msg});
      }else{
        const retry=now()+Math.min(900,60*Math.pow(3,j.attempt_count-1));
        await env.DB.prepare("UPDATE jobs SET status='retry',next_attempt_at=?,last_error_class='pre_publish',last_error=?,lease_until=NULL,updated_at=? WHERE id=?")
          .bind(retry,msg,now(),id).run();
        await event(env,id,"retry_scheduled",{retry_at:retry,error:msg});
      }
    }
  }
}

async function runDue(env){const t=now();const q=await env.DB.prepare("SELECT id FROM jobs WHERE status IN ('scheduled','retry') AND scheduled_at<=? AND COALESCE(next_attempt_at,scheduled_at)<=? ORDER BY scheduled_at LIMIT 10").bind(t,t).all();for(const r of q.results||[])await handleOne(env,r.id);return (q.results||[]).length}
async function metaHealth(env){const d=await graph(env,env.IG_USER_ID,{fields:"id,username"},"GET");return {ok:true,id:d.id,username:d.username}}
async function createJob(req,env){const b=await req.json();const ts=validateJob(b);const id=b.id||crypto.randomUUID();const exists=await readJob(env,id);if(exists)return json({ok:false,error:"job_exists"},409);const origin=new URL(req.url).origin;const j={id,content_id:b.content_id,package_sha256:b.package_sha256,kind:b.kind,scheduled_at:ts,caption:b.caption,media:b.media.map(x=>({key:x.key,url:origin+"/media/"+x.key,sha256:x.sha256})),authorization:b.authorization};const auth=await hmac(env.SCHEDULE_HMAC_KEY,canonicalJob(j));const t=now();await env.DB.prepare("INSERT INTO jobs(id,content_id,package_sha256,kind,scheduled_at,status,caption,media_json,authorization_json,job_auth,created_at,updated_at) VALUES(?,?,?,?,?,'scheduled',?,?,?,?,?,?)").bind(id,j.content_id,j.package_sha256,j.kind,j.scheduled_at,j.caption,JSON.stringify(j.media),JSON.stringify(j.authorization),auth,t,t).run();await event(env,id,"scheduled",{scheduled_at:ts,authorization:j.authorization});return json({ok:true,id,status:"scheduled",scheduled_at:ts},201)}
async function cancelJob(env,id){const q=await env.DB.prepare("UPDATE jobs SET status='cancelled',updated_at=? WHERE id=? AND status IN ('scheduled','retry')").bind(now(),id).run();if(!(q.meta?.changes||0))return json({ok:false,error:"not_cancellable"},409);await event(env,id,"cancelled",{});return json({ok:true,id,status:"cancelled"})}
async function uploadMedia(req,env,key){if(!/^[A-Za-z0-9._-]{3,180}$/.test(key))return json({ok:false,error:"invalid_media_key"},400);const u=new URL(req.url), expected=(u.searchParams.get("sha256")||"").toLowerCase(), ct=(req.headers.get("content-type")||"application/octet-stream").split(";")[0].trim().toLowerCase();if(!/^[0-9a-f]{64}$/.test(expected))return json({ok:false,error:"sha256_required"},400);if(!["image/jpeg","image/png","video/mp4"].includes(ct))return json({ok:false,error:"unsupported_content_type"},400);const b=await req.arrayBuffer();if(!b.byteLength||b.byteLength>25*1024*1024)return json({ok:false,error:"invalid_media_size"},400);const actual=await sha256(b);if(actual!==expected)return json({ok:false,error:"sha256_mismatch",actual},400);await env.MEDIA.put(key,b,{metadata:{sha256:actual,content_type:ct,bytes:b.byteLength,created_at:now()}});return json({ok:true,key,sha256:actual,bytes:b.byteLength,url:new URL("/media/"+key,req.url).toString()})}
async function serveMedia(req,env,key){if(!/^[A-Za-z0-9._-]{3,180}$/.test(key))return new Response("not found",{status:404});const got=await env.MEDIA.getWithMetadata(key,{type:"arrayBuffer",cacheTtl:60});if(!got.value)return new Response("not found",{status:404});return new Response(req.method==="HEAD"?null:got.value,{status:200,headers:{"content-type":got.metadata?.content_type||"application/octet-stream","content-length":String(got.metadata?.bytes||got.value.byteLength),"etag":'"'+(got.metadata?.sha256||"")+'"',"cache-control":"public, max-age=3600, immutable","x-content-type-options":"nosniff"}})}
async function route(req,env){const u=new URL(req.url);const pub=u.pathname.match(/^\/media\/([A-Za-z0-9._-]{3,180})$/);if(pub&&["GET","HEAD"].includes(req.method))return serveMedia(req,env,pub[1]);if(u.pathname==="/healthz")return json({ok:true,service:"velvetos-instagram-publisher",scheduler:"cloudflare-cron",storage:"d1+kv",publication:"instagram-graph",account:env.ACCOUNT_LABEL||"velvets_cloud"});if(!await requireAdmin(req,env))return json({ok:false,error:"unauthorized"},401);const up=u.pathname.match(/^\/v1\/media\/([A-Za-z0-9._-]{3,180})$/);if(up&&req.method==="PUT")return uploadMedia(req,env,up[1]);if(req.method==="GET"&&u.pathname==="/v1/meta-health")try{return json(await metaHealth(env))}catch(e){return json({ok:false,error:String(e?.message||e)},502)}if(req.method==="POST"&&u.pathname==="/v1/jobs")try{return await createJob(req,env)}catch(e){return json({ok:false,error:String(e?.message||e)},400)}if(req.method==="POST"&&u.pathname==="/v1/run")return json({ok:true,processed:await runDue(env)});const m=u.pathname.match(/^\/v1\/jobs\/([^/]+)(\/cancel)?$/);if(m&&req.method==="POST"&&m[2])return cancelJob(env,m[1]);if(m&&req.method==="GET"){const j=await readJob(env,m[1]);if(!j)return json({ok:false,error:"not_found"},404);delete j.job_auth;return json({ok:true,job:j})}if(req.method==="GET"&&u.pathname==="/v1/jobs"){const q=await env.DB.prepare("SELECT id,content_id,kind,scheduled_at,status,attempt_count,last_error_class,meta_media_id,permalink FROM jobs ORDER BY scheduled_at DESC LIMIT 100").all();return json({ok:true,jobs:q.results||[]})}return json({ok:false,error:"not_found"},404)}
export default {fetch:route,async scheduled(_event,env,ctx){ctx.waitUntil(runDue(env))}};
