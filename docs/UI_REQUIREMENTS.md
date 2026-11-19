# UI Requirements and Screen Specification

**Current implementation update (2026-11-18):** The Phase 1 demo requirements below are historical acceptance criteria. The current interface opens directly at sign-in, uses account data on Dashboard, Session, Analytics, and Settings, and labels Coach, Goals, and Achievements as previews. Timed sessions require an explicit camera start and show a live, server-backed timer. Provisional camera events pause it and offer false-alarm feedback with optional, explicitly shared short video. The camera permission click remains explicit.

## 1. Global application shell

### Desktop layout
- Persistent left sidebar with product logo/name and primary navigation.
- Main content area with page title, short contextual subtitle, and user/profile area.
- Consistent spacing, card radius, typography, chart styling, and status indicators.
- Sidebar may collapse if the existing project design supports it.

### Navigation
- Dashboard
- Study Session
- Analytics
- AI Study Coach
- Goals & Challenges
- Achievements
- Profile / Settings

All primary navigation items must work. Do not create dead links.

### Responsive behavior
- Desktop: full sidebar and multi-column cards.
- Tablet: compact/collapsible navigation and fewer columns.
- Mobile: accessible menu/drawer, stacked cards, charts that remain readable, and controls with touch-friendly targets.

## 2. Dashboard

Purpose: Give the student an at-a-glance summary and a clear path to start studying.

Required content:
- Greeting and date.
- Primary “Start Study Session” action.
- KPI cards: estimated attention, focused time, distraction count, current streak.
- Attention trend chart for today.
- Study activity chart for the week.
- Personal baseline comparison.
- AI coach insight preview.
- Daily goal progress.
- Recent sessions list.
- Privacy/status note explaining that the displayed dashboard uses demo data in presentation mode.

Interactions:
- Start Study Session opens the session screen or setup flow.
- Analytics cards/links navigate to Analytics.
- AI insight action opens AI Study Coach.
- Recent session item opens session details if that view is implemented.

## 3. Study Session

Purpose: Demonstrate the intended active study experience.

Session setup:
- Subject selection or text field.
- Optional topic field.
- Session duration/goal selection if practical.
- Start action.

Active session view:
- Subject and topic.
- Elapsed timer (can be simulated or locally timed).
- Estimated attention score with clear demo/simulation label.
- Focused time and distraction count.
- Attention progress visualization.
- Recent event/activity list.
- Pause/resume and end-session controls.
- Camera status panel that is explicitly a UI simulation unless real local camera processing has been implemented and approved.

Important:
- Do not request camera permission merely to display the UI.
- If a camera preview is not implemented, use a neutral placeholder/illustration and label it “Camera monitoring preview (demo)” or equivalent.
- Do not imply that a phone, gaze, or desk-presence detector is working when it is mock data.

## 4. Analytics

Provide period switching for Daily, Weekly, and Monthly views.

Metrics:
- Total study time.
- Estimated focused time.
- Average estimated attention.
- Distraction count.
- Focus efficiency.
- Number of sessions.
- Longest focus session.
- Best-performing time window (only as demo data until calculated from real history).

Charts:
- Estimated attention over time.
- Focused vs. non-focused time.
- Study duration by day.
- Distraction categories.
- Optional subject-wise study distribution.

Include sensible empty states for a new student with no history.

## 5. Personal baseline

Show:
- Personal baseline estimate.
- Current period average.
- Difference from baseline.
- Trend indicator.
- Explanation that baseline is meaningful only after enough valid sessions have been collected.

For presentation, use sample values and label them as demo data. Avoid claiming statistical confidence.

## 6. AI Study Coach

Show:
- A welcome/summary message.
- A few structured insights based on the demo analytics.
- Recommended session length.
- Suggested study window.
- Break suggestion.
- “Why this recommendation?” explanation.
- Example prompt chips or a simple input box if useful.

The presentation version may use predefined mock responses. Do not call a real LLM API in Phase 1. Mark generated-looking content as sample/demo insight.

Recommendations must be framed as suggestions, not medical or psychological conclusions.

## 7. Goals & Challenges

Show:
- Daily study-time goal.
- Progress bar and remaining time.
- Weekly goal.
- Daily challenge cards.
- Completion states.
- XP reward preview.

Interactions:
- Allow toggling a mock challenge as complete.
- Allow adjusting a goal locally if feasible.
- Keep values in local component state or local storage only if appropriate; no backend persistence is expected.

## 8. Achievements / Gamification

Show:
- Current level and XP progress to next level.
- Current focus streak and best streak.
- Badge grid with earned and locked states.
- Personal records (longest session, best estimated attention, most focused day).
- Recent reward/XP activity.
- A clear distinction between earned achievements and demo examples.

Suggested badge examples:
- First Focus: complete first study session.
- Week Warrior: achieve a seven-day goal streak.
- Deep Work: complete a long session above a chosen estimated-attention threshold.
- Goal Crusher: meet daily goal on multiple days.
- Comeback: improve against own baseline.

Avoid rewarding mere elapsed timer time as proof of attention.

## 9. Profile / Settings

Show:
- Profile details (demo user).
- Daily goal preference.
- Preferred session length.
- Notification preference (UI only).
- Privacy settings explanation.
- Webcam permission is opt-in in the eventual product.
- Raw footage is not stored by default.
- Clear demo-mode status.

## 10. Reusable UI components

Build reusable components where appropriate:
- AppShell / Sidebar / Header.
- PageHeader.
- StatCard.
- ChartCard.
- ProgressBar.
- BadgeCard.
- ChallengeCard.
- SessionTimer.
- AttentionScore.
- EmptyState.
- DemoDataLabel.
- PrivacyNotice.

Use the existing project's component conventions if already present.

## 11. UI quality requirements

- Strong visual hierarchy and consistent spacing.
- Accessible contrast and keyboard-operable controls.
- Visible focus states.
- Meaningful hover/active/disabled states.
- Avoid excessive gradients, clutter, and decorative charts without meaning.
- Use consistent units and date/time formatting.
- No horizontal overflow at common viewport widths.
- Charts must have readable axes, legends, and tooltips.
- Use a coherent mock-data source rather than inventing unrelated values in each component.
