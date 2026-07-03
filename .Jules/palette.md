
## 2026-07-03 - Accessible Keyboard-navigable Modals
**Learning:** Implementing custom modals requires explicit semantic markup (role='dialog', aria-modal='true') and keyboard handlers (Esc to close) for a complete accessibility experience. Relying on default mouse click events traps keyboard users and screen readers, isolating them from interactions.
**Action:** Always pair visual modal implementation with proper ARIA attributes, semantic tags (button vs div for dismissals), and global 'keydown' Escape listeners to assure unified keyboard and accessibility support.
