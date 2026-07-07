
## 2024-07-07 - Missing ARIA labels on Icon-only buttons
**Learning:** Found multiple icon-only buttons missing `aria-label`s, particularly within UI modals and corner menus. This leads to poor screen reader accessibility.
**Action:** Always ensure any `<button>` with only an icon (or an emoji, SVG, etc.) has a descriptive `aria-label` attribute, e.g. `aria-label="Close modal"`.
