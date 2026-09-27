#!/usr/bin/env python3
"""Run a local Healthchecks heartbeat/missed-heartbeat pilot using SQLite."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import timedelta as td
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "healthchecks" / "source"
VENDOR = ROOT / "tools" / "healthchecks" / "python"
DATA = ROOT / "tools" / "healthchecks" / "data"
RECEIPT = ROOT / "packages" / "vfharness" / "state" / "healthchecks-pilot-2026-09-27.json"

for entry in (VENDOR, SOURCE):
    sys.path.insert(0, str(entry))

DATA.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hc.settings")
os.environ.setdefault("DB", "sqlite")
os.environ.setdefault("DB_NAME", str(DATA / "hc.sqlite"))
os.environ.setdefault("SECRET_KEY", "velvetos-local-healthchecks-pilot-only")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("SITE_ROOT", "http://localhost")
os.environ.setdefault("DEBUG", "False")

def main() -> int:
    import django
    django.setup()

    from django.contrib.auth.models import User
    from django.core.management import call_command
    from django.test import Client
    from django.utils.timezone import now
    from hc.accounts.models import Project
    from hc.api.models import Check

    call_command("migrate", interactive=False, verbosity=0)

    User.objects.filter(username="velvetos-pilot").delete()
    user = User.objects.create_user(
        username="velvetos-pilot",
        email="velvetos-pilot@localhost.invalid",
        password=None,
    )
    project = Project.objects.create(
        owner=user,
        name="VelvetOS Reliability Pilot",
        api_key="L" * 32,
        badge_key="velvetos-pilot",
    )
    check = Check.objects.create(
        project=project,
        name="office-control-plane-heartbeat-pilot",
        timeout=td(seconds=60),
        grace=td(seconds=30),
    )

    job = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check-office-watchdog.py")],
        cwd=ROOT, text=True, capture_output=True, timeout=90,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    client = Client()
    response = client.get(f"/ping/{check.code}", HTTP_HOST="localhost")
    check.refresh_from_db()
    healthy = (
        job.returncode == 0
        and response.status_code == 200
        and response.content == b"OK"
        and check.status == "up"
        and check.n_pings == 1
        and check.get_status() == "up"
    )

    check.last_ping = now() - td(seconds=120)
    check.status = "up"
    check.save(update_fields=["last_ping", "status"])
    missed_status = check.get_status()
    missed_detected = missed_status == "down"

    receipt = {
        "schema": 1,
        "component": "healthchecks",
        "version": "v4.4",
        "commit": "49924faadf0f24a846abc3acf3014b396fdc1f29",
        "state": "PILOT",
        "deployment": "LOCAL_WINDOWS_SQLITE",
        "authority_role": "HEARTBEAT_SENSOR_ONLY",
        "scheduler_authority": False,
        "hosted_service_used": False,
        "paid_notifications_enabled": False,
        "database": "SQLite",
        "pilot_job": "scripts/check-office-watchdog.py",
        "pilot_job_execution": "PASS" if job.returncode == 0 else "FAIL",
        "healthy_ping": "PASS" if healthy else "FAIL",
        "missed_heartbeat_status": missed_status,
        "missed_heartbeat_detection": "PASS" if missed_detected else "FAIL",
        "production_job_wiring": "NOT_ENABLED_PILOT_ONLY",
        "incremental_recurring_cost_ils": 0,
    }
    RECEIPT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not healthy or not missed_detected:
        print("FAIL healthchecks pilot", file=sys.stderr)
        return 2
    print("OK healthchecks v4.4 local SQLite ping=PASS missed-heartbeat=PASS cost=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
