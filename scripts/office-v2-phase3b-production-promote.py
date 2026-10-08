#!/usr/bin/env python3
"""Explicit, evidence-backed, read-only Phase 3B Production Reader promotion on owner Windows."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE = Path(r"D:\Velvet\State\OfficeV2\project-state")
EVIDENCE = Path(r"D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07")
NEW_EVIDENCE = Path(r"D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-08")
RUNTIME = Path(r"D:\Velvet\OfficeV2Lab\artifacts\phase3b-security\shadow-runtime")
RUNTIME_RESOLVER = Path(r"D:\Velvet\Runtime\OfficeV2Lab\Resolve-Phase3B-ProductionSnapshot.ps1")
POINTER = STATE / "CURRENT.json"
CP016 = STATE / "checkpoint-016-v0-phase3b-pilot-active.json"
CP017 = STATE / "checkpoint-017-v0-phase3b-production-read-active.json"
BINDING = EVIDENCE / "production-runtime-binding.json"
PROMOTION = EVIDENCE / "production-promotion.json"
ACTIVATION = NEW_EVIDENCE / "production-read-activation.json"
ROUTER = REPO / "packages" / "vfigos" / "cloudflare_publisher_snapshot.py"
LOCK = STATE / ".phase3b-production-read-activation.lock"
CP16_ID = "office-v2-phase3b-v0-cp016-pilot-active"
CP17_ID = "office-v2-phase3b-v0-cp017-production-read-active"
PHASE17 = "PHASE_3B_PRODUCTION_READ_ACTIVE"
SCOPE = "instagram-publisher-snapshot-read"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def require(ok: bool, detail: str) -> None:
    if not ok:
        raise RuntimeError("PHASE3B_PRODUCTION_GATE: " + detail)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_hash(data: dict) -> str:
    d = dict(data)
    d.pop("content_hash", None)
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    require(not tmp.exists(), "transaction temp path already exists: " + tmp.name)
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def git(*arguments: str) -> str:
    call = subprocess.run(["git", "-C", str(REPO), *arguments], text=True, capture_output=True, timeout=30)
    require(call.returncode == 0, "git verification failed")
    return call.stdout.strip()


def exact_ci(sha: str, run: str) -> None:
    proc = subprocess.run(["gh", "run", "view", run, "--repo", "nocturney/velvetos-core", "--json", "headSha,status,conclusion,event"], text=True, capture_output=True, timeout=35)
    require(proc.returncode == 0, "exact merged-main CI receipt is unreachable")
    result = json.loads(proc.stdout)
    require(result.get("headSha") == sha and result.get("status") == "completed" and result.get("conclusion") == "success" and result.get("event") == "push", "exact-main CI did not pass")


def baseline(main_sha: str, ci_run: str, regression_path: Path) -> dict:
    require(os.name == "nt", "owner Windows machine is required for production cutover")
    who = subprocess.run(["whoami"], text=True, capture_output=True, timeout=10)
    require(who.returncode == 0 and who.stdout.strip().lower() == "chris\\chris", "owner DPAPI identity mismatch")
    require(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha), "merged main SHA invalid")
    require(git("rev-parse", "HEAD") == main_sha and git("rev-parse", "origin/main") == main_sha, "exact checked-out merged main required")
    require(not git("status", "--porcelain=v1"), "merged main working tree is not clean")
    exact_ci(main_sha, ci_run)
    regression = read(regression_path)
    require(regression.get("status") == "PASS" and regression.get("exact_sha") == main_sha and regression.get("sensors_pass") == 118 and regression.get("sensors_failed") == 0, "local exact-main full regression absent")
    current = read(POINTER)
    prior = read(CP016)
    require(current.get("schema") == "velvetos.office-v2.project-state-pointer.v0" and current.get("checkpoint_id") == CP16_ID and current.get("phase") == "PHASE_3B_PILOT_ACTIVE" and current.get("gate") == "GREEN", "Project State is not PILOT cp016 GREEN")
    require(current.get("current_checkpoint_ref", "").replace("\\", "/").casefold() == str(CP016).replace("\\", "/").casefold(), "PILOT checkpoint reference mismatch")
    require(prior.get("checkpoint_id") == CP16_ID and prior.get("migration_phase") == "PHASE_3B_PILOT_ACTIVE" and prior.get("gate_status", {}).get("verdict") == "GREEN", "PILOT checkpoint invalid")
    require(content_hash(prior) == prior.get("content_hash") == current.get("content_hash"), "cp016 self-hash or pointer mismatch")
    require(not CP017.exists() and not PROMOTION.exists(), "existing cp017/promotion must be reconciled, not overwritten")
    require(ROUTER.is_file() and RUNTIME_RESOLVER.is_file(), "canonical reader or installed resolver missing")
    repo_resolver = REPO / "packages" / "vfigos" / "officev2_production_snapshot_resolver.ps1"
    require(digest(repo_resolver) == digest(RUNTIME_RESOLVER), "installed production resolver differs from exact-main source")
    reader_sensor = subprocess.run([sys.executable, str(REPO / "scripts" / "check-office-v2-phase3b-production.py")], text=True, capture_output=True, cwd=REPO, timeout=40)
    require(reader_sensor.returncode == 0 and "reader_route=GATED" in reader_sensor.stdout, "production reader sensor did not pass")
    auth = read(EVIDENCE / "production-authority-transfer-authorization-v1.json")
    binding = read(BINDING)
    rotation = read(EVIDENCE / "production-provider-rotation.json")
    rollback = read(EVIDENCE / "production-rollback-drill.json")
    recovery = read(EVIDENCE / "production-recovery.json")
    bridge = read(EVIDENCE / "production-snapshot-bridge-probe.json")
    live = read(RUNTIME / "production-snapshot-read.json")
    require(auth.get("status") == "AUTHORIZED" and auth.get("scope_id") == SCOPE and auth.get("production_writer_change") is False and auth.get("external_mutation_allowed") is False, "owner production authority receipt invalid")
    require(binding.get("status") == "PASS" and binding.get("scope_id") == SCOPE and binding.get("mode") == "ROTATED_PRODUCTION_CREDENTIAL_READY_FOR_PROMOTION", "active production binding is not rotated")
    require(binding.get("authorization_receipt_sha256") == digest(EVIDENCE / "production-authority-transfer-authorization-v1.json"), "production authorization hash mismatch")
    require(binding.get("production_authority_active") is False and binding.get("production_promoted") is False and binding.get("production_writer_change") is False and binding.get("external_mutation_allowed") is False, "production binding was implicitly promoted")
    active = binding.get("active_credential_reference_sha256")
    require(isinstance(active, str) and len(active) == 64, "active production credential reference missing")
    require(rotation.get("status") == "PASS" and rotation.get("new_credential_reference_sha256") == active and rotation.get("old_credential_reference_sha256") == rollback.get("restored_credential_reference_sha256") and rotation.get("provider", {}).get("stable_full_boundary_checks", 0) >= 2, "new rotation and rollback lineage mismatch")
    require(rotation.get("provider", {}).get("old_after_rotate_http") == 401 and all(rotation.get("provider", {}).get(field) == 200 for field in ("new_runtime_http", "new_meta_health_http", "new_jobs_http")) and rotation.get("provider", {}).get("new_write_run_http") == 401, "provider boundary not proven")
    require(rotation.get("broker", {}).get("credential_reference_sha256") == active and rotation.get("broker", {}).get("generated_root_revoked") is True, "production broker rotation invalid")
    require(rollback.get("status") == "PASS" and rollback.get("production_promoted") is False and rollback.get("broker", {}).get("generated_root_revoked") is True, "rollback drill not PASS")
    require(recovery.get("status") == "PASS" and recovery.get("credential_reference_sha256") == active, "latest production recovery not linked")
    for component in ("opa", "zitadel", "openbao"):
        require(recovery.get(component, {}).get("outage_fail_closed") is True and recovery.get(component, {}).get("recovery") == "PASS", component + " recovery not proven")
    require(recovery.get("openbao", {}).get("unseal_without_persistent_root") is True, "OpenBao retained root key")
    require(bridge.get("status") == "PASS" and bridge.get("credential_reference_sha256") == active and bridge.get("broker_exact_scope_read_http") == 200 and bridge.get("broker_unrelated_scope_http") == 403 and bridge.get("provider_write_run_http") == 401, "secure bridge pre-production probe mismatch")
    require(bridge.get("control_token_read_or_reused") is False and bridge.get("meta_access_token_read_or_reused") is False and bridge.get("external_mutation_performed") is False, "bridge used forbidden credentials or mutation")
    require(live.get("status") == "PASS" and live.get("broker", {}).get("credential_reference_sha256") == active and live.get("provider", {}).get("write_run_http") == 401 and live.get("broker", {}).get("unrelated_scope_http") == 403, "correlated production runtime read not current")
    require(not LOCK.exists(), "another production promotion is already locked")
    return {"previous": prior, "pointer": current, "binding": binding, "credential_sha256": active, "current_pointer_sha256": digest(POINTER)}


def new_checkpoint(old: dict, main_sha: str, gate: str) -> dict:
    doc = copy.deepcopy(old)
    doc["checkpoint_id"] = CP17_ID
    doc["parent_checkpoint_id"] = CP16_ID
    doc["updated_at"] = utc()
    doc["current_goal"] = "Operate the exact named instagram-publisher-snapshot-read through production ZITADEL -> OPA -> OpenBao -> Cloudflare GET. Keep writer, admin credentials and canonical business truth unchanged."
    doc["scope_and_constraints"] = list(old.get("scope_and_constraints") or []) + [
        "Phase 3B Production Read is limited to instagram-publisher-snapshot-read; writer ownership and production mutation authority remain unchanged.",
        "The canonical Morning Green snapshot reader selects Office v2 only for exact cp017 GREEN or ACTIVATING, and must never fall back to CONTROL_TOKEN when Office v2 read fails.",
        "Production ZITADEL identity, OPA DENY-by-default and production OpenBao exact scope are active only for the named read operation.",
    ]
    doc["completed_work"] = list(old.get("completed_work") or []) + [{
        "item": "Phase 3B production reader promotion from cp016: rotated credential, correlated read, rollback and 3/3 recovery, merged-main CI, source routing and read-only activation verified.",
        "evidence_refs": [
            "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-07/production-provider-rotation.json",
            "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-07/production-recovery.json",
            "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-08/production-read-activation.json",
        ],
    }]
    doc["active_tasks"] = [{"task_id": "P3B-PRODUCTION-READ-OPERATIONS", "owner": "Office v2 execution", "status": "ACTIVE_READ_ONLY", "next_action": "Verify live snapshot routing, fail-closed boundaries and rollback on any production degradation. No new writer."}]
    doc["blockers"] = []
    doc["migration_phase"] = PHASE17
    doc["gate_status"] = {
        "phase": "PHASE_3B_PRODUCTION_READ",
        "verdict": gate,
        "reasons": [
            "Owner-authorized scoped production read; no publication writer or mutation authority transfer.",
            "Exact-main CI GREEN and 118/118 local checks PASS.",
            "Persistent ZITADEL service identity, DENY-by-default OPA, isolated production OpenBao and rotated Cloudflare read token.",
            "Read 200, unrelated broker 403, write 401, rollback PASS, OPA/ZITADEL/OpenBao outage-recovery PASS.",
            "Canonical Morning Green reader selects secure Office v2 route; CONTROL_TOKEN fallback prohibited.",
        ],
    }
    doc["rollback_point"] = {
        "available": True,
        "reference": str(CP016).replace("\\", "/"),
        "instructions": "Emergency fail-closed rollback: atomically repoint CURRENT to cp016 and disable production binding authority; preserve evidence, then revoke production AppRole/principal and provider token in a separate controlled cleanup.",
    }
    doc["receipt_refs"] = list(dict.fromkeys(list(old.get("receipt_refs") or []) + [
        "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-07/production-authority-transfer-authorization-v1.json",
        "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-07/production-provider-rotation.json",
        "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-07/production-recovery.json",
        "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-07/production-promotion.json",
        "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-08/production-read-activation.json",
    ]))
    doc["resume_instructions"] = [
        "Validate cp017 self-hash, CURRENT gate GREEN and exact merged-main CI receipt.",
        "Execute canonical Cloudflare snapshot CLI and prove reader_route=OFFICEV2_PRODUCTION_READ; verify correlated read 200/403/401 and current credential reference.",
        "If runtime read fails, never fall back to CONTROL_TOKEN. Record unavailable and explicitly roll back to cp016 with incident evidence if required.",
        "Publication writers, job creation, CONTROL_TOKEN and META_ACCESS_TOKEN remain outside this authority grant.",
    ]
    doc["risks"] = ["Production read unavailability must fail closed, not seek elevated fallback.", "Credential rotation and OpenBao recovery must preserve exact binding references."]
    doc["active_external_effects"] = []
    doc["code_baseline"] = {"repo": "nocturney/velvetos-core", "base_sha": main_sha, "branch": "main", "worktree_path": str(REPO).replace("\\", "/")}
    doc["context"] = {"summary": "Office v2 Phase 3B named production read authority is gated through the secure reader; publication writer authority remains incumbent.", "working_set": ["secure read observation", "rollback readiness"], "recent_observations": ["Production read promotion exact main: " + main_sha], "pressure_basis": "PHASE_BOUNDARY", "compaction_generation": 0}
    doc["verifier"] = {"last_status": ("PASS" if gate == "GREEN" else "PENDING_LIVE_READ"), "verified_at": utc(), "receipt_ref": str(ACTIVATION).replace("\\", "/")}
    doc.pop("content_hash", None)
    doc["content_hash"] = content_hash(doc)
    return doc


def pointer_doc(cp: dict, main_sha: str, gate: str) -> dict:
    return {
        "schema": "velvetos.office-v2.project-state-pointer.v0",
        "current_checkpoint_ref": str(CP017).replace("\\", "/"),
        "checkpoint_id": CP17_ID,
        "content_hash": cp["content_hash"],
        "phase": PHASE17,
        "gate": gate,
        "code_commit": main_sha,
        "updated_at": utc(),
    }


def production_receipt(main_sha: str, ci_run: str, active: str, gate: str, first_probe_sha: str | None = None) -> dict:
    return {
        "schema": "velvetos.office-v2.phase3b-production-promotion-runtime.v0",
        "captured_at": utc(),
        "status": gate,
        "scope_id": SCOPE,
        "credential_class": "PRODUCTION_READ",
        "active_credential_reference_sha256": active,
        "exact_main_sha": main_sha,
        "exact_main_ci_run_id": int(ci_run),
        "selected_composition": "composition-zitadel-opa-openbao",
        "principal": "svc:officev2-p3b-prod-publisher-snapshot",
        "production_authority_change_scope": "named snapshot read only",
        "production_writer_change": False,
        "external_mutation_allowed": False,
        "production_promoted": gate == "PASS",
        "first_secure_read_sha256": first_probe_sha,
        "rollback_checkpoint_id": CP16_ID,
        "raw_secret_recorded": False,
    }


def live_reader(out_path: Path, active: str) -> dict:
    require(not out_path.exists(), "prior live-reader output exists; refusing to overwrite")
    proc = subprocess.run([sys.executable, str(ROUTER), "--output", str(out_path)], cwd=REPO, text=True, capture_output=True, timeout=150)
    require(proc.returncode == 0 and "reader_route=OFFICEV2_PRODUCTION_READ" in proc.stdout, "canonical production reader denied or chose a nonsecure route")
    data = read(out_path)
    require(data.get("schema") == "vf.instagram.schedule-snapshot.v1" and data.get("source") == "cloudflare-instagram-publisher" and isinstance(data.get("scheduled"), list), "live snapshot schema invalid")
    live = read(RUNTIME / "production-snapshot-read.json")
    require(live.get("status") == "PASS" and live.get("broker", {}).get("credential_reference_sha256") == active, "live broker credential mismatch")
    require(live.get("authorization", {}).get("decision") == "ALLOW" and live.get("broker", {}).get("unrelated_scope_http") == 403, "live scoped authorization invalid")
    require(all(live.get("provider", {}).get(x) == 200 for x in ("runtime_http", "meta_health_http", "jobs_http")) and live.get("provider", {}).get("write_run_http") == 401, "live provider read/write boundary invalid")
    require(live.get("control_token_read_or_reused") is False and live.get("meta_access_token_read_or_reused") is False and live.get("external_mutation_performed") is False, "live reader used forbidden credential or mutation")
    return {"snapshot_sha256": digest(out_path), "scheduled_count": len(data["scheduled"]), "runtime_receipt_sha256": digest(RUNTIME / "production-snapshot-read.json"), "reader_route": "OFFICEV2_PRODUCTION_READ"}


def activate(main_sha: str, ci_run: str, regression: Path) -> None:
    proof = baseline(main_sha, ci_run, regression)
    NEW_EVIDENCE.mkdir(parents=True, exist_ok=True)
    original_current = POINTER.read_bytes()
    original_binding = BINDING.read_bytes()
    lock_fd = os.open(LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(lock_fd)
    committed = False
    try:
        require(digest(POINTER) == proof["current_pointer_sha256"], "concurrent project-state change before cutover")
        candidate = new_checkpoint(proof["previous"], main_sha, "ACTIVATING")
        atomic_write(PROMOTION, production_receipt(main_sha, ci_run, proof["credential_sha256"], "READY_FOR_READ_PROBE"))
        atomic_write(CP017, candidate)
        atomic_write(POINTER, pointer_doc(candidate, main_sha, "ACTIVATING"))
        first = live_reader(NEW_EVIDENCE / "production-read-activating-snapshot.json", proof["credential_sha256"])
        promoted = production_receipt(main_sha, ci_run, proof["credential_sha256"], "PASS", first["snapshot_sha256"])
        active_binding = copy.deepcopy(proof["binding"])
        active_binding["captured_at"] = utc()
        active_binding["production_authority_active"] = True
        active_binding["production_promoted"] = True
        active_binding["next_gate"] = "Verify canonical cp017 production snapshot on restart; maintain read-only monitoring and rollback."
        final_cp = new_checkpoint(proof["previous"], main_sha, "GREEN")
        atomic_write(PROMOTION, promoted)
        atomic_write(BINDING, active_binding)
        atomic_write(CP017, final_cp)
        atomic_write(POINTER, pointer_doc(final_cp, main_sha, "GREEN"))
        second = live_reader(NEW_EVIDENCE / "production-read-active-snapshot.json", proof["credential_sha256"])
        require(read(POINTER).get("gate") == "GREEN" and read(CP017).get("content_hash") == content_hash(read(CP017)), "cp017 postactivation readback failed")
        done = {
            "schema": "velvetos.office-v2.phase3b-production-read-activation.v0",
            "captured_at": utc(), "status": "PASS", "scope_id": SCOPE,
            "exact_main_sha": main_sha, "exact_main_ci_run_id": int(ci_run),
            "credential_reference_sha256": proof["credential_sha256"],
            "checkpoint_id": CP17_ID, "phase": PHASE17, "gate": "GREEN",
            "checkpoint_sha256": digest(CP017), "current_pointer_sha256": digest(POINTER),
            "promotion_receipt_sha256": digest(PROMOTION),
            "read_probe": first, "read_active": second,
            "production_writer_change": False, "external_mutation_allowed": False,
            "control_token_fallback_allowed": False, "production_promoted": True,
        }
        atomic_write(ACTIVATION, done)
        committed = True
        print("PASS PHASE3B_PRODUCTION_READ_ACTIVATED exact_sha=" + main_sha + " credential_ref=" + proof["credential_sha256"] + " scheduled=" + str(second["scheduled_count"]))
    except Exception as error:
        # A failed read never falls back to the former admin/control token. Restore only local read authority.
        if not committed:
            POINTER.write_bytes(original_current)
            BINDING.write_bytes(original_binding)
            if PROMOTION.exists():
                PROMOTION.replace(NEW_EVIDENCE / "production-promotion-aborted.json")
            atomic_write(NEW_EVIDENCE / "production-activation-failed.json", {
                "schema": "velvetos.office-v2.phase3b-production-activation-failed.v0",
                "captured_at": utc(), "status": "FAIL_CLOSED",
                "reason_type": type(error).__name__,
                "restored_checkpoint_id": CP16_ID,
                "production_writer_change": False, "external_mutation_allowed": False,
            })
        raise
    finally:
        LOCK.unlink(missing_ok=True)


def verify(active_sha: str) -> None:
    current = read(POINTER)
    cp = read(CP017)
    binding = read(BINDING)
    promotion = read(PROMOTION)
    require(current.get("checkpoint_id") == CP17_ID and current.get("phase") == PHASE17 and current.get("gate") == "GREEN", "cp017 is not active GREEN")
    require(cp.get("content_hash") == content_hash(cp) == current.get("content_hash"), "cp017 content hash mismatch")
    require(promotion.get("status") == "PASS" and promotion.get("production_promoted") is True and promotion.get("active_credential_reference_sha256") == active_sha, "production promotion receipt not current")
    require(binding.get("production_authority_active") is True and binding.get("production_promoted") is True and binding.get("active_credential_reference_sha256") == active_sha, "production binding authority mismatch")
    out = NEW_EVIDENCE / ("production-read-verify-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    data = live_reader(out, active_sha)
    print("PASS PHASE3B_PRODUCTION_READ_VERIFIED sha=" + data["snapshot_sha256"] + " count=" + str(data["scheduled_count"]))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("preflight", "activate", "verify"), required=True)
    p.add_argument("--main-sha", required=True)
    p.add_argument("--ci-run-id", required=True)
    p.add_argument("--regression-receipt", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    if args.mode == "verify":
        binding = read(BINDING)
        verify(str(binding.get("active_credential_reference_sha256") or ""))
        return
    proof = baseline(args.main_sha, args.ci_run_id, args.regression_receipt)
    if args.mode == "preflight":
        print("PASS PHASE3B_PRODUCTION_PREFLIGHT exact_sha=" + args.main_sha + " ci=" + args.ci_run_id + " checkpoint=" + CP16_ID + " writer_change=FALSE mutation=FALSE")
        return
    require(args.apply, "activation requires explicit --apply")
    activate(args.main_sha, args.ci_run_id, args.regression_receipt)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("FAIL_CLOSED " + str(err)[:240], file=sys.stderr)
        sys.exit(2)
