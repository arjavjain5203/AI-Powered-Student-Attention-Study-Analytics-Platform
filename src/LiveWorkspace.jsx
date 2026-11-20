import React, { Suspense, lazy, useEffect, useState } from 'react'
import { api } from './api'
import VisualMonitor from './VisualMonitor'
const PatternTracker = lazy(() => import('./PatternTracker'))

function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
    .map(part => String(part).padStart(2, '0')).join(':')
}

export default function LiveWorkspace({ screen = 'dashboard', onProfile = () => {} }) {
  const [token, setToken] = useState('')
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [subject, setSubject] = useState('')
  const [topic, setTopic] = useState('')
  const [profile, setProfile] = useState(null)
  const [sessions, setSessions] = useState([])
  const [timerSnapshot, setTimerSnapshot] = useState(null)
  const [clock, setClock] = useState(() => performance.now())
  const [analytics, setAnalytics] = useState(null)
  const [patterns, setPatterns] = useState(null)
  const [patternsError, setPatternsError] = useState('')
  const [plan, setPlan] = useState(null)
  const [period, setPeriod] = useState('daily')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [profileName, setProfileName] = useState('')
  const [profileGoal, setProfileGoal] = useState(240)
  const [profileZone, setProfileZone] = useState('UTC')
  const [profilePreferred, setProfilePreferred] = useState(45)
  const [profileNotifications, setProfileNotifications] = useState(true)
  const [alarm, setAlarm] = useState(null)
  const [reporting, setReporting] = useState(false)
  const [shareAccepted, setShareAccepted] = useState(false)
  const [clipUrl, setClipUrl] = useState('')
  const [falseAlarmReports, setFalseAlarmReports] = useState([])

  useEffect(() => {
    if (!alarm?.clip) { setClipUrl(''); return }
    const url = URL.createObjectURL(alarm.clip)
    setClipUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [alarm?.clip])

  async function refresh(auth = token, selected = period, resetCamera = false) {
    setLoading(true); setError('')
    try {
      const [p, listed, a, f, reports, patternResult] = await Promise.all([
        api('/api/profile', {token: auth}), api('/api/sessions', {token: auth}),
        api(`/api/analytics?period=${selected}`, {token: auth}), api('/api/focus/plan', {token: auth}),
        api('/api/false-alarms/mine', {token: auth}),
        api('/api/analytics/patterns', {token: auth}).then(data => ({data})).catch(error => ({error: error.message})),
      ])
      if (resetCamera) {
        await Promise.all(listed.filter(session => session.status === 'active' && session.camera_required)
          .map(session => api(`/api/sessions/${session.id}/visual-consent`, {token: auth, method:'DELETE'})))
      }
      const s = resetCamera ? await api('/api/sessions', {token: auth}) : listed
      const now = performance.now()
      const active = s.find(session => session.status === 'active')
      setProfile(p); onProfile(p); setProfileName(p.name); setProfileGoal(p.daily_goal_minutes); setProfileZone(p.time_zone || 'UTC'); setProfilePreferred(p.preferred_session_minutes); setProfileNotifications(p.notifications_enabled); setSessions(s); setTimerSnapshot(active ? {id: active.id, seconds: active.active_seconds, at: now} : null); setClock(now); setAnalytics(a); setPatterns(patternResult.data || null); setPatternsError(patternResult.error || ''); setPlan(f); setFalseAlarmReports(reports)
    } catch (e) {
      if (e.status === 401 || e.status === 403) {
        setToken(''); setProfile(null); onProfile(null); setSessions([]); setTimerSnapshot(null); setAnalytics(null); setPatterns(null); setPatternsError(''); setPlan(null); setFalseAlarmReports([]); setAlarm(null)
        setError('Your sign-in expired. Please sign in again.')
      } else setError(e.message)
    } finally { setLoading(false) }
  }
  useEffect(() => { if (token) refresh(token, period) }, [period])
  const openSession = sessions.find(session => ['active','paused','awaiting_camera'].includes(session.status))
  useEffect(() => {
    if (!openSession || openSession.status !== 'active') return
    const interval = window.setInterval(() => setClock(performance.now()), 250)
    return () => window.clearInterval(interval)
  }, [openSession?.id, openSession?.status])
  useEffect(() => {
    if (screen !== 'session' && openSession?.status === 'active' && openSession.camera_required) {
      api(`/api/sessions/${openSession.id}/visual-consent`, {token, method:'DELETE'}).then(() => refresh()).catch(e => setError(e.message))
    }
    if (screen !== 'session') setAlarm(null)
  }, [screen, openSession?.id, openSession?.status])
  function sessionSeconds(session) {
    if (session.status !== 'active' || timerSnapshot?.id !== session.id) return session.active_seconds
    return timerSnapshot.seconds + Math.floor(Math.max(0, clock - timerSnapshot.at) / 1000)
  }
  async function submitAuth(e) {
    e.preventDefault(); setLoading(true); setError('')
    try {
      const result = await api(`/api/auth/${mode}`, {method:'POST', body: mode==='register' ? {name,email,password} : {email,password}})
      setToken(result.access_token); setPassword(''); setShowPassword(false); await refresh(result.access_token, period, true)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }
  async function start(e) {
    e.preventDefault(); setLoading(true); setError('')
    try { await api('/api/sessions', {token, method:'POST', body:{subject,topic,goal_minutes:45,camera_required:true}}); setSubject(''); setTopic(''); await refresh() }
    catch(e) { setError(e.message) } finally { setLoading(false) }
  }
  async function change(id, action) {
    setLoading(true); setError('')
    try {
      const updated = await api(`/api/sessions/${id}/status/${action}`, {token,method:'POST'})
      const now = performance.now()
      setSessions(previous => previous.map(session => session.id === id ? updated : session))
      setTimerSnapshot(updated.status === 'active' ? {id, seconds: updated.active_seconds, at: now} : null)
      setClock(now)
      await refresh()
    }
    catch(e) { setError(e.message) } finally { setLoading(false) }
  }
  async function cameraReady(session) {
    if (session.status === 'active') { await refresh(); return }
    const action = session.status === 'awaiting_camera' ? 'activate' : 'status/resume'
    const updated = await api(`/api/sessions/${session.id}/${action}`, {token,method:'POST'})
    const now = performance.now()
    setSessions(previous => previous.map(item => item.id === session.id ? updated : item))
    setTimerSnapshot({id: session.id, seconds: updated.active_seconds, at: now})
    setClock(now)
    await refresh()
  }
  async function visualEvent(session, event) {
    setShareAccepted(false)
    setAlarm({sessionId: session.id, ...event, step:'review'})
    const updated = event.session
    const now = performance.now()
    setSessions(previous => previous.map(item => item.id === session.id ? updated : item))
    setTimerSnapshot(null)
    setClock(now)
    await refresh()
  }
  async function reportFalseAlarm(sendClip) {
    if (!alarm) return
    setReporting(true); setError('')
    try {
      const body = new FormData()
      body.append('category', alarm.category)
      body.append('share_clip', String(Boolean(sendClip && alarm.clip)))
      if (sendClip && alarm.clip) body.append('clip', alarm.clip, 'false-alarm.webm')
      await api(`/api/sessions/${alarm.sessionId}/false-alarms`, {token,method:'POST',body})
      setAlarm(null)
      setShareAccepted(false)
      await refresh()
    } catch (e) { setError(e.message) } finally { setReporting(false) }
  }
  async function deleteFalseAlarm(report) {
    if (!window.confirm('Delete this false-alarm report and its clip now?')) return
    try { await api(`/api/sessions/${report.session_id}/false-alarms/${report.id}`, {token, method:'DELETE'}); await refresh() }
    catch (e) { setError(e.message) }
  }
  async function deleteVisual(id) {
    if (!window.confirm('Delete all derived visual records for this session?')) return
    setError('')
    try { await api(`/api/sessions/${id}/visual-records`, {token, method:'DELETE'}); await refresh() }
    catch(e) { setError(e.message) }
  }
  async function saveProfile(e) {
    e.preventDefault(); setLoading(true); setError('')
    try {
      await api('/api/profile', {token, method:'PATCH', body:{name:profileName, daily_goal_minutes:Number(profileGoal), preferred_session_minutes:Number(profilePreferred), notifications_enabled:profileNotifications, time_zone:profileZone}})
      await refresh()
    } catch(e) { setError(e.message) } finally { setLoading(false) }
  }
  return <div className="live-workspace">
    <div className="privacy"><span>⌑</span><div><strong>Study workspace · Phase 3</strong><p>Digital engagement is a heuristic. Camera monitoring is required for timed sessions. Signals run locally; their index is provisional and distinct from validated visual attention. Estimated focused time remains unavailable.</p></div></div>
    {error && <div className="info-message error" role="alert">{error}</div>}
    {!token ? <section className="card live-auth"><h2>{mode==='login'?'Sign in':'Create account'}</h2><p className="muted">Connect to the local FastAPI backend. Your token stays in memory and clears on reload.</p><form onSubmit={submitAuth}>
      {mode==='register'&&<label>Name<input value={name} onChange={e=>setName(e.target.value)} required minLength="1"/></label>}
      <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label>
      <div className="auth-password"><label htmlFor="auth-password">Password</label><div className="password-field"><input id="auth-password" type={showPassword?'text':'password'} autoComplete={mode==='register'?'new-password':'current-password'} value={password} onChange={e=>setPassword(e.target.value)} required minLength={mode==='register'?10:1}/><button type="button" className="password-toggle" onClick={()=>setShowPassword(value=>!value)} aria-label={showPassword?'Hide password':'Show password'} aria-pressed={showPassword} title={showPassword?'Hide password':'Show password'}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>{showPassword&&<path d="M3 21 21 3"/>}</svg></button></div></div>
      <button className="primary" disabled={loading}>{loading?'Connecting…':mode==='login'?'Sign in':'Register'}</button>
    </form><button className="text-button" onClick={()=>{setMode(mode==='login'?'register':'login');setShowPassword(false)}}>{mode==='login'?'Create an account':'Use an existing account'}</button></section> : <>
      {profile?.presentation_account&&<div className="info-message">Presentation account: historical sessions are seeded sample data. New sessions are recorded in this account.</div>}<div className="live-toolbar"><strong>{profile?.name || 'Student'} · study workspace</strong><button className="secondary" onClick={()=>{setToken('');setProfile(null);onProfile(null);setAlarm(null);setSessions([]);setTimerSnapshot(null);setAnalytics(null);setPatterns(null);setPatternsError('');setPlan(null)}}>Sign out</button></div>
      {screen==='session' && !openSession && <section className="card"><div className="card-head"><h2>Start a study session</h2></div><form onSubmit={start} className="live-form"><label>Subject<input value={subject} onChange={e=>setSubject(e.target.value)} required/></label><label>Topic<input value={topic} onChange={e=>setTopic(e.target.value)}/></label><p className="muted">Create a session, then enable the camera to start counting study time. Camera warnings pause the clock. Video stays on your device unless you explicitly share a false-alarm clip.</p><button className="primary" disabled={loading||!subject.trim()}>Create session</button></form></section>}
      {screen==='session' && openSession && <VisualMonitor key={openSession.id} sessionId={openSession.id} token={token} session={openSession} alarm={alarm} timerText={formatDuration(sessionSeconds(openSession))} sessionStatus={openSession.status} canStart={!alarm} onReady={()=>cameraReady(openSession)} onStopped={()=>refresh()} onEvent={event=>visualEvent(openSession,event)} onPause={()=>change(openSession.id,'pause')} onEnd={()=>change(openSession.id,'end')}/>}
      {screen==='session' && plan && <details className="card session-plan"><summary>Focus plan · {plan.focus_minutes} min study / {plan.break_minutes} min break</summary><p className="muted">{plan.reasons.join(' ')} Source: {plan.score_source.replace('_',' ')} · {plan.confidence} sample confidence · provisional heuristic.</p></details>}
      {alarm&&screen==='session'&&<section className="card live-alarm" role="alert"><h2>{alarm.step==='review'?'Camera alert: study timer paused':'Was this a false alarm?'}</h2><p>The camera observed {alarm.category.replaceAll('_',' ')}. This can happen during normal studying. Time after the alert is excluded until the camera restarts.</p>{alarm.step==='review'?<div className="live-actions"><button className="primary" onClick={()=>setAlarm(null)}>Review complete</button><button className="secondary" onClick={()=>setAlarm(previous=>({...previous,step:'false'}))}>False alarm</button></div>:<><p>Send the recent clip to the local development team only if you choose. It expires after seven days and can show people or surroundings.</p><div className="live-clip-preview">{clipUrl&&<video controls src={clipUrl} aria-label="False alarm clip preview"/>}<label><input type="checkbox" checked={shareAccepted} onChange={event=>setShareAccepted(event.target.checked)}/> I agree to send this clip for developer review. It expires after seven days.</label></div><div className="live-actions"><button className="primary" disabled={reporting||!alarm.clip||!shareAccepted} onClick={()=>reportFalseAlarm(true)}>Send clip and continue</button><button className="secondary" disabled={reporting} onClick={()=>reportFalseAlarm(false)}>Continue without clip</button></div></>}<p className="muted">Use Start camera and timer above to resume the clock. Paused time is not added back.</p></section>}
      {(screen==='analytics'||screen==='dashboard'||screen==='live')&&<section className="card live-section"><div className="card-head"><h2>Recorded analytics</h2><select aria-label="Analytics period" value={period} onChange={e=>setPeriod(e.target.value)}><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></div>{analytics?<><div className="live-metrics"><div><strong>{analytics.session_count}</strong><span>sessions</span></div><div><strong>{Math.round(analytics.study_seconds/60)} min</strong><span>study time</span></div><div><strong>{analytics.average_digital_engagement_score == null?'Unavailable':`${analytics.average_digital_engagement_score}%`}</strong><span>avg. digital engagement</span></div><div><strong>{analytics.average_visual_attention_score == null?'Unavailable':`${analytics.average_visual_attention_score}%`}</strong><span>avg. visual attention</span></div><div><strong>{analytics.potential_distraction_count}</strong><span>client-reported potential distractions</span></div></div>{analytics.by_day?.length>0&&<div className="live-days">{analytics.by_day.map(day=><div key={day.date}><span>{day.date}</span><strong>{Math.round(day.study_seconds/60)} min study</strong></div>)}</div>}</>:<p className="muted">{loading?'Loading…':'Analytics unavailable.'}</p>}</section>}
      {screen==='analytics' && <Suspense fallback={<section className="card live-section"><p className="muted">Loading study patterns…</p></section>}><PatternTracker patterns={patterns} error={patternsError} onRetry={()=>refresh()}/></Suspense>}
      {(screen==='dashboard'||screen==='live')&&<section className="card live-section"><div className="card-head"><h2>Recorded sessions</h2><button className="text-button" onClick={()=>refresh()} disabled={loading}>Refresh ↻</button></div>{sessions.length===0?<div className="empty"><h3>No recorded sessions yet</h3><p>Start one in Study session.</p></div>:<div className="session-list">{sessions.map(s=><div className="session-row" key={s.id}><span className="subject-icon">▤</span><span className="row-main"><strong>{s.subject}</strong><small>{s.topic || 'Open study block'} · {s.status}</small></span><span className="row-metric">{formatDuration(sessionSeconds(s))}<small>active time</small></span>{s.status!=='ended'&&screen!=='session'&&<div className="live-actions">{s.status==='active'&&<button className="secondary" disabled={loading} onClick={()=>change(s.id,'pause')}>Pause</button>}<button className="danger-button" disabled={loading} onClick={()=>change(s.id,'end')}>End</button></div>}{s.status!=='active'&&<button className="text-button" onClick={()=>deleteVisual(s.id)}>Delete visual data</button>}</div>)}</div>}</section>}

      {screen==='settings'&&<section className="card live-section"><div className="card-head"><h2>Your false-alarm reports</h2></div><p className="muted">Only clips you explicitly sent are stored. Reports and clips expire after seven days. You can delete them sooner.</p>{falseAlarmReports.length===0?<p className="muted">No reports submitted.</p>:<div className="session-list">{falseAlarmReports.map(report=><div className="session-row" key={report.id}><span className="row-main"><strong>{report.category.replaceAll('_',' ')}</strong><small>{new Date(report.submitted_at).toLocaleString()} · {report.clip_shared?'Clip shared':'No clip'}</small></span><button className="danger-button" onClick={()=>deleteFalseAlarm(report)}>Delete report</button></div>)}</div>}</section>}
      {(screen==='settings'||screen==='live')&&<section className="card live-section"><div className="card-head"><h2>Recorded profile</h2></div><form className="live-form" onSubmit={saveProfile}><label>Name<input value={profileName} onChange={e=>setProfileName(e.target.value)} required/></label><label>Daily goal (minutes)<input type="number" min="30" max="720" value={profileGoal} onChange={e=>setProfileGoal(e.target.value)} required/></label><label>Preferred session length (minutes)<input type="number" min="10" max="180" value={profilePreferred} onChange={e=>setProfilePreferred(e.target.value)} required/></label><label>Time zone<select value={profileZone} onChange={e=>setProfileZone(e.target.value)}><option value="UTC">UTC</option><option value="Asia/Kolkata">Asia/Kolkata</option><option value="Europe/London">Europe/London</option><option value="America/New_York">America/New_York</option></select></label><label className="live-check"><input type="checkbox" checked={profileNotifications} onChange={e=>setProfileNotifications(e.target.checked)}/> Notification preference (no messages are sent yet)</label><button className="primary" disabled={loading}>Save profile</button></form></section>}
    </>}
  </div>
}
