FROM python:3.11-slim

# git + ssh for GitOps sync, ca-certificates for HTTPS in collector scripts
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        openssh-client \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system safe.directory '*'

WORKDIR /app/backend

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.110.0" \
    "uvicorn[standard]>=0.29.0" \
    "RestrictedPython>=7.0" \
    "pydantic>=2.0" \
    "python-dotenv>=1.0" \
    "requests>=2.0" \
    "mkdocs>=1.5" \
    "mkdocs-material>=9.5"

# Backend source (WORKDIR is /app/backend so `src` is importable directly)
COPY backend/src ./src

# Frontend static files
COPY frontend/src /app/frontend/src

# Build MkDocs docs from source (docs/site is gitignored, built here instead)
COPY docs /app/docs
RUN cd /app/docs && mkdocs build --site-dir site

RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
