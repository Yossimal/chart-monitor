# Research: Core Chart-Monitor Application

## Frontend Styling & Asset Management

**Decision**: Pure Vanilla CSS, completely removing Tailwind CSS and any external build tools (like Node.js/npm). All web assets (fonts, icons) must be downloaded and hosted directly inside the repository.
**Rationale**: The user explicitly rejected Tailwind after initial implementation attempts resulted in unstyled components and complex build pipelines. For true on-prem, air-gapped support without CDNs, pure vanilla CSS is the simplest, most resilient approach. It directly aligns with Constitution Principle V.
**Alternatives considered**: Local Tailwind build via Node CLI (rejected due to added complexity and user preference for vanilla), Tailwind CDN (rejected due to on-prem air-gap requirements).

## Frontend Routing & Architecture

**Decision**: The entire frontend (HTML, JS, CSS, and structural assets) will be served directly by the Python FastAPI backend via `StaticFiles`.
**Rationale**: The user requested that the frontend jump off the same pod and executable. This removes the need for a separate web server (like NGINX) or separate container for the frontend.
**Alternatives considered**: Separate NGINX container (rejected per explicit user request), Next.js (rejected due to Constitution V framework lock-in rules).

## Secure Execution

**Decision**: Use `RestrictedPython`.
**Rationale**: Standard, well-tested Python library for sandboxing.
**Alternatives considered**: WASM (too bleeding edge for simple Python scripts), Docker-in-Docker (too heavy).
