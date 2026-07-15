## 2024-07-15 - Keyboard Accessibility on Non-Semantic Elements
**Learning:** In legacy layouts, interactive buttons are sometimes built using `<div>` or `<span>` tags. Converting these to `<button>` can break strict CSS styling (like `clip-path` or specific borders) unexpectedly.
**Action:** Instead of converting them, apply `role="button"`, `tabindex="0"`, `aria-label`, and an `onkeydown` handler for Enter/Space keys (including `e.preventDefault()` for Space to prevent page scroll) to make them fully keyboard accessible without risking layout regressions.

## 2024-07-15 - Top-Level Escape Key Modal Dismissal
**Learning:** Adding `Escape` key handlers directly inline to modal trigger elements can cause focus management issues or fail to capture the event if focus moves inside the modal.
**Action:** Use a top-level `window.addEventListener('keydown', ...)` capturing the `Escape` key to centralize modal dismissal. When closing programmatically, always invoke the component's native teardown functions (like `closePicker()`) rather than directly manipulating class lists (`.classList.remove('open')`) to preserve internal state logic.
