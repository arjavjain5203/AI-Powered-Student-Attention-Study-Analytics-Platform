import React, { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { addSample, cameraWarning, emptyWindow } from './visualSignals'

export default function VisualMonitor({ sessionId, token, sessionStatus, session, alarm, timerText, onReady, onStopped, onEvent, onPause, onEnd, canStart = true }) {
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
    try { old.objectDetector?.close() } catch { /* Camera cleanup continues. */ }
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
    setState('starting'); setMessage('Requesting camera permission and loading the face and phone models…')
    const run = { stream: null, landmarker: null, objectDetector: null, sampleTimer: null, uploadTimer: null,
      consented: false, window: emptyWindow(), inferenceMs: 0, inferenceCount: 0,
      uploading: false, uploadController: null, recorder: null, recordTimer: null, chunks: [],
      warningCategory: null, warningCount: 0, alerting: false }
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
      const { FaceLandmarker, ObjectDetector, FilesetResolver } = await import('@mediapipe/tasks-vision')
      const fileset = await FilesetResolver.forVisionTasks('/mediapipe/wasm')
      run.landmarker = await FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/mediapipe/face_landmarker.task', delegate: 'CPU' },
        runningMode: 'VIDEO', numFaces: 1,
      })
      if (runtime.current !== run) { run.landmarker.close(); return }
      run.objectDetector = await ObjectDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/int8/1/efficientdet_lite0.tflite', delegate: 'CPU' },
        runningMode: 'VIDEO', categoryAllowlist: ['cell phone'], scoreThreshold: 0.35, maxResults: 2,
      })
      if (runtime.current !== run) { run.objectDetector.close(); return }
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
      setState('on'); setMessage('Camera monitoring is on. Face, head and visible-phone warnings are provisional. Only derived counts and warnings leave this browser.')
      run.sampleTimer = setInterval(() => {
        if (runtime.current !== run || run.alerting) return
        if (!run.stream.getVideoTracks().some(track => track.readyState === 'live')) {
          cleanup().then(() => onStopped?.()); setState('error'); setMessage('Camera signal was lost. Monitoring stopped.'); return
        }
        try {
          if (!video.current || video.current.readyState < 2) { addSample(run.window, null, false); return }
          const started = performance.now()
          const result = run.landmarker.detectForVideo(video.current, started)
          const landmarks = result.faceLandmarks?.[0] || null
          addSample(run.window, landmarks)
          const objects = run.objectDetector.detectForVideo(video.current, performance.now())
          run.inferenceMs += performance.now() - started
          run.inferenceCount += 1
          // QA-only injection is compiled out of normal builds; it exercises timer/API warning flows.
          const category = import.meta.env.VITE_ENABLE_SYNTHETIC_SIGNALS === 'true'
            ? (window.__focusAtlasQaCategory || cameraWarning(landmarks, objects.detections))
            : cameraWarning(landmarks, objects.detections)
          run.warningCount = category && category === run.warningCategory ? run.warningCount + 1 : category ? 1 : 0
          run.warningCategory = category
          if (run.warningCount >= 2) {
            run.alerting = true
            ;(async () => {
              try {
                if (run.recorder?.state === 'recording') {
                  await new Promise(resolve => {
                    const timeout = setTimeout(resolve, 150)
                    run.recorder.addEventListener('dataavailable', () => { clearTimeout(timeout); resolve() }, { once: true })
                    run.recorder.requestData()
                  })
                }
                const clip = run.chunks.length ? new Blob(run.chunks, { type: 'video/webm' }) : null
                const event = await api(`/api/sessions/${sessionId}/visual-events`, { token, method: 'POST', body: {
                  category, algorithm_version: category === 'phone_visible'
                    ? 'mediapipe-efficientdet-lite0-v1' : 'face-presence-head-orientation-v1',
                } })
                if (runtime.current !== run) return
                cleanup(false)
                setState('off')
                setEvents(previous => [event, ...previous].slice(0, 100))
                setMessage('Camera warning paused the study timer. Review the warning below.')
                onEvent?.({ category, clip, session: event.session })
              } catch (error) {
                if (runtime.current !== run) return
                cleanup().then(() => onStopped?.())
                setState('error')
                setMessage(`Camera warning could not be saved. Monitoring stopped: ${error.message}`)
              }
            })()
          }
        } catch (error) {
          if (runtime.current !== run) return
          cleanup().then(() => onStopped?.())
          setState('error')
          setMessage(`Camera inference failed. The study timer was paused: ${error.message}`)
        }
      }, 500)
      run.uploadTimer = setInterval(async () => {
        if (runtime.current !== run || run.uploading || run.alerting) return
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
            setInference(run.inferenceCount ? Math.round(run.inferenceMs / run.inferenceCount) : null)
            run.inferenceMs = 0; run.inferenceCount = 0
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

  return <section className="card live-section visual-monitor"><div className="card-head"><h2>{session.subject}</h2><span className={'pill ' + (sessionStatus === 'active' ? 'green' : 'amber')}>{sessionStatus === 'active' ? 'Studying' : sessionStatus === 'awaiting_camera' ? 'Awaiting camera' : 'Paused'}</span></div>
    <p className="muted">{session.topic || 'Open study block'} · {session.goal_minutes}-minute goal · Camera signals are provisional observations.</p>
    <div className="camera-stage"><video ref={video} autoPlay muted playsInline className="visual-preview" aria-label="Local camera preview" />{alarm && <div className="camera-banner">Camera warning: {alarm.category.replaceAll('_', ' ')} · timer paused</div>}<div className="camera-clock"><span>STUDY TIME</span><strong role="timer" aria-label="Active study session time">{timerText}</strong><small>{sessionStatus === 'active' ? 'Camera monitoring · live' : 'Paused time is excluded'}</small></div></div>
    <div className="visual-actions">{state === 'on' || state === 'starting' ? <button className="secondary" onClick={stop}>Stop camera and pause</button> : <button className="primary" disabled={!canStart} onClick={() => start()}>{sessionStatus==='active'?'Restart camera':'Start camera and timer'}</button>}
      {sessionStatus === 'active' && <button className="secondary" onClick={onPause}>Pause</button>}
      <button className="danger-button" onClick={onEnd}>End session</button></div>
    <p className="muted">The clock counts only while the camera is running. A visible phone, missing face or turned head can pause it; these warnings can be false. No frames or landmarks are uploaded automatically.</p>
    {devices.length > 1 && <label className="visual-device">Camera device<select aria-label="Camera device" value={deviceId} onChange={switchDevice}>
      {devices.map((device, index) => <option key={device.deviceId} value={device.deviceId}>{device.label || `Camera ${index + 1}`}</option>)}
    </select></label>}
    <p role="status" className="muted">{message}</p>
    <details className="camera-details"><summary>Camera details and saved signals</summary><button className="danger-button" onClick={deleteRecords} disabled={!records.length}>Delete derived records</button>
    <div className="visual-result"><strong>{latest?.visual_signal_index == null ? 'No usable visual signal yet' : `${latest.visual_signal_index}/100 provisional visual signal index`}</strong>
      {latest && <small>{latest.reasons.join(' · ')}</small>}<small>{records.length} saved window{records.length === 1 ? '' : 's'} · automatically expire after 90 days</small>
      {latest && <small>Usable sample coverage: {Math.round((latest.sample_coverage || 0) * 100)}% · {latest.quality} quality</small>}
      <small>{events.length} provisional camera-observed event{events.length === 1 ? '' : 's'} · absence or head orientation can reflect normal studying, not distraction</small>
      {inference != null && <small>Average local inference: {inference} ms per processed frame (this device)</small>}</div></details>
  </section>
}
