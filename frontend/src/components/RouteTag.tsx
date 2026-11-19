import type { Counts, Route } from '../lib/api'
import { percent } from '../lib/format'
import { deptColor, departmentName, intentLabel } from '../lib/text'

/** Listede bir rotanın kısa gösterimi: departman rengi, adı ve e-posta türü. */
export default function RouteTag({ route, counts }: { route: Route; counts: Counts | undefined }) {
  const done = route.status === 'done'
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-xs ${
        done ? 'border-rule text-steel line-through decoration-steel/50' : 'border-rule bg-white'
      }`}
      title={`${departmentName(counts, route.department)}: ${intentLabel(counts, route.department, route.intent)} (güven ${percent(route.confidence)})`}
    >
      <span className="size-2 rounded-sm" style={{ background: deptColor(route.department) }} aria-hidden />
      <span className="font-semibold">{departmentName(counts, route.department)}</span>
      <span className="text-steel">{intentLabel(counts, route.department, route.intent)}</span>
    </span>
  )
}
