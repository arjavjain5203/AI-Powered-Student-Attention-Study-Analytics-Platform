// Geometry is a coarse orientation proxy, not eye tracking or a mental-state measure.
export const ALGORITHM_VERSION = 'face-presence-head-orientation-v1'

export function forwardOrientation(landmarks) {
  if (!landmarks || landmarks.length < 264) return null
  const left = landmarks[33], right = landmarks[263], nose = landmarks[1]
  if (!left || !right || !nose) return null
  const eyeSpan = Math.hypot(right.x - left.x, right.y - left.y)
  if (eyeSpan < 0.04) return null
  const centerX = (left.x + right.x) / 2
  const eyeY = (left.y + right.y) / 2
  const yawProxy = (nose.x - centerX) / eyeSpan
  const pitchProxy = (nose.y - eyeY) / eyeSpan
  return Math.abs(yawProxy) <= 0.22 && pitchProxy >= 0.12 && pitchProxy <= 0.7
}

export function emptyWindow() {
  return { algorithm_version: ALGORITHM_VERSION, total_samples: 0, valid_samples: 0,
    face_samples: 0, forward_samples: 0 }
}

export function addSample(window, landmarks, processed = true) {
  window.total_samples += 1
  if (!processed) return window
  window.valid_samples += 1
  if (landmarks?.length) {
    window.face_samples += 1
    if (forwardOrientation(landmarks)) window.forward_samples += 1
  }
  return window
}

export function visiblePhone(detections) {
  return detections?.some(item => item.categories?.some(category =>
    category.categoryName === 'cell phone' && category.score >= 0.35)) || false
}

export function cameraWarning(landmarks, detections) {
  if (visiblePhone(detections)) return 'phone_visible'
  if (!landmarks?.length) return 'face_not_visible'
  if (forwardOrientation(landmarks) === false) return 'head_not_forward'
  return null
}
