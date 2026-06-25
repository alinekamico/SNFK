'use client'
import { useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'

export default function EsqueciSenhaPage() {
  const [email, setEmail] = useState('')
  const [enviado, setEnviado] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/esqueci-senha', { email })
    } catch {
      // sempre mostra mensagem genérica por segurança
    } finally {
      setEnviado(true)
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
          {enviado ? (
            <div className="text-center space-y-4">
              <div className="w-14 h-14 bg-kami-red/10 rounded-full flex items-center justify-center mx-auto">
                <span className="text-kami-red text-2xl">✓</span>
              </div>
              <h2 className="font-heading text-2xl text-kami-charcoal">Verifique seu e-mail</h2>
              <p className="text-kami-charcoal/70 font-body text-sm">
                Se o e-mail estiver cadastrado, você receberá as instruções para redefinir sua senha em breve.
              </p>
              <Link href="/login" className="block mt-4 text-kami-red hover:underline font-body text-sm">
                Voltar ao login
              </Link>
            </div>
          ) : (
            <>
              <h2 className="font-heading text-2xl text-kami-charcoal mb-2">Esqueci minha senha</h2>
              <p className="text-kami-charcoal/60 font-body text-sm mb-6">
                Informe seu e-mail cadastrado e enviaremos um link para redefinição.
              </p>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-kami-charcoal mb-1 font-body">E-mail</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    placeholder="seu@kamico.com.br"
                    className="w-full border border-kami-charcoal/30 rounded-lg px-4 py-2.5 bg-white text-kami-charcoal placeholder-kami-charcoal/40 focus:outline-none focus:ring-2 focus:ring-kami-red font-body text-sm"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-kami-red text-white rounded-lg py-3 font-heading text-lg tracking-wider hover:bg-kami-red-light disabled:opacity-50 transition-colors uppercase"
                >
                  {loading ? 'Enviando...' : 'Enviar link'}
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
