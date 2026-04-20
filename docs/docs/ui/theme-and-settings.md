# Theme & Settings

Chart-Monitor supports light and dark display modes.

---

## Toggling the theme

Click the **🌙 Dark** / **☀️ Light** button in the header to switch between dark and light mode. The preference is saved to browser local storage and persists across page reloads and sessions.

```
[Docs]  [🌙 Dark]  ● 12:34:56
```

---

## Theme persistence

The selected theme is stored in the browser's `localStorage` under the key `theme` with values `"dark"` or `"light"`.

- On page load, Chart-Monitor reads this value and applies the matching theme
- If no preference is stored, the OS/browser `prefers-color-scheme` setting is used as the default

---

## Theme on the docs page

The Chart-Monitor documentation page (`/docs`) uses the **MkDocs Material** theme's built-in light/dark toggle. It reads the OS `prefers-color-scheme` preference on first visit.

!!! info "Independent toggles"
    The docs page and the main app each have their own theme toggle. Changes in one do not automatically sync to the other.

---

## Accessibility

All UI elements — table cells, buttons, banners, and the column filter menu — are designed to meet adequate contrast ratios in both light and dark themes. If you encounter a contrast issue, please open a bug report.
