'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Building2, FileText, Shield, LayoutDashboard, LogOut } from 'lucide-react'
import { logout } from '@/lib/auth'

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/documentos', label: 'Documentos', icon: FileText },
  { href: '/empresas', label: 'Empresas', icon: Building2 },
  { href: '/certificados', label: 'Certificados', icon: Shield },
]

export default function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="w-64 bg-[#1e3a5f] text-white flex flex-col min-h-screen">
      <div className="p-6 border-b border-blue-800">
        <h1 className="text-xl font-bold">KAMI CO.</h1>
        <p className="text-blue-300 text-xs mt-1">Documentos Fiscais</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              pathname.startsWith(href)
                ? 'bg-blue-600 text-white'
                : 'text-blue-200 hover:bg-blue-800 hover:text-white'
            }`}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-blue-800">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm text-blue-200 hover:bg-blue-800 hover:text-white transition-colors"
        >
          <LogOut size={18} />
          Sair
        </button>
      </div>
    </aside>
  )
}
