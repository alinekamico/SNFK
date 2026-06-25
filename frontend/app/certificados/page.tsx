'use client'
import { useEffect, useState } from 'react'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { Shield, Upload, AlertTriangle } from 'lucide-react'

interface Empresa { id: string; razao_social: string; cnpj: string }
interface Certificado { id: string; empresa_id: string; nome: string; validade?: string; ativo: boolean }

export default function CertificadosPage() {
  const [certs, setCerts] = useState<Certificado[]>([])
  const [empresas, setEmpresas] = useState<Empresa[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ empresa_id: '', nome: '', senha: '' })
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)
  const [erro, setErro] = useState('')

  const load = () => {
    api.get('/certificados').then(r => setCerts(r.data))
    api.get('/empresas').then(r => setEmpresas(r.data))
  }
  useEffect(() => { load() }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!arquivo) { setErro('Selecione o arquivo .pfx'); return }
    setSaving(true); setErro('')
    try {
      const fd = new FormData()
      fd.append('empresa_id', form.empresa_id)
      fd.append('nome', form.nome)
      fd.append('senha', form.senha)
      fd.append('arquivo', arquivo)
      await api.post('/certificados', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setShowForm(false)
      setForm({ empresa_id: '', nome: '', senha: '' })
      setArquivo(null)
      load()
    } catch (err: any) {
      setErro(err?.response?.data?.detail || 'Erro ao salvar certificado')
    } finally { setSaving(false) }
  }

  const getEmpresa = (id: string) => empresas.find(e => e.id === id)

  const isVencendo = (validade?: string) => {
    if (!validade) return false
    const dias = (new Date(validade).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    return dias < 30
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Certificados Digitais</h2>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-[#2563eb] text-white px-4 py-2 rounded-lg hover:bg-[#1d4ed8] transition-colors">
            <Upload size={18} /> Upload Certificado
          </button>
        </div>

        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
              <h3 className="text-lg font-bold mb-4">Novo Certificado Digital</h3>
              <form onSubmit={handleSave} className="space-y-3">
                <select required value={form.empresa_id} onChange={e => setForm(f => ({...f, empresa_id: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm">
                  <option value="">Selecione a empresa</option>
                  {empresas.map(e => <option key={e.id} value={e.id}>{e.razao_social} — {e.cnpj}</option>)}
                </select>
                <input required placeholder="Nome do certificado (ex: e-CNPJ A1 2024)" value={form.nome} onChange={e => setForm(f => ({...f, nome: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" />
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Arquivo .pfx</label>
                  <input required type="file" accept=".pfx,.p12" onChange={e => setArquivo(e.target.files?.[0] || null)} className="w-full text-sm" />
                </div>
                <input required type="password" placeholder="Senha do certificado" value={form.senha} onChange={e => setForm(f => ({...f, senha: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" />
                {erro && <p className="text-red-600 text-sm">{erro}</p>}
                <div className="flex gap-2 justify-end pt-2">
                  <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">Cancelar</button>
                  <button type="submit" disabled={saving} className="px-4 py-2 bg-[#2563eb] text-white rounded-lg text-sm disabled:opacity-50">{saving ? 'Enviando...' : 'Salvar'}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid gap-4">
          {certs.map(c => {
            const emp = getEmpresa(c.empresa_id)
            const vencendo = isVencendo(c.validade)
            return (
              <div key={c.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
                <div className={`p-3 rounded-lg ${vencendo ? 'bg-yellow-50 text-yellow-600' : 'bg-green-50 text-green-700'}`}>
                  {vencendo ? <AlertTriangle size={22} /> : <Shield size={22} />}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-800">{c.nome}</p>
                  <p className="text-sm text-gray-500">{emp?.razao_social || c.empresa_id}</p>
                  {c.validade && (
                    <p className={`text-xs mt-1 ${vencendo ? 'text-yellow-600 font-medium' : 'text-gray-400'}`}>
                      Validade: {new Date(c.validade).toLocaleDateString('pt-BR')}
                      {vencendo && ' — Vencendo em breve!'}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
          {certs.length === 0 && <p className="text-gray-400 text-center py-12">Nenhum certificado cadastrado ainda.</p>}
        </div>
      </main>
    </div>
  )
}
