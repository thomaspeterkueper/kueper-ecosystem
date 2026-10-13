import test from 'node:test'
import assert from 'node:assert/strict'
import {
  PROJECTION_CAVEATS,
  PROJECTION_NOTE,
  PROJECTION_SOURCE,
  SEED_EVENTS,
  UTOPIA_MARS_SCOPE,
  type UniverseEvent,
} from '../app/internal/universe/timeline/seed-projection'
import { temporalToYear } from '../app/internal/universe/timeline/timeline-math'

const PRECISIONS = new Set([
  'day',
  'year',
  'decade',
  'century',
  'millennium',
  'era',
  'half-century',
  'unspecified',
])
const CERTAINTIES = new Set(['exact', 'approximate', 'speculative'])
const CANONICALITIES = new Set(['canonical', 'provisional', 'draft', 'deprecated'])
const EPISTEMIC = new Set(['established', 'theoretical', 'speculative', 'fictional'])

const REAL_ANCHORS = ['EVENT:UTOPIA_MARS:zhurong_landung', 'EVENT:UTOPIA_MARS:space_science_roadmap_2050']
const NEW_DOCUMENTS = [
  'OTA-HIS-0004-2021-DE',
  'OTA-SCI-0090-2026-DE',
  'OTA-HIS-0005-2050-DE',
  'OTA-META-0004-2076-DE',
  'OTA-ORG-0008-2087-DE',
  'OTA-CHR-0001-2072-DE',
  'OTA-SOC-0001-2076-DE',
]

function strand(): UniverseEvent[] {
  return SEED_EVENTS.filter((event) => event.universe_or_scope === UTOPIA_MARS_SCOPE)
}

function byId(id: string): UniverseEvent {
  const event = SEED_EVENTS.find((candidate) => candidate.id === id)
  assert.ok(event, `missing event ${id}`)
  return event
}

test('every projected event satisfies the timeline contract', () => {
  for (const event of SEED_EVENTS) {
    assert.ok(event.id.length > 0, 'id must not be empty')
    assert.ok(event.title.length > 0, `${event.id}: title must not be empty`)
    assert.ok(event.summary.length > 0, `${event.id}: summary must not be empty`)
    assert.ok(PRECISIONS.has(event.time.precision), `${event.id}: unknown precision ${event.time.precision}`)
    assert.ok(CERTAINTIES.has(event.time.certainty), `${event.id}: unknown certainty ${event.time.certainty}`)
    assert.ok(event.time.display.length > 0, `${event.id}: display must not be empty`)
    assert.ok(CANONICALITIES.has(event.canonicality), `${event.id}: unknown canonicality ${event.canonicality}`)
    assert.ok(EPISTEMIC.has(event.epistemic_status), `${event.id}: unknown epistemic status ${event.epistemic_status}`)
    assert.ok(Array.isArray(event.source_refs), `${event.id}: source_refs must be an array`)
    assert.ok(Array.isArray(event.relation_refs), `${event.id}: relation_refs must be an array`)
    if (event.time.start !== undefined) {
      assert.notEqual(temporalToYear(event.time), null, `${event.id}: time.start is not parseable`)
    }
  }
})

test('event ids are unique across the projection', () => {
  const ids = SEED_EVENTS.map((event) => event.id)
  assert.equal(new Set(ids).size, ids.length)
})

test('real anchors stay distinguishable from the fictional continuation', () => {
  for (const id of REAL_ANCHORS) {
    const event = byId(id)
    assert.equal(event.epistemic_status, 'established', `${id}: real anchor must be established`)
    assert.equal(event.canonicality, 'canonical', `${id}: real anchor must be canonical`)
    assert.deepEqual(event.relation_refs, [], `${id}: real anchor must not be claimed as NOXIA fiction`)
    assert.match(event.summary, /\[R\]/, `${id}: real anchor must be marked [R]`)
  }

  for (const event of strand().filter((candidate) => !REAL_ANCHORS.includes(candidate.id))) {
    assert.notEqual(event.epistemic_status, 'established', `${event.id}: fictional continuation must not claim real status`)
  }
})

test('provisional Utopia/Mars statements are not projected as canon', () => {
  assert.equal(strand().length, 7, 'the Utopia/Mars strand must contain the seven candidate events')

  const provisional = strand()
    .filter((event) => event.canonicality === 'provisional')
    .map((event) => event.id)
    .sort()
  assert.deepEqual(provisional, [
    'EVENT:UTOPIA_MARS:erste_besatzung',
    'EVENT:UTOPIA_MARS:grosse_stille_kompetenztest',
    'EVENT:UTOPIA_MARS:robotische_vorbereitung',
    'EVENT:UTOPIA_MARS:zweiter_marsknoten',
  ])

  const canonical = strand()
    .filter((event) => event.canonicality === 'canonical')
    .map((event) => event.id)
    .sort()
  assert.deepEqual(canonical, [
    'EVENT:UTOPIA_MARS:maryem_hamid_geburt',
    'EVENT:UTOPIA_MARS:space_science_roadmap_2050',
    'EVENT:UTOPIA_MARS:zhurong_landung',
  ])

  for (const event of strand().filter((candidate) => candidate.canonicality === 'provisional')) {
    assert.notEqual(event.epistemic_status, 'established', `${event.id}: provisional phase must not be a real claim`)
  }
})

test('no settlement coordinate is projected', () => {
  for (const event of strand()) {
    assert.doesNotMatch(event.location ?? '', /°/, `${event.id}: location must not contain coordinates`)
  }

  const payload = JSON.stringify({ events: SEED_EVENTS, note: PROJECTION_NOTE, caveats: PROJECTION_CAVEATS })
  assert.doesNotMatch(payload, /45\s*°|110\s*°|44\s*[–-]\s*47|105\s*[–-]\s*115/, 'search-corridor coordinates must not be projected')
})

test('the strand references the OTA sources with full, disambiguated signatures', () => {
  for (const event of strand()) {
    for (const ref of event.source_refs) {
      assert.match(ref, /^OTA-[A-Z]+-\d{4}-\d{4}(?:-[A-Z]{2})?$/, `${event.id}: source ${ref} is not a full signature`)
    }
  }

  const refs = new Set(strand().flatMap((event) => event.source_refs))
  for (const document of NEW_DOCUMENTS) {
    assert.ok(refs.has(document), `new OTA document ${document} is not referenced`)
  }
})

test('the strand attaches to existing cross-project anchors', () => {
  const fictional = strand().filter((event) => event.epistemic_status !== 'established')
  for (const event of fictional) {
    assert.ok(
      event.relation_refs.includes('WORK:NOXIA:generation_mars'),
      `${event.id}: missing existing anchor WORK:NOXIA:generation_mars`
    )
  }
  assert.ok(
    byId('EVENT:UTOPIA_MARS:maryem_hamid_geburt').relation_refs.includes('CHAR:NOXIA:maryem_hamid'),
    'Maryem Hamid birth must reference the character anchor'
  )
})

test('projection metadata marks the timeline as non-canonical and documents the rules', () => {
  assert.equal(PROJECTION_SOURCE, 'local-seed-v0.2.0')
  assert.match(PROJECTION_NOTE, /Nicht kanonisch/)
  assert.ok(PROJECTION_CAVEATS.length >= 4)
  const caveats = PROJECTION_CAVEATS.join(' ')
  assert.match(caveats, /provisional/)
  assert.match(caveats, /Kaiwu/)
  assert.match(caveats, /Suchzentrum/)
})
