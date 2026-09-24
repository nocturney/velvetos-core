# VelvetOS Control API — Cloud Run image
# Build context MUST be the repository root:
#   gcloud builds submit . --config packages/velvetos_control_api/cloudbuild.json
#   or: docker build -f packages/velvetos_control_api/Dockerfile .
#
# Isolation: do NOT mount Instagram mutation secrets, delivery-approval private
# keys, or unrelated high-privilege credentials onto this service.
# Least privilege: read projection of repo checkout + optional bearer from GSM.

# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app/packages

WORKDIR /app

# stdlib HTTP only — no Starlette/FastAPI required for Control API v1
RUN useradd -r -u 10003 controlapi

# Projection sources (read-only catalog). No Meta tokens. No approval private keys.
COPY packages/velvetos_control_api /app/packages/velvetos_control_api
COPY scripts/vf_jobs_adapter.py /app/scripts/vf_jobs_adapter.py
COPY scripts/vf_control_plane.py /app/scripts/vf_control_plane.py
COPY scripts/vf_autonomy.py /app/scripts/vf_autonomy.py
COPY scripts/vf_paths.py /app/scripts/vf_paths.py
COPY scripts/vf_office.py /app/scripts/vf_office.py
COPY office /app/office
COPY packages/vfops/hq/capabilities.json /app/packages/vfops/hq/capabilities.json
COPY packages/vfigos/CAPABILITIES.json /app/packages/vfigos/CAPABILITIES.json
COPY packages/velvetos/living-studio /app/packages/velvetos/living-studio
COPY constitution/PUBLIC_CTA.md /app/constitution/PUBLIC_CTA.md
COPY constitution/CONSTITUTION.md /app/constitution/CONSTITUTION.md
COPY constitution/ORCHESTRA.md /app/constitution/ORCHESTRA.md
COPY packages/vfgrowth/data /app/packages/vfgrowth/data
COPY packages/vfprod/hq /app/packages/vfprod/hq
COPY packages/vfmedia/catalog.json /app/packages/vfmedia/catalog.json

# Ensure package __init__ paths exist for copied JSON-only trees
RUN mkdir -p /app/packages/vfops/hq /app/packages/vfigos /app/packages/vfmedia \
    /app/packages/vfgrowth /app/packages/vfprod /app/constitution /app/scripts \
    && chown -R controlapi:controlapi /app

USER controlapi

EXPOSE 8080

# VELVETOS_CONTROL_API_TOKEN must be provided via GSM / Cloud Run secrets — never baked in.
CMD ["python3", "-m", "velvetos_control_api"]
