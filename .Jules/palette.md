## 2025-02-12 - Keyboard Accessibility and Semantic Modals
**Learning:** Found that custom modals lacked standard WAI-ARIA keyboard accessibility features (specifically `Escape` key support to close) and used non-semantic tags or buttons missing explicit `aria-label`s for the close actions. This pattern disrupts users who rely on screen readers or keyboard navigation.
**Action:** Always bind `keydown` listeners to the document for `Escape` to close `.open` modals. Ensure modal close triggers are semantic `<button>` tags accompanied by explicit `aria-label="Close"`.
