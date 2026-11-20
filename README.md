# FocusAtlas — Student Study Analytics

FocusAtlas is a responsive study companion for planning sessions and reviewing study history. Students sign in to their own account, create a study session, and see a clock that advances live while camera monitoring is running. The clock pauses when they pause, stop monitoring, leave the study screen, or receive a provisional camera alert. Dashboard, Analytics, Study Session, and Settings use the local FastAPI and MongoDB backend. AI Coach, Goals, and Achievements remain clearly labeled previews.

The camera prototype checks face presence, coarse head orientation, and phones visible in the camera frame. Its index and alerts are **provisional**: looking away, leaving the frame, or having a phone visible does not prove distraction. The clock measures a monitored session interval, not a validated focused-time estimate or a student's mental state. Analytics now show a personal provisional visual-signal baseline and study patterns when enough recorded history exists. Estimated focused time and validated visual attention remain unavailable.

## Run locally

For a complete step-by-step checklist, accounts, expected behavior, and troubleshooting, see the [local testing guide](docs/development/TESTING_GUIDE.md).

Requires Node.js, Python, and a running local MongoDB Community Server. The project-local MongoDB can be installed from the [official Community Server ZIP](https://www.mongodb.com/try/download/community): place it at `.local/mongodb.zip`, run `python backend/scripts/install_local_mongo.py`, then keep `python backend/scripts/start_local_mongo.py` running in a terminal.

From the project root:

```powershell
python -m pip install -r backend/requirements.txt
python backend/scripts/setup_local_env.py
npm install
```

Once MongoDB is running, use another terminal to run `python backend/scripts/seed_presentation_accounts.py` from the project root.

Start the API and frontend in separate terminals:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
npm run dev
```

Open `http://localhost:5173`. If port 8000 is already in use, stop the older API process before starting the updated one. The frontend uses `http://127.0.0.1:8000` unless `VITE_API_BASE_URL` is set. `backend/.env` is ignored by Git; deployment uses environment variables for `MONGO_URI`, `MONGO_DB`, `JWT_SECRET`, `CORS_ORIGINS`, and `REVIEW_ADMIN_TOKEN`.

In local development, the API accepts Vite on port 5173 from localhost, loopback, or a private-network address. Other origins require an explicit `CORS_ORIGINS` entry and API restart; deployed environments do not use the development-only LAN rule.

## Presentation accounts

The local-only seed script creates or updates these accounts. All use password **`StudyDemo123!`** by default. It resets only the existing `test@gmail.com` password and keeps that account's sessions. Any older unmonitored active test session is paused without adding time, so you can resume it with the camera or end it. Re-running the script refreshes the three fictional students' labeled sample history to keep it within the 30-day tracker window; it preserves their separately recorded sessions.

| Email | Student | Data |
| --- | --- | --- |
| `test@gmail.com` | Test Student | Your recorded sessions; no fabricated history is added |
| `maya.student@example.com` | Maya Sharma | Labeled sample study history |
| `arjun.student@example.com` | Arjun Mehta | Labeled sample study history |
| `zoya.student@example.com` | Zoya Khan | Labeled sample study history |

These credentials are for local presentations only. The seed script refuses a non-local MongoDB URI. Accounts remain isolated: signing in as one student does not reveal another student's sessions.

## Study sessions and privacy

Create a session, then click **Start camera and timer** and allow camera access. Setup time is excluded. The clock updates without a refresh and stops when monitoring stops. A provisional camera event pauses the timer and shows an alert. Choose **Review complete** or **False alarm**, then restart monitoring. Time spent paused stays excluded in either case. The alert can arrive after the behavior began, so the app does not claim to subtract an exact earlier distraction interval.

Only derived sample counts and warning categories are uploaded automatically. During monitoring, a short WebM segment remains in browser memory. After a false alarm, the student may preview it and explicitly agree to **Send clip and continue**. Otherwise, **Continue without clip** reports the false alarm without video. Submitted clips are limited to 5 MB, expire after seven days, can be deleted in Settings, and are available only through a restricted local review API. No raw footage is stored by default. Derived visual windows expire after 90 days and can also be deleted. The phone model downloads from Google's model host when monitoring starts; camera frames stay in the browser.

The Analytics screen groups actual active study intervals by local hour and weekday, shows session duration and subject history, and displays a provisional visual-signal baseline only after sufficient usable windows. The three fictional presentation accounts have labeled sample patterns; the test account has no fabricated history.

For local developer review, run `python backend/scripts/review_false_alarms.py` to list reports. Add `--download REPORT_ID` to save one student-shared clip under ignored `.local/review-clips/`. Delete downloaded copies when review ends; their local files are outside MongoDB's seven-day expiry.

## Tests and development status

Run `python -m pip install -r backend/requirements-dev.txt` and `python -m pytest -q` from `backend/`; run `npm test`, `npm run build`, and `npm run test:browser` from the project root. `python backend/scripts/run_real_mongo_check.py` runs the real-database integration test. Browser QA uses an isolated temporary database and synthetic camera, then removes the database. Its screenshots and report are under ignored `.local/browser-qa/`.

Phase 3 remains active until physical-camera and labeled-signal validation are complete. Phase 4A–B provisional baseline and pattern-tracker engineering is implemented; Phase 4C–F remains upcoming. See [TODO.md](TODO.md), the [development roadmap](docs/development/DEVELOPMENT_ROADMAP.md), and the [Phase 3 validation protocol](docs/development/PHASE_03_VALIDATION.md). FlowFocus provenance and adapted ideas are documented in [integration notes](docs/FLOWFOCUS_INTEGRATION.md); the former `/dummy` folder is not needed at runtime.
