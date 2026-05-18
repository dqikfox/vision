---
applyTo: "**/*.html"
---

# Vision HTML/Web UI Instructions

## Design Philosophy
Vision's web interfaces use a **futuristic, accessible dark theme** inspired by sci-fi operator terminals. All UIs should be:
- Modern and visually striking
- Fully accessible (WCAG AA compliant)
- Keyboard navigable
- Screen reader friendly
- Mobile responsive

## Color Palette (Consistent Across UIs)
Use these CSS custom properties:
```css
:root {
  /* Backgrounds */
  --bg: #020209;
  --bg2: #05050f;
  --panel-bg: rgba(4,4,18,.88);
  --panel-border: rgba(124,58,237,.25);

  /* Accent Colors */
  --p: #7c3aed;      /* Purple primary */
  --p2: #a78bfa;     /* Purple light */
  --c: #06b6d4;      /* Cyan */
  --c2: #38bdf8;     /* Cyan light */
  --g: #10b981;      /* Green */
  --g2: #34d399;     /* Green light */
  --gold: #f59e0b;   /* Orange/Gold */
  --r: #ef4444;      /* Red */

  /* Text */
  --tx: #d4d4f0;     /* Primary text */
  --tx2: #7878a8;    /* Dim text */

  /* Fonts */
  --font-ui: 'Orbitron', monospace;
  --font-mono: 'Share Tech Mono', monospace;
}
```

## Typography
- Use **Orbitron** font for headers, titles, UI labels (bold, futuristic)
- Use **Share Tech Mono** or **Consolas** for monospace text, code, data
- Minimum font size: 12px for accessibility
- Use `clamp()` for responsive sizing: `font-size: clamp(14px, 2vw, 18px);`

## Accessibility Requirements

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Provide visible focus indicators: `outline: 2px solid var(--p);`
- Use `tabindex` appropriately
- Support common shortcuts (Escape to close, Enter to submit, etc.)

### Screen Reader Support
- Use semantic HTML5 elements (`<nav>`, `<main>`, `<article>`, `<button>`)
- Add `aria-label` to icon-only buttons
- Use `aria-live` regions for dynamic updates
- Provide `alt` text for all images

### Color Contrast
- Ensure WCAG AA compliance (4.5:1 for normal text, 3:1 for large text)
- Don't rely solely on color to convey information
- Provide text labels for color-coded states

Example:
```html
<button aria-label="Mute microphone" class="mute-btn">
  <span class="icon">🎙</span>
  <span class="label">Mute</span>
</button>
```

## WebSocket Integration
Vision UIs connect to backend via WebSocket at `ws://localhost:8765/ws`.

Connection pattern:
```javascript
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onopen = () => {
  console.log('Connected to Vision Core');
  // Request initial state
  ws.send(JSON.stringify({ type: 'get_state' }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch(msg.type) {
    case 'init':
      updateProviders(msg);
      break;
    case 'state':
      updateState(msg.state);
      break;
    case 'volume':
      updateVUMeter(msg.level);
      break;
  }
};

ws.onerror = (err) => {
  console.error('WebSocket error:', err);
  showConnectionError();
};

ws.onclose = () => {
  console.log('Disconnected from Vision Core');
  attemptReconnect();
};
```

## Visual Effects

### Scan Lines (Retro CRT Effect)
```css
body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    to bottom,
    rgba(0,0,20,.05) 0,
    rgba(0,0,20,.05) 1px,
    transparent 1px,
    transparent 3px
  );
  animation: scanPan 12s linear infinite;
}
```

### Glows and Shadows
```css
.active-element {
  box-shadow: 
    0 0 20px rgba(124,58,237,.4),
    0 0 40px rgba(124,58,237,.2);
  filter: drop-shadow(0 0 10px var(--p));
}
```

### Smooth Transitions
```css
.element {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

## Canvas Visualizations
For orb visualizations and VU meters, use HTML5 Canvas with `requestAnimationFrame`:
```javascript
function drawOrb() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw orb with gradient
  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
  gradient.addColorStop(0, 'rgba(124,58,237,0.8)');
  gradient.addColorStop(1, 'rgba(124,58,237,0)');

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  requestAnimationFrame(drawOrb);
}
```

## Mobile Responsiveness
- Use CSS Grid and Flexbox for layout
- Mobile-first approach with min-width media queries
- Touch-friendly hit targets (minimum 44x44px)
- Disable double-tap zoom on buttons: `touch-action: manipulation;`

Example:
```css
.button {
  min-width: 44px;
  min-height: 44px;
  touch-action: manipulation;
}

@media (min-width: 768px) {
  .container {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}
```

## State Management
Use data attributes for state-driven styling:
```html
<div class="status-indicator" data-state="listening">
  <span class="text">Listening...</span>
</div>
```

```css
.status-indicator[data-state="idle"] { color: var(--tx2); }
.status-indicator[data-state="listening"] { color: var(--c2); }
.status-indicator[data-state="thinking"] { color: var(--gold); }
.status-indicator[data-state="speaking"] { color: var(--g2); }
```

## Performance
- Minimize reflows: batch DOM updates
- Use CSS transforms over position changes
- Debounce WebSocket message handlers
- Lazy load heavy resources
- Use `will-change` sparingly for GPU acceleration

## Testing
- Test with keyboard only (no mouse)
- Test with Windows Narrator screen reader
- Test on mobile devices (iOS Safari, Android Chrome)
- Verify WebSocket reconnection on network loss
- Check console for errors (should be zero)
