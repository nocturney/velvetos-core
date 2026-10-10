#!/usr/bin/env python3
"""Single temporary Mac mTLS read-only provider-observed fixture server.

Fixtures are written only by a separately invoked Mac provider state probe.
No Git effect, no etcd mutation or network activity in offline selftest.
"""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import ssl
import sys

SLUG="p0-epoch604-etcd-github-cutover-20261010"
ROOT=next((p for p in Path(__file__).resolve().parents if p.name==SLUG),None)
PORT=32781
PHASES=("seed","unsafe_expired","cutover","stale_denied","fresh_new","cleanup")
REF="refs/heads/office-v2-lab-604-epoch-cutover-20261010"
BASE="04ba7ae09d8c4197fd02afe496e15aad755af3cb"
PROVIDER_CONDITIONS=dict(
 seed=("old","LIVE_OLD_LEASE_ACTIVE","accepted"),
 unsafe_expired=("old","EXPIRED_OWNER_NO_AUTHORITATIVE_PROVIDER_LEASE","accepted"),
 cutover=("new","PENDING_NEW_OWNER_NOT_YET_ADMITTED","accepted"),
 stale_denied=("old","STALE_OWNER_AFTER_NEW_EPOCH_ACTIVE","rejected_stale"),
 fresh_new=("new","ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF","accepted"),
 cleanup=("new","ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF","accepted"),
)
CLIENT_CN="vf604-epoch-win-sink"

class Refuse(Exception):pass
def need(x,m):
 if not x:raise Refuse(m)

def verify_fixture(name,v):
 need(name in PHASES and type(v) is dict and
      set(v)=={"schema","repo","ref","base_sha","phase",
               "expected_sha","generation","owner_actor",
               "provider_condition","provider_observed_revision",
               "expected_result","production_authority"},
      "FIXTURE_EXACT_SCHEMA_REQUIRED")
 need(v["schema"]=="vf604.epoch-github-mtls-fixture.v1"
      and v["repo"]=="nocturney/velvetos-core"
      and v["ref"]==REF and v["base_sha"]==BASE
      and v["phase"]==name and v["production_authority"] is False,
      "UNEXPECTED_TARGET_AUTHORITY")
 need(type(v["generation"]) is int and 0<v["generation"]<10**11
      and type(v["provider_observed_revision"]) is int
      and v["provider_observed_revision"]>=v["generation"],
      "PROVIDER_GENERATION_OR_REVISION_MISSING")
 need((v["owner_actor"],v["provider_condition"],v["expected_result"])
      ==PROVIDER_CONDITIONS[name],"INCORRECT_PROVIDER_STATE_OR_TEST_PURPOSE")
 old=v["expected_sha"]
 need(type(old) is str and
      (old=="" if name=="seed" else bool(re.fullmatch("[0-9a-f]{40}",old))),
      "EXPECTED_EXACT_REMOTE_SHA_REQUIRED")
 return v

class App(BaseHTTPRequestHandler):
 server_version="VF604-epoch-provider-fixture/1"
 sys_version=""
 def log_message(self,*_):return
 def do_GET(self):
  try:
   need(self.path.startswith("/v1/fixture/"),"NO_OTHER_ENDPOINT")
   phase=self.path.removeprefix("/v1/fixture/")
   need(phase in PHASES,"UNREGISTERED_PHASE")
   peer=self.connection.getpeercert()
   sub=dict((k,v) for group in peer.get("subject",())
            for k,v in group)
   need(sub.get("commonName")==CLIENT_CN,"WINDOWS_CLIENT_CERT_REQUIRED")
   file=ROOT/"runtime/fixtures"/(phase+".json")
   need(file.is_file() and not file.is_symlink() and
        file.stat().st_size<2300,"FIXTURE_NOT_ISSUED")
   obj=verify_fixture(phase,json.loads(file.read_text()))
   raw=json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
   self.send_response(200)
  except (Refuse,TypeError,ValueError,OSError):
   raw=b'{"status":"FAIL_CLOSED","reason":"MISSING_OR_UNTRUSTED_MAC_FIXTURE"}'
   self.send_response(409)
  self.send_header("Content-Type","application/json")
  self.send_header("Content-Length",str(len(raw)))
  self.end_headers()
  self.wfile.write(raw)

def serve():
 need(ROOT is not None and ROOT.name==SLUG,"INCORRECT_ISOLATED_ROOT")
 pid=ROOT/"runtime/mac-fixture.pid"
 need(not pid.exists(),"EXISTING_FIXTURE_PROCESS_UNVERIFIED")
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
 ctx.minimum_version=ssl.TLSVersion.TLSv1_2
 ctx.load_cert_chain(str(ROOT/"private/fixture.crt"),
                     str(ROOT/"private/fixture.key"))
 ctx.load_verify_locations(cafile=str(ROOT/"private/ca.crt"))
 ctx.verify_mode=ssl.CERT_REQUIRED
 server=ThreadingHTTPServer(("192.168.0.217",PORT),App)
 server.socket=ctx.wrap_socket(server.socket,server_side=True)
 try:
  with pid.open("x") as f:f.write(str(os.getpid()))
  print(json.dumps({"status":"LIVE_EPHEMERAL_MAC_EPOCH_FIXTURE_ONLY",
                    "pid":os.getpid(),"port":PORT,
                    "git_remote_effect_writes":0,
                    "provider_source_of_truth":"ETCD_ONLY"}),flush=True)
  server.serve_forever(poll_interval=0.12)
 finally:server.server_close()

def selftest():
 n=0
 for phase,(actor,condition,result) in PROVIDER_CONDITIONS.items():
  obj={"schema":"vf604.epoch-github-mtls-fixture.v1",
       "repo":"nocturney/velvetos-core","ref":REF,
       "base_sha":BASE,"phase":phase,
       "expected_sha":"" if phase=="seed" else "1"*40,
       "generation":12,"owner_actor":actor,
       "provider_condition":condition,
       "provider_observed_revision":20,
       "expected_result":result,
       "production_authority":False}
  verify_fixture(phase,obj);n+=1
  for key,wrong in (("repo","other/repo"),
                    ("ref","refs/heads/main"),
                    ("base_sha","0"*40),
                    ("owner_actor","other"),
                    ("expected_result","production"),
                    ("provider_condition","ACTIVE"),
                    ("generation",0),
                    ("provider_observed_revision",1),
                    ("production_authority",True),
                    ("phase","../seed")):
   bad=dict(obj);bad[key]=wrong
   try:verify_fixture(phase,bad)
   except Refuse:n+=1
   else:raise AssertionError("UNSAFE_MAC_FIXTURE_"+phase+key)
 need(n==66,"NEGATIVE_QA_TEST_COUNT_CHANGED")
 return {"status":"PASS_OFFLINE","cases":n,
         "real_provider_requests":0,"http_listeners":0,
         "git_remote_writes":0,"production_authority":False}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("mode",choices=("selftest","serve"))
 a=p.parse_args()
 print(json.dumps(selftest(),sort_keys=True)) if a.mode=="selftest" else serve()

if __name__=="__main__":
 try:main()
 except (Refuse,OSError) as e:
  print(json.dumps({"status":"FAIL_CLOSED","reason":str(e)[:120]}))
  sys.exit(3)
