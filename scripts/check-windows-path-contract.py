#!/usr/bin/env python3
"""Validate the Windows D: path contract without touching host state."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "packages" / "velvetos" / "WINDOWS-PATH-CONTRACT.md"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL {message}")


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def require(blob: str, needle: str, label: str) -> None:
    if needle not in blob:
        fail(f"{label} missing {needle}")


contract = CONTRACT.read_text(encoding="utf-8")
for needle in (
    r"VELVET_ROOT=D:\Velvet",
    r"VELVETOS_REPO_ROOT=D:\Velvet\Repos\velvetos-core",
    r"VELVETOS_RUNTIME_ROOT=D:\Velvet\Runtime\VelvetOS",
    r"VELVETOS_STATE_ROOT=D:\Velvet\State\VelvetOS",
):
    require(contract, needle, "path contract")

for rel, needles in {
    "scripts/bootstrap-edge-host-windows.ps1": (
        "VELVETOS_REPO_ROOT", "VELVETOS_RUNTIME_ROOT", "VELVETOS_STATE_ROOT", "$LegacyRoot"
    ),
    "scripts/bootstrap-speech-host-windows.ps1": (
        "VELVETOS_REPO_ROOT", "VELVETOS_STATE_ROOT", "$LegacyRoot"
    ),
    "scripts/bootstrap-manim-host-windows.ps1": (
        "VELVETOS_RUNTIME_ROOT", "VELVETOS_STATE_ROOT", "$LegacyRoot"
    ),
    "packages/vfmem/scripts/vf_cognee_runtime.py": ("VELVETOS_RUNTIME_ROOT",),
    "packages/vfmem/scripts/vf_cognee.py": ("VELVETOS_RUNTIME_ROOT",),
    "scripts/vfmem.py": ("VELVETOS_RUNTIME_ROOT",),
}.items():
    blob = read(rel)
    for needle in needles:
        require(blob, needle, rel)
    if r"C:\Users\Chris" in blob:
        fail(f"Chris-specific absolute path in {rel}")

hosts = json.loads(read("packages/vfmcp/RENDER-HOSTS.json"))
windows = hosts["hosts"]["sderot-windows"]
if windows.get("repoPath") != r"%VELVETOS_REPO_ROOT%":
    fail("Windows repoPath must use VELVETOS_REPO_ROOT")
if windows.get("localState") != r"%VELVETOS_STATE_ROOT%\edge-host.json":
    fail("Windows edge state must use VELVETOS_STATE_ROOT")
if windows.get("speechLocalState") != r"%VELVETOS_STATE_ROOT%\speech-host.json":
    fail("Windows speech state must use VELVETOS_STATE_ROOT")

video = json.loads(read("packages/vfom/VIDEO-TOOLCHAIN.json"))
manim = video["animationSlots"]["manim"]["hostEvidence"]
if manim.get("toolchain") != r"%VELVETOS_RUNTIME_ROOT%\Toolchains\manim-0.21.0-py312":
    fail("Manim host evidence must use VELVETOS_RUNTIME_ROOT")

grok = json.loads(read("automation/grok/cognee-routines.json"))
prompts = "\n".join(str(row.get("prompt") or "") for row in grok.get("routines", []))
for needle in (
    r"%VELVETOS_RUNTIME_ROOT%\Cognee\cognee-core",
    r"%VELVETOS_RUNTIME_ROOT%\Cognee\cognee-venv",
    r"%VELVETOS_RUNTIME_ROOT%\Cognee\cognee\active-state.json",
):
    require(prompts, needle, "Grok Cognee path contract")
if r"C:\Users\Chris" in prompts:
    fail("Grok Cognee prompts still contain Chris-specific absolute paths")

fallback = read("packages/vfmcp/WINDOWS-EDGE-FALLBACK.md")
require(fallback, "WINDOWS-PATH-CONTRACT.md", "Windows fallback playbook")
require(fallback, r"%VELVETOS_STATE_ROOT%\edge-host.json", "Windows fallback playbook")

print("OK windows-path-contract vars=4 legacy-fallback=yes chris-absolute=0")
