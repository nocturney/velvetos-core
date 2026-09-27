# syntax=docker/dockerfile:1
# Build context MUST be the repository root so approval/ + CAPABILITIES + core-mcp
# are available. Private signing keys are NEVER copied into this image.
# Base pinned 2026-09-26: python:3.12-slim resolved to 3.12.14-slim-trixie (index digest, multi-arch).
FROM python:3.12.14-slim-trixie@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MCP_PATH=/mcp \
    HOST=0.0.0.0 \
    PYTHONPATH=/app/packages

WORKDIR /app

# Exact pins resolved together on py3.12 (pip check clean; boot-tested /healthz,
# 401 without bearer, initialize). starlette/cryptography match requirements-sensors.txt.
RUN pip install --no-cache-dir \
    "adelaidasofia-instagram-mcp==0.1.2" \
    "fastmcp==3.4.7" \
    "uvicorn[standard]==0.54.0" \
    "starlette==1.7.0" \
    "cryptography==50.0.1" \
    "google-cloud-storage==3.15.0"

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
