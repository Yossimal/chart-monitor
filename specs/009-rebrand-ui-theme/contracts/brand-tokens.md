# Contract: Brand Tokens

This contract defines the **names**, **types**, and **consumers** of the brand tokens produced by this feature. Any consumer (current or future) that wants to stay on-brand MUST reference these names.

## 1. CSS custom properties (frontend)

Declared on `:root` (light) and `:root[data-theme="dark"]` (dark) in `frontend/src/styles.css`.

| Token | Type | Required | Example (light) | Example (dark) |
|---|---|---|---|---|
| `--brand-primary` | `<color>` | yes | `#RRGGBB` | `#RRGGBB` |
| `--brand-primary-fg` | `<color>` | yes | contrast-tested against `--brand-primary` | same |
| `--brand-accent` | `<color>` | yes | `#RRGGBB` | `#RRGGBB` |
| `--surface-bg` | `<color>` | yes | near-white | near-black |
| `--surface-fg` | `<color>` | yes | near-black | near-white |
| `--surface-raised` | `<color>` | yes | slightly elevated bg | slightly elevated bg |
| `--border-subtle` | `<color>` | yes | low-contrast neutral | low-contrast neutral |
| `--focus-ring` | `<color>` | yes | derived from `--brand-primary` | same |

**Contract rules**:
- Each token MUST be defined in both schemes; no scheme may fall back to the other.
- `{--surface-fg, --surface-bg}` contrast ≥ 4.5:1 in both schemes.
- `{--brand-primary-fg, --brand-primary}` contrast ≥ 4.5:1 in both schemes.
- Consumer components MUST NOT hardcode colors outside this palette for any primary/accent/surface role; neutrals for e.g. shadows are permitted.

## 2. MkDocs Material palette (docs)

Declared under `theme.palette` in `docs/mkdocs.yml`. Two entries: one `scheme: default` (light), one `scheme: slate` (dark).

```yaml
theme:
  name: material
  logo: assets/brand/logo-header.png
  favicon: assets/brand/favicon.ico
  palette:
    - scheme: default
      primary: <material-named-color-nearest-brand-primary>
      accent: <material-named-color-nearest-brand-accent>
      toggle: { icon: material/brightness-7, name: Switch to dark mode }
    - scheme: slate
      primary: <same or dark-mode variant>
      accent: <same or dark-mode variant>
      toggle: { icon: material/brightness-4, name: Switch to light mode }
```

**Contract rules**:
- If no Material-named color is within ΔE ≤ ~12 of `--brand-primary`, fall back to setting `--md-primary-fg-color` (and `--md-accent-fg-color`) in `docs/docs/assets/extra.css` and registering it under `extra_css:` in `mkdocs.yml`.
- `theme.logo` and `theme.favicon` MUST point to files under `docs/docs/assets/brand/` so they ship with `mkdocs build`.

## 3. HTML `<head>` references (frontend)

`frontend/src/index.html` MUST declare the following in `<head>`:

```html
<link rel="icon" type="image/x-icon" href="./assets/brand/favicon.ico" />
<link rel="icon" type="image/png" sizes="192x192" href="./assets/brand/logo-192.png" />
<link rel="icon" type="image/png" sizes="512x512" href="./assets/brand/logo-512.png" />
<link rel="apple-touch-icon" href="./assets/brand/logo-192.png" />
```

The header branding MUST render `<img src="./assets/brand/logo-header.png" alt="Chart-Monitor" class="brand-logo" />` in place of the current `<div class="logo">CM</div>` (two occurrences at `index.html:26` and `index.html:114`).

## 4. Icon contract

| UI element | Icon | Source | Delivery |
|---|---|---|---|
| Sync button (top of sidebar) | `git-branch` (Lucide) | https://lucide.dev/icons/git-branch | Inline `<svg>` in `index.html` or injected by `app.js` |
| Refresh buttons (all) | `refresh-cw` (Lucide) | https://lucide.dev/icons/refresh-cw | Inline `<svg>`, `stroke="currentColor"` so it inherits theme colors |

**Contract rules**:
- Icons use `stroke="currentColor"` and `fill="none"` so a single definition styles correctly in both themes.
- Icon SVGs MUST NOT reference external URLs at runtime (CSP + offline).
- The GitHub octocat mark MUST NOT appear on the sync button (FR-011).
