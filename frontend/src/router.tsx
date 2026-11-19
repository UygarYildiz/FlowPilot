import { QueryClient } from '@tanstack/react-query'
import type { RouteObject } from 'react-router'
import AuditLog from './pages/AuditLog'
import EmailPage from './pages/EmailPage'
import Inbox from './pages/Inbox'
import Layout from './pages/Layout'
import Login from './pages/Login'

export const routes: RouteObject[] = [
  { path: '/giris', element: <Login /> },
  {
    element: <Layout />,
    children: [
      { index: true, element: <Inbox mode="all" /> },
      { path: 'inceleme', element: <Inbox mode="review" /> },
      { path: 'onay', element: <Inbox mode="approval" /> },
      { path: 'denetim', element: <AuditLog /> },
      { path: 'departman/:key', element: <Inbox mode="department" /> },
      { path: 'eposta/:id', element: <EmailPage /> },
    ],
  },
]

export function createQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { staleTime: 15_000, refetchOnWindowFocus: true } } })
}
