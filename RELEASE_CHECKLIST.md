# AgentForge v1.0 Release Checklist

## 1. Functional Testing
- [x] **Node Creation**: Drag-and-drop from palette works smoothly.
- [x] **Connections**: Linking agents (Source -> Target) works.
- [x] **Interaction**: Agents can be selected, edited, and deleted.
- [x] **Execution**: Workflow runs with real-time feedback (simulated or API).
- [x] **Persistence**: Workflows auto-save to LocalStorage and restore on reload.

## 2. Technical Stability
- [x] **Console Errors**: Clean console during normal operation.
- [x] **Performance**:
    - [x] Canvas handles 30+ nodes > 60fps.
    - [x] Memory usage stable during long sessions.
- [x] **Accessibility**:
    - [x] ARIA labels present on Zoom, Theme, and FAB controls.
    - [x] Contrast ratios meet WCAG AA standards (Indigo/Gray).
    - [x] Keyboard shortcuts (Delete, Ctrl+Z, Ctrl+Y, Ctrl+S) functioning.

## 3. User Experience
- [x] **Onboarding**: "Drag agents to build" empty state prompt is visible.
- [x] **Feedback**: Toast notifications for errors, success, and info.
- [x] **Visual Polish**:
    - [x] Glassmorphism prompt bar.
    - [x] Smooth transitions and hover states.
    - [x] Dark Mode toggle works instantly.

## 4. Known Issues (Medium/Low Severity)
- **Node Overlap**: Dropped nodes do not strictly avoid overlapping existing nodes (Manual adjustment required).
- **Mobile Layout**: Canvas controls stack vertically; complex graphs are better viewed on Desktop.
- **Git Sync**: Occasional network timeouts when sinking large histories (User environment specific).

## 5. Deployment
- [ ] **Live Demo**: Deployed to GitHub Pages (or Vercel/Netlify).
- [ ] **Assets**: Hero screenshot recorded.
