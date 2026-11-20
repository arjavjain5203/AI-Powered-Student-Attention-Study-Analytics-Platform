"""Explainable study patterns from owned history; visual values remain provisional."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from zoneinfo import ZoneInfo

from app.services.visual import ALGORITHM_VERSION

LOOKBACK_DAYS = 30
MIN_WINDOWS = 30
MIN_SESSIONS = 3
MIN_DAYS = 3
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _mean(values):
    return round(sum(values) / len(values), 1) if values else None


def _completed_intervals(session, now):
    intervals = [(part.get("started_at"), part.get("ended_at"))
                 for part in session.get("active_intervals", [])]
    if session.get("status") == "active" and session.get("active_since"):
        intervals.append((session["active_since"], now))
    return [(start, end) for start, end in intervals if start and end and end > start]


def _active_elapsed(intervals, captured_at):
    elapsed = 0.0
    for start, end in intervals:
        if captured_at <= start:
            break
        elapsed += max(0.0, (min(captured_at, end) - start).total_seconds())
    return elapsed


def _allocate_minutes(intervals, since, now, zone):
    hourly = [0.0] * 24
    weekdays = [0.0] * 7
    distinct_days = set()
    for start, end in intervals:
        cursor = max(start, since)
        end = min(end, now)
        while cursor < end:
            next_minute = cursor.replace(second=0, microsecond=0) + timedelta(minutes=1)
            next_cursor = min(next_minute, end)
            seconds = (next_cursor - cursor).total_seconds()
            local = cursor.astimezone(zone)
            hourly[local.hour] += seconds
            weekdays[local.weekday()] += seconds
            distinct_days.add(local.date())
            cursor = next_cursor
    return hourly, weekdays, distinct_days


def summarize_patterns(sessions, visual_records, *, now=None, time_zone="UTC", truncated=False, sample_data=False):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must have a time zone")
    zone = ZoneInfo(time_zone)
    since = now - timedelta(days=LOOKBACK_DAYS)
    by_id = {str(session["_id"]): session for session in sessions}
    intervals = {sid: _completed_intervals(session, now) for sid, session in by_id.items()}
    eligible = []
    for record in visual_records:
        session = by_id.get(record.get("session_id"))
        captured = record.get("captured_at")
        if (session and (session.get("camera_required") or session.get("presentation_seed")) and
                session.get("status") == "ended" and
                captured and since <= captured <= now and record.get("algorithm_version") == ALGORITHM_VERSION and
                record.get("quality") == "usable" and record.get("valid_samples", 0) >= 10 and
                record.get("sample_coverage", 0) >= 0.8 and
                isinstance(record.get("visual_signal_index"), (int, float))):
            eligible.append(record)
    eligible.sort(key=lambda row: row["captured_at"])
    visual_ids = {record["session_id"] for record in eligible}
    visual_days = {record["captured_at"].astimezone(zone).date() for record in eligible}
    enough = not truncated and len(eligible) >= MIN_WINDOWS and len(visual_ids) >= MIN_SESSIONS and len(visual_days) >= MIN_DAYS
    values = [record["visual_signal_index"] for record in eligible]
    recent = [record["visual_signal_index"] for record in eligible if record["captured_at"] >= now - timedelta(days=7)]
    prior = [record["visual_signal_index"] for record in eligible if record["captured_at"] < now - timedelta(days=7)]
    comparison = len(recent) >= 10 and len(prior) >= 20
    delta = round(_mean(recent) - _mean(prior), 1) if enough and comparison else None
    baseline = {
        "status": "ready" if enough else "insufficient_history",
        "value": _mean(values) if enough else None,
        "window_count": len(eligible), "session_count": len(visual_ids), "day_count": len(visual_days),
        "required_windows": MIN_WINDOWS, "required_sessions": MIN_SESSIONS, "required_days": MIN_DAYS,
        "source": "provisional_visual_signal", "algorithm_version": ALGORITHM_VERSION,
        "recent_value": _mean(recent) if delta is not None else None,
        "prior_value": _mean(prior) if delta is not None else None,
        "delta": delta,
        "trend": None if delta is None else "higher" if delta >= 5 else "lower" if delta <= -5 else "similar",
    }

    hourly = [0.0] * 24
    weekdays = [0.0] * 7
    study_days = set()
    legacy = 0
    durations = []
    subjects = defaultdict(lambda: {"study_seconds": 0, "sessions": 0, "durations": [], "days": set()})
    for sid, session in by_id.items():
        session_intervals = intervals[sid]
        if not session_intervals and session.get("active_seconds", 0) > 0 and session.get("started_at") and session["started_at"] >= since:
            legacy += 1
        h, w, days = _allocate_minutes(session_intervals, since, now, zone)
        hourly = [a + b for a, b in zip(hourly, h)]
        weekdays = [a + b for a, b in zip(weekdays, w)]
        study_days.update(days)
        if session.get("status") == "ended" and session.get("started_at") and since <= session["started_at"] <= now:
            seconds = session.get("active_seconds", 0)
            if seconds > 0:
                durations.append(seconds / 60)
                key = session.get("subject", "Other").strip().casefold() or "other"
                subjects[key]["study_seconds"] += seconds
                subjects[key]["sessions"] += 1
                subjects[key]["durations"].append(seconds / 60)
                subjects[key]["days"].add(session["started_at"].astimezone(zone).date())
                subjects[key]["label"] = session.get("subject", "Other").strip() or "Other"

    by_session = defaultdict(list)
    by_window = defaultdict(list)
    for record in eligible:
        by_session[record["session_id"]].append(record)
        local = record["captured_at"].astimezone(zone)
        by_window[local.hour // 6].append(record)
    declines = []
    for sid, records in by_session.items():
        if len(records) < 6 or not intervals[sid]:
            continue
        elapsed = [_active_elapsed(intervals[sid], record["captured_at"]) for record in records]
        if max(elapsed) < 600:
            continue
        half = max(elapsed) / 2
        early = [row["visual_signal_index"] for row, minute in zip(records, elapsed) if minute <= half]
        late = [row["visual_signal_index"] for row, minute in zip(records, elapsed) if minute > half]
        if len(early) >= 3 and len(late) >= 3:
            declines.append({"delta": round(_mean(late) - _mean(early), 1), "half_minutes": round(half / 60)})
    decline_ready = len(declines) >= 3 and not truncated
    decline_delta = _mean([row["delta"] for row in declines]) if decline_ready else None
    higher_windows = []
    if enough:
        for bucket, records in sorted(by_window.items()):
            days = {row["captured_at"].astimezone(zone).date() for row in records}
            value = _mean([row["visual_signal_index"] for row in records])
            if len(records) >= 20 and len(days) >= 3 and value >= baseline["value"] + 5:
                higher_windows.append({"start_hour": bucket * 6, "end_hour": (bucket + 1) * 6,
                                       "mean_index": value, "window_count": len(records), "day_count": len(days)})
    higher_windows.sort(key=lambda row: row["mean_index"], reverse=True)

    insights = []
    if len(study_days) >= 3:
        block = max(range(4), key=lambda i: sum(hourly[i * 6:(i + 1) * 6]))
        seconds = round(sum(hourly[block * 6:(block + 1) * 6]))
        if seconds > 0:
            insights.append({"text": f"Most recorded study time in this period was between {block * 6:02d}:00 and {(block + 1) * 6:02d}:00.",
                             "source": "active_intervals", "sample_count": len(study_days)})
    if decline_ready and decline_delta <= -5:
        insights.append({"text": f"The provisional camera signal averaged {abs(decline_delta):.1f} points lower in later session halves.",
                         "source": "provisional_visual_signal", "sample_count": len(declines)})
    if higher_windows:
        top = higher_windows[0]
        insights.append({"text": f"Your provisional camera signal was higher between {top['start_hour']:02d}:00 and {top['end_hour']:02d}:00 in eligible windows.",
                         "source": "provisional_visual_signal", "sample_count": top["window_count"]})
    durations_sorted = sorted(durations)
    buckets = [sum(1 for value in durations if low <= value < high) for low, high in
               [(0, 15), (15, 30), (30, 45), (45, 60), (60, float("inf"))]]
    subject_rows = [{"subject": value["label"], "study_seconds": value["study_seconds"],
                     "sessions": value["sessions"], "day_count": len(value["days"]),
                     "status": "ready" if value["sessions"] >= 3 and len(value["days"]) >= 2 else "insufficient_history",
                     "median_minutes": round(median(value["durations"]), 1)
                     if value["sessions"] >= 3 and len(value["days"]) >= 2 else None}
                    for value in subjects.values()]
    return {
        "window_days": LOOKBACK_DAYS, "time_zone": time_zone, "data_status": "truncated" if truncated else "recorded" if sessions else "empty",
        "sample_data": sample_data,
        "visual_attention_score": None, "estimated_focused_seconds": None, "baseline": baseline,
        "study_time": {"by_hour": [{"hour": hour, "study_seconds": round(value)} for hour, value in enumerate(hourly)],
                       "by_weekday": [{"day": WEEKDAYS[i], "study_seconds": round(value)} for i, value in enumerate(weekdays)],
                       "day_count": len(study_days), "legacy_session_count": legacy},
        "session_duration": {"count": len(durations), "median_minutes": round(median(durations_sorted), 1) if durations else None,
                             "buckets": [{"label": label, "sessions": count} for label, count in
                                         zip(("<15", "15–29", "30–44", "45–59", "60+"), buckets)]},
        "visual_decline": {"status": "ready" if decline_ready else "insufficient_history",
                           "session_count": len(declines), "late_minus_early": decline_delta,
                           "typical_half_minutes": round(median([row["half_minutes"] for row in declines])) if decline_ready else None},
        "higher_signal_windows": higher_windows,
        "subjects": sorted(subject_rows, key=lambda row: row["study_seconds"], reverse=True),
        "insights": [] if truncated else insights[:3],
    }
