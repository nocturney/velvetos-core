#!/usr/bin/env python3
"""Shared path roots for VelvetOS scripts.

``ROOT`` — repository root (read packs/constitution).
``OFFICE_ROOT`` — mutable office/ledger/control/runtime writes.

Set ``VF_OFFICE_ROOT`` to a temporary tree for non-mutating commissioning.
Never invent a second SoT — sandbox is a disposable copy for tests only.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICE_ROOT = Path(os.environ.get("VF_OFFICE_ROOT") or ROOT)


def office_path(*parts: str) -> Path:
    return OFFICE_ROOT.joinpath(*parts)


def repo_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)
