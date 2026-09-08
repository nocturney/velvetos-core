"""Durable media intake — inbox scan → catalog → verify download → move to source.

Phases (report separately; visual review never blocks intake):
  registered — row in canonical catalog.json (persisted before Drive move)
  verified   — real download bytes checked + moved inbox→source
  visual     — optional later; independent of verified

Drive credentials on the background runner are required to complete the requirement.
"""

from .runner import (
    EXIT_AUTH,
    EXIT_BUSY,
    EXIT_FAIL,
    EXIT_OK,
    EXIT_PERSIST,
    run_intake,
    run_selftest,
)

__all__ = [
    "EXIT_OK",
    "EXIT_FAIL",
    "EXIT_BUSY",
    "EXIT_AUTH",
    "EXIT_PERSIST",
    "run_intake",
    "run_selftest",
]
