
## 2025-05-18 - Modal Accessibility Improvements
**Learning:** Adding semantic attributes (`role="dialog"`, `aria-modal="true"`) to custom modal divs, attaching a global Escape key event listener to invoke specific close functions, and making close div elements keyboard accessible (`role="button"`, `tabindex="0"`, `onkeydown`) significantly improves modal accessibility while respecting existing constraints.
**Action:** Always ensure modals have `role="dialog"`, a way to be dismissed via `Escape`, and that their close elements have keyboard support and ARIA labels. When adding global Escape listeners, use DOMContentLoaded and invoke native component teardown functions rather than manually manipulating CSS classes where applicable.
