# Phase 0 Research — Rebrand UI & Theme Refresh

## R1. Git & Refresh icon source

**Decision**: Use Lucide icons inlined as SVG markup — specifically `git-branch` for the sync button (vendor-neutral Git glyph) and `refresh-cw` for refresh controls.

**Rationale**:
- Lucide is MIT-licensed, framework-free, ships as plain SVG, and pairs well with vanilla JS (no runtime needed — we paste the SVG into `index.html` or template it in `app.js`).
- `git-branch` is a generic branching mark — explicitly not GitHub-specific, satisfying FR-011.
- `refresh-cw` is the standard circular-arrow refresh glyph recognized across modern UIs.
- Inline SVG avoids an icon-font HTTP request, respects CSP, and allows `currentColor` to inherit theme colors cleanly.

**Alternatives considered**:
- **Font Awesome**: requires either a runtime JS kit or a large CSS/font payload; overkill for two icons.
- **Material Symbols**: great catalog but adds a webfont dependency; inline SVG is leaner.
- **Hand-drawn SVGs**: time sink with no upside for common glyphs.
- **Heroicons**: viable, but `git-branch` in Heroicons is less neutral than Lucide's variant.

## R2. Asset derivation pipeline

**Decision**: Derive the asset set from `chart-monitor-logo.png` using Pillow in a small one-shot Python script checked into `scripts/generate-brand-assets.py` (or a `make brand-assets` target). Outputs: `favicon.ico` (16/32/48), `logo-192.png`, `logo-512.png`, `logo-header.png` (~96px tall for 2× header at 48 CSS px). Run once and commit the outputs; rerun whenever the source logo changes.

**Rationale**:
- Pillow is already available in the Python-heavy backend toolchain; no new language added.
- Committed outputs mean CI/runtime don't regenerate on every build (faster serve, deterministic).
- A single script keeps the regeneration step documented and reproducible.

**Alternatives considered**:
- **ImageMagick CLI**: works but adds an OS-level dependency many contributors won't have on Windows.
- **Runtime resizing in the browser**: introduces layout shift and wastes cycles.
- **Manual export from an image editor**: non-reproducible; rejected.

## R3. Primary brand color extraction

**Decision**: Sample the dominant non-neutral hue from `chart-monitor-logo.png` at generation time using Pillow's `Image.quantize(colors=8)` + filter out near-grayscale pixels (saturation < 0.15 or value extremes). Emit the top hue as `--brand-primary` and a complementary (hue + 30° split-complement) as `--brand-accent`. Surface the extracted hex values in `research.md`/quickstart so a human can approve them before palette commit.

**Rationale**:
- Deterministic, reproducible, and tied to the actual source image rather than guesswork.
- Lets the same script that produces image derivatives also produce the color tokens — one source of truth.
- Human gate on the output prevents picking an ugly complementary pair if the algorithm misfires.

**Alternatives considered**:
- **Hand-picked hex values by a designer**: higher quality, but no designer is in the loop for this feature.
- **`vibrant.js` in the browser at runtime**: runtime cost and inconsistent results per-browser.
- **Hardcoding `teal/blue/etc.`**: was explicitly rejected during clarification (Q3/A: sample from logo).

## R4. Full-height no-scroll layout strategy

**Decision**: Switch the top-level app shell to a `height: 100vh; display: grid` layout with three rows (header, main, optional footer) and a two-column main (`sidebar | content`). Internal scrollable regions (`.sidebar-nav`, chart lists, tables) get `overflow: auto; min-height: 0` to scroll locally. Apply a media query at `max-width: 1440px` that switches the grid to stacked rows (header → sidebar collapses to top-strip or drawer → content scrolls as a single column).

**Rationale**:
- CSS Grid with `100vh` root is the simplest modern way to achieve a no-outer-scroll desktop shell.
- `min-height: 0` on flex/grid children is the canonical fix for nested scrolling regions.
- A single `1440px` breakpoint matches the clarified threshold; no need for a cascade of breakpoints at this feature's scope.

**Alternatives considered**:
- **Flexbox column with `flex: 1` regions**: works but grid gives cleaner naming of named areas and handles the two-column main more readably.
- **JS-driven height calculation**: brittle, poor for resize events; rejected.

## R5. MkDocs Material palette integration

**Decision**: Keep the existing two-scheme palette structure in `docs/mkdocs.yml` but add explicit `primary:` and `accent:` keys derived from R3's extracted hex (using Material's named-color slot that's closest to the extracted hue, or `custom` via extra CSS if none is close enough). Reference the brand logo via `theme.logo: assets/brand/logo-header.png` and `theme.favicon: assets/brand/favicon.ico`.

**Rationale**:
- Material's palette system is config-driven — matches the Q2 clarification ("configure, don't override").
- Using the nearest named color avoids a custom-CSS escape hatch when the extracted hue is close to a standard Material swatch.
- When the hue doesn't match a named color closely enough, a minimal `extra.css` with `--md-primary-fg-color` CSS-variable overrides keeps the footprint small.

**Alternatives considered**:
- **Full Material theme override**: rejected per Q2 clarification (over-scoped).
- **Keep defaults (indigo/indigo)**: fails FR-004 (colors must harmonize with the logo).

## R6. Accessibility contrast verification

**Decision**: After the palette is emitted, run a WCAG AA contrast check on the `{text, primary}` and `{text, surface}` pairs in both schemes using a simple luminance-ratio helper. If any pair fails AA, darken/lighten the offending token until it passes and regenerate. Record pass/fail in `quickstart.md`.

**Rationale**:
- FR-005 mandates WCAG AA; we need a repeatable check, not a one-shot manual audit.
- Contrast-ratio computation is a <20-line helper; doesn't justify a library dep.

**Alternatives considered**:
- **axe-core in CI**: useful long-term but out of scope for this single feature.
- **Trust the Material theme defaults**: Material's defaults are AA against its defaults, not against our overridden primary.

## Open items

None — all five clarification answers from Session 2026-04-15 are reflected above; no `NEEDS CLARIFICATION` markers remain.
