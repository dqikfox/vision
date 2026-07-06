## 2024-07-06 - Modal Accessibility Standards
**Learning:** Custom modals (screenshot viewer, model picker, system map) lacked standard accessibility attributes and keyboard interactions. Screen readers could not easily identify them as dialogs, and users couldn't dismiss them with the Escape key.
**Action:** When implementing custom modals/overlays, always include `role="dialog"` and `aria-modal="true"`, use semantic `<button>` tags with `aria-label`s for close actions, and support `Escape` key dismissal to adhere to established accessibility patterns.
