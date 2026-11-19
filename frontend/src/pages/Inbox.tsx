import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import RouteTag from '../components/RouteTag'
import { api, type EmailQuery } from '../lib/api'
import { senderLabel, shortTime } from '../lib/format'
import { useCounts } from '../lib/hooks'
import { deptColor } from '../lib/text'

type Mode = 'all' | 'review' | 'approval' | 'department'

const ROUTE_STATUS_TABS = [
  { value: 'open', label: 'Açık işler' },
  { value: 'done', label: 'Kapananlar' },
  { value: 'any', label: 'Hepsi' },
] as const

const EMPTY: Record<Mode, string> = {
  all: 'Henüz e-posta yok. Kurgusal e-postaları içeri almak için: uv run flowpilot ingest seed',
  review: 'İnceleme bekleyen e-posta yok. Yapay zekânın emin olamadığı e-postalar burada toplanır.',
  approval: 'Onay bekleyen öneri yok. Departman ajanlarının hazırladığı öneriler burada toplanır.',
  department: 'Bu departmanın açık işi yok.',
}

function PaperclipIcon() {
  return (
    <svg viewBox="0 0 16 16" className="size-4 text-steel" aria-label="Ekli dosya var" role="img">
      <path
        d="M10.5 4.5 5.8 9.2a1.5 1.5 0 0 0 2.1 2.1l5-5a3 3 0 0 0-4.2-4.2l-5 5a4.5 4.5 0 0 0 6.4 6.4l4.2-4.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  )
}

export default function Inbox({ mode }: { mode: Mode }) {
  const { key } = useParams()
  const [params, setParams] = useSearchParams()
  const routeStatus = (params.get('durum') ?? 'open') as 'open' | 'done' | 'any'
  const search = params.get('ara') ?? ''
  const [draft, setDraft] = useState(search)
  const counts = useCounts()

  const query: EmailQuery = {
    view: mode,
    department: mode === 'department' ? key : undefined,
    route_status: mode === 'department' ? routeStatus : undefined,
    q: search || undefined,
  }
  const emails = useQuery({
    queryKey: ['emails', query],
    queryFn: () => api.emails(query),
    placeholderData: keepPreviousData,
  })

  const department = counts.data?.departments.find((d) => d.key === key)
  const title =
    mode === 'review'
      ? 'İnsan baksın'
      : mode === 'approval'
        ? 'Onay bekleyenler'
        : mode === 'department'
          ? (department?.name ?? '')
          : 'Tüm e-postalar'
  const subtitle =
    mode === 'review'
      ? 'Yapay zekânın emin olamadığı ya da hiçbir departmanla eşleştiremediği e-postalar. Doğru departmana yönlendir ya da ilgisizse kapat.'
      : mode === 'approval'
        ? 'Departman ajanlarının hazırladığı, onayını bekleyen öneriler. Onaylanan öneri bir kez uygulanır; reddedilen hiç uygulanmaz.'
        : mode === 'department'
          ? department?.description
          : 'Gelen her e-posta ve yapay zekânın onu hangi departmana gönderdiği.'

  const submitSearch = (event: FormEvent) => {
    event.preventDefault()
    const next = new URLSearchParams(params)
    if (draft.trim()) next.set('ara', draft.trim())
    else next.delete('ara')
    setParams(next)
  }

  return (
    <div className="px-5 lg:px-10 py-8 max-w-6xl">
      <header className="flex flex-wrap items-end gap-x-8 gap-y-4 justify-between">
        <div className="max-w-2xl">
          <h1 className="wide text-3xl font-extrabold flex items-center gap-3">
            {mode === 'department' && key && (
              <span className="size-4 rounded-sm" style={{ background: deptColor(key) }} aria-hidden />
            )}
            {title}
          </h1>
          {subtitle && <p className="mt-2 text-steel leading-relaxed">{subtitle}</p>}
        </div>
        <form onSubmit={submitSearch} role="search" className="w-full sm:w-72">
          <label className="sr-only" htmlFor="ara">
            Konu, gönderen ya da metinde ara
          </label>
          <input
            id="ara"
            className="field"
            placeholder="Konu, gönderen ya da metinde ara"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
        </form>
      </header>

      {mode === 'department' && (
        <div className="mt-6 flex gap-1 border-b border-rule" role="tablist">
          {ROUTE_STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              role="tab"
              aria-selected={routeStatus === tab.value}
              className={`px-3 py-2 -mb-px border-b-2 cursor-pointer ${
                routeStatus === tab.value ? 'border-ink font-semibold' : 'border-transparent text-steel'
              }`}
              onClick={() => {
                const next = new URLSearchParams(params)
                next.set('durum', tab.value)
                setParams(next)
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      <section className="mt-6" aria-live="polite">
        {emails.isPending && <p className="text-steel">Yükleniyor…</p>}
        {emails.isError && <p className="text-danger">E-postalar yüklenemedi: {emails.error.message}</p>}
        {emails.data && emails.data.items.length === 0 && (
          <p className="rounded-md border border-dashed border-rule bg-panel px-5 py-8 text-steel">
            {search ? `"${search}" için sonuç yok.` : EMPTY[mode]}
          </p>
        )}
        {emails.data && emails.data.items.length > 0 && (
          <>
            <p className="text-sm text-steel mb-2 num">{emails.data.total} e-posta</p>
            <ul className="rounded-md border border-rule bg-panel divide-y divide-rule overflow-hidden">
              {emails.data.items.map((email) => {
                const sender = senderLabel(email.from_addr)
                const review = email.status === 'needs_review'
                const closed = email.status === 'done'
                return (
                  <li key={email.id} className="relative">
                    {review && <span className="absolute inset-y-0 left-0 w-1 bg-signal" aria-hidden />}
                    <Link
                      to={`/eposta/${email.id}`}
                      className={`grid grid-cols-[1fr_auto] gap-x-4 gap-y-1.5 px-5 py-3.5 hover:bg-ground/60 ${
                        closed ? 'opacity-60' : ''
                      }`}
                    >
                      <span className="min-w-0 flex items-baseline gap-2">
                        <span className="font-semibold truncate">{sender.name}</span>
                        <span className="text-sm text-steel truncate">{sender.domain}</span>
                      </span>
                      <span className="text-sm text-steel num whitespace-nowrap">
                        {shortTime(email.received_at)}
                      </span>
                      <span className="min-w-0 col-span-2 sm:col-span-1">
                        <span className="block truncate font-medium">{email.subject || '(konusuz)'}</span>
                        <span className="block truncate text-sm text-steel">{email.snippet}</span>
                      </span>
                      <span className="hidden sm:flex items-start justify-end">
                        {email.attachment_count > 0 && <PaperclipIcon />}
                      </span>
                      <span className="col-span-2 flex flex-wrap gap-1.5">
                        {review && (
                          <span className="rounded bg-signal-soft px-1.5 py-0.5 text-xs font-semibold">
                            İnsan baksın
                          </span>
                        )}
                        {closed && (
                          <span className="rounded bg-ground px-1.5 py-0.5 text-xs font-semibold text-steel">
                            Kapandı
                          </span>
                        )}
                        {email.routes.map((route) => (
                          <RouteTag key={route.id} route={route} counts={counts.data} />
                        ))}
                      </span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </>
        )}
      </section>
    </div>
  )
}
