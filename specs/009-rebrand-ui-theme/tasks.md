# Tasks: Rebrand UI & Theme Refresh

**Input**: Design documents from `/specs/009-rebrand-ui-theme/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/brand-tokens.md ✅, quickstart.md ✅

**Tests**: Not requested — no test tasks generated. Verification is manual per quickstart.md.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1–US4 maps to spec.md user stories)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create brand-asset pipeline and directory scaffolding before any user story work begins.

- [x] T001 Create `frontend/src/assets/brand/` directory (placeholder `.gitkeep` if empty initially)
- [x] T002 [P] Create `docs/docs/assets/brand/` directory (placeholder `.gitkeep` if empty initially)
- [x] T003 Create `scripts/generate-brand-assets.py` — Pillow-based script that reads `chart-monitor-logo.png` from repo root, outputs: `frontend/src/assets/brand/favicon.ico` (16/32/48), `frontend/src/assets/brand/logo-192.png`, `frontend/src/assets/brand/logo-512.png`, `frontend/src/assets/brand/logo-header.png`, `docs/docs/assets/brand/favicon.ico` (copy), `docs/docs/assets/brand/logo-header.png` (copy), and `specs/009-rebrand-ui-theme/brand-tokens.json` (extracted dominant hue + complement + WCAG AA contrast report)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Generate all derived assets and extract palette tokens — these outputs are required by every subsequent user story phase.

**⚠️ CRITICAL**: All user story work depends on these outputs existing.

- [x] T004 Run `python scripts/generate-brand-assets.py` from repo root; confirm all outputs exist in `frontend/src/assets/brand/` and `docs/docs/assets/brand/`; review printed `--brand-primary` / `--brand-accent` hex values and WCAG AA report in `specs/009-rebrand-ui-theme/brand-tokens.json` — adjust `--hue-override` param if dominant color was undesired, then rerun
- [x] T005 Add a `/* brand-tokens:begin */ … /* brand-tokens:end */` block to the top of `frontend/src/styles.css` declaring `:root` (light) and `:root[data-theme="dark"]` (dark) CSS custom properties: `--brand-primary`, `--brand-primary-fg`, `--brand-accent`, `--surface-bg`, `--surface-fg`, `--surface-raised`, `--border-subtle`, `--focus-ring` — values taken directly from `specs/009-rebrand-ui-theme/brand-tokens.json`

**Checkpoint**: `frontend/src/assets/brand/` contains 4 files; `docs/docs/assets/brand/` contains 2 files; `styles.css` declares both theme token blocks.

---

## Phase 3: User Story 1 — Cohesive Brand Identity Across App & Docs (Priority: P1) 🎯 MVP

**Goal**: Replace all "CM" placeholder marks with the new logo and apply the logo-derived theme palette to both the web app and the MkDocs documentation in light and dark modes.

**Independent Test**: Open app in browser — tab icon and header show the new logo; toggling light/dark changes colors and both themes are visibly derived from the logo palette. Open docs (`mkdocs serve`) — same logo in header and tab; palette toggles correctly. Run `mkdocs build --strict` with no errors.

### Implementation for User Story 1

- [x] T006 [US1] Update `frontend/src/index.html` lines 26 and 114: replace both `<div class="logo" ...>CM</div>` elements with `<img src="./assets/brand/logo-header.png" alt="Chart-Monitor" class="brand-logo" />`
- [x] T007 [P] [US1] Update `frontend/src/index.html` `<head>`: add `<link rel="icon" type="image/x-icon" href="./assets/brand/favicon.ico" />`, `<link rel="icon" type="image/png" sizes="192x192" href="./assets/brand/logo-192.png" />`, `<link rel="icon" type="image/png" sizes="512x512" href="./assets/brand/logo-512.png" />`, `<link rel="apple-touch-icon" href="./assets/brand/logo-192.png" />`; remove any previous favicon link if present
- [x] T008 [P] [US1] Update `frontend/src/styles.css`: replace all hardcoded color values in the existing light/dark palette rules to reference the new CSS custom properties from T005 (`--brand-primary`, `--surface-bg`, `--surface-fg`, etc.) — do not alter layout, spacing, or non-color rules in this task
- [x] T009 [P] [US1] Add `.brand-logo` CSS rule to `frontend/src/styles.css`: `max-height: 48px; width: auto; display: block;` (renders crisply at 48 CSS px on 2× DPR since source is 96px)
- [x] T010 [US1] Update `docs/mkdocs.yml`: set `theme.logo: assets/brand/logo-header.png`, `theme.favicon: assets/brand/favicon.ico`, and update both `theme.palette[]` entries with `primary:` and `accent:` nearest to the brand tokens from `brand-tokens.json` (use Material named-color closest by hue)
- [x] T011 [US1] If no Material named-color is within an acceptable hue distance: create `docs/docs/assets/extra.css` with `--md-primary-fg-color` and `--md-accent-fg-color` overrides; add `extra_css: [assets/extra.css]` to `docs/mkdocs.yml`

**Checkpoint**: US1 fully testable — both surfaces show new logo; both surfaces apply logo-derived palette in light and dark modes. `mkdocs build --strict` passes.

---

## Phase 4: User Story 2 — No-Scroll Layout on Normal Screens (Priority: P1)

**Goal**: Restructure the app shell so the full UI (header + sidebar + content) fits a 1440px+ viewport with no outer page scrollbar. Internal regions scroll locally. Below 1440px the layout is fully responsive.

**Independent Test**: Open app at 1920×1080 and 1440×900 — no outer vertical scrollbar; all chrome visible. Resize to 1280, 1024, 768, 360 — layout collapses/stacks responsively with no clipped controls.

### Implementation for User Story 2

- [x] T012 [US2] Update `frontend/src/styles.css`: add root shell rules — `html, body { height: 100%; margin: 0; }` and a CSS Grid layout on the main app wrapper (`display: grid; grid-template-rows: auto 1fr; height: 100vh; overflow: hidden`) so header is fixed height and the body row fills remaining space
- [x] T013 [US2] Update `frontend/src/styles.css`: make the `.sidebar` + main content row a nested CSS Grid or Flexbox (`display: flex; flex-direction: row; overflow: hidden; min-height: 0`) so each column fills height without overflowing the viewport
- [x] T014 [US2] Update `frontend/src/styles.css`: add `overflow: auto; min-height: 0;` to all inner scrollable containers (`.sidebar-nav`, chart list/table containers, main content area) so they scroll internally rather than expanding the page
- [x] T015 [US2] Update `frontend/src/styles.css`: add responsive breakpoint at `@media (max-width: 1440px)` — switch grid/flex to single-column stacked layout; sidebar collapses to a top strip or hidden drawer; content area regains `overflow: auto` on the outer page; ensure all controls remain reachable at 1280, 1024, 768, and 360px widths
- [x] T016 [US2] Update `frontend/src/index.html` if needed: adjust wrapper element classes/structure to match the new grid areas defined in T012–T013 (e.g., ensure `<aside class="sidebar">` and `<main>` are direct children of the grid container)

**Checkpoint**: US2 fully testable — 1440px+ shows no outer scroll; responsive below 1440px with no clipped controls.

---

## Phase 5: User Story 3 — Vertical Sidebar with Sync at Top (Priority: P2)

**Goal**: Hoist the sync button to the top of the sidebar (currently at the bottom) and replace its `↕` glyph with the Lucide `git-branch` SVG icon.

**Independent Test**: Open app — sidebar runs top-to-bottom; first clickable element is the sync button; sync button shows the Lucide `git-branch` SVG (not `↕`, not the GitHub octocat); clicking still triggers the sync modal unchanged.

### Implementation for User Story 3

- [x] T017 [US3] Obtain the Lucide `git-branch` SVG markup (from lucide.dev/icons/git-branch, MIT-licensed); save as inline snippet with `stroke="currentColor" fill="none" width="18" height="18"` for reference
- [x] T018 [US3] Update `frontend/src/index.html`: move the `<div class="sidebar-sync">` block (currently lines 144–151, after `.sidebar-nav`) to immediately after the opening `<aside class="sidebar">` tag, before `.sidebar-label` and `.sidebar-nav` — so sync is the first element in the sidebar DOM order
- [x] T019 [US3] Update `frontend/src/index.html`: inside `#sync-btn`, replace the `↕` text glyph with the Lucide `git-branch` inline SVG from T017; keep the existing button text " Sync Scripts" or adjust spacing as needed
- [x] T020 [P] [US3] Update `frontend/src/styles.css`: add/adjust `.sidebar-sync` rules if positional styles (e.g., `margin-top: auto`) relied on bottom placement — remove those and add appropriate top-of-sidebar spacing

**Checkpoint**: US3 fully testable — sync button is topmost sidebar element with Git icon; sync behavior unchanged.

---

## Phase 6: User Story 4 — Refresh Button Shows Refresh Icon (Priority: P3)

**Goal**: Add the Lucide `refresh-cw` circular-arrow icon to every refresh control in the app (global and per-chart).

**Independent Test**: Locate every refresh button/control in the rendered UI — each displays the `refresh-cw` SVG; clicking any of them triggers the same refresh behavior as before.

### Implementation for User Story 4

- [x] T021 [US4] Obtain the Lucide `refresh-cw` SVG markup (from lucide.dev/icons/refresh-cw, MIT-licensed); save as inline snippet with `stroke="currentColor" fill="none" width="16" height="16"` for reference; confirm it renders as a circular-arrow
- [x] T022 [US4] Audit `frontend/src/index.html` and `frontend/src/app.js` for all refresh controls — list each element (id, line number, and whether it is static HTML or JS-injected); note which are in `index.html` and which are created dynamically in `app.js`
- [x] T023 [US4] Update each static refresh control found in `frontend/src/index.html`: prepend the Lucide `refresh-cw` inline SVG from T021 inside the button element, before any existing text label
- [x] T024 [US4] Update each dynamically-injected refresh control in `frontend/src/app.js`: inject the `refresh-cw` SVG string alongside the button text where the element is constructed — keep `stroke="currentColor"` so it inherits the button's text color in both themes

**Checkpoint**: US4 fully testable — every refresh control in the UI shows the circular-arrow icon; all refresh behaviors unchanged.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final accessibility verification, docs build validation, and cleanup.

- [x] T025 [P] Run WCAG AA contrast audit on the rebranded app in both light and dark modes (browser DevTools "Issues" panel or axe extension); fix any failing token pairs in `frontend/src/styles.css`
- [x] T026 [P] Run `mkdocs build --strict` from `docs/` and confirm zero warnings or errors; fix any broken asset references
- [x] T027 [P] Verify the app loads correctly at representative widths: 360, 768, 1280, 1440, 1920 — check for no outer scroll at 1440+, no clipped controls below 1440; fix any regressions in `frontend/src/styles.css`
- [x] T028 Verify the existing theme-toggle behavior (user-selectable light/dark, preference persisted) continues to work after palette changes in `frontend/src/styles.css` — no forced reset
- [x] T029 Remove `.gitkeep` files from `frontend/src/assets/brand/` and `docs/docs/assets/brand/` now that real assets are committed
- [x] T030 [P] Update `specs/009-rebrand-ui-theme/brand-tokens.json` with final approved hex values if they were adjusted during T004

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T001 and T002 can run in parallel.
- **Foundational (Phase 2)**: Depends on Phase 1 (T003 must exist before T004). T004 must complete before T005.
- **User Stories (Phases 3–6)**: All depend on Phase 2 completion (assets + tokens must exist).
  - US1 (Phase 3) and US2 (Phase 4) are both P1 — can run in parallel if staffed.
  - US3 (Phase 5) depends only on Phase 2 — can run in parallel with US1 and US2.
  - US4 (Phase 6) depends only on Phase 2 — can run in parallel with any of the above.
- **Polish (Phase 7)**: Depends on all desired user stories complete.

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. No dependency on US2/US3/US4.
- **US2 (P1)**: Depends on Phase 2 only. No dependency on US1/US3/US4.
- **US3 (P2)**: Depends on Phase 2 only. Integrates cleanly with US2 layout (sidebar is a grid child) but does not block or depend on it.
- **US4 (P3)**: Depends on Phase 2 only. Works on independent controls from US1–US3.

### Within Each User Story

- T006 and T007–T009 within US1 can run in parallel (different files/sections).
- T010 and T011 in US1 are sequential (T011 only runs if T010 needs a CSS fallback).
- T012 → T013 → T014 in US2 are sequential (each layer depends on the previous).
- T015 and T016 in US2 can run in parallel after T012–T014.
- T017 must complete before T018–T019 in US3 (icon markup needed).
- T021 must complete before T023–T024 in US4 (icon markup needed).

---

## Parallel Execution Examples

### Phase 1 (parallel)
```
T001  Create frontend/src/assets/brand/
T002  Create docs/docs/assets/brand/
```

### Phase 3 — US1 (after T004+T005 complete)
```
T006  Replace CM logo in index.html (lines 26 + 114)
T007  Add favicon <link> tags to index.html <head>
T008  Re-wire colors to CSS custom properties in styles.css
T009  Add .brand-logo CSS rule to styles.css
```
*(T010 → T011 are sequential after T006–T009)*

### Phase 4 — US2 (parallel with US1 after Phase 2)
```
T012 → T013 → T014 (sequential)
T015 and T016 (parallel after T012–T014)
```

### Phase 7 — Polish (parallel)
```
T025  WCAG AA contrast audit
T026  mkdocs build --strict
T027  Responsive width verification
```

---

## Implementation Strategy

### MVP First (US1 + US2 only — both P1)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005)
3. Complete Phase 3: US1 — Brand Identity (T006–T011)
4. Complete Phase 4: US2 — No-Scroll Layout (T012–T016)
5. **STOP and VALIDATE**: brand + layout working together
6. Deploy/demo

### Incremental Delivery

1. Phase 1 + Phase 2 → assets and tokens ready
2. Phase 3 (US1) → logo + colors visible on both app and docs → demo-able
3. Phase 4 (US2) → no-scroll desktop layout → demo-able
4. Phase 5 (US3) → sync button at top with Git icon → demo-able
5. Phase 6 (US4) → refresh icons on all controls → demo-able
6. Phase 7 → polish, contrast, responsive verification → ship-ready

---

## Notes

- [P] tasks operate on different files or independent sections — no merge conflicts when parallelized.
- `scripts/generate-brand-assets.py` (T003) is a one-time generation tool; commit the *outputs*, not just the script.
- After T004, eyeball the extracted `--brand-primary` color before writing it to `styles.css` (T005) — the automated hue extraction can occasionally pick a near-neutral if the logo has low saturation.
- The Lucide SVG snippets (T017, T021) should be pasted inline — no external CDN reference at runtime.
- Stop at any checkpoint to validate the story independently before proceeding to the next phase.
