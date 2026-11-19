import { type FormEvent, useState } from 'react'
import type { Counts, Priority, Route, RouteInput } from '../lib/api'
import { priorityLabel, UNKNOWN } from '../lib/text'

interface Props {
  counts: Counts
  current: Route[]
  pending: boolean
  error: string | null
  onSubmit: (routes: RouteInput[], reason: string) => void
  onCancel: () => void
}

function firstIntent(counts: Counts, department: string) {
  return counts.departments.find((d) => d.key === department)?.intents[0]?.key ?? ''
}

export default function CorrectionForm({ counts, current, pending, error, onSubmit, onCancel }: Props) {
  const initial = current
    .filter((r) => r.department !== UNKNOWN && r.intent)
    .map((r) => ({ department: r.department, intent: r.intent as string, priority: r.priority }))
  const [rows, setRows] = useState<RouteInput[]>(
    initial.length
      ? initial
      : [{ department: counts.departments[0].key, intent: firstIntent(counts, counts.departments[0].key), priority: 'normal' }],
  )
  const [reason, setReason] = useState('')

  const update = (index: number, patch: Partial<RouteInput>) =>
    setRows((all) => all.map((row, i) => (i === index ? { ...row, ...patch } : row)))

  const unused = counts.departments.filter((d) => !rows.some((r) => r.department === d.key))

  const submit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit(rows, reason)
  }

  return (
    <form onSubmit={submit} className="space-y-4" aria-label="Yönlendirmeyi düzelt">
      {rows.map((row, index) => {
        const department = counts.departments.find((d) => d.key === row.department)
        return (
          <fieldset key={index} className="grid grid-cols-[1fr_auto] gap-2 items-end rounded-md border border-rule p-3">
            <legend className="sr-only">Departman {index + 1}</legend>
            <label className="text-sm col-span-2">
              <span className="text-steel">Departman</span>
              <select
                className="field mt-1"
                value={row.department}
                onChange={(e) =>
                  update(index, { department: e.target.value, intent: firstIntent(counts, e.target.value) })
                }
              >
                {counts.departments
                  .filter((d) => d.key === row.department || !rows.some((r) => r.department === d.key))
                  .map((d) => (
                    <option key={d.key} value={d.key}>
                      {d.name}
                    </option>
                  ))}
              </select>
            </label>
            <label className="text-sm col-span-2">
              <span className="text-steel">E-posta türü</span>
              <select className="field mt-1" value={row.intent} onChange={(e) => update(index, { intent: e.target.value })}>
                {department?.intents.map((intent) => (
                  <option key={intent.key} value={intent.key} title={intent.description}>
                    {intent.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="text-steel">Öncelik</span>
              <select
                className="field mt-1"
                value={row.priority}
                onChange={(e) => update(index, { priority: e.target.value as Priority })}
              >
                {(Object.keys(priorityLabel) as Priority[]).map((p) => (
                  <option key={p} value={p}>
                    {priorityLabel[p]}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="btn btn-quiet"
              disabled={rows.length === 1}
              onClick={() => setRows((all) => all.filter((_, i) => i !== index))}
            >
              Kaldır
            </button>
          </fieldset>
        )
      })}
      {unused.length > 0 && (
        <button
          type="button"
          className="text-sm underline cursor-pointer"
          onClick={() =>
            setRows((all) => [
              ...all,
              { department: unused[0].key, intent: firstIntent(counts, unused[0].key), priority: 'normal' },
            ])
          }
        >
          Bir departman daha ekle
        </button>
      )}
      <label className="block text-sm">
        <span className="text-steel">Neden düzeltiyorsun? (kayda geçer, yapay zekânın ölçümünde kullanılır)</span>
        <textarea
          className="field mt-1 min-h-20"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
        />
      </label>
      {error && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
      <div className="flex gap-2">
        <button className="btn" disabled={pending || !reason.trim()}>
          {pending ? 'Kaydediliyor…' : 'Yönlendirmeyi kaydet'}
        </button>
        <button type="button" className="btn btn-quiet" onClick={onCancel}>
          Vazgeç
        </button>
      </div>
    </form>
  )
}
