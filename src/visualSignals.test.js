import test from 'node:test'
import assert from 'node:assert/strict'
import { addSample, cameraWarning, emptyWindow, forwardOrientation, visiblePhone } from './visualSignals.js'

function face(noseX = 0.5) {
  const points = Array.from({ length: 264 }, () => ({ x: 0.5, y: 0.5 }))
  points[33] = { x: 0.4, y: 0.4 }
  points[263] = { x: 0.6, y: 0.4 }
  points[1] = { x: noseX, y: 0.47 }
  return points
}

test('orientation proxy and missing geometry', () => {
  assert.equal(forwardOrientation(face()), true)
  assert.equal(forwardOrientation(face(0.6)), false)
  assert.equal(forwardOrientation(null), null)
})

test('window counts stay nested and include missing samples', () => {
  const window = emptyWindow()
  addSample(window, face())
  addSample(window, face(0.6))
  addSample(window, null)
  addSample(window, null, false)
  assert.deepEqual([window.total_samples, window.valid_samples, window.face_samples, window.forward_samples], [4, 3, 2, 1])
  assert.equal('frame' in window, false)
})

test('camera warnings distinguish visible phones, face loss, and head turns', () => {
  const phone = [{ categories: [{ categoryName: 'cell phone', score: 0.7 }] }]
  assert.equal(visiblePhone(phone), true)
  assert.equal(cameraWarning(face(), phone), 'phone_visible')
  assert.equal(cameraWarning(null, []), 'face_not_visible')
  assert.equal(cameraWarning(face(0.6), []), 'head_not_forward')
  assert.equal(cameraWarning(face(), []), null)
  assert.equal(visiblePhone([{ categories: [{ categoryName: 'cell phone', score: 0.2 }] }]), false)
})
