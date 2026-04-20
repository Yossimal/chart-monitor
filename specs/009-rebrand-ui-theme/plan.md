# Implementation Plan: Rebrand UI & Theme Refresh

**Branch**: `009-rebrand-ui-theme` | **Date**: 2026-04-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-rebrand-ui-theme/spec.md`

## Summary

Rebrand the chart-monitor web application and its MkDocs documentation around the new `chart-monitor-logo.png`. Replace all placeholder "CM" marks and the current favicon with derivative assets (favicon.ico, 192/512 PNGs, header PNG) generated from the source logo. Re-derive the app's light/dark CSS-variable palette and the MkDocs Material `palette.primary`/`palette.accent` from the logo's dominant non-neutral hue. Restructure the application shell into a full-height layout that fits 1440px+ viewports with no outer page scroll (inner regions scroll locally) and gracefully collapses/stacks below that width. Keep the sidebar vertical (already is), hoist the sync button to its top, swap the sync glyph from `↕` to a vendor-neutral Git icon, and add a circular-arrow refresh icon to every refresh control (global + per-chart). No backend or data-layer changes.

## Technical Context

**Language/Version**: Vanilla HTML5 / CSS3 / ES2020 JS (frontend); MkDocs (Python-rendered static docs)
**Primary Dependencies**: MkDocs + `mkdocs-material` (already in use — see `docs/mkdocs.yml`); Lucide (inline SVG icon set) for Git and refresh glyphs delivered as static SVG markup (no JS runtime dep)
**Storage**: N/A — brand assets live in `frontend/src/assets/brand/` and `docs/docs/assets/brand/`; source-of-truth PNG stays at repo root
**Testing**: Manual responsive verification at 360 / 768 / 1280 / 1440 / 1920 widths; Lighthouse/axe accessibility contrast audit; MkDocs build smoke test (`mkdocs build --strict`)
**Target Platform**: Modern evergreen desktop browsers (Chrome, Firefox, Edge, Safari); docs served as static HTML
**Project Type**: Web application with separate static documentation site
**Performance Goals**: First contentful paint unchanged (±5%); cumulative layout shift unaffected by header/sidebar restructure
**Constraints**: 1440px+ viewport MUST have no outer page scroll; WCAG AA contrast on primary text + interactive elements in both themes; no new JS frameworks (constitution V — Vanilla Desktop-First UI)
**Scale/Scope**: Single feature-branch change across ~3 frontend files (`index.html`, `styles.css`, `app.js`), ~1 MkDocs config file, and ~1 asset directory per surface; no new screens

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Dynamic Data Engine | ✅ N/A | No change to collector/script engine. |
| II. Storage Agnostic & GitOps First | ✅ N/A | No storage-backend change. |
| III. Strict Typing & Clean Code | ✅ Pass | Feature edits pre-existing vanilla-JS frontend files; introduces no new untyped code paths. Frontend's vanilla-JS status is pre-existing and out of scope for this rebrand. |
| IV. Secure Execution Sandbox | ✅ N/A | No sandbox or execution-path change. |
| V. Vanilla Desktop-First UI | ✅ Pass | Uses Vanilla HTML/CSS/JS only; desktop-first target is 1920×1080 with 1440px no-scroll floor; icons are inline SVG (no icon-font runtime). |

**Result**: No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/009-rebrand-ui-theme/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (brand-asset inventory)
├── quickstart.md        # Phase 1 output (asset regeneration + local verify)
├── contracts/
│   └── brand-tokens.md  # CSS-variable + MkDocs palette contract
└── checklists/
    └── requirements.md  # From /speckit.specify
```

### Source Code (repository root)

```text
chart-monitor-logo.png                       # Source-of-truth brand asset (unchanged)

frontend/
├── src/
│   ├── index.html                           # Update: favicon links, header logo <img>, sidebar order, sync/refresh icons
│   ├── styles.css                           # Update: CSS vars (light+dark), full-height flex layout, 1440px breakpoint
│   ├── app.js                               # Update: refresh-button icon injection, sync-button icon swap
│   └── assets/
│       └── brand/                           # NEW: derived logo assets
│           ├── logo-header.png              # ~40–48px tall, 2x-aware
│           ├── logo-192.png                 # PWA / high-DPI
│           ├── logo-512.png                 # PWA / large surfaces
│           └── favicon.ico                  # multi-size 16/32/48

docs/
├── mkdocs.yml                               # Update: theme.palette (primary+accent), theme.logo, theme.favicon
└── docs/
    └── assets/
        └── brand/                           # NEW: docs copies of logo-header.png + favicon.ico
```

**Structure Decision**: Existing web-app + static-docs layout. No new top-level directories. Derived brand assets live in dedicated `assets/brand/` folders under each surface so regeneration replaces a known set without touching unrelated assets. Source PNG stays at repo root as the documented regeneration input.

## Complexity Tracking

> No Constitution Check violations. Section intentionally left empty.
