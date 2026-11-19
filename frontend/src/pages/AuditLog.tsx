import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { api, type AuditItem, type Counts } from '../lib/api'
import { fullTime } from '../lib/format'
import { keys, useCounts } from '../lib/hooks'
import { departmentName, describeAction, describeActor } from '../lib/text'

const PAGE = 50

/** Olayın kısa ayrıntısı: gerekçe, öneri özeti ya da hata. */
function detail(item: AuditItem, counts: Counts | undefined): string | null {
  const d = item.data
  for (const key of ['reason', 'note', 'error', 'summary'] as const) {
    const value = d[key]
    if (typeof value === 'string' && value) return value
  }
  if (Array.isArray(d.routes)) {
    const names = d.routes
      .map((r) => (r && typeof r === 'object' && 'department' in r ? String(r.department) : ''))
      .filter(Boolean)
    if (names.length) return names.map((n) => departmentName(counts, n)).join(', ')
  }
  return null
}

/** Tüm sistemin denetim kaydı (yalnızca yönetici). Kayıtlar yalnızca eklenir. */
export default function AuditLog() {
  const [params, setParams] = useSearchParams()
  const search = params.get('ara') ?? ''
  const offset = Number(params.get('bas') ?? '0') || 0
  const [draft, setDraft] = useState(search)
  const counts = useCounts()
  const log = useQuery({
    queryKey: [...keys.audit, search, offset],
    queryFn: () => api.audit(search, offset),
    placeholderData: keepPreviousData,
  })

  const go = (next: { ara?: string; bas?: number }) => {
    const p = new URLSearchParams()
    const q = next.ara ?? search
    const start = next.bas ?? 0
    if (q) p.set('ara', q)
    if (start) p.set('bas', String(start))
    setParams(p)
  }
  const submit = (event: FormEvent) => {
    event.preventDefault()
    go({ ara: draft.trim(), bas: 0 })
  }

  return (
    <div className="px-5 lg:px-10 py-8 max-w-6xl">
      <header className="flex flex-wrap items-end gap-x-8 gap-y-4 justify-between">
        <div className="max-w-2xl">
          <h1 className="wide text-3xl font-extrabold">Denetim kaydı</h1>
          <p className="mt-2 text-steel">
            Sistemde olan her şey: kim, ne zaman, ne yaptı. Kayıtlar yalnızca eklenir; değiştirilemez ve silinemez.
          </p>
        </div>
        <form onSubmit={submit} className="flex gap-2" role="search">
          <input
            className="field w-56"
            placeholder="Kişi ya da işlem ara"
            aria-label="Denetim kaydında ara"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <button className="btn btn-quiet">Ara</button>
        </form>
      </header>

      {log.isError && <p className="mt-6 text-danger">{log.error.message}</p>}
      {log.data && (
        <>
          <p className="mt-6 text-sm text-steel num">{log.data.total} kayıt</p>
          {log.data.items.length === 0 ? (
            <p className="mt-4 rounded-md border border-dashed border-rule px-5 py-4 text-steel">
              {search ? `"${search}" için kayıt yok.` : 'Henüz kayıt yok.'}
            </p>
          ) : (
            <ol className="mt-3 divide-y divide-rule rounded-md border border-rule bg-panel">
              {log.data.items.map((item) => {
                const note = detail(item, counts.data)
                return (
                  <li
                    key={item.id}
                    className="grid gap-x-6 gap-y-1 px-5 py-3 md:grid-cols-[11rem_minmax(0,1fr)_minmax(0,14rem)]"
                  >
                    <p className="text-sm text-steel num">{fullTime(item.at)}</p>
                    <div className="min-w-0">
                      <p className="font-semibold">{describeAction(item.action)}</p>
                      {item.email_subject !== null && (
                        <Link to={`/eposta/${item.entity_id}`} className="text-sm underline break-words">
                          {item.email_subject || '(konusuz)'}
                        </Link>
                      )}
                      {note && <p className="text-sm text-ink/80 break-words">“{note}”</p>}
                    </div>
                    <p className="text-sm text-steel break-all md:text-right">{describeActor(item.actor)}</p>
                  </li>
                )
              })}
            </ol>
          )}
          {log.data.total > PAGE && (
            <div className="mt-4 flex items-center gap-3 text-sm">
              <button
                className="btn btn-quiet"
                disabled={offset === 0}
                onClick={() => go({ bas: Math.max(0, offset - PAGE) })}
              >
                Daha yeni
              </button>
              <span className="text-steel num">
                {offset + 1}–{Math.min(offset + PAGE, log.data.total)} / {log.data.total}
              </span>
              <button
                className="btn btn-quiet"
                disabled={offset + PAGE >= log.data.total}
                onClick={() => go({ bas: offset + PAGE })}
              >
                Daha eski
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
