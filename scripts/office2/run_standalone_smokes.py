#!/usr/bin/env python3
"""Reproduce the 2026-10-19 cloud-VM smokes. check-all does not run this file.

check-all discovers only scripts/check-*.py. This helper stays under
scripts/office2/ on purpose. It installs nothing. It posts nothing.
A non-loopback TCP connect is refused. Pass --execute only when the
venvs from the recorded run already exist and OFFICE2_STANDALONE_SMOKE=1.
"""
from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "office2" / "standalone-candidate-tests-2026-10-19.md"

PINS = (
    "langgraph==1.2.16",
    "langgraph-checkpoint==4.3.0",
    "crewai==1.15.28",
    "autogen-core==0.7.5",
    "dbos==3.3.0",
    "pydantic-ai==2.57.0",
    "litellm==1.88.6",
    "agent-framework-core==1.22.0",
    "ifixai==4.2.0",
    "promptfoo@0.124.1",
    "temporal CLI v1.9.1",
    "goose v1.55.0",
    "opencode v1.19.3",
)


def refuse_non_loopback() -> None:
    """Install the same connect refusal used during the recorded smokes."""
    connect = socket.socket.connect

    def guarded(self, address):  # type: ignore[no-untyped-def]
        if isinstance(address, tuple) and address:
            host = str(address[0])
            if host not in {"127.0.0.1", "::1", "localhost"}:
                raise OSError("refused non-loopback connect to " + repr(address))
        return connect(self, address)

    socket.socket.connect = guarded  # type: ignore[method-assign]


def main(argv: list[str]) -> int:
    if os.environ.get("OFFICE2_STANDALONE_SMOKE") != "1" or "--execute" not in argv:
        print("Office 2.0 standalone smokes are recorded in:")
        print(DOC)
        print("Pins:", ", ".join(PINS))
        print("Refusing to install or run. Set OFFICE2_STANDALONE_SMOKE=1 and pass --execute.")
        return 2
    if not DOC.is_file():
        print("missing", DOC)
        return 1
    refuse_non_loopback()
    print("guard armed; recorded results stay in the doc. This helper does not reinstall packages.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
