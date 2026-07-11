## 2024-07-11 - Missing ARIA Labels on Icon-Only Buttons
**Learning:** Icon-only buttons with just a `title` attribute are insufficient for accessibility. Screen readers rely heavily on `aria-label` for clear navigation, especially when the visual content is purely decorative or semantic like an emoji.
**Action:** When adding icon-only buttons, I must always include `aria-label` alongside the `title` attribute for tooltips.
