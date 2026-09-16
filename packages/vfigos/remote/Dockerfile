# syntax=docker/dockerfile:1
# Build context MUST be the repository root so approval/ + CAPABILITIES + core-mcp
# are available. Private signing keys are NEVER copied into this image.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MCP_PATH=/mcp \
    HOST=0.0.0.0 \
    PYTHONPATH=/app/packages

WORKDIR /app

RUN pip install --no-cache-dir \
    "adelaidasofia-instagram-mcp>=0.1.2" \
    "fastmcp>=3.4.2,<4" \
    "uvicorn[standard]>=0.30" \
    "starlette>=0.37" \
    "cryptography>=41" \
    "google-cloud-storage>=2.14"

# Remote MCP entry + overlays
COPY packages/vfigos/remote/*.py /app/
# Shared delivery-approval verify/spend (public keys only — no private key material)
COPY packages/vfigos/approval /app/packages/vfigos/approval
COPY packages/vfigos/__init__.py /app/packages/vfigos/__init__.py
COPY packages/vfigos/CAPABILITIES.json /app/packages/vfigos/CAPABILITIES.json
COPY packages/vfmcp/core-mcp.json /app/packages/vfmcp/core-mcp.json

RUN useradd -r -u 10001 mcp && chown -R mcp:mcp /app
USER mcp

EXPOSE 8080

# Meta + connector secrets are injected by Cloud Run / Secret Manager at runtime.
# Do NOT mount VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64 or issuer token here.
CMD ["python3", "/app/http_server.py"]
