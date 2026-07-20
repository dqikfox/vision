## 2026-07-20 - [Accessible Non-Semantic Elements]
**Learning:** In strict layout scenarios, interactive elements are sometimes implemented as non-semantic tags (like `<span>`) to avoid layout breakage that would occur by converting them to `<button>`.
**Action:** Instead of converting them to `<button>` which might break layout constraints, add `role="button"`, `tabindex="0"`, `aria-label`, and an `onkeydown` handler supporting Enter and Space keys (with `event.preventDefault()` for Space to prevent page scrolling) to ensure full keyboard and screen reader accessibility.
