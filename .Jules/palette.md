## 2025-07-21 - Global Escape Key Modal Dismissal
**Learning:** Custom modals (screenshot, model picker, system map) built without native `<dialog>` elements in `live_chat_ui.html` lack keyboard accessibility for dismissal (e.g., using the Escape key), forcing users to rely on mouse clicks to close them.
**Action:** Attached a global 'keydown' event listener for the Escape key at the top level to programmatically close open custom modals by invoking their native close functions or manipulating CSS classes, adhering to the requirement for top-level global listeners.
