import type { Counts, Decision, Route, User } from '../lib/api'
import { fullTime, percent } from '../lib/format'
import { deptColor, departmentName, intentLabel, priorityLabel, UNKNOWN } from '../lib/text'

const THRESHOLD = 0.75

/** Güven göstergesi: eşiğin (0,75) altı insana gider; çizgi eşiği gösterir. */
function Confidence({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2" title={`Güven ${percent(value)}; ${percent(THRESHOLD)} altı insana gider`}>
      <div className="relative h-1.5 w-24 rounded-full bg-rule overflow-hidden" aria-hidden>
        <div className="absolute inset-y-0 left-0" style={{ width: `${value * 100}%`, background: color }} />
        <div className="absolute inset-y-[-2px] w-px bg-ink/60" style={{ left: `${THRESHOLD * 100}%` }} />
      </div>
      <span className="num text-sm font-semibold">{percent(value)}</span>
      <span className="sr-only">güven</span>
    </div>
  )
}

function Stamp({ route, counts }: { route: Route; counts: Counts | undefined }) {
  const color = deptColor(route.department)
  return (
    <span
      className="wide inline-block rounded-[3px] border-2 px-2 py-0.5 text-sm font-extrabold -rotate-2 bg-white"
      style={{ borderColor: color, color }}
    >
      {departmentName(counts, route.department)}
    </span>
  )
}

interface Props {
  decision: Decision
  counts: Counts | undefined
  user: User
  onDone?: (route: Route) => void
  donePending?: boolean
  /** Geçmiş kararlar için: işlem düğmeleri gösterilmez. */
  readOnly?: boolean
  /** E-posta kapandıysa "insan baksın" uyarısı artık gösterilmez. */
  closed?: boolean
}

export default function RoutingSlip({ decision, counts, user, onDone, donePending, readOnly, closed }: Props) {
  const manual = decision.model === 'manual'
  return (
    <div className="rounded-md border border-ink/20 bg-panel shadow-[0_1px_0_var(--color-rule),0_8px_24px_-16px_rgb(22_38_58/0.35)]">
      <div className="flex items-baseline justify-between gap-4 border-b border-dashed border-rule px-5 py-3">
        <h2 className="wide font-extrabold">Yönlendirme fişi</h2>
        <p className="text-xs text-steel text-right">
          {manual ? 'Elle düzeltildi' : `Yapay zekâ: ${decision.model.replace(/^[a-z]+:/, '')}`}
          <br />
          {fullTime(decision.created_at)}
        </p>
      </div>

      {decision.needs_review && !closed && !readOnly && (
        <div className="bg-signal-soft border-b border-signal px-5 py-3 text-sm">
          <p className="font-bold">İnsan baksın</p>
          <p className="text-ink/80">
            {decision.review_reason?.includes('eşleşmedi')
              ? 'Yapay zekâ bu e-postayı hiçbir departmanla eşleştiremedi.'
              : decision.review_reason?.includes('eşiğin')
                ? `Yapay zekâ kararından yeterince emin değil (${percent(THRESHOLD)} altı).`
                : (decision.review_reason ?? 'Yapay zekâ geçerli bir karar üretemedi.')}
          </p>
        </div>
      )}

      <ol className="divide-y divide-rule">
        {decision.routes.length === 0 && (
          <li className="px-5 py-4 text-steel text-sm">Bu kararda departman yok.</li>
        )}
        {decision.routes.map((route) => {
          const canClose =
            !readOnly &&
            onDone !== undefined &&
            route.department !== UNKNOWN &&
            route.status === 'open' &&
            !decision.needs_review &&
            (user.role === 'admin' || user.departments.includes(route.department))
          return (
            <li key={route.id} className="px-5 py-4 space-y-2.5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <Stamp route={route} counts={counts} />
                {route.department !== UNKNOWN && route.origin === 'ai' && (
                  <Confidence value={route.confidence} color={deptColor(route.department)} />
                )}
              </div>
              <dl className="grid grid-cols-[7rem_1fr] gap-y-1 text-sm">
                <dt className="text-steel">E-posta türü</dt>
                <dd className="font-semibold">{intentLabel(counts, route.department, route.intent)}</dd>
                {route.department !== UNKNOWN && (
                  <>
                    <dt className="text-steel">Öncelik</dt>
                    <dd className={route.priority === 'urgent' || route.priority === 'high' ? 'font-semibold' : ''}>
                      {priorityLabel[route.priority]}
                    </dd>
                  </>
                )}
                {route.suggested_action && (
                  <>
                    <dt className="text-steel">Yapılacak iş</dt>
                    <dd>{route.suggested_action}</dd>
                  </>
                )}
              </dl>
              {route.status === 'done' ? (
                <p className="text-sm text-steel">
                  Kapatıldı: {route.done_by}
                  {route.done_at && `, ${fullTime(route.done_at)}`}
                </p>
              ) : (
                canClose && (
                  <button className="btn btn-quiet text-sm" disabled={donePending} onClick={() => onDone?.(route)}>
                    İşlendi olarak kapat
                  </button>
                )
              )}
            </li>
          )
        })}
      </ol>

      {decision.reasoning && (
        <div className="border-t border-dashed border-rule px-5 py-3 text-sm">
          <p className="text-steel">{manual ? 'Düzeltme gerekçesi' : 'Yapay zekânın gerekçesi'}</p>
          <p className="mt-1 leading-relaxed whitespace-pre-line">{decision.reasoning}</p>
        </div>
      )}
    </div>
  )
}
