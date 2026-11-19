import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import CorrectionForm from '../components/CorrectionForm'
import RoutingSlip from '../components/RoutingSlip'
import { api, type AuditEvent, type EmailDetail, type RouteInput } from '../lib/api'
import { fileSize, fullTime } from '../lib/format'
import { keys, useCounts, useMe } from '../lib/hooks'
import { describeAction, describeActor, statusLabel } from '../lib/text'

const PARSE_LABEL = {
  ok: 'Metni okundu',
  unsupported: 'Metni okunamadı (desteklenmeyen dosya türü)',
  failed: 'Dosya bozuk, okunamadı',
} as const

function Attachments({ email }: { email: EmailDetail }) {
  if (email.attachments.length === 0) return null
  return (
    <section className="mt-8">
      <h2 className="wide font-bold">Ekler</h2>
      <ul className="mt-3 space-y-2">
        {email.attachments.map((a) => (
          <li key={a.id} className="rounded-md border border-rule bg-panel">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3">
              <a className="font-semibold underline break-all" href={api.attachmentUrl(email.id, a.id)}>
                {a.filename}
              </a>
              <span className="text-sm text-steel num">{fileSize(a.size)}</span>
              <span className={`text-sm ${a.parse_status === 'ok' ? 'text-steel' : 'text-danger'}`}>
                {PARSE_LABEL[a.parse_status]}
              </span>
            </div>
            {a.text_preview && (
              <details className="border-t border-rule">
                <summary className="px-4 py-2 text-sm cursor-pointer">Sistemin okuduğu metni göster</summary>
                <pre className="px-4 pb-4 text-sm whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-auto">
                  {a.text_preview}
                  {a.text_truncated && '\n…'}
                </pre>
              </details>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

function History({ events }: { events: AuditEvent[] }) {
  return (
    <section className="mt-8">
      <h2 className="wide font-bold">Geçmiş</h2>
      <ol className="mt-3 border-l-2 border-rule ml-1.5 space-y-4">
        {events.map((event, index) => (
          <li key={index} className="relative pl-5">
            <span className="absolute -left-[7px] top-1.5 size-3 rounded-full border-2 border-rule bg-ground" aria-hidden />
            <p className="text-sm font-semibold">{describeAction(event.action)}</p>
            <p className="text-sm text-steel">
              {describeActor(event.actor)}, {fullTime(event.at)}
            </p>
            {typeof event.data.reason === 'string' && event.data.reason && (
              <p className="text-sm mt-0.5">“{event.data.reason}”</p>
            )}
            {typeof event.data.note === 'string' && event.data.note && (
              <p className="text-sm mt-0.5">“{event.data.note}”</p>
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}

export default function EmailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const me = useMe()
  const counts = useCounts()
  const queryClient = useQueryClient()
  const email = useQuery({ queryKey: keys.email(id), queryFn: () => api.email(id) })
  const [editing, setEditing] = useState(false)
  const [dismissReason, setDismissReason] = useState('')
  const [dismissing, setDismissing] = useState(false)

  const refresh = (detail: EmailDetail) => {
    queryClient.setQueryData(keys.email(id), detail)
    queryClient.invalidateQueries({ queryKey: keys.emails })
    queryClient.invalidateQueries({ queryKey: keys.counts })
  }
  const correct = useMutation({
    mutationFn: ({ routes, reason }: { routes: RouteInput[]; reason: string }) => api.correct(id, routes, reason),
    onSuccess: (detail) => {
      refresh(detail)
      setEditing(false)
    },
  })
  const done = useMutation({ mutationFn: (routeId: string) => api.routeDone(routeId), onSuccess: refresh })
  const dismiss = useMutation({
    mutationFn: () => api.dismiss(id, dismissReason),
    onSuccess: (detail) => {
      refresh(detail)
      setDismissing(false)
    },
  })

  if (email.isPending || !me.data) return <p className="p-8 text-steel">Yükleniyor…</p>
  if (email.isError)
    return (
      <div className="p-8">
        <p className="text-danger">{email.error.message}</p>
        <Link to="/" className="underline">
          Tüm e-postalara dön
        </Link>
      </div>
    )

  const data = email.data
  const user = me.data
  const decision = data.current_decision
  const canDismiss = user.role === 'admin' && data.status !== 'done'

  return (
    <div className="px-5 lg:px-10 py-8 max-w-7xl">
      <button className="text-sm text-steel underline cursor-pointer" onClick={() => navigate(-1)}>
        Listeye dön
      </button>
      <div className="mt-4 grid gap-10 xl:grid-cols-[minmax(0,1fr)_26rem]">
        <article className="min-w-0">
          <p className="text-sm text-steel">{statusLabel[data.status]}</p>
          <h1 className="wide text-2xl lg:text-3xl font-extrabold leading-tight mt-1">
            {data.subject || '(konusuz)'}
          </h1>
          <dl className="mt-4 grid grid-cols-[5rem_1fr] gap-y-1 text-sm">
            <dt className="text-steel">Gönderen</dt>
            <dd className="font-semibold break-all">{data.from_addr}</dd>
            <dt className="text-steel">Alıcı</dt>
            <dd className="break-all">{data.to_addrs.join(', ') || '-'}</dd>
            {data.cc_addrs.length > 0 && (
              <>
                <dt className="text-steel">CC</dt>
                <dd className="break-all">{data.cc_addrs.join(', ')}</dd>
              </>
            )}
            <dt className="text-steel">Tarih</dt>
            <dd>{fullTime(data.received_at)}</dd>
          </dl>
          <div className="mt-6 rounded-md border border-rule bg-panel px-6 py-5 whitespace-pre-wrap leading-relaxed max-w-[75ch]">
            {data.body_text || <span className="text-steel">(gövde boş)</span>}
          </div>
          <Attachments email={data} />
          <History events={data.events} />
        </article>

        <aside className="space-y-4 xl:sticky xl:top-6 self-start">
          {decision ? (
            <RoutingSlip
              decision={decision}
              counts={counts.data}
              user={user}
              closed={data.status === 'done'}
              donePending={done.isPending}
              onDone={(route) => done.mutate(route.id)}
            />
          ) : (
            <p className="rounded-md border border-dashed border-rule px-5 py-4 text-steel">
              Bu e-posta henüz sınıflandırılmadı. Sınıflandırmak için: uv run flowpilot classify
            </p>
          )}
          {done.isError && <p className="text-sm text-danger">{done.error.message}</p>}

          {data.status !== 'done' && counts.data && (
            <div className="rounded-md border border-rule bg-panel px-5 py-4">
              {editing ? (
                <CorrectionForm
                  counts={counts.data}
                  current={decision?.routes ?? []}
                  pending={correct.isPending}
                  error={correct.isError ? correct.error.message : null}
                  onSubmit={(routes, reason) => correct.mutate({ routes, reason })}
                  onCancel={() => setEditing(false)}
                />
              ) : dismissing ? (
                <form
                  className="space-y-3"
                  onSubmit={(e) => {
                    e.preventDefault()
                    dismiss.mutate()
                  }}
                >
                  <label className="block text-sm">
                    <span className="text-steel">Neden ilgisiz? (ör. reklam, iş başvurusu)</span>
                    <input
                      className="field mt-1"
                      value={dismissReason}
                      onChange={(e) => setDismissReason(e.target.value)}
                      required
                    />
                  </label>
                  {dismiss.isError && <p className="text-sm text-danger">{dismiss.error.message}</p>}
                  <div className="flex gap-2">
                    <button className="btn" disabled={dismiss.isPending || !dismissReason.trim()}>
                      İlgisiz olarak kapat
                    </button>
                    <button type="button" className="btn btn-quiet" onClick={() => setDismissing(false)}>
                      Vazgeç
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <button className="btn" onClick={() => setEditing(true)}>
                    {decision?.needs_review ? 'Departmana yönlendir' : 'Yönlendirmeyi düzelt'}
                  </button>
                  {canDismiss && (
                    <button className="btn btn-quiet" onClick={() => setDismissing(true)}>
                      İlgisiz olarak kapat
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {data.previous_decisions.length > 0 && (
            <details className="rounded-md border border-rule bg-panel px-5 py-3 text-sm">
              <summary className="cursor-pointer">Önceki kararlar ({data.previous_decisions.length})</summary>
              <div className="mt-3 space-y-4">
                {data.previous_decisions.map((d) => (
                  <RoutingSlip key={d.id} decision={d} counts={counts.data} user={user} readOnly />
                ))}
              </div>
            </details>
          )}
        </aside>
      </div>
    </div>
  )
}
