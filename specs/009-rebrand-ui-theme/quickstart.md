# Quickstart — Rebrand UI & Theme Refresh

How to regenerate, preview, and verify the rebrand locally.

## Prerequisites

- Python 3.11+ with `Pillow` available (backend environment already provides this).
- Node/npm not required (frontend is vanilla).
- MkDocs + `mkdocs-material` for the docs preview (already in the docs toolchain).

## 1. Regenerate brand assets

From repo root:

```bash
python scripts/generate-brand-assets.py
```

This reads `chart-monitor-logo.png` and writes:

- `frontend/src/assets/brand/favicon.ico` (multi-size 16/32/48)
- `frontend/src/assets/brand/logo-192.png`
- `frontend/src/assets/brand/logo-512.png`
- `frontend/src/assets/brand/logo-header.png`
- `docs/docs/assets/brand/favicon.ico` (copy)
- `docs/docs/assets/brand/logo-header.png` (copy)
- `specs/009-rebrand-ui-theme/brand-tokens.json` (extracted palette for review)

The script prints the extracted `--brand-primary`, `--brand-accent`, and each WCAG AA contrast ratio. **Eyeball the primary/accent before committing** — if the dominant hue was an undesired color, adjust the quantize params or supply `--hue-override` and rerun.

## 2. Apply tokens

- Paste the `:root` / `:root[data-theme="dark"]` block the script prints into `frontend/src/styles.css` (top of file, replacing any previous palette block marked with `/* brand-tokens:begin */ … /* brand-tokens:end */`).
- Update `docs/mkdocs.yml` `theme.palette.primary` / `.accent` to the nearest Material-named color (script prints a suggestion). If no color is within ΔE ≤ 12, add `extra_css: [assets/extra.css]` and copy the `--md-primary-fg-color` overrides the script prints into `docs/docs/assets/extra.css`.

## 3. Preview the app

Serve `frontend/src/` with any static server (e.g., `python -m http.server` from `frontend/src`). Then verify:

- Browser tab shows the new favicon.
- Header shows the new logo (no "CM" square).
- Sidebar is vertical, full height, with the sync button at the **top**, displaying the Lucide `git-branch` icon (not `↕`).
- Every refresh control shows the Lucide `refresh-cw` glyph.
- At 1920×1080 and 1440×900: **no outer page scrollbar**. Long chart lists scroll inside their containers only.
- At 1280, 1024, 768, 360 widths: the layout is responsive — sidebar collapses/stacks, content scrolls as one column, **no clipped controls**.
- Toggle light ↔ dark: colors shift, logo remains visible and legible.

## 4. Preview the docs

From `docs/`:

```bash
mkdocs serve --strict
```

Verify:

- Browser tab shows the new favicon.
- Docs header shows the new logo.
- Palette toggle between light and dark uses the brand palette.
- No `--strict` warnings introduced by the asset paths.

## 5. Accessibility pass

Run an automated contrast check (browser devtools "Issues" panel, or `axe` browser extension) on:

- App primary surface, in both themes.
- Docs landing page, in both themes.

**Acceptance**: no AA violations on body text or on the sync/refresh buttons.

## 6. Commit set

Once happy:

```
frontend/src/index.html
frontend/src/styles.css
frontend/src/app.js
frontend/src/assets/brand/*
docs/mkdocs.yml
docs/docs/assets/brand/*
docs/docs/assets/extra.css        # only if palette required CSS-var overrides
scripts/generate-brand-assets.py
```

Do **not** commit `site/` (MkDocs build output) or any intermediate previews.
