## 2024-05-18 - Making interactive non-semantic divs accessible without breaking constraints
**Learning:** When improving accessibility for existing non-semantic interactive elements (`div` or `span`) under strict CSS constraints, converting them to `<button>` tags can sometimes break the layout.
**Action:** Instead, add `role="button"`, `tabindex="0"`, `aria-label`s, and `onkeydown` event handlers for keyboard activation (Enter and Space keys). Be sure to include `event.preventDefault()` specifically for the Space key handler to prevent unwanted default browser behaviors like page scrolling.
