// Öneri verisinin genel görünümü: alanlar, satır tabloları ve doğrulama uyarıları.
// Departmana özel değildir; alan adları text.ts'deki sözlükten okunur, bilinmeyen ad olduğu gibi görünür.
import { byFieldOrder, fieldLabel, valueLabel } from '../lib/text'

interface Issue {
  field: string
  level: 'error' | 'warning'
  message: string
}

const NUMERIC = /^-?\d+(\.\d+)?$/
const NOT_NUMBERS = new Set(['product_code', 'quote_no', 'request_no'])
const HIDDEN = new Set(['issues'])

function isIssue(value: unknown): value is Issue {
  return typeof value === 'object' && value !== null && 'field' in value && 'level' in value && 'message' in value
}

const MONEY = /(price|total|subtotal|vat)/

function formatNumber(value: number, name = ''): string {
  const money = MONEY.test(name)
  return value.toLocaleString('tr-TR', { minimumFractionDigits: money ? 2 : 0, maximumFractionDigits: 4 })
}

function Scalar({ name, value }: { name: string; value: unknown }) {
  if (value === null || value === undefined || value === '') return <span className="text-steel">—</span>
  if (typeof value === 'number') return <span className="num">{formatNumber(value, name)}</span>
  if (typeof value === 'string' && NUMERIC.test(value) && !NOT_NUMBERS.has(name))
    return <span className="num">{formatNumber(Number(value), name)}</span>
  if (typeof value === 'boolean') return <>{value ? 'Evet' : 'Hayır'}</>
  if (typeof value === 'string' && value.includes('\n'))
    return <span className="block whitespace-pre-line rounded bg-ground px-2 py-1.5">{value}</span>
  if (typeof value === 'string') return <>{valueLabel(name, value)}</>
  if (Array.isArray(value) && value.length === 0) return <span className="text-steel">Yok</span>
  if (Array.isArray(value) && value.every((v) => typeof v === 'string')) return <>{value.join(', ')}</>
  if (Array.isArray(value)) return <span className="text-steel">{value.length} kayıt</span>
  if (typeof value === 'object')
    return (
      <span>
        {Object.entries(value as Record<string, unknown>)
          .filter(([, v]) => v !== null && typeof v !== 'object')
          .map(([k, v], i) => (
            <span key={k}>
              {i > 0 && ' · '}
              <span className="text-steel">{fieldLabel(k)}:</span> <Scalar name={k} value={v} />
            </span>
          ))}
      </span>
    )
  return <>{String(value)}</>
}

function Table({ name, rows, flagged }: { name: string; rows: Record<string, unknown>[]; flagged: Set<string> }) {
  const columns = [...new Set(rows.flatMap((r) => Object.keys(r)))]
    .filter((c) => !HIDDEN.has(c) && rows.some((r) => r[c] !== null && r[c] !== undefined && r[c] !== ''))
    .sort(byFieldOrder)
  return (
    <div className="mt-1 overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="text-left text-steel">
            {columns.map((c) => (
              <th key={c} className="font-normal border-b border-rule px-1.5 py-1 whitespace-nowrap">
                {fieldLabel(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="align-top">
              {columns.map((c) => {
                const bad = flagged.has(`${name}[${i}].${c}`)
                return (
                  <td
                    key={c}
                    className={`border-b border-rule px-1.5 py-1 ${bad ? 'text-danger font-bold bg-danger/5' : ''}`}
                    title={bad ? 'Doğrulama bu değeri şüpheli buldu' : undefined}
                  >
                    <Scalar name={c} value={row[c]} />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ProposalPayload({ data }: { data: Record<string, unknown> }) {
  const issues = Array.isArray(data.issues) ? data.issues.filter(isIssue) : []
  const flagged = new Set(issues.filter((i) => i.level === 'error').map((i) => i.field))
  const entries = Object.entries(data)
    .filter(([k, v]) => !HIDDEN.has(k) && v !== null && v !== undefined && v !== '')
    .sort(([a], [b]) => byFieldOrder(a, b))
  const tables = entries.filter(
    ([, v]) => Array.isArray(v) && v.length > 0 && v.every((x) => typeof x === 'object' && x !== null),
  ) as [string, Record<string, unknown>[]][]
  const scalars = entries.filter(([k]) => !tables.some(([t]) => t === k))

  return (
    <div className="mt-3 space-y-3 text-sm">
      {issues.length > 0 && (
        <ul className="space-y-1 rounded border border-rule px-3 py-2">
          {issues.map((issue, i) => (
            <li key={i} className={issue.level === 'error' ? 'text-danger' : 'text-steel'}>
              <span className="font-bold">{issue.level === 'error' ? 'Şüpheli' : 'Uyarı'}</span> ·{' '}
              {fieldLabel(
                issue.field
                  .replace(/\[\d+\]/, '')
                  .split('.')
                  .pop() ?? issue.field,
              )}
              {/\[(\d+)\]/.test(issue.field) && ` (${Number(/\[(\d+)\]/.exec(issue.field)?.[1]) + 1}. satır)`}:{' '}
              {issue.message}
            </li>
          ))}
        </ul>
      )}
      <dl className="grid grid-cols-[minmax(6rem,auto)_1fr] gap-x-3 gap-y-1">
        {scalars.map(([key, value]) => (
          <div key={key} className="contents">
            <dt className="text-steel">{fieldLabel(key)}</dt>
            <dd className={`min-w-0 break-words ${flagged.has(key) ? 'text-danger font-bold' : ''}`}>
              <Scalar name={key} value={value} />
            </dd>
          </div>
        ))}
      </dl>
      {tables.map(([key, rows]) => (
        <div key={key}>
          <p className="text-steel">{fieldLabel(key)}</p>
          <Table name={key} rows={rows} flagged={flagged} />
        </div>
      ))}
    </div>
  )
}
