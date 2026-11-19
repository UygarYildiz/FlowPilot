import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Navigate, NavLink, Outlet, useNavigate } from 'react-router'
import { api, ApiError } from '../lib/api'
import { useCounts, useMe } from '../lib/hooks'
import { deptColor } from '../lib/text'

function NavItem({
  to,
  label,
  count,
  mark,
  attention,
}: {
  to: string
  label: string
  count?: number
  mark?: string
  attention?: boolean
}) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        `flex items-center gap-2.5 rounded-md px-3 py-2 ${
          isActive ? 'bg-white text-ink font-semibold shadow-[inset_3px_0_0_var(--color-ink)]' : 'text-ink/80 hover:bg-white/60'
        }`
      }
    >
      {mark && <span className="size-2.5 rounded-sm shrink-0" style={{ background: mark }} aria-hidden />}
      <span className="flex-1">{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className={`num text-xs font-bold rounded px-1.5 py-0.5 ${
            attention ? 'bg-signal text-ink' : 'text-steel'
          }`}
        >
          {count}
        </span>
      )}
    </NavLink>
  )
}

export default function Layout() {
  const me = useMe()
  const counts = useCounts()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: () => {
      queryClient.clear()
      navigate('/giris', { replace: true })
    },
  })

  if (me.isPending) return <p className="p-8 text-steel">Yükleniyor…</p>
  if (me.error instanceof ApiError && me.error.status === 401) return <Navigate to="/giris" replace />
  if (me.isError) return <p className="p-8 text-danger">Panel açılamadı: {me.error.message}</p>

  const user = me.data
  const isAdmin = user.role === 'admin'

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
      <aside className="border-b lg:border-b-0 lg:border-r border-rule px-3 py-5 lg:min-h-screen flex flex-col gap-6">
        <p className="wide font-extrabold text-lg px-3">FlowPilot</p>
        <nav className="flex flex-col gap-0.5" aria-label="Gelen kutuları">
          <NavItem to="/" label="Tüm e-postalar" count={counts.data?.all} />
          <NavItem to="/onay" label="Onay bekleyenler" count={counts.data?.awaiting_approval} attention />
          {isAdmin && (
            <NavItem
              to="/inceleme"
              label="İnsan baksın"
              count={counts.data?.needs_review}
              attention
            />
          )}
          {isAdmin && <NavItem to="/denetim" label="Denetim kaydı" />}
        </nav>
        <nav className="flex flex-col gap-0.5" aria-label="Departmanlar">
          <p className="px-3 pb-1 text-sm text-steel">Departmanlar</p>
          {counts.data?.departments.map((d) => (
            <NavItem
              key={d.key}
              to={`/departman/${d.key}`}
              label={d.name}
              count={d.open_count}
              mark={deptColor(d.key)}
            />
          ))}
        </nav>
        <div className="mt-auto px-3 text-sm">
          <p className="font-semibold">{user.name}</p>
          <p className="text-steel break-all">{user.email}</p>
          <button className="mt-2 underline text-steel hover:text-ink cursor-pointer" onClick={() => logout.mutate()}>
            Çıkış yap
          </button>
        </div>
      </aside>
      <main className="min-w-0">
        <Outlet />
      </main>
    </div>
  )
}
