# syntax=docker/dockerfile:1
# Build context MUST be the repository root:
#   gcloud builds submit . --config packages/vfigos/approval/issuer/cloudbuild.yaml
#   or: docker build -f packages/vfigos/approval/issuer/Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app/packages

WORKDIR /app

RUN pip install --no-cache-dir \
    "cryptography>=41" \
    "uvicorn[standard]>=0.30" \
    "starlette>=0.37"

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
