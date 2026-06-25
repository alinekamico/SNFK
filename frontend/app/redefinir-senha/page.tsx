'use client'
import { useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff } from 'lucide-react'
import api from '@/lib/api'

function RedefinirSenhaForm() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token') ?? ''

  const [novaSenha, setNovaSenha] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [mostrar1, setMostrar1] = useState(false)
  const [mostrar2, setMostrar2] = useState(false)
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)
  const [sucesso, setSucesso] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErro('')
    if (novaSenha !== confirmar) {
      setErro('As senhas não coincidem')
      return
    }
    if (novaSenha.length < 8) {
      setErro('A senha deve ter no mínimo 8 caracteres')
      return
    }
    setLoading(true)
    try {
      await api.post('/auth/redefinir-senha', { token, nova_senha: novaSenha })
      setSucesso(true)
      setTimeout(() => router.push('/login'), 3000)
    } catch {
      setErro('Link inválido ou expirado. Solicite um novo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-kami-charcoal">
      <div className="w-full max-w-md px-4">
        <div className="text-center mb-8">
          <h1 className="font-heading text-5xl text-kami-cream tracking-widest uppercase">
            KAMI CO<span className="text-kami-red">.</span>
          </h1>
          <p className="text-kami-cream/50 mt-2 text-xs font-body tracking-widest uppercase">
            Sistema de Notas Fiscais
          </p>
        </div>

        <div className="bg-kami-cream rounded-2xl shadow-2xl p-8">
          {sucesso ? (
            <div className="text-center space-y-4">
              <div className="w-14 h-14 bg-kami-red/10 rounded-full flex items-center justify-center mx-auto">
                <span className="text-kami-red text-2xl">✓</span>
              </div>
              <h2 className="font-heading text-2xl text-kami-charcoal">Senha redefinida!</h2>
              <p className="text-kami-charcoal/70 font-body text-sm">
                Sua senha foi alterada com sucesso. Redirecionando para o login...
              </p>
            </div>
          ) : (
            <>
              <h2 className="font-heading text-2xl text-kami-charcoal mb-2">Redefinir senha</h2>
              <p className="text-kami-charcoal/60 font-body text-sm mb-6">
                Escolha uma nova senha para sua conta.
              </p>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-kami-charcoal mb-1 font-body">Nova senha</label>
                  <div className="relative">
                    <input
                      type={mostrar1 ? 'text' : 'password'}
                      value={novaSenha}
                      onChange={e => setNovaSenha(e.target.value)}
                      required
                      minLength={8}
                      className="w-full border border-kami-charcoal/30 rounded-lg px-4 py-2.5 pr-11 bg-white text-kami-charcoal focus:outline-none focus:ring-2 focus:ring-kami-red font-body text-sm"
                    />
                    <button type="button" onClick={() => setMostrar1(v => !v)} tabIndex={-1}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-kami-charcoal/50 hover:text-kami-charcoal">
                      {mostrar1 ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-kami-charcoal mb-1 font-body">Confirmar senha</label>
                  <div className="relative">
                    <input
                      type={mostrar2 ? 'text' : 'password'}
                      value={confirmar}
                      onChange={e => setConfirmar(e.target.value)}
                      required
                      className="w-full border border-kami-charcoal/30 rounded-lg px-4 py-2.5 pr-11 bg-white text-kami-charcoal focus:outline-none focus:ring-2 focus:ring-kami-red font-body text-sm"
                    />
                    <button type="button" onClick={() => setMostrar2(v => !v)} tabIndex={-1}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-kami-charcoal/50 hover:text-kami-charcoal">
                      {mostrar2 ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                {erro && <p className="text-kami-red text-sm font-body">{erro}</p>}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-kami-red text-white rounded-lg py-3 font-heading text-lg tracking-wider hover:bg-kami-red-light disabled:opacity-50 transition-colors uppercase"
                >
                  {loading ? 'Salvando...' : 'Salvar nova senha'}
                </button>
                <div className="text-center">
                  <Link href="/login" className="text-xs text-kami-charcoal/50 hover:text-kami-charcoal font-body">
                    Voltar ao login
                  </Link>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function RedefinirSenhaPage() {
  return (
    <Suspense>
      <RedefinirSenhaForm />
    </Suspense>
  )
}
