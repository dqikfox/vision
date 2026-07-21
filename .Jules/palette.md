## 2024-07-18 - Escape Key Accessibility for Modals
**Learning:** Closing modals with the Escape key is an expected keyboard interaction that significantly improves UX/a11y but requires a global keydown listener since non-semantic UI overlays often don't trap focus. Using a top-level listener allows integration with existing `closePicker()` and similar logic.
**Action:** Always implement global Escape key listeners for custom modal/overlay implementations, delegating to native close functions to maintain state rather than simply manipulating DOM classes manually.
