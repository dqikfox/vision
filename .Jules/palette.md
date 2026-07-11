## 2023-11-09 - Ensure Semantic Buttons for Accessibility
**Learning:** Found several non-semantic elements (`<span>` and `<div>`) used as interactive icon buttons or close triggers, and icon-only buttons missing ARIA labels. This impairs screen reader experience and keyboard accessibility.
**Action:** Always use semantic `<button>` tags with explicit `aria-label` attributes for icon-only interactions. When converting `<span>` or `<div>` to `<button>`, ensure CSS resets (like `border:none; background:none; padding:0;`) are applied to avoid breaking the existing layout.
