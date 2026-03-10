# Implementation Plan: Core Chart-Monitor Application

**Branch**: `001-core-engine` | **Date**: 2026-03-10 | **Spec**: [spec.md](file:///d:/Develop/cloudops/chart-monitor/specs/001-core-engine/spec.md)
**Input**: Feature specification from `/specs/001-core-engine/spec.md`

## Summary

Build the core Chart-Monitor application, a dynamic data engine that securely executes Python collectors to fetch data and renders the output via a vanilla frontend interface. The frontend will use pure Vanilla CSS (no Tailwind, no CDNs, all assets downloaded locally) and will be served directly by the FastAPI backend application on the same pod.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), Vanilla HTML/JS/CSS (Frontend)
**Primary Dependencies**: FastAPI, RestrictedPython, Pytest
**Storage**: File-system (Pure GitOps)
**Testing**: Pytest (unit/integration), Manual UI validation
**Target Platform**: Linux server, Docker Desktop (on-prem)
**Project Type**: Web service + bundled frontend
**Performance Goals**: 30s default scrape intervals, sub-second API responses
**Constraints**: Pure vanilla frontend, NO CDNs, NO external build steps for CSS, serve frontend directly from backend.
**Scale/Scope**: Dozens of collectors, small operator teams

## Constitution Check

*GATE: Passed*

- **I. Dynamic Data Engine**: Core mechanic fulfilled via CodeExecutor.
- **II. Storage Agnostic**: FileStore implementation decoupled from K8s.
- **III. Strict Typing & Clean Code**: Python 3.11 typed backend.
- **IV. Secure Execution Sandbox**: RestrictedPython utilized.
- **V. Vanilla Desktop-First UI**: Tailwind removed per user request; strict Vanilla HTML/CSS/JS with locally hosted assets.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Tasks
```

### Source Code

```text
backend/
├── src/
│   ├── api/
│   ├── engine/
│   ├── models/
│   ├── storage/
│   └── main.py          # FastAPI app serving static frontend from ../frontend/src
├── tests/
└── store/               # Mounted user scripts

frontend/
└── src/
    ├── index.html
    ├── app.js
    ├── styles.css       # Vanilla CSS
    └── assets/          # Downloaded fonts/icons (No CDNs)
```

**Structure Decision**: A bundled web application where `backend/src/main.py` serves the API routes as well as mounting the `frontend/src` directory as static files. No frontend build step is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| None      | N/A        | N/A                                  |
