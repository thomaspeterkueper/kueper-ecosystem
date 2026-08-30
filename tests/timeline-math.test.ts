import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildTicks,
  clusterByPixel,
  formatAxisYear,
  panViewport,
  temporalToYear,
  zoomViewport,
  type TimelineTemporal,
} from '../app/internal/universe/timeline/timeline-math'

function temporal(start: string): TimelineTemporal {
  return {
    start,
    precision: 'day',
    certainty: 'exact',
    display: start,
  }
}

test('uses a continuous BCE/CE coordinate without historical year zero', () => {
  assert.equal(temporalToYear(temporal('-1')), 0)
  assert.equal(temporalToYear(temporal('1')), 1)
  assert.equal(temporalToYear(temporal('-60000')), -59999)
  assert.equal(temporalToYear(temporal('0')), null)
  assert.equal(formatAxisYear(0, 100), '1 BCE')
  assert.equal(formatAxisYear(1, 100), '1 CE')
  assert.equal(formatAxisYear(-1, 100), '2 BCE')
})

test('validates calendar dates instead of accepting impossible month/day combinations', () => {
  assert.equal(temporalToYear(temporal('2026-02-29')), null)
  assert.notEqual(temporalToYear(temporal('2024-02-29')), null)
  assert.equal(temporalToYear(temporal('2026-04-31')), null)
  assert.notEqual(temporalToYear(temporal('2087-04-12')), null)
})

test('zoom and pan remain clamped to timeline bounds', () => {
  const bounds = { min: -100, max: 100 }
  assert.deepEqual(panViewport({ min: -50, max: 50 }, bounds, -100), { min: -100, max: 0 })
  assert.deepEqual(panViewport({ min: -50, max: 50 }, bounds, 100), { min: 0, max: 100 })

  const zoomed = zoomViewport({ min: -50, max: 50 }, bounds, 0.5, 0.5)
  assert.deepEqual(zoomed, { min: -25, max: 25 })
})

test('ticks never invent fractional historical years at maximum zoom', () => {
  const ticks = buildTicks({ min: 0, max: 2 }, 10)
  assert.deepEqual(ticks, [0, 1, 2])
})

test('pixel clustering groups nearby events and keeps distant events separate', () => {
  const items = [
    { id: 'a', temporal: temporal('100') },
    { id: 'b', temporal: temporal('101') },
    { id: 'c', temporal: temporal('150') },
  ]
  const clusters = clusterByPixel(items, { min: 90, max: 160 }, 700, 15)
  assert.equal(clusters.length, 2)
  assert.deepEqual(clusters[0].items.map((item) => item.id), ['a', 'b'])
  assert.deepEqual(clusters[1].items.map((item) => item.id), ['c'])
})
