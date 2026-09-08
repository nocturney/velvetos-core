# VelvetOS — remote Instagram MCP (Streamable HTTP + bearer gate)
# Upstream tools: adelaidasofia-instagram-mcp (do not rewrite).
# Cloud Run injects PORT; serve.py binds 0.0.0.0:$PORT.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    INSTAGRAM_MCP_HOST=0.0.0.0 \
    INSTAGRAM_MCP_PATH=/mcp \
    INSTAGRAM_MCP_TRANSPORT=streamable-http \
    PORT=8080

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY serve.py /app/serve.py

# Non-root
RUN useradd -m -u 10001 mcp && chown -R mcp:mcp /app
USER mcp

EXPOSE 8080

# App-layer bearer auth is mandatory (VELVET_INSTAGRAM_MCP_BEARER_TOKEN).
# Live MCP probe: scripts/vf_instagram_mcp_remote_health.py
CMD ["python", "/app/serve.py"]
