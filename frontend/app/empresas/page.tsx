'use client'
import { useEffect, useState } from 'react'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { Plus, Building2 } from 'lucide-react'

interface Empresa { id: string; razao_social: string; nome_fantasia?: string; cnpj: string; email?: string; ativa: boolean }

export default function EmpresasPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ razao_social: '', nome_fantasia: '', cnpj: '', email: '' })
  const [saving, setSaving] = useState(false)

  const load = () => api.get('/empresas').then(r => setEmpresas(r.data))
  useEffect(() => { load() }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post('/empresas', form)
      setShowForm(false)
      setForm({ razao_social: '', nome_fantasia: '', cnpj: '', email: '' })
      load()
    } finally { setSaving(false) }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Empresas</h2>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-[#2563eb] text-white px-4 py-2 rounded-lg hover:bg-[#1d4ed8] transition-colors">
            <Plus size={18} /> Nova Empresa
          </button>
        </div>

        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
              <h3 className="text-lg font-bold mb-4">Nova Empresa</h3>
              <form onSubmit={handleSave} className="space-y-3">
                <input required placeholder="Razão Social" value={form.razao_social} onChange={e => setForm(f => ({...f, razao_social: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" />
                <input placeholder="Nome Fantasia" value={form.nome_fantasia} onChange={e => setForm(f => ({...f, nome_fantasia: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" />
                <input required placeholder="CNPJ (somente números)" value={form.cnpj} onChange={e => setForm(f => ({...f, cnpj: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" maxLength={14} />
                <input type="email" placeholder="E-mail" value={form.email} onChange={e => setForm(f => ({...f, email: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" />
                <div className="flex gap-2 justify-end pt-2">
                  <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">Cancelar</button>
                  <button type="submit" disabled={saving} className="px-4 py-2 bg-[#2563eb] text-white rounded-lg text-sm disabled:opacity-50">{saving ? 'Salvando...' : 'Salvar'}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid gap-4">
          {empresas.map(e => (
            <div key={e.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
              <div className="p-3 bg-blue-50 rounded-lg text-blue-700"><Building2 size={22} /></div>
              <div className="flex-1">
                <p className="font-semibold text-gray-800">{e.razao_social}</p>
                {e.nome_fantasia && <p className="text-sm text-gray-500">{e.nome_fantasia}</p>}
                <p className="text-xs text-gray-400 mt-1">CNPJ: {e.cnpj}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${e.ativa ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {e.ativa ? 'Ativa' : 'Inativa'}
              </span>
            </div>
          ))}
          {empresas.length === 0 && <p className="text-gray-400 text-center py-12">Nenhuma empresa cadastrada ainda.</p>}
        </div>
      </main>
    </div>
  )
}
