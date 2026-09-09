# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MCP_PATH=/mcp \
    HOST=0.0.0.0

WORKDIR /app

RUN pip install --no-cache-dir \
    "adelaidasofia-instagram-mcp>=0.1.2" \
    "fastmcp>=3.4.2,<4" \
    "uvicorn[standard]>=0.30" \
    "starlette>=0.37"

# Remote entry + Graph v21 insights / mutation / CTA audit overlays.
COPY *.py /app/

# Non-root
RUN useradd -r -u 10001 mcp && chown -R mcp:mcp /app
USER mcp

EXPOSE 8080

# Meta + connector secrets are injected by Cloud Run / Secret Manager at runtime.
CMD ["python3", "/app/http_server.py"]
