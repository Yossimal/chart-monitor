# Phase 1 Data Model — Rebrand UI & Theme Refresh

This feature does not introduce or alter any runtime or persisted data. Instead, it introduces a small set of **static brand artifacts** that are produced from a single source-of-truth image and referenced by both the web app and the documentation. This file documents that artifact set as the feature's "data model."

## Source of truth

- **chart-monitor-logo.png** (repo root)
  - Role: authoritative brand mark.
  - Format: PNG with alpha.
  - Lifecycle: replaced only when the brand changes; all other artifacts are regenerated from it.

## Derived brand artifacts

| Artifact | Path (app) | Path (docs) | Dimensions | Purpose |
|---|---|---|---|---|
| `favicon.ico` | `frontend/src/assets/brand/favicon.ico` | `docs/docs/assets/brand/favicon.ico` | 16 / 32 / 48 (multi-size) | Browser tab icon |
| `logo-192.png` | `frontend/src/assets/brand/logo-192.png` | — | 192×192 | PWA / high-DPI favicon fallback |
| `logo-512.png` | `frontend/src/assets/brand/logo-512.png` | — | 512×512 | PWA / social share / large surfaces |
| `logo-header.png` | `frontend/src/assets/brand/logo-header.png` | `docs/docs/assets/brand/logo-header.png` | ~96×96 (rendered at 48 CSS px, 2× DPR) | App header + MkDocs theme logo |

**Validation rules**:
- All derived artifacts MUST be regenerated from the source PNG via `scripts/generate-brand-assets.py` (no hand-edits).
- `favicon.ico` MUST contain at least the 16/32/48 entries.
- `logo-header.png` MUST be provided at 2× the largest CSS rendering size to remain crisp on retina displays.

## Derived theme tokens

Extracted alongside the image artifacts by the same generation script and emitted into two consumption points:

1. `frontend/src/styles.css` — as CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark).
2. `docs/mkdocs.yml` — as `theme.palette[].primary` / `theme.palette[].accent` (or as `extra.css` `--md-primary-fg-color` overrides when no named color matches).

| Token | Light mode | Dark mode | Source |
|---|---|---|---|
| `--brand-primary` | sampled dominant non-neutral hue | same hue, lightness-adjusted for dark bg | Pillow quantize of source PNG |
| `--brand-accent` | split-complement (hue + 150°..210°) | same, lightness-adjusted | Derived from `--brand-primary` |
| `--surface-bg` | near-white tinted toward primary | near-black tinted toward primary | Standard Material-style derivation |
| `--surface-fg` | near-black | near-white | Contrast-tested against `--surface-bg` |
| `--border-subtle` | low-contrast neutral | low-contrast neutral | Derived |

**Validation rules**:
- `{--surface-fg, --surface-bg}` contrast ratio MUST be ≥ 4.5:1 (WCAG AA body text) in both schemes.
- `{text-on-primary, --brand-primary}` contrast ratio MUST be ≥ 4.5:1 in both schemes.
- Tokens are **not** environment- or user-configurable at runtime; they are compile-time constants keyed to the source logo.

## Relationships

```
chart-monitor-logo.png (source)
        │
        ▼ generate-brand-assets.py
        ├──► favicon.ico           ──► referenced by frontend/src/index.html AND docs/mkdocs.yml
        ├──► logo-192.png          ──► referenced by frontend/src/index.html (PWA meta)
        ├──► logo-512.png          ──► referenced by frontend/src/index.html (PWA meta)
        ├──► logo-header.png       ──► referenced by frontend/src/index.html (header <img>) AND docs/mkdocs.yml (theme.logo)
        └──► brand-tokens.json     ──► consumed into styles.css + mkdocs.yml palette
```

## Lifecycle / state transitions

The artifact set has two states only:

- **Stale**: `chart-monitor-logo.png` has been modified after any derived artifact's mtime.
- **Fresh**: all derived artifacts' mtimes are ≥ the source's mtime.

The regeneration script MUST move the set from Stale → Fresh atomically (write to temp paths, then rename) so partial states never reach the repo.
