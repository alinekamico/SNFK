'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Building2, FileText, Shield, LayoutDashboard, LogOut } from 'lucide-react'
import { logout, getUser } from '@/lib/auth'

const nav = [
  { href: '/dashboard',    label: 'Dashboard',    icon: LayoutDashboard },
  { href: '/documentos',   label: 'Documentos',   icon: FileText },
  { href: '/empresas',     label: 'Empresas',     icon: Building2 },
  { href: '/certificados', label: 'Certificados', icon: Shield },
]

export default function Sidebar() {
  const pathname = usePathname()
  const user = getUser()

  return (
    <aside className="w-64 bg-kami-charcoal text-kami-cream flex flex-col min-h-screen">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <h1 className="font-heading text-3xl tracking-widest uppercase">
          KAMI CO<span className="text-kami-red">.</span>
        </h1>
        <p className="text-kami-cream/50 text-xs mt-1 font-body uppercase tracking-wider">
          Notas Fiscais
        </p>
      </div>

      {/* Navegação */}
      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-body font-medium transition-colors ${
              pathname.startsWith(href)
                ? 'bg-kami-red text-white'
                : 'text-kami-cream/70 hover:bg-white/10 hover:text-kami-cream'
            }`}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>

      {/* Usuário + sair */}
      <div className="p-4 border-t border-white/10 space-y-3">
        {user && (
          <div className="px-3 py-2">
            <p className="text-xs text-kami-cream/40 font-body uppercase tracking-wider">Perfil</p>
            <p className="text-kami-cream text-sm font-body font-medium">{user.perfil}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm font-body text-kami-cream/60 hover:bg-white/10 hover:text-kami-cream transition-colors"
        >
          <LogOut size={18} />
          Sair
        </button>
      </div>
    </aside>
  )
}
