import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../lib/api'
import { keys } from '../lib/hooks'

// Kurgusal demo hesapları (`uv run flowpilot users demo`).
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD ?? 'flowpilot-demo'
const DEMO_ACCOUNTS = [
  { email: 'yonetici@atlas-endustri.example', who: 'Yönetici', note: 'Her şeyi görür, inceleme kuyruğunu yönetir' },
  { email: 'satinalma@atlas-endustri.example', who: 'Satın Alma', note: 'Yalnızca kendi departmanı' },
  { email: 'finans@atlas-endustri.example', who: 'Finans', note: 'Yalnızca kendi departmanı' },
  { email: 'lojistik@atlas-endustri.example', who: 'Lojistik', note: 'Yalnızca kendi departmanı' },
]

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const login = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: (user) => {
      queryClient.clear()
      queryClient.setQueryData(keys.me, user)
      navigate('/', { replace: true })
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    login.mutate()
  }

  return (
    <main className="min-h-screen grid lg:grid-cols-[1.1fr_1fr]">
      <section className="bg-ink text-white px-8 py-12 lg:px-16 flex flex-col justify-between gap-12">
        <p className="wide text-lg font-bold">FlowPilot</p>
        <div className="max-w-xl">
          <h1 className="wide text-4xl lg:text-5xl font-extrabold leading-[1.05]">
            Gelen her e&#8209;posta, doğru masaya.
          </h1>
          <p className="mt-6 text-white/75 text-lg leading-relaxed max-w-[52ch]">
            Atlas Endüstri'ye gelen e-postaları yapay zekâ okur ve ilgili departmana yönlendirir. Emin
            olmadığı her e-postayı bir insana bırakır.
          </p>
        </div>
        <p className="text-white/50 text-sm">
          Atlas Endüstri kurgusal bir şirkettir; bu paneldeki tüm kişiler ve e-postalar örnektir.
        </p>
      </section>

      <section className="px-8 py-12 lg:px-16 flex items-center">
        <div className="w-full max-w-sm">
          <h2 className="wide text-2xl font-bold">Giriş yap</h2>
          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block">
              <span className="text-sm font-semibold">E-posta</span>
              <input
                className="field mt-1"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="block">
              <span className="text-sm font-semibold">Şifre</span>
              <input
                className="field mt-1"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {login.isError && (
              <p role="alert" className="text-sm text-danger">
                {login.error.message}
              </p>
            )}
            <button className="btn w-full justify-center" disabled={login.isPending}>
              {login.isPending ? 'Giriş yapılıyor…' : 'Giriş yap'}
            </button>
          </form>

          <div className="mt-10">
            <p className="text-sm font-semibold">Demo hesapla dene</p>
            <ul className="mt-2 divide-y divide-rule border-y border-rule">
              {DEMO_ACCOUNTS.map((account) => (
                <li key={account.email}>
                  <button
                    type="button"
                    className="w-full text-left py-2.5 hover:bg-white/60 cursor-pointer"
                    onClick={() => {
                      setEmail(account.email)
                      setPassword(DEMO_PASSWORD)
                    }}
                  >
                    <span className="font-semibold">{account.who}</span>
                    <span className="block text-sm text-steel">{account.note}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </main>
  )
}
