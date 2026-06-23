## 2024-11-06 - Semantic HTML and Aria-labels for Icon-Only Buttons
**Learning:** Found a pattern of missing aria-labels on icon-only buttons in the UI, and the use of non-semantic tags (`<div>`, `<span>`) for clickable action elements instead of native `<button>` tags. This creates significant accessibility barriers for screen reader users and keyboard navigation.
**Action:** Always verify that interactive elements use semantic HTML (e.g., `<button>`) and ensure icon-only buttons include descriptive `aria-label` attributes.
