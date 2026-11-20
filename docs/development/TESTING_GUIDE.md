# FocusAtlas local testing guide

This guide covers the current **backend-connected** website. Use Windows PowerShell and run the commands from `C:\ai_student_attention_docs` unless a step says otherwise. Keep MongoDB, the API, and Vite running in separate terminals.

## 1. One-time setup

Install dependencies and create the ignored local environment file:

```powershell
cd C:\ai_student_attention_docs
python -m pip install -r backend/requirements-dev.txt
npm install
python backend/scripts/setup_local_env.py
```

If the project-local MongoDB has not been installed, download the official MongoDB Community Server ZIP, save it as `.local/mongodb.zip`, and run:

```powershell
python backend/scripts/install_local_mongo.py
```

The presentation accounts are seeded after MongoDB starts in the next section. The seed script refuses a non-local MongoDB URI. Do not use these accounts or the shared password in a deployed environment.

## 2. Start the application

**Terminal 1 — MongoDB** (keep open):

```powershell
cd C:\ai_student_attention_docs
python backend/scripts/start_local_mongo.py
```

If MongoDB is already running on port 27017, leave that process running and skip starting another. Check its port with `Get-NetTCPConnection -LocalPort 27017 -State Listen`.

**Once MongoDB is running**, seed the local presentation accounts from another terminal:

```powershell
cd C:\ai_student_attention_docs
python backend/scripts/seed_presentation_accounts.py
```

The seed is safe to rerun. It refreshes the three fictional students' labeled sample history within the rolling 30-day window, preserves their separately recorded sessions, sets the development password for `test@gmail.com`, preserves that account's sessions, and pauses an older unmonitored active test session without adding time.

**Terminal 2 — API** (keep open):

```powershell
cd C:\ai_student_attention_docs\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 3 — frontend** (keep open):

```powershell
cd C:\ai_student_attention_docs
npm run dev
```

Open `http://127.0.0.1:5173/` in Chrome or Edge. Before signing in, verify the API and database from another PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/db
```

Both should report `status: ok`. A `503` from `/api/health/db` usually means MongoDB is not running or `MONGO_URI` is wrong.

## 3. Test accounts

All four local presentation accounts use **`StudyDemo123!`**. The password is case-sensitive. The earlier short password `test` is no longer used.

| Email | Name | What to expect |
| --- | --- | --- |
| `test@gmail.com` | Test Student | Existing recorded history; no fabricated sessions are added |
| `maya.student@example.com` | Maya Sharma | Three labeled sample sessions in mathematics and physics |
| `arjun.student@example.com` | Arjun Mehta | Three labeled sample sessions in computing and statistics |
| `zoya.student@example.com` | Zoya Khan | Three labeled sample sessions in biology and chemistry |

Sign in separately to each account. The three fictional accounts show a **Presentation account** notice because their older history is sample data. Sessions you start while signed in are recorded under that account. One account must never show another account's sessions.

## 4. Manual website checks

1. Sign in as `test@gmail.com`. The site should open on **Overview** without a Demo/Recorded switch or a separate Recorded workspace page. If an older `math` session is paused, end it or resume it with the camera before creating another session.
2. Go to **Study session**, enter a subject and optional topic, and select **Create session**. The timer should show `00:00:00` while the session is **Awaiting camera**.
3. Select **Start camera and timer** and allow camera permission. The timer should advance on screen every second without clicking Refresh. Camera setup time is excluded. If permission is denied, the timer stays paused.
4. Select **Pause**, wait several seconds, and verify the displayed time does not increase. Select **Start camera and timer** to resume. **Stop monitoring**, leave the Study session page, or end the session and confirm counting stops.
5. If a provisional face, head, or visible-phone alert appears, check that the timer pauses and an on-screen warning appears. Choose **Review complete** or **False alarm**. Either choice keeps the paused interval excluded; restart the camera to resume counting. An alert may occur after the behavior began, so the app does not subtract an exact earlier interval.
6. On **False alarm**, preview the local clip. **Continue without clip** sends only event feedback. To share video, check the explicit agreement and select **Send clip and continue**. In **Profile & settings**, verify the report appears and **Delete report** removes it. Sent clips expire from MongoDB after seven days; derived visual windows expire after 90 days.
7. Sign out and use each fictional student login. Check Overview, Analytics, Study session, and Settings for that student's own data. Analytics should show a clearly labeled sample 30-day provisional baseline and study patterns for the fictional accounts; `test@gmail.com` should show insufficient history until you record enough sessions. AI Coach, Goals, and Achievements are still labeled previews.

The camera index and alerts are provisional observations. They do not establish mental attention, learning, or validated focused time. Physical-camera behavior, false alerts, browser performance, and signal accuracy still need the [Phase 3 validation protocol](PHASE_03_VALIDATION.md).

## 5. Automated checks

With MongoDB running, run these from the project root unless noted:

```powershell
cd C:\ai_student_attention_docs
npm test
npm run build
python backend/scripts/run_real_mongo_check.py
npm run test:browser
cd backend
python -m pytest -q
```

`npm run test:browser` launches isolated temporary API and Vite servers, uses a synthetic blank camera and a temporary MongoDB database, then removes that database. It requires local Chrome or Edge; set `PLAYWRIGHT_CHROME_EXECUTABLE` if neither is found at its standard Windows location. Screenshots and the last report are saved under ignored `.local/browser-qa/`. The real-Mongo test also creates and removes its own uniquely named test database. The regular backend suite skips that separate real-Mongo test unless explicitly enabled.

## 6. Developer review of false alarms

The local admin review token is generated in ignored `backend/.env`; it is not shown in the website. With the API running, list reports from the project root:

```powershell
python backend/scripts/review_false_alarms.py
```

To download a clip the student explicitly shared:

```powershell
python backend/scripts/review_false_alarms.py --download REPORT_ID
```

The clip is saved under ignored `.local/review-clips/`. Delete downloaded copies when review ends: local downloaded files are outside the database's seven-day expiry. No clip is sent automatically or to an external inbox.

## 7. Common startup problems

| Symptom | Check |
| --- | --- |
| `WinError 10048` on port 8000 or 5173 | A server is already listening. Check `Get-NetTCPConnection -LocalPort 8000 -State Listen` (or `5173`), inspect that PID's command line, and use the existing server or stop the verified older process. |
| Sign-in says database unavailable | Start MongoDB, then confirm `/api/health/db` returns `status: ok`. |
| API logs `OPTIONS /api/auth/login` with `400` | The page origin is missing from CORS. Localhost, loopback, and private-network Vite addresses on port 5173 are allowed when `APP_ENV=development`. For a different host or port, add its exact origin to `CORS_ORIGINS` in `backend/.env` and restart the API. Check the browser address bar for the exact origin. |
| Camera permission fails | Use `localhost` or `127.0.0.1` (or HTTPS), allow camera permission, and close another app using the camera. |
| Timer remains at zero | A new session waits for **Start camera and timer** and successful camera/model initialization. |
| The test account cannot start a new session | End or resume its older paused session first; each account can have only one open session. |
| API changes do not appear | Restart Uvicorn if it was started without `--reload`; refresh the browser after frontend changes. |

For implementation status, see [TODO.md](../../TODO.md) and the [development roadmap](DEVELOPMENT_ROADMAP.md).
