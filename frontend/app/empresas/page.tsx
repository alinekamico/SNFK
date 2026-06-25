'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import { Plus, Building2, Pencil } from 'lucide-react'

interface Empresa { id: string; razao_social: string; nome_fantasia?: string; cnpj: string; email?: string; ativa: boolean; tiny_token?: string }

function formatCNPJ(v: string) {
  const d = v.replace(/\D/g, '').slice(0, 14)
  return d
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
}

export default function EmpresasPage() {
  const router = useRouter()
  const [empresas, setEmpresas] = useState<Empresa[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editando, setEditando] = useState<Empresa | null>(null)
  const [form, setForm] = useState({ razao_social: '', nome_fantasia: '', cnpj: '', email: '', tiny_token: '' })
  const [saving, setSaving] = useState(false)
  const [erro, setErro] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.replace('/login'); return }
    load()
  }, [router])

  const load = () => api.get('/empresas').then(r => setEmpresas(r.data))

  const abrirEdicao = (e: Empresa) => {
    setEditando(e)
    setForm({ razao_social: e.razao_social, nome_fantasia: e.nome_fantasia || '', cnpj: e.cnpj, email: e.email || '', tiny_token: e.tiny_token || '' })
    setErro('')
    setShowForm(true)
  }

  const abrirNovo = () => {
    setEditando(null)
    setForm({ razao_social: '', nome_fantasia: '', cnpj: '', email: '', tiny_token: '' })
    setErro('')
    setShowForm(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setErro('')
    setSaving(true)
    try {
      if (editando) {
        await api.patch(`/empresas/${editando.id}`, {
          razao_social: form.razao_social,
          nome_fantasia: form.nome_fantasia,
          email: form.email,
          tiny_token: form.tiny_token || null,
        })
      } else {
        const cnpjNumeros = form.cnpj.replace(/\D/g, '')
        if (cnpjNumeros.length !== 14) { setErro('CNPJ deve ter 14 dígitos'); setSaving(false); return }
        await api.post('/empresas', { ...form, cnpj: cnpjNumeros })
      }
      setShowForm(false)
      load()
    } catch (err: any) {
      setErro(err?.response?.data?.detail || 'Erro ao salvar empresa')
    } finally {
      setSaving(false)
    }
  }

  const inputClass = "w-full border border-kami-charcoal/30 rounded-lg px-3 py-2.5 text-sm font-body bg-white text-kami-charcoal focus:outline-none focus:ring-2 focus:ring-kami-red"

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8 bg-kami-cream">
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-heading text-3xl text-kami-charcoal">Empresas</h2>
          <button
            onClick={abrirNovo}
            className="flex items-center gap-2 bg-kami-red text-white px-4 py-2.5 rounded-lg hover:bg-kami-red-light transition-colors font-body text-sm"
          >
            <Plus size={18} /> Nova Empresa
          </button>
        </div>

        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-kami-cream rounded-xl p-6 w-full max-w-lg shadow-xl">
              <h3 className="font-heading text-2xl text-kami-charcoal mb-4">
                {editando ? 'Editar Empresa' : 'Nova Empresa'}
              </h3>
              <form onSubmit={handleSave} className="space-y-3">
                <input required placeholder="Razão Social" value={form.razao_social}
                  onChange={e => setForm(f => ({...f, razao_social: e.target.value}))} className={inputClass} />
                <input placeholder="Nome Fantasia" value={form.nome_fantasia}
                  onChange={e => setForm(f => ({...f, nome_fantasia: e.target.value}))} className={inputClass} />
                {!editando && (
                  <>
                    <input required placeholder="CNPJ" value={form.cnpj}
                      onChange={e => setForm(f => ({...f, cnpj: formatCNPJ(e.target.value)}))}
                      className={inputClass} maxLength={18} />
                    <p className="text-xs text-kami-charcoal/50 font-body -mt-1">Digite os 14 dígitos do CNPJ</p>
                  </>
                )}
                {editando && (
                  <div className={`${inputClass} bg-kami-charcoal/5 cursor-not-allowed`}>
                    {form.cnpj}
                  </div>
                )}
                <input type="email" placeholder="E-mail" value={form.email}
                  onChange={e => setForm(f => ({...f, email: e.target.value}))} className={inputClass} />
                <div className="border-t border-kami-charcoal/10 pt-3 mt-1">
                  <p className="text-xs font-body text-kami-charcoal/50 mb-2 uppercase tracking-wider">Integrações</p>
                  <input placeholder="Token API Tiny (opcional)" value={form.tiny_token}
                    onChange={e => setForm(f => ({...f, tiny_token: e.target.value}))} className={inputClass} />
                </div>
                {erro && <p className="text-kami-red text-sm font-body">{erro}</p>}
                <div className="flex gap-2 justify-end pt-2">
                  <button type="button" onClick={() => setShowForm(false)}
                    className="px-4 py-2 border border-kami-charcoal/30 rounded-lg text-sm font-body hover:bg-kami-charcoal/10 text-kami-charcoal">
                    Cancelar
                  </button>
                  <button type="submit" disabled={saving}
                    className="px-4 py-2 bg-kami-red text-white rounded-lg text-sm font-body disabled:opacity-50 hover:bg-kami-red-light">
                    {saving ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid gap-4">
          {empresas.map(e => (
            <div key={e.id} className="bg-white rounded-xl border border-kami-charcoal/10 shadow-sm p-5 flex items-center gap-4">
              <div className="p-3 bg-kami-red/10 rounded-lg text-kami-red"><Building2 size={22} /></div>
              <div className="flex-1">
                <p className="font-heading text-lg text-kami-charcoal">{e.razao_social}</p>
                {e.nome_fantasia && <p className="text-sm text-kami-charcoal/60 font-body">{e.nome_fantasia}</p>}
                <p className="text-xs text-kami-charcoal/40 font-body mt-1">CNPJ: {e.cnpj}</p>
                {e.tiny_token && <p className="text-xs text-green-600 font-body mt-0.5">✓ Token Tiny configurado</p>}
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-body font-medium ${e.ativa ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {e.ativa ? 'Ativa' : 'Inativa'}
              </span>
              <button onClick={() => abrirEdicao(e)}
                className="p-2 rounded-lg hover:bg-kami-charcoal/10 text-kami-charcoal/60 hover:text-kami-charcoal transition-colors">
                <Pencil size={16} />
              </button>
            </div>
          ))}
          {empresas.length === 0 && (
            <p className="text-kami-charcoal/40 font-body text-center py-12">Nenhuma empresa cadastrada ainda.</p>
          )}
        </div>
      </main>
    </div>
  )
}
