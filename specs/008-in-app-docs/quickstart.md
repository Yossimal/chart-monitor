# Quickstart: In-App Documentation — 008-in-app-docs

## Integration Scenarios

These scenarios describe how to verify the feature end-to-end after implementation.

---

### Scenario 1: Build and serve the docs locally

**Goal**: Confirm MkDocs builds successfully and FastAPI serves the output at `/docs`.

**Steps**:
1. Install docs dependencies: `pip install -e "backend[docs]"` (from repo root)
2. Build the docs: `cd docs && mkdocs build`
3. Start the backend: `cd backend && uvicorn src.main:app --reload`
4. Open `http://localhost:8000/docs` in a browser
5. Verify: the MkDocs Material page loads, the left/right navigation is present, the search box works

**Expected**: Chart-Monitor Docs landing page renders with all sections in the navigation tree.

---

### Scenario 2: Verify Swagger moved to /api/docs

**Goal**: Confirm the old `/docs` route no longer returns Swagger UI, and `/api/docs` does.

**Steps**:
1. With the backend running, open `http://localhost:8000/api/docs`
2. Verify: FastAPI Swagger UI renders with all API endpoints listed
3. Open `http://localhost:8000/docs` — verify: MkDocs docs render (not Swagger)

**Expected**: Swagger is accessible only at `/api/docs`.

---

### Scenario 3: Deep-link to a specific section

**Goal**: Confirm fragment anchors work correctly (FR-004 / SC-004).

**Steps**:
1. Open `http://localhost:8000/docs/how-to/create-collector/`
2. Verify: the "Creating a Collector" page loads
3. Open `http://localhost:8000/docs/how-to/create-collector/#full-yaml-schema` (or any heading anchor)
4. Verify: the page loads scrolled to that heading and the ToC entry is highlighted

**Expected**: Deep-linked headings land at the correct position on first paint.

---

### Scenario 4: "Docs" link in the main app

**Goal**: Confirm the persistent "Docs" link appears and navigates correctly (FR-021).

**Steps**:
1. Open `http://localhost:8000/` (main app)
2. Verify: a "Docs" link appears in the header alongside the theme toggle
3. Click the "Docs" link
4. Verify: browser navigates to `http://localhost:8000/docs`
5. Navigate to a dashboard (GitOps must be configured), confirm "Docs" link is still visible

**Expected**: "Docs" link visible and functional on every page of the main app.

---

### Scenario 5: "Docs" link on the GitOps-unconfigured page

**Goal**: Confirm the "Docs" link is accessible before GitOps is configured (FR-021 / FR-002).

**Steps**:
1. Set `GIT_SSH_URL` env var to empty/unset so the app shows the GitOps setup page
2. Open `http://localhost:8000/`
3. Verify: the GitOps setup page renders AND a "Docs" link is visible in the header area
4. Click the "Docs" link — verify it opens `/docs`

**Expected**: New users can reach the docs before completing GitOps setup.

---

### Scenario 6: Dark mode follows app preference

**Goal**: Confirm docs page respects system/user theme preference (FR-025 — partial).

**Steps**:
1. Set OS to dark mode
2. Open `http://localhost:8000/docs` without any prior docs visit
3. Verify: the MkDocs Material dark palette is applied automatically

**Expected**: Docs renders in dark mode when OS preference is dark.

---

### Scenario 7: MkDocs dev server for authoring

**Goal**: Confirm content authors can preview changes live without running the full backend.

**Steps**:
1. `cd docs && mkdocs serve`
2. Open `http://localhost:8001` (default MkDocs port)
3. Edit any `.md` file — verify hot-reload shows the change within 2 seconds

**Expected**: Live preview works independently of the FastAPI backend.
