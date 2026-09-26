# syntax=docker/dockerfile:1
# Build context MUST be the repository root:
#   gcloud builds submit . --config packages/vfigos/approval/issuer/cloudbuild.json
#   or: docker build -f packages/vfigos/approval/issuer/Dockerfile .
# Base pinned 2026-09-26: python:3.12-slim resolved to 3.12.14-slim-trixie (index digest, multi-arch).
FROM python:3.12.14-slim-trixie@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app/packages

WORKDIR /app

# Exact pins; starlette/cryptography match requirements-sensors.txt, uvicorn matches remote/.
RUN pip install --no-cache-dir \
    "cryptography==50.0.1" \
    "uvicorn[standard]==0.54.0" \
    "starlette==1.7.0"

# Approval library + capability SoT (no Instagram MCP package, no Meta token).
COPY packages/vfigos/approval /app/packages/vfigos/approval
COPY packages/vfigos/CAPABILITIES.json /app/packages/vfigos/CAPABILITIES.json
COPY packages/vfigos/__init__.py /app/packages/vfigos/__init__.py
COPY packages/vfmcp/core-mcp.json /app/packages/vfmcp/core-mcp.json

# Ensure vfmcp package path exists for relative layout (file-only is enough).
RUN mkdir -p /app/packages/vfmcp && \
    useradd -r -u 10002 issuer && \
    chown -R issuer:issuer /app

USER issuer

EXPOSE 8080

CMD ["python3", "-m", "vfigos.approval.issuer.http_issuer"]
