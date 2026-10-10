#!/usr/bin/env python3
"""Office 2.0 P0 offline local-first fallback admission policy.

LAB-ONLY DECISION SUPPORT: does not call models, Cursor, Perplexity, APIs,
external processes, Git, devices, networks, schedulers, production services.
Existing #612 owns quality/agent execution; Phase 3C provider-failure contract
and #604 fleet placement remain untouched.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

SCHEMA = "velvetos.office-v2.p0-local-first-fallback-evaluation.v0"
AUTHORITY = "LAB_LOCAL_NO_EXTERNAL_EFFECT"
CODE = "CODE"
RESEARCH = "RESEARCH"
LOCAL_PASS = "LOCAL_VERIFIED_PASS"
LOCAL_HARNESS_FAILED = "LOCAL_HARNESS_FAILED"
LOCAL_QA_FAILED = "LOCAL_QA_FAILED"
LOCAL_PROVIDER_RETRYABLE = "LOCAL_PROVIDER_RETRYABLE_FAILURE"
LOCAL_RESEARCH_GAP = "LOCAL_RESEARCH_SOURCE_GAP"
LOCAL_UNKNOWN = "UNKNOWN_OUTCOME"
LOCAL_DENIED = "POLICY_DENY"
STATUSES = {LOCAL_PASS, LOCAL_HARNESS_FAILED, LOCAL_QA_FAILED,
            LOCAL_PROVIDER_RETRYABLE, LOCAL_RESEARCH_GAP,
            LOCAL_UNKNOWN, LOCAL_DENIED}

def verdict(status, route, reason, **extras):
    return {
        "schema": "velvetos.office-v2.p0-local-first-fallback-decision.v0",
        "status": status,
        "route": route,
        "reason": reason,
        "executable_by_this_script": False,
        "automatic_dispatch_authorized": False,
        "external_effect_authority_changed": False,
        "requires_independent_qa": True,
        "source_provenance_required_for_research": True,
        **extras,
    }

def evaluate(payload):
    """One deterministic offline decision, NEVER an automatic provider call."""
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return verdict("DENIED", "NONE", "SCHEMA_INVALID")
    if payload.get("authority") != AUTHORITY or payload.get("scope") != "DISPOSABLE_FIXTURE":
        return verdict("DENIED", "NONE", "LAB_ONLY_SCOPE_REQUIRED")
    if payload.get("task_kind") not in {CODE, RESEARCH}:
        return verdict("DENIED", "NONE", "UNKNOWN_TASK_KIND")
    if payload.get("policy") == "DENY":
        return verdict("DENIED", "NONE", "POLICY_DENY_NEVER_ESCALATE")
    if payload.get("policy") != "ALLOW":
        return verdict("BLOCKED", "NONE", "POLICY_UNVERIFIED")
    if payload.get("external_effects") or payload.get("other_writer_active"):
        return verdict("BLOCKED", "NONE", "UNRECONCILED_EFFECT_OR_WRITER")
    local = payload.get("local") or {}
    status = local.get("outcome")
    if status not in STATUSES:
        return verdict("BLOCKED", "NONE", "LOCAL_OUTCOME_UNVERIFIED")
    if status == LOCAL_DENIED:
        return verdict("DENIED", "NONE", "LOCAL_POLICY_DENIED")
    if status == LOCAL_UNKNOWN:
        return verdict("BLOCKED", "RECONCILE", "UNKNOWN_OUTCOME_NO_BLIND_RETRY")
    if status == LOCAL_PASS:
        if local.get("independent_qa") == "PASS":
            return verdict("PASS", "KEEP_LOCAL", "LOCAL_QUALITY_VERIFIED")
        return verdict("BLOCKED", "NONE", "LOCAL_SUCCESS_NOT_INDEPENDENTLY_VERIFIED")
    # A failure is only actionable when independently established or a
    # transport/provider transient is conclusively classified (no UNKNOWN).
    if local.get("independent_qa") not in {"PASS", "VERIFIED_FAILURE"}:
        return verdict("BLOCKED", "NONE", "FAILURE_NOT_INDEPENDENTLY_VERIFIED")
    if status == LOCAL_HARNESS_FAILED and not local.get("local_aider_tried"):
        return verdict("MANUAL_LAB_ONLY", "LOCAL_AIDER_FIRST",
                       "LOCAL_MODEL_MAY_WORK_WITH_ALTERNATE_TOOL_HARNESS")
    if payload["task_kind"] == CODE and status == LOCAL_RESEARCH_GAP:
        return verdict("DENIED", "NONE", "INVALID_CODE_FAILURE_CLASSIFICATION")
    if payload["task_kind"] == RESEARCH and status != LOCAL_RESEARCH_GAP:
        return verdict("BLOCKED", "NONE", "RESEARCH_FALLBACK_NEEDS_VERIFIED_SOURCE_GAP")
    if payload["task_kind"] == CODE and status == LOCAL_QA_FAILED:
        if not local.get("tests_fail") or local.get("local_aider_tried") is not True:
            return verdict("BLOCKED", "NONE", "QA_OR_LOCAL_ALTERNATIVE_GATE_MISSING")
    if not payload.get("manual_pilot_authorized"):
        return verdict("BLOCKED", "NONE", "MANUAL_PILOT_AUTHORIZATION_REQUIRED")
    billing = payload.get("billing") or {}
    if billing.get("mode") != "EXISTING_SUBSCRIPTION" or billing.get("new_paid_api") is not False:
        return verdict("BLOCKED", "NONE", "BILLING_REVIEW_REQUIRED")
    if billing.get("quota") == "EXHAUSTED":
        return verdict("BLOCKED", "NONE", "SUBSCRIPTION_QUOTA_EXHAUSTED")
    if billing.get("quota") not in {"AVAILABLE", "UNKNOWN"}:
        return verdict("BLOCKED", "NONE", "SUBSCRIPTION_QUOTA_UNVERIFIED")
    provider = payload.get("provider") or {}
    if payload["task_kind"] == CODE:
        if provider.get("cursor_signed_in") is not True:
            return verdict("BLOCKED", "NONE", "CURSOR_LOGIN_UNVERIFIED")
        if provider.get("cursor_model") != "composer-2.5":
            return verdict("BLOCKED", "NONE", "CURSOR_MODEL_OUTSIDE_TESTED_LANE")
        if provider.get("codex_cli") is not False:
            return verdict("DENIED", "NONE", "CODEX_CLI_NOT_AUTHORIZED")
        target = "CURSOR_CLI_CODING_LAB"
        reason = "LOCAL_FAILURE_VERIFIED_AND_CURSOR_LAB_AVAILABLE"
    else:
        if provider.get("perplexity_gui_signed_in") is not True:
            return verdict("BLOCKED", "NONE", "PERPLEXITY_LOGIN_UNVERIFIED")
        if provider.get("perplexity_search_on") is not True or provider.get("perplexity_computer_off") is not True:
            return verdict("DENIED", "NONE", "PERPLEXITY_SEARCH_ONLY_NO_COMPUTER")
        target = "PERPLEXITY_GUI_RESEARCH_LAB"
        reason = "LOCAL_FRESH_SOURCE_GAP_VERIFIED_AND_GUI_LAB_AVAILABLE"
    return verdict(
        "MANUAL_LAB_ONLY", target, reason,
        subscription_quota_confirmed=billing["quota"] == "AVAILABLE",
        subscription_usage_must_be_measured=True,
        no_auto_retry_on_unknown=True,
        independent_final_answer_or_diff_verification_required=True,
    )

def fixture(kind=CODE, outcome=LOCAL_QA_FAILED):
    return {
        "schema":SCHEMA,
        "authority":AUTHORITY,
        "scope":"DISPOSABLE_FIXTURE",
        "task_kind":kind,
        "policy":"ALLOW",
        "external_effects":[],
        "other_writer_active":False,
        "manual_pilot_authorized":True,
        "local":{"outcome":outcome,"independent_qa":"VERIFIED_FAILURE",
                 "local_aider_tried":True,"tests_fail":True},
        "billing":{"mode":"EXISTING_SUBSCRIPTION","new_paid_api":False,
                   "quota":"UNKNOWN"},
        "provider":{"cursor_signed_in":True,"cursor_model":"composer-2.5",
                    "codex_cli":False,
                    "perplexity_gui_signed_in":True,
                    "perplexity_search_on":True,"perplexity_computer_off":True},
    }

def selftest():
    cases=[]
    def check(name,p,route,status=None):
        result=evaluate(p)
        assert result["route"]==route, (name,result)
        if status:
            assert result["status"]==status, (name,result)
        assert result["executable_by_this_script"] is False
        assert result["automatic_dispatch_authorized"] is False
        assert result["external_effect_authority_changed"] is False
        cases.append(name)
    p=fixture()
    check("code_failure_cursor_manual",p,"CURSOR_CLI_CODING_LAB","MANUAL_LAB_ONLY")
    r=fixture(kind=RESEARCH,outcome=LOCAL_RESEARCH_GAP)
    check("research_source_gap_perplexity_manual",r,"PERPLEXITY_GUI_RESEARCH_LAB","MANUAL_LAB_ONLY")
    x=fixture();x["local"]={"outcome":LOCAL_PASS,"independent_qa":"PASS"}
    check("local_success_kept",x,"KEEP_LOCAL","PASS")
    x=fixture();x["local"]["outcome"]=LOCAL_HARNESS_FAILED;x["local"]["local_aider_tried"]=False
    check("try_local_aider_first",x,"LOCAL_AIDER_FIRST")
    x=fixture();x["local"]["outcome"]=LOCAL_UNKNOWN
    check("unknown_no_retry",x,"RECONCILE","BLOCKED")
    x=fixture();x["policy"]="DENY"
    check("policy_deny_never_fallback",x,"NONE","DENIED")
    x=fixture();x["external_effects"]=["unknown_upload"]
    check("unknown_external_effects_blocked",x,"NONE","BLOCKED")
    x=fixture();x["other_writer_active"]=True
    check("parallel_writer_blocked",x,"NONE","BLOCKED")
    x=fixture();x["authority"]="PRODUCTION"
    check("production_denied",x,"NONE","DENIED")
    x=fixture();x["manual_pilot_authorized"]=False
    check("explicit_pilot_auth_required",x,"NONE","BLOCKED")
    x=fixture();x["billing"]["new_paid_api"]=True
    check("paid_api_denied",x,"NONE","BLOCKED")
    x=fixture();x["billing"]["quota"]="EXHAUSTED"
    check("quota_exhausted",x,"NONE","BLOCKED")
    x=fixture();x["provider"]["codex_cli"]=True
    check("codex_cli_denied",x,"NONE","DENIED")
    x=fixture();x["provider"]["cursor_signed_in"]=False
    check("cursor_unavailable",x,"NONE","BLOCKED")
    x=fixture();x["provider"]["cursor_model"]="gpt-5.3-codex"
    check("model_allowlist",x,"NONE","BLOCKED")
    x=fixture();x["local"]["tests_fail"]=False
    check("unverified_failure",x,"NONE","BLOCKED")
    x=fixture(kind=RESEARCH,outcome=LOCAL_RESEARCH_GAP);x["provider"]["perplexity_computer_off"]=False
    check("computer_mode_denied",x,"NONE","DENIED")
    x=fixture(kind=RESEARCH,outcome=LOCAL_RESEARCH_GAP);x["provider"]["perplexity_gui_signed_in"]=False
    check("research_login_unverified",x,"NONE","BLOCKED")
    x=fixture(kind=RESEARCH,outcome=LOCAL_QA_FAILED)
    check("research_without_source_gap_rejected",x,"NONE","BLOCKED")
    x=fixture();x["schema"]="INVALID"
    check("malformed_envelope_denied",x,"NONE","DENIED")
    x=fixture();x["local"]["independent_qa"]="UNKNOWN"
    check("failure_without_independent_qa",x,"NONE","BLOCKED")
    x=fixture();x["billing"]["quota"]="AVAILABLE"
    check("quota_available_still_manual",x,"CURSOR_CLI_CODING_LAB","MANUAL_LAB_ONLY")
    return {"status":"PASS","cases":len(cases),
            "proof":"DETERMINISTIC_OFFLINE_POLICY_ONLY",
            "scenarios":cases,
            "model_invocations":0,
            "production_mutations":0,
            "automatic_fallback_enabled":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("selftest")
    task=sub.add_parser("evaluate")
    task.add_argument("--request",required=True)
    args=parser.parse_args()
    if args.command=="selftest":
        print(json.dumps(selftest(),ensure_ascii=False,sort_keys=True,indent=2))
        return 0
    path=Path(args.request)
    payload=json.loads(path.read_text(encoding="utf8"))
    print(json.dumps(evaluate(payload),ensure_ascii=False,sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
