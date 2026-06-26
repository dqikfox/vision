## 2024-06-26 - Missing aria-labels on icon buttons
**Learning:** Found multiple icon-only buttons (`requestScreen()` and `openRPanelTab()`) in `live_chat_ui.html` that have `title` attributes but lack `aria-label` attributes. This is a common accessibility issue where screen readers may not read the title properly or the title might not be fully descriptive for assistive tech.
**Action:** Always verify that icon-only buttons have explicit `aria-label` attributes for screen readers in addition to `title` tooltips for sighted users.
