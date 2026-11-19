import { useQuery } from '@tanstack/react-query'
import { api } from './api'

export const keys = {
  me: ['me'] as const,
  counts: ['counts'] as const,
  emails: ['emails'] as const,
  email: (id: string) => ['email', id] as const,
  audit: ['audit'] as const,
}

export function useMe() {
  return useQuery({ queryKey: keys.me, queryFn: api.me, retry: false })
}

export function useCounts() {
  return useQuery({ queryKey: keys.counts, queryFn: api.counts })
}
