## 2024-05-19 - Modal Keyboard Accessibility
**Learning:** Adding `Escape` key listeners to modals and explicit `role="dialog"` attributes makes UI components significantly more intuitive and compliant for keyboard-only or screen-reader users, and is essential for robust state management compared to simply stripping CSS classes inline.
**Action:** Always implement global Escape key listeners that trigger native cleanup/close functions (e.g. `closeScreenshot()`) for new modals or overlays to ensure semantic correctness and reliable keyboard interactions.
