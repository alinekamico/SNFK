'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff } from 'lucide-react'
import { login } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErro('')
    setLoading(true)
    try {
      await login(email, senha)
      router.push('/dashboard')
    } catch {
      setErro('E-mail ou senha incorretos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-kami-charcoal">
      <div className="w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="font-heading text-5xl text-kami-cream tracking-widest uppercase">
            KAMI CO<span className="text-kami-red">.</span>
          </h1>
          <p className="text-kami-cream/50 mt-2 text-xs font-body tracking-widest uppercase">
            Sistema de Notas Fiscais
          </p>
        </div>

        {/* Card */}
        <div className="bg-kami-cream rounded-2xl shadow-2xl p-8">
          <h2 className="font-heading text-2xl text-kami-charcoal mb-6">Acesso ao sistema</h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-kami-charcoal mb-1 font-body">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="seu@kamico.com.br"
                className="w-full border border-kami-charcoal/30 rounded-lg px-4 py-2.5 bg-white text-kami-charcoal placeholder-kami-charcoal/40 focus:outline-none focus:ring-2 focus:ring-kami-red font-body text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-kami-charcoal mb-1 font-body">Senha</label>
              <div className="relative">
                <input
                  type={mostrarSenha ? 'text' : 'password'}
                  value={senha}
                  onChange={e => setSenha(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full border border-kami-charcoal/30 rounded-lg px-4 py-2.5 pr-11 bg-white text-kami-charcoal focus:outline-none focus:ring-2 focus:ring-kami-red font-body text-sm"
                />
                <button
                  type="button"
                  onClick={() => setMostrarSenha(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-kami-charcoal/50 hover:text-kami-charcoal transition-colors"
                  tabIndex={-1}
                >
                  {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="text-right">
              <Link href="/esqueci-senha" className="text-xs text-kami-red hover:underline font-body">
                Esqueci minha senha
              </Link>
            </div>

            {erro && <p className="text-kami-red text-sm font-body">{erro}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-kami-red text-white rounded-lg py-3 font-heading text-lg tracking-wider hover:bg-kami-red-light disabled:opacity-50 transition-colors uppercase"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>
        </div>

        <p className="text-center text-kami-cream/30 text-xs mt-6 font-body">
          Smart Beauty Made by People
        </p>
      </div>
    </div>
  )
}
