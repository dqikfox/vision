## 2024-05-19 - Accessible Modals with Escape Support
**Learning:** Custom UI modals missing explicit semantic `role="dialog"` and `aria-modal="true"` attributes degrade the screen reader experience. Keyboard accessibility is heavily lacking if overlays do not dismiss on Escape key presses, leading to user lock-in.
**Action:** Implemented semantic dialog attributes, explicit ARIA labels on all modal close buttons, and a global document-level keydown event listener to close active overlays when Escape is hit. This pattern will be rigorously checked for all future modal creation.
