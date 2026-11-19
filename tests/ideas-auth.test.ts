import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import { createElement, type ComponentType, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import seed from '../data/idea-workshop-seed.json'

const TOKEN = 'ideas-test-token-2026'
const WRONG_SAME_LENGTH = 'ideas-test-token-2027'
const WRONG_SHORT = 'ideas-test-token'
const WRONG_LONG = `${TOKEN}-extra`
const DENIED_MARKER = 'Dieser Bereich ist intern'
const SEED_IDS = seed.items.map((item) => item.id)

const originalSecret = process.env.KUEPER_IDEAS_ADMIN_TOKEN
let currentAuthorization: string | null = null

function stubModule(filename: string, exports: Record<string, unknown>): void {
  require.cache[filename] = {
    id: filename,
    filename,
    loaded: true,
    exports,
  } as unknown as NodeModule
}

// The page is a Next.js server component. Replace its request-scoped imports
// with deterministic stubs so the real component can render outside a request.
stubModule(require.resolve('next/headers'), {
  __esModule: true,
  headers: () => ({
    get: (name: string) => (name.toLowerCase() === 'authorization' ? currentAuthorization : null),
  }),
})

const LinkStub: ComponentType<{ href: string; children?: ReactNode }> = ({ href, children }) =>
  createElement('a', { href }, children)
stubModule(require.resolve('next/link'), { __esModule: true, default: LinkStub })

type IdeasPageModule = { default: () => ReactNode }
function loadIdeasPage(): IdeasPageModule {
  return require('../app/dashboard/ideas/page') as IdeasPageModule
}

function renderIdeasPage(authorization: string | null, secret: string | undefined): string {
  currentAuthorization = authorization
  if (secret === undefined) {
    delete process.env.KUEPER_IDEAS_ADMIN_TOKEN
  } else {
    process.env.KUEPER_IDEAS_ADMIN_TOKEN = secret
  }
  return renderToStaticMarkup(createElement(loadIdeasPage().default))
}

function assertDenied(html: string): void {
  assert.ok(html.includes(DENIED_MARKER), 'unauthorized response must render the denial notice')
  for (const id of SEED_IDS) {
    assert.ok(!html.includes(id), `unauthorized response leaked seed item ${id}`)
  }
}

function assertGranted(html: string): void {
  assert.ok(!html.includes(DENIED_MARKER), 'authorized response must not show the denial notice')
  for (const id of SEED_IDS) {
    assert.ok(html.includes(id), `authorized response is missing seed item ${id}`)
  }
  assert.ok(html.includes(`${seed.items.length} Themen`), 'authorized response must render the seed count')
}

after(() => {
  currentAuthorization = null
  if (originalSecret === undefined) {
    delete process.env.KUEPER_IDEAS_ADMIN_TOKEN
  } else {
    process.env.KUEPER_IDEAS_ADMIN_TOKEN = originalSecret
  }
})

test('rejects a missing Authorization header even with a configured secret', () => {
  assertDenied(renderIdeasPage(null, TOKEN))
})

test('rejects non-Bearer or malformed Authorization schemes', () => {
  assertDenied(renderIdeasPage(`Basic ${TOKEN}`, TOKEN))
  assertDenied(renderIdeasPage(TOKEN, TOKEN))
  assertDenied(renderIdeasPage('Bearer', TOKEN))
  assertDenied(renderIdeasPage('Bearer ', TOKEN))
})

test('rejects a wrong token of equal length', () => {
  assert.equal(WRONG_SAME_LENGTH.length, TOKEN.length)
  assertDenied(renderIdeasPage(`Bearer ${WRONG_SAME_LENGTH}`, TOKEN))
})

test('rejects a token whose length differs from the secret', () => {
  assert.notEqual(WRONG_SHORT.length, TOKEN.length)
  assert.notEqual(WRONG_LONG.length, TOKEN.length)
  assertDenied(renderIdeasPage(`Bearer ${WRONG_SHORT}`, TOKEN))
  assertDenied(renderIdeasPage(`Bearer ${WRONG_LONG}`, TOKEN))
  assertDenied(renderIdeasPage(`Bearer ${TOKEN} `, TOKEN))
})

test('fails closed when the server secret is unset', () => {
  assertDenied(renderIdeasPage(`Bearer ${TOKEN}`, undefined))
  // Empty received token would compare equal to an empty secret without the guard.
  assertDenied(renderIdeasPage('Bearer ', undefined))
})

test('fails closed when the server secret is empty', () => {
  assertDenied(renderIdeasPage(`Bearer ${TOKEN}`, ''))
  assertDenied(renderIdeasPage('Bearer ', ''))
})

test('grants access only for the exact bearer token', () => {
  assertGranted(renderIdeasPage(`Bearer ${TOKEN}`, TOKEN))
})
