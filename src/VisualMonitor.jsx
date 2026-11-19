import React, { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { addSample, emptyWindow } from './visualSignals'

export default function VisualMonitor({ sessionId, token, sessionStatus, onReady, onStopped, onEvent, canStart = true }) {
  const video = useRef(null)
  const runtime = useRef(null)
  const [state, setState] = useState('off')
  const [message, setMessage] = useState('Camera is off. Start monitoring only if you want local visual-signal estimates.')
  const [latest, setLatest] = useState(null)
  const [records, setRecords] = useState([])
  const [events, setEvents] = useState([])
  const [devices, setDevices] = useState([])
  const [deviceId, setDeviceId] = useState('')
  const [inference, setInference] = useState(null)

  function cleanup(revoke = true) {
    const old = runtime.current
    runtime.current = null
    if (!old) return Promise.resolve()
    clearInterval(old.sampleTimer)
    clearInterval(old.uploadTimer)
    clearInterval(old.recordTimer)
    old.uploadController?.abort()
    if (old.recorder?.state === 'recording') old.recorder.stop()
    old.chunks = []
    old.stream?.getTracks().forEach(track => { track.onended = null; track.stop() })
    try { old.landmarker?.close() } catch { /* The camera still stops if inference cleanup fails. */ }
    if (video.current) video.current.srcObject = null
    if (revoke && old.consented) return api(`/api/sessions/${sessionId}/visual-consent`, { token, method: 'DELETE' }).catch(() => {})
    return Promise.resolve()
  }

  async function refreshDevices() {
    if (!navigator.mediaDevices?.enumerateDevices) return
    try { setDevices((await navigator.mediaDevices.enumerateDevices()).filter(device => device.kind === 'videoinput')) }
    catch { setDevices([]) }
  }

  useEffect(() => {
    api(`/api/sessions/${sessionId}/visual-records`, { token }).then(items => { setRecords(items); setLatest(items[0] || null) }).catch(() => {})
    api(`/api/sessions/${sessionId}/visual-events`, { token }).then(setEvents).catch(() => {})
    return () => cleanup()
  }, [sessionId, token])

  useEffect(() => {
    if (sessionStatus !== 'active' && runtime.current && state === 'on') {
      cleanup(); setState('off'); setMessage('Monitoring paused with the study session.')
    }
  }, [sessionStatus])

  useEffect(() => {
    const onHidden = () => {
      if (document.hidden && runtime.current) { cleanup().then(() => onStopped?.()); setState('off'); setMessage('Monitoring stopped when this tab became hidden.') }
    }
    document.addEventListener('visibilitychange', onHidden)
    return () => document.removeEventListener('visibilitychange', onHidden)
  }, [sessionId, token])

  useEffect(() => {
    const onPageHide = () => cleanup()
    window.addEventListener('pagehide', onPageHide)
    navigator.mediaDevices?.addEventListener?.('devicechange', refreshDevices)
    return () => {
      window.removeEventListener('pagehide', onPageHide)
      navigator.mediaDevices?.removeEventListener?.('devicechange', refreshDevices)
    }
  }, [sessionId, token])

  async function start(preferredDeviceId = deviceId) {
    if (runtime.current) return
    if (!navigator.mediaDevices?.getUserMedia) { setState('error'); setMessage('Camera access requires a supported browser and a secure context such as localhost or HTTPS.'); return }
    setState('starting'); setMessage('Requesting camera permission and loading the local face model…')
    const run = { stream: null, landmarker: null, sampleTimer: null, uploadTimer: null,
      consented: false, window: emptyWindow(), inferenceMs: 0, inferenceCount: 0,
      uploading: false, uploadController: null, recorder: null, recordTimer: null, chunks: [] }
    runtime.current = run
    try {
      run.stream = await navigator.mediaDevices.getUserMedia({ video: {
        ...(preferredDeviceId ? { deviceId: { exact: preferredDeviceId } } : { facingMode: 'user' }),
        width: { ideal: 640 }, height: { ideal: 480 } }, audio: false })
      if (runtime.current !== run) { run.stream.getTracks().forEach(track => track.stop()); return }
      await refreshDevices()
      const selected = run.stream.getVideoTracks()[0]?.getSettings()?.deviceId
      if (selected) setDeviceId(selected)
      run.stream.getVideoTracks().forEach(track => { track.onended = () => {
        if (runtime.current === run) { cleanup().then(() => onStopped?.()); setState('error'); setMessage('Camera disconnected. Monitoring stopped.') }
      } })
      if (video.current) { video.current.srcObject = run.stream; await video.current.play() }
      if (runtime.current !== run) return
      const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')
      const fileset = await FilesetResolver.forVisionTasks('/mediapipe/wasm')
      run.landmarker = await FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/mediapipe/face_landmarker.task', delegate: 'CPU' },
        runningMode: 'VIDEO', numFaces: 1,
      })
      if (runtime.current !== run) { run.landmarker.close(); return }
      await api(`/api/sessions/${sessionId}/visual-consent`, { token, method: 'POST' })
      run.consented = true
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported('video/webm')) {
        const startSegment = () => {
          const recorder = new MediaRecorder(run.stream, { mimeType: 'video/webm', videoBitsPerSecond: 400000 })
          run.recorder = recorder
          run.chunks = []
          recorder.ondataavailable = event => {
            if (event.data.size && runtime.current === run && run.recorder === recorder) run.chunks.push(event.data)
          }
          recorder.onstop = () => { if (runtime.current === run) startSegment() }
          recorder.start(1000)
        }
        startSegment()
        run.recordTimer = setInterval(() => { if (run.recorder?.state === 'recording') run.recorder.stop() }, 8000)
      }
      await onReady?.()
      if (runtime.current !== run) return
      setState('on'); setMessage('Local monitoring is on. Only 10-second sample counts leave this browser. A short clip remains in memory unless you choose to send it after a false alarm.')
      run.sampleTimer = setInterval(() => {
        if (runtime.current !== run) return
        if (!run.stream.getVideoTracks().some(track => track.readyState === 'live')) {
          cleanup().then(() => onStopped?.()); setState('error'); setMessage('Camera signal was lost. Monitoring stopped.'); return
        }
        try {
          if (!video.current || video.current.readyState < 2) { addSample(run.window, null, false); return }
          const started = performance.now()
          const result = run.landmarker.detectForVideo(video.current, started)
          run.inferenceMs += performance.now() - started
          run.inferenceCount += 1
          addSample(run.window, result.faceLandmarks?.[0] || null)
        } catch { addSample(run.window, null, false) }
      }, 500)
      run.uploadTimer = setInterval(async () => {
        if (runtime.current !== run || run.uploading) return
        const payload = run.window
        run.window = emptyWindow()
        run.uploading = true
        run.uploadController = new AbortController()
        try {
          const result = await api(`/api/sessions/${sessionId}/visual-records`, {
            token, method: 'POST', body: payload, signal: run.uploadController.signal,
          })
          if (runtime.current === run) {
            setLatest(result); setRecords(previous => [result, ...previous].slice(0, 100))
            if (result.potential_visual_event) setEvents(previous => [{
              category: result.potential_visual_event, occurred_at: result.captured_at,
              source: 'provisional_visual_heuristic', minimum_observed_seconds: 20,
            }, ...previous].slice(0, 100))
            setInference(run.inferenceCount ? Math.round(run.inferenceMs / run.inferenceCount) : null)
            run.inferenceMs = 0; run.inferenceCount = 0
            if (result.potential_visual_event) {
              const clip = run.chunks.length ? new Blob(run.chunks, { type: 'video/webm' }) : null
              onEvent?.({ category: result.potential_visual_event, clip })
            }
          }
        } catch (error) {
          if (runtime.current === run) { cleanup().then(() => onStopped?.()); setState('error'); setMessage(`Monitoring stopped: ${error.message}`) }
        } finally { run.uploading = false; run.uploadController = null }
      }, 10000)
    } catch (error) {
      if (runtime.current !== run) return
      cleanup()
      setState('error')
      setMessage(error.name === 'NotAllowedError' ? 'Camera permission was denied. The study timer remains paused.'
        : error.name === 'NotFoundError' || error.name === 'OverconstrainedError' ? 'The selected camera is unavailable. Choose another camera to start the timer.'
          : `Camera unavailable: ${error.message}`)
    }
  }

  async function stop() { await cleanup(); onStopped?.(); setState('off'); setMessage('Monitoring stopped. Previously saved derived records remain until deleted or their 90-day expiry.') }
  async function switchDevice(event) {
    const nextId = event.target.value
    await cleanup()
    await onStopped?.()
    setDeviceId(nextId)
    setState('off')
    setMessage('Camera changed. Start monitoring again to resume the timer.')
  }
  async function deleteRecords() {
    if (!window.confirm('Delete all derived visual records for this session?')) return
    try { await api(`/api/sessions/${sessionId}/visual-records`, { token, method: 'DELETE' }); setRecords([]); setEvents([]); setLatest(null); setMessage('This session’s derived visual records and events were deleted.') }
    catch (error) { setMessage(`Could not delete records: ${error.message}`) }
  }

  return <section className="card live-section visual-monitor"><div className="card-head"><h2>Camera monitoring</h2><span className="pill">{state === 'on' ? 'Monitoring on' : 'Camera off'}</span></div>
    <p className="muted">The camera is required to count a timed session. Face presence and coarse head orientation are provisional signals and may produce false alerts. Up to 10 seconds of video stays in browser memory; only you can choose to send a clip after a false alarm. No video or landmarks are uploaded automatically.</p>
    <video ref={video} autoPlay muted playsInline className="visual-preview" aria-label="Local camera preview" />
    {devices.length > 1 && <label className="visual-device">Camera device<select aria-label="Camera device" value={deviceId} onChange={switchDevice}>
      {devices.map((device, index) => <option key={device.deviceId} value={device.deviceId}>{device.label || `Camera ${index + 1}`}</option>)}
    </select></label>}
    <p role="status" className="muted">{message}</p>
    <div className="visual-actions">{state === 'on' || state === 'starting' ? <button className="secondary" onClick={stop}>Stop monitoring</button> : <button className="primary" disabled={!canStart} onClick={() => start()}>{sessionStatus==='active'?'Restart camera':'Start camera and timer'}</button>}
      <button className="danger-button" onClick={deleteRecords} disabled={!records.length}>Delete derived records</button></div>
    <div className="visual-result"><strong>{latest?.visual_signal_index == null ? 'No usable visual signal yet' : `${latest.visual_signal_index}/100 provisional visual signal index`}</strong>
      {latest && <small>{latest.reasons.join(' · ')}</small>}<small>{records.length} saved window{records.length === 1 ? '' : 's'} · automatically expire after 90 days</small>
      {latest && <small>Usable sample coverage: {Math.round((latest.sample_coverage || 0) * 100)}% · {latest.quality} quality</small>}
      <small>{events.length} provisional camera-observed event{events.length === 1 ? '' : 's'} · absence or head orientation can reflect normal studying, not distraction</small>
      {inference != null && <small>Average local inference: {inference} ms per processed frame (this device)</small>}</div>
  </section>
}
