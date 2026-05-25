# chart-monitor Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-09

## Active Technologies
- Backend: Python 3.11+. Frontend: HTML/JS/CSS (Vanilla + Tailwind). + Backend: `FastAPI`, `RestrictedPython`, `hvac` (Vault). Frontend: TailwindCSS. (001-core-engine)
- File System (GitOps-mapped volume containing YAML configurations). (001-core-engine)
- Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend) + FastAPI, RestrictedPython, HashiCorp Vault (or k8s secrets) client, Tailwind CSS (001-core-engine)
- FileSystem (`FileStore` implementation, GitOps ready), future SQLite in-memory support. (001-core-engine)
- Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend) + FastAPI, RestrictedPython, Pytest (001-core-engine)
- File-system (Pure GitOps) (001-core-engine)
- Python 3.11+ (Backend), TypeScript / Vanilla JS (Frontend) + FastAPI (Backend), DOM API / Vanilla JS (Frontend) [NEEDS CLARIFICATION: Best lightweight, framework-free library for virtualizing 10k rows if raw DOM is insufficient?] (001-ui-enhancements)
- N/A (State kept in browser/URL) (001-ui-enhancements)
- Python 3.11+ (Backend), TypeScript/Vanilla (Frontend) + FastAPI, RestrictedPython, Pytest (Backend) (002-gitops-sync)
- Git repository (remote), Local Filesystem (target path) (002-gitops-sync)
- Vanilla JS (ES6+) + sql.js (already bundled as `frontend/src/assets/sql-wasm.*`) — no new dependencies (007-column-filter-menu)
- `URLSearchParams` + `history.replaceState()` (browser-native, no external storage) (007-column-filter-menu)
- Python 3.11+ (backend/build), Vanilla HTML/CSS/JS (main frontend) + MkDocs ≥1.5, mkdocs-material ≥9.5, FastAPI (existing), Pygments (transitive via mkdocs-material) (008-in-app-docs)
- File-system only — docs source in `docs/docs/*.md`, build output in `docs/site/` (gitignored) (008-in-app-docs)
- Vanilla HTML5 / CSS3 / ES2020 JS (frontend); MkDocs (Python-rendered static docs) + MkDocs + `mkdocs-material` (already in use — see `docs/mkdocs.yml`); Lucide (inline SVG icon set) for Git and refresh glyphs delivered as static SVG markup (no JS runtime dep) (009-rebrand-ui-theme)
- N/A — brand assets live in `frontend/src/assets/brand/` and `docs/docs/assets/brand/`; source-of-truth PNG stays at repo root (009-rebrand-ui-theme)
- YAML / Helm Go templates, Helm 3.x + Helm 3, Kubernetes API 1.24+, `route.openshift.io/v1` (OpenShift 4.10+) (010-helm-chart-deploy)
- PersistentVolumeClaim — StorageClass driven by `persistence.storageClass` value (empty = cluster default) (010-helm-chart-deploy)
- Python 3.11+ (backend), YAML (Helm chart) + FastAPI, subprocess (stdlib), Helm 3 (011-git-skip-verify)
- N/A (no storage changes) (011-git-skip-verify)
- Python 3.11+ (backend), YAML (Helm chart) + FastAPI, subprocess + tempfile + urllib.parse + shutil (stdlib), Helm 3 (012-git-http-auth)

- Python 3.11+ (Backend), TypeScript/Vanilla Web (Frontend) + FastAPI, RestrictedPython, PyYAML, Tailwind CSS (via CDN or simple build) (001-core-engine)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11+ (Backend), TypeScript/Vanilla Web (Frontend): Follow standard conventions

## Recent Changes
- 012-git-http-auth: Added Python 3.11+ (backend), YAML (Helm chart) + FastAPI, subprocess + tempfile + urllib.parse + shutil (stdlib), Helm 3
- 011-git-skip-verify: Added Python 3.11+ (backend), YAML (Helm chart) + FastAPI, subprocess (stdlib), Helm 3
- 010-helm-chart-deploy: Added YAML / Helm Go templates, Helm 3.x + Helm 3, Kubernetes API 1.24+, `route.openshift.io/v1` (OpenShift 4.10+)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
