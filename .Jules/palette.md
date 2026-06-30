## 2026-06-29 - Accessible Custom Modals
**Learning:** Custom UI overlays/modals require explicit semantic attributes (`role="dialog"`, `aria-modal="true"`, `aria-label`) and global keyboard event listeners (like dismissing via `Escape` key) to be properly interpreted by screen readers and usable by keyboard-only users.
**Action:** Always add dialog semantics to custom modals and ensure `Escape` key dismissal is bound globally for overlays across the application.
