
## 2025-07-21 - Accessible Custom Modals and Keyboard Events
**Learning:** Custom UI overlay panels (like `#pickerModal`, `#systemMapModal`, `#screenshotModal`) relied on manual JS `.classList.add('open')` for visibility without native `<dialog>` tags or accessibility features, making them inaccessible to screen readers and difficult to dismiss via keyboard.
**Action:** When working with custom modals in this repo, ensure they implement semantic attributes (`role="dialog"`, `aria-modal="true"`, `aria-label`), use accessible close triggers (e.g., `<div role="button">` with `aria-label`s and `onkeydown` handlers), and support `Escape` key dismissal via a global event listener at the top-level script, invoking their native tear-down/close functions.
