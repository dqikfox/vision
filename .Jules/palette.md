## 2024-05-18 - Missing `aria-label`s on critical icon buttons
**Learning:** Found several icon-only buttons (screenshot, memory add, modal close) that were completely invisible/unusable to screen reader users because they lacked textual descriptions.
**Action:** Added `aria-label` attributes to these buttons (e.g., `aria-label="Take screenshot"`) to provide clear semantic meaning for assistive technologies, without altering the visual design. Always verify icon-only interactive elements have an accessible name.
