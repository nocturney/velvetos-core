"""VelvetOS Instagram delivery-approval trust boundary.

Shared verification + spend + capability loading for:
- owner-approval issuer (signs; holds private key)
- Instagram mutation service (verifies + atomic claim only)
- vf_project_preflight (advisory verify only)

MUTATION_SERVICE_HAS_PRIVATE_KEY must remain false.
"""

from __future__ import annotations

__all__ = [
    "SCHEMA_ID",
    "canonical_payload_bytes",
    "verify_receipt",
    "mutation_tool_ids",
]

from .schema import SCHEMA_ID
from .canonical import canonical_payload_bytes
from .verify import verify_receipt
from .capabilities import mutation_tool_ids
