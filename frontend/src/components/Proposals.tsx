import { useState } from 'react'
import type { AgentRun, Counts, Proposal, User } from '../lib/api'
import { fullTime } from '../lib/format'
import { departmentName, describeActor, proposalStatusLabel } from '../lib/text'

const STATUS_STYLE: Record<Proposal['status'], string> = {
  pending: 'bg-signal-soft text-ink border-signal',
  approved: 'text-steel border-rule',
  rejected: 'text-steel border-rule',
  executed: 'text-ok border-ok',
  failed: 'text-danger border-danger',
}

function Value({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="text-steel">—</span>
  if (typeof value === 'number') return <span className="num">{value.toLocaleString('tr-TR')}</span>
  if (typeof value === 'string' || typeof value === 'boolean') return <>{String(value)}</>
  return <pre className="whitespace-pre-wrap font-sans text-xs">{JSON.stringify(value, null, 2)}</pre>
}

function Payload({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data)
  if (entries.length === 0) return null
  return (
    <dl className="mt-3 grid grid-cols-[minmax(6rem,auto)_1fr] gap-x-3 gap-y-1 text-sm">
      {entries.map(([key, value]) => (
        <div key={key} className="contents">
          <dt className="text-steel break-all">{key}</dt>
          <dd className="min-w-0 break-words">
            <Value value={value} />
          </dd>
        </div>
      ))}
    </dl>
  )
}

interface CardProps {
  proposal: Proposal
  canDecide: boolean
  pending: boolean
  onApprove: () => void
  onReject: (reason: string) => void
  onRetry: () => void
}

function ProposalCard({ proposal, canDecide, pending, onApprove, onReject, onRetry }: CardProps) {
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const decidable = canDecide && proposal.current

  return (
    <li className="rounded-md border border-rule bg-panel px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs text-steel">{proposal.type_label}</p>
          <p className="font-semibold leading-snug">{proposal.summary || proposal.type_label}</p>
        </div>
        <span className={`shrink-0 rounded border px-1.5 py-0.5 text-xs font-bold ${STATUS_STYLE[proposal.status]}`}>
          {proposalStatusLabel[proposal.status]}
        </span>
      </div>
      {!proposal.current && (
        <p className="mt-2 text-xs text-steel">Yönlendirme düzeltildiği için bu öneri artık geçerli değil.</p>
      )}

      <Payload data={proposal.payload} />

      {proposal.decided_by && proposal.status !== 'pending' && (
        <p className="mt-3 text-xs text-steel">
          {proposal.status === 'rejected' ? 'Reddeden' : 'Onaylayan'}: {describeActor(proposal.decided_by)}
          {proposal.decided_at && `, ${fullTime(proposal.decided_at)}`}
        </p>
      )}
      {proposal.reason && <p className="mt-1 text-sm">“{proposal.reason}”</p>}
      {proposal.status === 'failed' && proposal.error && (
        <p className="mt-2 text-sm text-danger">
          Hata ({proposal.attempts}. deneme): {proposal.error}
        </p>
      )}

      {decidable && proposal.status === 'pending' && !rejecting && (
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="btn" disabled={pending} onClick={onApprove}>
            Onayla ve uygula
          </button>
          <button className="btn btn-quiet" disabled={pending} onClick={() => setRejecting(true)}>
            Reddet
          </button>
        </div>
      )}
      {decidable && proposal.status === 'pending' && rejecting && (
        <form
          className="mt-3 space-y-2"
          onSubmit={(e) => {
            e.preventDefault()
            onReject(reason)
          }}
        >
          <label className="block text-sm">
            <span className="text-steel">Neden reddediyorsun?</span>
            <input
              className="field mt-1"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              autoFocus
              required
            />
          </label>
          <div className="flex gap-2">
            <button className="btn" disabled={pending || !reason.trim()}>
              Reddet
            </button>
            <button type="button" className="btn btn-quiet" onClick={() => setRejecting(false)}>
              Vazgeç
            </button>
          </div>
        </form>
      )}
      {decidable && proposal.status === 'failed' && (
        <button className="btn btn-quiet mt-3" disabled={pending} onClick={onRetry}>
          Yeniden dene
        </button>
      )}
    </li>
  )
}

interface Props {
  proposals: Proposal[]
  runs: AgentRun[]
  counts: Counts | undefined
  user: User
  pending: boolean
  error: string | null
  onApprove: (id: string) => void
  onReject: (id: string, reason: string) => void
  onRetry: (id: string) => void
}

/** Departman ajanlarının önerileri: insan onaylar ya da gerekçeyle reddeder (ADR-014). */
export default function Proposals({
  proposals,
  runs,
  counts,
  user,
  pending,
  error,
  onApprove,
  onReject,
  onRetry,
}: Props) {
  const failedRuns = runs.filter((r) => r.status === 'failed')
  if (proposals.length === 0 && failedRuns.length === 0) return null
  const departments = [...new Set([...runs.map((r) => r.department), ...proposals.map((p) => p.department)])]

  return (
    <section className="rounded-md border border-ink/20 bg-panel">
      <h2 className="wide font-extrabold border-b border-dashed border-rule px-5 py-3">Ajan önerileri</h2>
      <div className="px-5 py-4 space-y-5">
        {departments.map((department) => {
          const own = proposals.filter((p) => p.department === department)
          const failed = failedRuns.find((r) => r.department === department)
          const canDecide = user.role === 'admin' || user.departments.includes(department)
          return (
            <div key={department}>
              <p className="text-sm text-steel">{departmentName(counts, department)}</p>
              {failed && (
                <p className="mt-2 text-sm text-danger">
                  Ajan bu e-postayı işleyemedi ({failed.attempts}. deneme): {failed.error}
                </p>
              )}
              {own.length > 0 && (
                <ul className="mt-2 space-y-3">
                  {own.map((p) => (
                    <ProposalCard
                      key={p.id}
                      proposal={p}
                      canDecide={canDecide}
                      pending={pending}
                      onApprove={() => onApprove(p.id)}
                      onReject={(reason) => onReject(p.id, reason)}
                      onRetry={() => onRetry(p.id)}
                    />
                  ))}
                </ul>
              )}
            </div>
          )
        })}
        {error && <p className="text-sm text-danger">{error}</p>}
        <p className="text-xs text-steel">
          Onaylanan öneri bir kez uygulanır. Reddedilen öneri hiçbir zaman uygulanmaz.
        </p>
      </div>
    </section>
  )
}
