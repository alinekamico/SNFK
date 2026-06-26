'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import { FileText, Building2, TrendingDown, TrendingUp } from 'lucide-react'

interface Stats { total: number; recebidas: number; emitidas: number; empresas: number }

export default function Dashboard() {
  const router = useRouter()
  const [stats, setStats] = useState<Stats>({ total: 0, recebidas: 0, emitidas: 0, empresas: 0 })

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login')
      return
    }
    Promise.all([
      api.get('/documentos/stats').catch(() => ({ data: { total: 0, recebidas: 0, emitidas: 0 } })),
      api.get('/empresas').catch(() => ({ data: [] })),
    ]).then(([statsData, emps]) => {
      setStats({
        total: statsData.data.total ?? 0,
        recebidas: statsData.data.recebidas ?? 0,
        emitidas: statsData.data.emitidas ?? 0,
        empresas: Array.isArray(emps.data) ? emps.data.length : 0,
      })
    })
  }, [router])

  const cards = [
    { label: 'Empresas Cadastradas', value: stats.empresas,  icon: Building2,   color: 'bg-kami-red/10 text-kami-red' },
    { label: 'Documentos Total',     value: stats.total,     icon: FileText,    color: 'bg-kami-charcoal/10 text-kami-charcoal' },
    { label: 'NF-e Recebidas',       value: stats.recebidas, icon: TrendingDown, color: 'bg-kami-red/10 text-kami-red' },
    { label: 'NF-e Emitidas',        value: stats.emitidas,  icon: TrendingUp,  color: 'bg-kami-charcoal/10 text-kami-charcoal' },
  ]

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8 bg-kami-cream">
        <h2 className="font-heading text-3xl text-kami-charcoal mb-8">Dashboard</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white rounded-xl shadow-sm border border-kami-charcoal/10 p-5 flex items-center gap-4">
              <div className={`p-3 rounded-lg ${color}`}><Icon size={22} /></div>
              <div>
                <p className="text-xs font-body text-kami-charcoal/60 uppercase tracking-wider">{label}</p>
                <p className="text-2xl font-heading text-kami-charcoal">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
