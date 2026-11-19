# Master Context

## Project identity

**Name:** AI-Powered Student Attention & Study Analytics Platform

**Product concept:** A privacy-first AI study companion that helps students understand how they use study time, estimates attention from observable signals, tracks distraction patterns, identifies personal study habits, and provides actionable recommendations.

**Current implementation update (2026-11-18):** The Phase 1 presentation requirements below describe the original UI milestone. The app now opens in a backend-connected workspace. Timed sessions require the student to explicitly start camera monitoring; camera alerts provisionally pause elapsed session time and can be reported as false alarms. Only a clip explicitly shared after a false alarm is stored, for seven days. This product choice does not validate visual attention or focused time.

## Problem

Traditional study timers measure elapsed time but cannot explain how much of a session appeared focused, when attention signals changed, or which habits recur. Students need more useful feedback than a total-duration number.

## Product goal

Move from basic time tracking to study-behavior analytics:
- Track study sessions and subjects/topics.
- Estimate attention from observable behavioral signals.
- Identify potential distraction events.
- Separate elapsed study time from estimated focused time.
- Show daily, weekly, and monthly trends.
- Learn an individual baseline from accumulated data.
- Provide personalized recommendations.
- Encourage consistency with goals and gamification.
- Protect privacy; raw webcam footage is not stored by default.

## Target user

A student who studies independently and wants to understand their study habits, improve consistency, and make better use of focused study periods.

## Immediate delivery target

The next presentation requires the **complete UI**. The active work is frontend UI development only. The interface should demonstrate the intended product using realistic mock data. Backend, database, real computer vision, ML, and GenAI execution are future phases.

## Core product areas

1. Dashboard overview.
2. Study session controls and live-session presentation.
3. Attention and distraction presentation.
4. Daily/weekly/monthly analytics.
5. Personal attention baseline and trends.
6. AI Study Coach and recommendations.
7. Goals and daily challenges.
8. Gamification: XP, levels, streaks, badges, personal records.
9. Profile and privacy/settings.

## Accuracy and trust requirements

- Use the phrase **estimated attention** rather than claiming to measure true mental focus.
- Looking at a screen is not proof of understanding or concentration.
- Face absence, head orientation, and gaze estimates are imperfect behavioral signals.
- Do not present mock values as real measured results.
- In the UI demo, use a subtle “Demo data” or “Simulated” label on screens or cards whose values are fabricated.
- Webcam use must be opt-in in the eventual product.
- Raw webcam frames/video must not be stored by default.
- Do not send raw webcam footage to a GenAI model.

## Agreed technology direction

### Frontend
- React
- Tailwind CSS
- Recharts
- Axios (for future API integration)

### Future backend
- Python
- FastAPI
- JWT authentication
- Pydantic
- MongoDB / MongoDB Atlas

### Future computer vision
- OpenCV
- MediaPipe
- Optional YOLO for object detection

### Future ML and GenAI
- Scikit-learn
- Optional XGBoost / PyTorch if justified by data and evaluation
- One provider initially: Gemini or OpenAI API

### Future deployment
- Docker
- Vercel for frontend
- Render or Railway for backend

These are intended technologies, not verified installed dependencies. Codex must inspect the repository and use its existing setup where possible.

## Implementation status

This documentation is a requirements handoff, not evidence that the application already exists. No source code was supplied for inspection. Treat every feature as planned unless verified in the actual repository.

## Four workstreams for the eventual full project

1. Frontend & UX.
2. Backend & data.
3. Computer vision & attention estimation.
4. ML, GenAI & gamification logic.

During the current presentation milestone, only workstream 1 is in scope. Workstreams 2–4 may supply mock-data contracts, but must not be implemented as production services yet.
