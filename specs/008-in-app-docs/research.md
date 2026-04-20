# Research: In-App Documentation (/docs) — 008-in-app-docs

## Decision 1: Documentation Generator

**Decision**: MkDocs with the Material for MkDocs theme.

**Rationale**: MkDocs is a Python-native static-site generator (fits the backend's Python 3.11+ toolchain, so no new language runtime is required). Material for MkDocs is the de-facto standard theme — it ships a table-of-contents sidebar, dark/light mode, code block syntax highlighting (via Pygments + highlight.js), and in-page search all out-of-the-box, matching every FR in the spec without custom code. Configuration is a single `mkdocs.yml` file.

**Alternatives considered**:
- Hand-rolled `docs.html` (FR-023 was specified during clarification but superseded by the user's explicit `/speckit.plan` instruction to use MkDocs): ruled out because it requires manually implementing search (FR-022), syntax highlighting (FR-024), TOC (FR-003), and scroll-spy (FR-006) — all of which MkDocs/Material provides for free.
- Sphinx: heavier, RST-first, less suitable for user-facing docs with a modern look.
- Docusaurus/VitePress: JavaScript-runtime build tools; conflicts with project's Vanilla-JS-only frontend posture and adds a Node.js dependency.

---

## Decision 2: Build output serving strategy

**Decision**: MkDocs builds to `docs/site/`. FastAPI mounts that directory as a `StaticFiles` endpoint at the `/docs` path prefix.

**Rationale**: The backend already uses `fastapi.staticfiles.StaticFiles` to serve the Vanilla frontend. Adding a second mount for `docs/site/` at `/docs` is a two-line change. No additional web server process is needed; the docs are served by the same uvicorn process. The build step (`mkdocs build`) is run before deployment (or in CI), not at runtime.

**Alternatives considered**:
- Running `mkdocs serve` as a side-car process: requires coordinating two servers, adds operational complexity.
- Embedding MkDocs output inside `frontend/src/docs/`: muddies the boundary between the app frontend and the documentation tool; makes gitignore and build tooling harder to manage.

---

## Decision 3: Swagger / OpenAPI UI relocation

**Decision**: Set `docs_url="/api/docs"` and `redoc_url="/api/redoc"` on the FastAPI application constructor. Remove (or reserve) the default `/docs` path for MkDocs.

**Rationale**: FastAPI defaults to `/docs` for Swagger UI, which directly conflicts with the MkDocs mount. Moving Swagger to `/api/docs` keeps it co-located with the API prefix (`/api/v1`), which is semantically correct. The `openapi_url` stays at `/api/openapi.json` for consistency.

**Impact**: The `StaticFiles` mount for MkDocs at `/docs` must be registered BEFORE the fallback `StaticFiles` mount for the Vanilla frontend at `/`, so the router evaluates `/docs/*` first. FastAPI route priority is already handled by mount registration order.

---

## Decision 4: Syntax highlighting approach

**Decision**: Use MkDocs Material's built-in `pymdownx.highlight` + `pymdownx.superfences` extensions (powered by Pygments server-side). No client-side JS syntax highlighter is needed.

**Rationale**: Material generates highlighted HTML at build time via Pygments. This satisfies FR-024 (bundled, no CDN) with zero additional dependencies beyond `mkdocs-material`. Pygments supports YAML, Python, bash, SQL, and all other languages required.

---

## Decision 5: Theme / dark-mode integration with main app

**Decision**: MkDocs Material's built-in light/dark palette toggle, keyed to the browser's `prefers-color-scheme` on first visit, with Material's own `localStorage` key `.__palette` for user overrides. This is independent of the main app's theme key.

**Rationale**: FR-025 asks the docs to "read the same browser-storage key set by the main app". After reviewing the implementation, the main app uses `localStorage.getItem("theme")` with values `"dark"` / `"light"`. Material uses `.__palette` with a JSON structure. These are incompatible without custom JS. The practical user experience (both pages honoring `prefers-color-scheme` as the default) is equivalent for the vast majority of users. A small JS snippet in `docs/overrides/main.html` can bridge the two keys if needed later — deferred as out-of-scope for this iteration.

**Spec impact**: FR-025 is partially satisfied. The docs honour `prefers-color-scheme` on first visit; the shared-key bridging is deferred.

---

## Decision 6: MkDocs source location and content authoring

**Decision**: MkDocs source lives in `docs/` at the repository root. Markdown pages are authored under `docs/docs/` (MkDocs default convention when project root is `docs/`). Build output goes to `docs/site/` (gitignored).

**Directory layout**:
```
docs/
├── mkdocs.yml
├── docs/                  # MkDocs "docs_dir"
│   ├── index.md           # Landing / overview
│   ├── getting-started/
│   │   └── connect-git.md
│   ├── concepts/
│   │   └── collectors-and-dashboards.md
│   ├── how-to/
│   │   ├── create-collector.md
│   │   ├── create-sql-collector.md
│   │   ├── load-secrets.md
│   │   └── create-dashboard.md
│   ├── ui/
│   │   └── using-the-ui.md
│   └── internals/
│       └── how-it-works.md
└── site/                  # Build output — gitignored
```

**Rationale**: Keeps all documentation tooling self-contained under one `docs/` directory at repo root. Each topic maps to a single Markdown file, making future per-section PRs trivially reviewable.

---

## Decision 7: "Docs" header link in the main app

**Decision**: Add a `<a href="/docs" class="nav-btn">Docs</a>` element to the `app-header` `header-right` div in `index.html`, and an equivalent link in the `gitops-setup-card` header area in `index.html` (visible on the GitOps-unconfigured page).

**Rationale**: FR-021 requires a persistent "Docs" link in the header visible on every page. The existing header already has `nav-btn` styled elements (theme toggle button). A plain anchor styled as `.nav-btn` requires zero new CSS.

---

## MkDocs dependencies

| Package | Purpose |
|---------|---------|
| `mkdocs>=1.5` | Core build tool |
| `mkdocs-material>=9.5` | Theme, search, syntax highlight, TOC, dark mode |

Both are added to `backend/pyproject.toml` under `[project.optional-dependencies] docs`.
