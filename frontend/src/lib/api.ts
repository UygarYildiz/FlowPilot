// Backend API'si (backend/src/flowpilot/api/schemas.py ile aynı biçim).

export type Priority = 'low' | 'normal' | 'high' | 'urgent'
export type EmailStatus =
  | 'received'
  | 'classifying'
  | 'routed'
  | 'needs_review'
  | 'processing'
  | 'awaiting_approval'
  | 'done'

export interface User {
  email: string
  name: string
  role: 'admin' | 'department_user'
  departments: string[]
}

export interface Intent {
  key: string
  label: string
  description: string
}

export interface Department {
  key: string
  name: string
  description: string
  intents: Intent[]
  open_count: number
}

export interface Counts {
  all: number
  needs_review: number
  awaiting_approval: number
  departments: Department[]
}

export interface Route {
  id: string
  department: string
  intent: string | null
  priority: Priority
  confidence: number
  suggested_action: string
  origin: 'ai' | 'manual'
  status: 'open' | 'done'
  done_by: string | null
  done_at: string | null
}

export interface EmailListItem {
  id: string
  from_addr: string
  subject: string
  snippet: string
  received_at: string
  status: EmailStatus
  attachment_count: number
  routes: Route[]
}

export interface Attachment {
  id: string
  filename: string
  mime: string
  size: number
  parse_status: 'ok' | 'unsupported' | 'failed'
  parse_error: string | null
  text_preview: string | null
  text_truncated: boolean
}

export interface Decision {
  id: string
  created_at: string
  model: string
  prompt_version: string
  reasoning: string
  needs_review: boolean
  review_reason: string | null
  routes: Route[]
}

export interface AuditEvent {
  at: string
  actor: string
  action: string
  data: Record<string, unknown>
}

export type ProposalStatus = 'pending' | 'approved' | 'rejected' | 'executed' | 'failed'

export interface Proposal {
  id: string
  department: string
  type: string
  type_label: string
  summary: string
  payload: Record<string, unknown>
  status: ProposalStatus
  requires_approval: boolean
  created_at: string
  decided_by: string | null
  decided_at: string | null
  reason: string | null
  executed_at: string | null
  attempts: number
  result: Record<string, unknown> | null
  error: string | null
  /** Öneri e-postanın geçerli yönlendirmesine mi ait? Düzeltilmişse eskidir. */
  current: boolean
}

export interface AgentRun {
  id: string
  department: string
  status: 'running' | 'succeeded' | 'failed'
  attempts: number
  error: string | null
  started_at: string
  finished_at: string | null
}

export interface AuditItem {
  id: number
  at: string
  actor: string
  action: string
  entity_type: string
  entity_id: string
  email_subject: string | null
  data: Record<string, unknown>
}

export interface EmailDetail {
  id: string
  message_id: string
  source: string
  from_addr: string
  to_addrs: string[]
  cc_addrs: string[]
  subject: string
  body_text: string
  received_at: string
  status: EmailStatus
  attachments: Attachment[]
  current_decision: Decision | null
  previous_decisions: Decision[]
  agent_runs: AgentRun[]
  proposals: Proposal[]
  events: AuditEvent[]
}

export interface RouteInput {
  department: string
  intent: string
  priority: Priority
}

export interface EmailQuery {
  view: 'all' | 'review' | 'approval' | 'department'
  department?: string
  route_status?: 'open' | 'done' | 'any'
  q?: string
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: 'same-origin',
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  })
  if (!response.ok) {
    let message = `İstek başarısız oldu (${response.status}).`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      // gövde JSON değil; varsayılan mesaj kalır
    }
    throw new ApiError(response.status, message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  me: () => request<User>('/api/auth/me'),
  login: (email: string, password: string) => post<User>('/api/auth/login', { email, password }),
  logout: () => request<void>('/api/auth/logout', { method: 'POST' }),
  counts: () => request<Counts>('/api/counts'),
  emails: (query: EmailQuery) => {
    const params = new URLSearchParams({ view: query.view })
    if (query.department) params.set('department', query.department)
    if (query.route_status) params.set('route_status', query.route_status)
    if (query.q) params.set('q', query.q)
    return request<{ items: EmailListItem[]; total: number }>(`/api/emails?${params}`)
  },
  email: (id: string) => request<EmailDetail>(`/api/emails/${id}`),
  correct: (id: string, routes: RouteInput[], reason: string) =>
    post<EmailDetail>(`/api/emails/${id}/correction`, { routes, reason }),
  dismiss: (id: string, reason: string) => post<EmailDetail>(`/api/emails/${id}/dismiss`, { reason }),
  routeDone: (routeId: string, reason = '') =>
    post<EmailDetail>(`/api/routes/${routeId}/done`, { reason }),
  approve: (proposalId: string) => post<EmailDetail>(`/api/proposals/${proposalId}/approve`, {}),
  reject: (proposalId: string, reason: string) =>
    post<EmailDetail>(`/api/proposals/${proposalId}/reject`, { reason }),
  retry: (proposalId: string) => post<EmailDetail>(`/api/proposals/${proposalId}/retry`, {}),
  audit: (q: string, offset: number) => {
    const params = new URLSearchParams({ limit: '50', offset: String(offset) })
    if (q) params.set('q', q)
    return request<{ items: AuditItem[]; total: number }>(`/api/audit?${params}`)
  },
  attachmentUrl: (emailId: string, attachmentId: string) =>
    `/api/emails/${emailId}/attachments/${attachmentId}`,
}
