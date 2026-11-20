import React from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function MinutesChart({ rows, labelKey, valueKey = 'study_seconds', suffix = ' min' }) {
  return <div className="pattern-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} margin={{ top: 12, right: 8, bottom: 2, left: -16 }}>
    <CartesianGrid stroke="#e9ebf2" vertical={false} /><XAxis dataKey={labelKey} tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
    <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} allowDecimals={false} />
    <Tooltip formatter={value => [`${value}${suffix}`, 'Recorded']} />
    <Bar dataKey={valueKey} fill="#5b55e8" radius={[6, 6, 0, 0]} maxBarSize={42} /></BarChart></ResponsiveContainer></div>
}

export default function PatternTracker({ patterns, error, onRetry }) {
  if (error) return <section className="card live-section"><h2>Study patterns unavailable</h2><p className="muted">{error}</p><button className="secondary" onClick={onRetry}>Retry patterns</button></section>
  if (!patterns) return <section className="card live-section"><h2>Study patterns</h2><p className="muted">Loading recorded patterns…</p></section>
  if (patterns.data_status === 'truncated') return <section className="card live-section"><h2>Study patterns</h2><p className="muted">This account has more history than the current pattern limit. Patterns are withheld so a partial result is not mistaken for complete history.</p></section>
  if (patterns.data_status === 'empty') return <section className="pattern-tracker" aria-label="Study pattern tracker"><div className="pattern-intro"><h2>Your 30-day study patterns</h2><p>Based on recorded active intervals in {patterns.time_zone}. Camera values are provisional signals, not a measure of mental focus.</p></div><div className="card live-section"><h3>No recorded sessions yet</h3><p className="muted">Complete a monitored study session to start building your history. A personal provisional visual-signal baseline needs at least {patterns.baseline.required_windows} usable windows across {patterns.baseline.required_sessions} sessions and {patterns.baseline.required_days} days.</p></div></section>
  const baseline = patterns.baseline
  const hourly = Array.from({ length: 4 }, (_, index) => ({
    label: `${String(index * 6).padStart(2, '0')}–${String((index + 1) * 6).padStart(2, '0')}`,
    study_seconds: Math.round(patterns.study_time.by_hour.slice(index * 6, index * 6 + 6)
      .reduce((sum, row) => sum + row.study_seconds, 0) / 60),
  }))
  const weekday = patterns.study_time.by_weekday.map(row => ({ day: row.day, study_seconds: Math.round(row.study_seconds / 60) }))
  const durations = patterns.session_duration.buckets.map(row => ({ label: row.label, sessions: row.sessions }))
  return <section className="pattern-tracker" aria-label="Study pattern tracker">
    <div className="pattern-intro"><h2>Your 30-day study patterns</h2><p>Based on recorded active intervals in {patterns.time_zone}. Camera values are provisional signals, not a measure of mental focus.</p>
      {patterns.sample_data && <strong>Presentation account: these historical patterns use seeded sample records.</strong>}</div>
    <div className="pattern-grid">
      <section className="card pattern-baseline"><h3>Personal visual-signal baseline</h3>
        {baseline.status === 'ready' ? <><strong className="pattern-number">{baseline.value}/100</strong><p className="muted">Provisional 30-day mean · {baseline.window_count} usable windows across {baseline.session_count} sessions and {baseline.day_count} days.</p>
          {baseline.delta != null && <p className="pattern-note">Recent seven days: {baseline.recent_value}/100 · earlier history: {baseline.prior_value}/100 · {Math.abs(baseline.delta)} points {baseline.trend === 'lower' ? 'lower' : baseline.trend === 'higher' ? 'higher' : 'apart'}.</p>}</>
          : <><strong className="pattern-unavailable">More history needed</strong><p className="muted">{baseline.window_count}/{baseline.required_windows} usable windows · {baseline.session_count}/{baseline.required_sessions} sessions · {baseline.day_count}/{baseline.required_days} days.</p></>}
        <small>Eligible windows need at least 80% usable coverage. Validated visual attention and estimated focused time remain unavailable.</small></section>
      <section className="card"><h3>Session durations</h3><strong className="pattern-summary">{patterns.session_duration.median_minutes == null ? 'No completed sessions' : `${patterns.session_duration.median_minutes} min median`}</strong>
        <MinutesChart rows={durations} labelKey="label" valueKey="sessions" suffix=" sessions" /></section>
      <section className="card"><h3>Study time by local time</h3><p className="muted">Minutes counted only while sessions were active.</p><MinutesChart rows={hourly} labelKey="label" />
        {patterns.study_time.legacy_session_count > 0 && <small>{patterns.study_time.legacy_session_count} older session(s) lack exact active intervals and are excluded here.</small>}</section>
      <section className="card"><h3>Study time by weekday</h3><p className="muted">Time is split at local midnight.</p><MinutesChart rows={weekday} labelKey="day" /></section>
      <section className="card"><h3>Subjects studied</h3>{patterns.subjects.length ? <div className="pattern-subjects">{patterns.subjects.map(row => <div key={row.subject}><span>{row.subject}</span><strong>{Math.round(row.study_seconds / 60)} min · {row.sessions} session{row.sessions === 1 ? '' : 's'}{row.status === 'ready' ? ` · ${row.median_minutes} min median` : ' · more sessions needed for a pattern'}</strong></div>)}</div> : <p className="muted">No completed sessions in this period.</p>}</section>
      <section className="card"><h3>Provisional signal patterns</h3>
        {patterns.visual_decline.status === 'ready' ? <p className="muted">Later session halves averaged {patterns.visual_decline.late_minus_early === 0 ? 'the same provisional signal index' : `${Math.abs(patterns.visual_decline.late_minus_early)} points ${patterns.visual_decline.late_minus_early < 0 ? 'lower' : 'higher'}`} across {patterns.visual_decline.session_count} eligible sessions. The midpoint was around {patterns.visual_decline.typical_half_minutes} active minutes.</p> : <p className="muted">Not enough eligible sessions to describe a typical within-session signal change.</p>}
        {patterns.higher_signal_windows.length ? <p className="pattern-note">Higher provisional signal observed between {String(patterns.higher_signal_windows[0].start_hour).padStart(2, '0')}:00 and {String(patterns.higher_signal_windows[0].end_hour).padStart(2, '0')}:00 across {patterns.higher_signal_windows[0].day_count} days.</p> : <p className="muted">No recurring higher-signal time window has enough evidence yet.</p>}</section>
    </div>
    <section className="card pattern-insights"><h3>What your history shows</h3>{patterns.insights.length ? <ul>{patterns.insights.map((item, index) => <li key={index}>{item.text} <small>Based on {item.sample_count} {item.source === 'active_intervals' ? 'study days' : 'eligible observations'}.</small></li>)}</ul> : <p className="muted">Record more sessions to see personal patterns.</p>}</section>
  </section>
}
