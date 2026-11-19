# Phase 2 data and trust contract

## Sources and meanings

| Field | Current meaning | May be `null`? | Source |
| --- | --- | --- | --- |
| `study_seconds` | Server-tracked active session duration for sessions started in the selected calendar period | No | Session lifecycle |
| `digital_engagement_score` | Provisional 0–100 interaction heuristic | Yes | Server calculation from client-reported counts |
| `visual_attention_score` | Future estimate from a validated opt-in local visual pipeline | Yes; always `null` in Phase 2 | Phase 3 only |
| `combined_study_engagement` | Future calibrated combination of independent signals | Yes; always `null` in Phase 2 | Future evaluation |
| `estimated_focused_seconds` | Future duration inferred from eligible visual records | Yes; always `null` in Phase 2 | Phase 3/4 rules |
| `potential_distraction_count` | Count of client-reported event records | No | Owned session event API |

The visual-record API accepts derived counts, never raw frames or a client-supplied visual score. A separate false-alarm endpoint accepts a short clip only after an explicit student action and sharing agreement. Digital counts may be inaccurate or forged; neither they nor an elapsed timer prove learning. The focus planner labels its score source and provisional heuristic status. It falls back to an explicitly unpersonalized suggestion when fewer than three valid scores are available.

The Study Session screen displays `active_seconds` as a running clock. A camera-required session begins in `awaiting_camera` with zero active time. After camera setup and consent, activation starts server time. The clock advances each second while `active`, stops while `paused` or `ended`, and resynchronizes from the server. Camera stop, loss, route exit, and consent-lease expiry pause a camera-required session. A provisional camera event also pauses it at alert time and presents a false-alarm choice. The student must restart monitoring to resume; paused time is not added back even for a false alarm. This interval cannot determine whether the student was actually studying, and it does not retroactively subtract an unknown earlier distraction period. `estimated_focused_seconds` remains `null` pending validated rules.

## Time and ownership

All stored timestamps are UTC and durations are seconds. Profile `time_zone` is an IANA name; daily begins at local midnight, weekly on local Monday, and monthly on the local first day. Periods end at the current instant. Sessions are assigned to the period in which they start; splitting a session across midnight is a future analytics refinement. Every session, record, and report query is scoped to the authenticated user. A dependent record can be created only for an owned active session.

## Future visual-signal gate

Phase 3 has consent timestamps and a 60-second renewable lease, a versioned bounded count payload, server-side provisional index calculation, sample coverage/quality markers, 90-day expiry, per-session deletion, and cross-user tests. The separate `visual_records` and `visual_events` collections are not merged into `attention_records` or existing distraction analytics; `visual_attention_score` and analytics averages remain `null` pending a consented validation study. Clients cannot submit arbitrary score fields, but client-supplied counts remain forgeable. Camera-observed events are provisional and can reflect normal study behavior. A false-alarm report requires a recent owned event; any student-shared WebM clip is limited to 5 MB, stored separately, and has seven-day TTL and owner deletion. The server checks file type and EBML header but does not independently verify clip duration or content.

## Authentication and deployment review

Phase 2 uses a 12-hour Bearer JWT kept only in browser memory. Refresh requires sign-in; no token is written to local storage. Passwords are bcrypt-hashed, emails are uniquely indexed, and authenticated requests resolve the token subject to an existing user. JWT secrets must be 32+ random characters and set through environment variables. The local MongoDB server is loopback-only and unauthenticated; deployment must use a secured MongoDB URI with authentication and TLS, restricted CORS origins, HTTPS, secret management, and the Phase 5 security review. `backend/.env` and `.local/` are Git-ignored.
