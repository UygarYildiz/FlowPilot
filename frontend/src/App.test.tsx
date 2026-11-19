import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, expect, test, vi } from 'vitest'
import { createQueryClient, routes } from './router'

function respond(map: Record<string, { status: number; body?: unknown }>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      const path = input.split('?')[0]
      const hit = map[path] ?? { status: 404, body: { detail: 'yok' } }
      return new Response(hit.body === undefined ? null : JSON.stringify(hit.body), { status: hit.status })
    }),
  )
}

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

afterEach(() => vi.unstubAllGlobals())

test('giriş yapılmamışsa giriş sayfasına yönlendirir', async () => {
  respond({ '/api/auth/me': { status: 401, body: { detail: 'Giriş yapmanız gerekiyor.' } } })
  renderAt('/')
  expect(await screen.findByRole('heading', { name: 'Giriş yap' })).toBeDefined()
})

test('gelen kutusunu ve inceleme rozetini gösterir', async () => {
  respond({
    '/api/auth/me': {
      status: 200,
      body: { email: 'yonetici@atlas-endustri.example', name: 'Demo Yönetici', role: 'admin', departments: [] },
    },
    '/api/counts': {
      status: 200,
      body: {
        all: 1,
        needs_review: 1,
        departments: [
          {
            key: 'procurement',
            name: 'Satın Alma',
            description: '',
            open_count: 0,
            intents: [{ key: 'new_quote', label: 'Yeni teklif', description: '' }],
          },
        ],
      },
    },
    '/api/emails': {
      status: 200,
      body: {
        total: 1,
        items: [
          {
            id: 'e1',
            from_addr: 'satis@ozkanrulman.example',
            subject: 'Fiyat teklifimiz',
            snippet: 'Teklifimiz ektedir',
            received_at: '2026-11-19T09:00:00Z',
            status: 'needs_review',
            attachment_count: 1,
            routes: [
              {
                id: 'r1',
                department: 'procurement',
                intent: 'new_quote',
                priority: 'normal',
                confidence: 0.6,
                suggested_action: '',
                origin: 'ai',
                status: 'open',
                done_by: null,
                done_at: null,
              },
            ],
          },
        ],
      },
    },
  })
  renderAt('/')
  expect(await screen.findByText('Fiyat teklifimiz')).toBeDefined()
  expect(screen.getByText('Yeni teklif')).toBeDefined()
  expect(screen.getAllByText('İnsan baksın').length).toBeGreaterThan(0)
})
