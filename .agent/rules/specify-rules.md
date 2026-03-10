# chart-monitor Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-09

## Active Technologies
- Backend: Python 3.11+. Frontend: HTML/JS/CSS (Vanilla + Tailwind). + Backend: `FastAPI`, `RestrictedPython`, `hvac` (Vault). Frontend: TailwindCSS. (001-core-engine)
- File System (GitOps-mapped volume containing YAML configurations). (001-core-engine)
- Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend) + FastAPI, RestrictedPython, HashiCorp Vault (or k8s secrets) client, Tailwind CSS (001-core-engine)
- FileSystem (`FileStore` implementation, GitOps ready), future SQLite in-memory support. (001-core-engine)
- Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend) + FastAPI, RestrictedPython, Pytest (001-core-engine)
- File-system (Pure GitOps) (001-core-engine)

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
- 001-core-engine: Added Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend) + FastAPI, RestrictedPython, Pytest
- 001-core-engine: Added Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend) + FastAPI, RestrictedPython, HashiCorp Vault (or k8s secrets) client, Tailwind CSS
- 001-core-engine: Added Backend: Python 3.11+. Frontend: HTML/JS/CSS (Vanilla + Tailwind). + Backend: `FastAPI`, `RestrictedPython`, `hvac` (Vault). Frontend: TailwindCSS.


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
