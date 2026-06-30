'use client'
import { useEffect, useState, useCallback, useRef } from 'react'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { Download, FileText, FileSearch, RefreshCw, ChevronDown } from 'lucide-react'

interface Empresa { id: string; razao_social: string; nome_fantasia?: string; cnpj: string; ativa: boolean }
interface Documento {
  id: string; chave_acesso: string; tipo: string; fonte: string
  razao_emitente?: string; razao_destinatario?: string
  numero_nota?: string; data_emissao?: string; valor_total?: number
  status?: string; has_xml: boolean; has_danfe: boolean
  empresa_id: string
}

type Aba = 'emitidas' | 'recebidas'

function EmpresaDropdown({ empresas, selecionadas, onChange }: {
  empresas: Empresa[]
  selecionadas: string[]
  onChange: (ids: string[]) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const toggle = (id: string) =>
    onChange(selecionadas.includes(id) ? selecionadas.filter(x => x !== id) : [...selecionadas, id])

  const label = selecionadas.length === 0
    ? 'Todas as empresas'
    : selecionadas.length === 1
      ? empresas.find(e => e.id === selecionadas[0])?.razao_social.split(' ').slice(0, 3).join(' ') || '1 empresa'
      : `${selecionadas.length} empresas`

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 border border-kami-charcoal/20 rounded-lg px-3 py-2 text-sm font-body text-kami-charcoal bg-white hover:border-kami-red min-w-[200px] justify-between"
      >
        <span className="truncate">{label}</span>
        <ChevronDown size={14} className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute z-50 mt-1 bg-white border border-kami-charcoal/15 rounded-xl shadow-lg w-72 max-h-64 overflow-y-auto">
          {selecionadas.length > 0 && (
            <button onClick={() => onChange([])} className="w-full text-left px-4 py-2 text-xs text-kami-red font-body hover:bg-kami-cream border-b border-kami-charcoal/10">
              Limpar seleção
            </button>
          )}
          {empresas.map(e => (
            <label key={e.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-kami-cream cursor-pointer">
              <input type="checkbox" checked={selecionadas.includes(e.id)} onChange={() => toggle(e.id)}
                className="accent-kami-red" />
              <span className="text-sm font-body text-kami-charcoal">{e.nome_fantasia || e.razao_social}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

export default function DocumentosPage() {
  const [aba, setAba] = useState<Aba>('emitidas')
  const [docs, setDocs] = useState<Documento[]>([])
  const [empresas, setEmpresas] = useState<Empresa[]>([])
  const [selecionados, setSelecionados] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [coletando, setColetando] = useState<string | null>(null)
  const [filtros, setFiltros] = useState({
    empresa_id: [] as string[],
    fonte: [] as string[],
    data_inicio: '', data_fim: '', numero_nota: '',
  })

  const load = useCallback(async () => {
    setLoading(true)
    setSelecionados([])
    try {
      const params: Record<string, string> = {
        tipo: aba === 'emitidas' ? 'emitida' : 'recebida',
        per_page: '100',
      }
      if (filtros.empresa_id.length === 1) params.empresa_id = filtros.empresa_id[0]
      if (filtros.fonte.length === 1) params.fonte = filtros.fonte[0]
      if (filtros.data_inicio) params.data_inicio = filtros.data_inicio
      if (filtros.data_fim) params.data_fim = filtros.data_fim
      if (filtros.numero_nota) params.numero_nota = filtros.numero_nota
      const { data } = await api.get('/documentos', { params })
      setDocs(data)
    } finally { setLoading(false) }
  }, [filtros, aba])

  useEffect(() => {
    api.get('/empresas').then(r => setEmpresas(r.data.filter((e: Empresa) => e.ativa)))
  }, [])
  useEffect(() => { load() }, [load])

  const toggleSel = (id: string) =>
    setSelecionados(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])

  const toggleFonte = (f: string) =>
    setFiltros(prev => ({
      ...prev,
      fonte: prev.fonte.includes(f) ? prev.fonte.filter(x => x !== f) : [...prev.fonte, f],
    }))

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

  const temFiltro = filtros.empresa_id.length > 0 || filtros.fonte.length > 0 || filtros.data_inicio || filtros.data_fim || filtros.numero_nota

  const fmtValor = (v?: number) => v ? v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : '—'
  const fmtData = (d?: string) => d ? new Date(d).toLocaleDateString('pt-BR') : '—'
  const fontes = ['sefaz', 'tiny', 'uno']

  const chipClass = (ativo: boolean) =>
    `px-3 py-1.5 rounded-lg text-xs font-body font-medium cursor-pointer border transition-colors ${
      ativo ? 'bg-kami-red text-white border-kami-red' : 'bg-white text-kami-charcoal border-kami-charcoal/20 hover:border-kami-red hover:text-kami-red'
    }`

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8 bg-kami-cream">
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-heading text-3xl text-kami-charcoal">Documentos Fiscais</h2>
          <div className="flex gap-2">
            {selecionados.length > 0 && (
              <button onClick={downloadLote} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-body">
                <Download size={16} /> Baixar {selecionados.length} (ZIP)
              </button>
            )}
            {filtros.empresa_id.length === 1 && (
              <button onClick={() => coletar(filtros.empresa_id[0])} disabled={!!coletando}
                className="flex items-center gap-2 bg-kami-charcoal text-white px-4 py-2 rounded-lg hover:bg-kami-charcoal/80 text-sm font-body disabled:opacity-50">
                <RefreshCw size={16} className={coletando ? 'animate-spin' : ''} />
                {coletando ? 'Coletando...' : 'Coletar SEFAZ'}
              </button>
            )}
          </div>
        </div>

        {/* Abas */}
        <div className="flex gap-2 mb-4">
          {(['emitidas', 'recebidas'] as Aba[]).map(a => (
            <button key={a} onClick={() => setAba(a)}
              className={`px-6 py-2.5 rounded-lg font-body text-sm font-medium transition-colors ${
                aba === a ? 'bg-kami-red text-white shadow-sm' : 'bg-white text-kami-charcoal border border-kami-charcoal/15 hover:border-kami-red hover:text-kami-red'
              }`}>
              {a === 'emitidas' ? 'NF-e Emitidas' : 'NF-e Recebidas'}
            </button>
          ))}
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-xl border border-kami-charcoal/10 shadow-sm p-4 mb-4 space-y-3">
          <div className="flex flex-wrap gap-3 items-center">
            <EmpresaDropdown
              empresas={empresas}
              selecionadas={filtros.empresa_id}
              onChange={ids => setFiltros(f => ({ ...f, empresa_id: ids }))}
            />
            <div className="flex gap-2">
              {fontes.map(f => (
                <button key={f} onClick={() => toggleFonte(f)} className={chipClass(filtros.fonte.includes(f))}>
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
            <input type="date" value={filtros.data_inicio}
              onChange={e => setFiltros(f => ({...f, data_inicio: e.target.value}))}
              className="border border-kami-charcoal/20 rounded-lg px-3 py-1.5 text-sm font-body text-kami-charcoal" />
            <input type="date" value={filtros.data_fim}
              onChange={e => setFiltros(f => ({...f, data_fim: e.target.value}))}
              className="border border-kami-charcoal/20 rounded-lg px-3 py-1.5 text-sm font-body text-kami-charcoal" />
            <input placeholder="Nº Nota" value={filtros.numero_nota}
              onChange={e => setFiltros(f => ({...f, numero_nota: e.target.value}))}
              className="border border-kami-charcoal/20 rounded-lg px-3 py-1.5 text-sm font-body text-kami-charcoal w-28" />
            {temFiltro && (
              <button onClick={() => setFiltros({ empresa_id: [], fonte: [], data_inicio: '', data_fim: '', numero_nota: '' })}
                className="text-xs text-kami-red font-body hover:underline">
                Limpar
              </button>
            )}
          </div>
        </div>

        {/* Tabela */}
        <div className="bg-white rounded-xl border border-kami-charcoal/10 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-kami-charcoal/5 border-b border-kami-charcoal/10">
              <tr>
                <th className="p-3 text-left w-8">
                  <input type="checkbox" onChange={e => setSelecionados(e.target.checked ? docs.map(d => d.id) : [])} />
                </th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Emitente / Destinatário</th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Nº Nota</th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Emissão</th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Valor</th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Fonte</th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Status</th>
                <th className="p-3 text-left font-body font-medium text-kami-charcoal/60">Downloads</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-kami-charcoal/5">
              {loading && <tr><td colSpan={8} className="text-center py-8 text-kami-charcoal/40 font-body">Carregando...</td></tr>}
              {!loading && docs.length === 0 && (
                <tr><td colSpan={8} className="text-center py-12 text-kami-charcoal/40 font-body">
                  <FileSearch className="mx-auto mb-2 text-kami-charcoal/20" size={32} />
                  Nenhum documento encontrado
                </td></tr>
              )}
              {docs.map(doc => (
                <tr key={doc.id} className="hover:bg-kami-cream/50">
                  <td className="p-3"><input type="checkbox" checked={selecionados.includes(doc.id)} onChange={() => toggleSel(doc.id)} /></td>
                  <td className="p-3">
                    <p className="font-medium text-kami-charcoal truncate max-w-[200px]">{doc.razao_emitente || '—'}</p>
                    <p className="text-xs text-kami-charcoal/40 truncate max-w-[200px] font-body">→ {doc.razao_destinatario || '—'}</p>
                  </td>
                  <td className="p-3 font-mono text-kami-charcoal/70">{doc.numero_nota || '—'}</td>
                  <td className="p-3 text-kami-charcoal/70 font-body">{fmtData(doc.data_emissao)}</td>
                  <td className="p-3 font-medium text-kami-charcoal">{fmtValor(doc.valor_total)}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-xs font-body font-medium bg-kami-charcoal/10 text-kami-charcoal/70 uppercase">{doc.fonte}</span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-body ${doc.status === 'Autorizada' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
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
                        <button onClick={() => downloadArquivo(doc.id, 'danfe', doc.chave_acesso, doc.numero_nota)} className="p-1.5 text-kami-red hover:bg-kami-red/10 rounded" title="Baixar DANFe">
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
