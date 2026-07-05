## 2024-07-05 - Initialized Palette Journal

## 2024-07-05 - Added Escape key support to close modals
**Learning:** Users naturally expect the Escape key to close modals and overlays. Adding this support significantly improves keyboard accessibility and overall user experience, as they don't have to precisely click a small close button.
**Action:** When creating new custom modals or overlays, always ensure they can be dismissed via the Escape key, using a global event listener or by focusing the modal and handling the keydown event.
