"""VelvetOS Control API — HTTP projection gateway over canonical SoTs.

Not a Control Plane, runtime, queue, database, or second source of truth.
Projects existing adapters (control plane, jobs, capabilities, autonomy).
"""

from __future__ import annotations

__version__ = "1.0.0"
SCHEMA = "velvetos.control.v1"
SERVICE_NAME = "velvetos-control-api"
