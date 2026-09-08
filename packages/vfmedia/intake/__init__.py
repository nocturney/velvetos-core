"""Durable media intake — inbox scan → catalog → verify download → move to source.

Phases (report separately; visual review never blocks intake):
  registered — row in canonical catalog.json
  verified   — download checked + moved inbox→source
  visual     — optional later; independent of verified
"""

from .runner import EXIT_AUTH, EXIT_BUSY, EXIT_FAIL, EXIT_OK, run_intake, run_selftest

__all__ = [
    "EXIT_OK",
    "EXIT_FAIL",
    "EXIT_BUSY",
    "EXIT_AUTH",
    "run_intake",
    "run_selftest",
]
