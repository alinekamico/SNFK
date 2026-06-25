'use client'
import { useEffect, useState, useCallback } from 'react'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { Download, FileText, FileSearch, RefreshCw } from 'lucide-react'

interface Empresa { id: string; razao_social: string; cnpj: string }
interface Documento {
  id: string; chave_acesso: string; tipo: string; fonte: string
  razao_emitente?: string; razao_destinatario?: string
  numero_nota?: string; data_emissao?: string; valor_total?: number
  status?: string; has_xml: boolean; has_danfe: boolean
  empresa_id: string
}

export default function DocumentosPage() {
  const [docs, setDocs] = useState<Documento[]>([])
  const [empresas, setEmpresas] = useState<Empresa[]>([])
  const [selecionados, setSelecionados] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [coletando, setColetando] = useState<string | null>(null)
  const [filtros, setFiltros] = useState({
    empresa_id: '', tipo: '', fonte: '',
    data_inicio: '', data_fim: '', numero_nota: '',
  })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries(filtros).filter(([,v]) => v))
      const { data } = await api.get('/documentos', { params: { ...params, per_page: 100 } })
      setDocs(data)
    } finally { setLoading(false) }
  }, [filtros])

  useEffect(() => { api.get('/empresas').then(r => setEmpresas(r.data)) }, [])
  useEffect(() => { load() }, [load])

  const toggleSel = (id: string) =>
    setSelecionados(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])

  const downloadLote = async () => {
    if (!selecionados.length) return
    const resp = await api.post('/documentos/download-lote', selecionados, { responseType: 'blob' })
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a'); a.href = url; a.download = 'documentos_fiscais.zip'; a.click()
    URL.revokeObjectURL(url)
  }

  const downloadArquivo = async (id: string, tipo: 'xml' | 'danfe', chave: string, num?: string) => {
    const resp = await api.get(`/documentos/${id}/${tipo}`, { responseType: 'blob' })
    const ext = tipo === 'xml' ? 'xml' : 'pdf'
    const nome = tipo === 'xml' ? `${chave}.${ext}` : `DANFE_${num || chave}.${ext}`
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a'); a.href = url; a.download = nome; a.click()
    URL.revokeObjectURL(url)
  }

  const coletar = async (empresaId: string) => {
    setColetando(empresaId)
    try {
      await api.post(`/coleta/sefaz/${empresaId}?ambiente=2`)
      setTimeout(load, 3000)
    } finally { setColetando(null) }
  }

  const fmtValor = (v?: number) => v ? v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : '—'
  const fmtData = (d?: string) => d ? new Date(d).toLocaleDateString('pt-BR') : '—'

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Documentos Fiscais</h2>
          <div className="flex gap-2">
            {selecionados.length > 0 && (
              <button onClick={downloadLote} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm">
                <Download size={16} /> Baixar {selecionados.length} selecionados (ZIP)
              </button>
            )}
            {filtros.empresa_id && (
              <button
                onClick={() => coletar(filtros.empresa_id)}
                disabled={!!coletando}
                className="flex items-center gap-2 bg-[#1e3a5f] text-white px-4 py-2 rounded-lg hover:bg-[#2563eb] text-sm disabled:opacity-50"
              >
                <RefreshCw size={16} className={coletando ? 'animate-spin' : ''} />
                {coletando ? 'Coletando...' : 'Coletar SEFAZ'}
              </button>
            )}
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <select value={filtros.empresa_id} onChange={e => setFiltros(f => ({...f, empresa_id: e.target.value}))} className="border rounded-lg px-2 py-1.5 text-sm col-span-2">
            <option value="">Todas as empresas</option>
            {empresas.map(e => <option key={e.id} value={e.id}>{e.razao_social}</option>)}
          </select>
          <select value={filtros.tipo} onChange={e => setFiltros(f => ({...f, tipo: e.target.value}))} className="border rounded-lg px-2 py-1.5 text-sm">
            <option value="">Tipo</option>
            <option value="recebida">Recebidas</option>
            <option value="emitida">Emitidas</option>
          </select>
          <select value={filtros.fonte} onChange={e => setFiltros(f => ({...f, fonte: e.target.value}))} className="border rounded-lg px-2 py-1.5 text-sm">
            <option value="">Fonte</option>
            <option value="sefaz">SEFAZ</option>
            <option value="tiny">Tiny</option>
            <option value="uno">UNO</option>
          </select>
          <input type="date" value={filtros.data_inicio} onChange={e => setFiltros(f => ({...f, data_inicio: e.target.value}))} className="border rounded-lg px-2 py-1.5 text-sm" placeholder="Data início" />
          <input type="date" value={filtros.data_fim} onChange={e => setFiltros(f => ({...f, data_fim: e.target.value}))} className="border rounded-lg px-2 py-1.5 text-sm" placeholder="Data fim" />
        </div>

        {/* Tabela */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-3 text-left w-8">
                  <input type="checkbox" onChange={e => setSelecionados(e.target.checked ? docs.map(d => d.id) : [])} />
                </th>
                <th className="p-3 text-left font-medium text-gray-600">Emitente / Destinatário</th>
                <th className="p-3 text-left font-medium text-gray-600">Nº Nota</th>
                <th className="p-3 text-left font-medium text-gray-600">Emissão</th>
                <th className="p-3 text-left font-medium text-gray-600">Valor</th>
                <th className="p-3 text-left font-medium text-gray-600">Tipo</th>
                <th className="p-3 text-left font-medium text-gray-600">Status</th>
                <th className="p-3 text-left font-medium text-gray-600">Downloads</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading && (
                <tr><td colSpan={8} className="text-center py-8 text-gray-400">Carregando...</td></tr>
              )}
              {!loading && docs.length === 0 && (
                <tr><td colSpan={8} className="text-center py-12 text-gray-400">
                  <FileSearch className="mx-auto mb-2 text-gray-300" size={32} />
                  Nenhum documento encontrado
                </td></tr>
              )}
              {docs.map(doc => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="p-3"><input type="checkbox" checked={selecionados.includes(doc.id)} onChange={() => toggleSel(doc.id)} /></td>
                  <td className="p-3">
                    <p className="font-medium text-gray-800 truncate max-w-[200px]">{doc.razao_emitente || '—'}</p>
                    <p className="text-xs text-gray-400 truncate max-w-[200px]">→ {doc.razao_destinatario || '—'}</p>
                  </td>
                  <td className="p-3 font-mono text-gray-600">{doc.numero_nota || '—'}</td>
                  <td className="p-3 text-gray-600">{fmtData(doc.data_emissao)}</td>
                  <td className="p-3 font-medium text-gray-800">{fmtValor(doc.valor_total)}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${doc.tipo === 'recebida' ? 'bg-purple-100 text-purple-700' : 'bg-orange-100 text-orange-700'}`}>
                      {doc.tipo}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${doc.status === 'Autorizada' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {doc.status || '—'}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex gap-1">
                      {doc.has_xml && (
                        <button onClick={() => downloadArquivo(doc.id, 'xml', doc.chave_acesso)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded" title="Baixar XML">
                          <FileText size={16} />
                        </button>
                      )}
                      {doc.has_danfe && (
                        <button onClick={() => downloadArquivo(doc.id, 'danfe', doc.chave_acesso, doc.numero_nota)} className="p-1.5 text-green-600 hover:bg-green-50 rounded" title="Baixar DANFe">
                          <Download size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
