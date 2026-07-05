## 2024-07-04 - Accessibility improvements for live chat UI
**Learning:** Adding ARIA labels to icon-only buttons improves accessibility for screen readers. Some icon buttons in `live_chat_ui.html` lack `aria-label`s.
**Action:** Always verify all icon-only interactive elements contain screen-reader friendly `aria-label` tags, and ensure custom modals have semantic attributes (`role="dialog"`, `aria-modal="true"`) and an accessible close button.
