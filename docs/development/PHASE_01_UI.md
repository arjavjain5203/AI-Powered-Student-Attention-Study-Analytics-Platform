# Phase 01 — UI development and presentation

## Objective and status

Deliver a complete student-facing presentation. The owner regards this phase as completed. Source inspection confirms the seven screens. The Vite build and a headless Chrome browser smoke test pass. Screenshots at 375, 768, and 1440 CSS pixels were inspected; a clipped mobile chart axis was corrected. The demo requests no camera access.

## Scope and features

React 19, Vite, Tailwind CSS 4, Recharts 3; Dashboard, Study Session, Analytics, AI Coach, Goals & Challenges, Achievements, Profile & Settings. `src/main.jsx` holds navigation, screen views, and local state; `src/data.js` holds fixtures; `src/style.css` holds responsive styling. No backend, camera, or AI call is part of this phase.

## Execution order and relevant files

1. Preserve the current app and fixture contracts in `src/main.jsx` and `src/data.js`.
2. Verify each navigation button and session, analytics-period, goal, challenge, coach-chip, and settings control.
3. Check mobile drawer and layouts at 375, 768, and 1440 CSS pixels; record console and overflow results.
4. Keep demo labels visible until real data is available through the Phase 2 adapter.

## Dependencies, API, database, integration

Install from root `package.json`; run `npm run dev` and `npm run build`. No Phase 1 API or database changes. The Phase 2 frontend adapter must preserve the fixture-driven presentation path and distinguish recorded from demo values.

## Testing and acceptance

Build and browser smoke test pass. The test navigates all routes, exercises keyboard navigation and focus outline, checks no horizontal overflow at three widths, inspects console errors, and confirms no camera request in demo mode. A no-history analytics view is present. A physical-device visual review can still find issues that headless screenshots miss.

## Risks and checklist

- [x] Seven presentation screens and reusable shell exist.
- [x] Shared mock values and simulation/privacy labels exist.
- [x] Production build passes.
- [x] Browser interaction and responsive visual QA recorded in `tests/browser-smoke.mjs` and ignored `.local/browser-qa/` screenshots.
- [x] Console and overflow inspection recorded.

Dependency on previous phases: none. Large bundle size is a known optimization risk, not a failed build.

