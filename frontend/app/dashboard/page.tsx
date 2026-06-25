'use client'
import { useEffect, useState } from 'react'
import Sidebar from '@/components/Sidebar'
import api from '@/lib/api'
import { FileText, Building2, TrendingDown, TrendingUp } from 'lucide-react'

interface Stats { total: number; recebidas: number; emitidas: number; empresas: number }

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({ total: 0, recebidas: 0, emitidas: 0, empresas: 0 })

  useEffect(() => {
    Promise.all([
      api.get('/documentos?per_page=1').catch(() => ({ data: [] })),
      api.get('/empresas').catch(() => ({ data: [] })),
    ]).then(([docs, emps]) => {
      setStats(s => ({ ...s, empresas: Array.isArray(emps.data) ? emps.data.length : 0 }))
    })
  }, [])

  const cards = [
    { label: 'Empresas Cadastradas', value: stats.empresas, icon: Building2, color: 'bg-blue-50 text-blue-700' },
    { label: 'Documentos Total', value: stats.total, icon: FileText, color: 'bg-green-50 text-green-700' },
    { label: 'NF-e Recebidas', value: stats.recebidas, icon: TrendingDown, color: 'bg-purple-50 text-purple-700' },
    { label: 'NF-e Emitidas', value: stats.emitidas, icon: TrendingUp, color: 'bg-orange-50 text-orange-700' },
  ]

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
              <div className={`p-3 rounded-lg ${color}`}><Icon size={22} /></div>
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-2xl font-bold text-gray-800">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
