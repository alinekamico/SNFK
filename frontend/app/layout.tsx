import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SNFK — Sistema de Notas Fiscais KAMI CO.',
  description: 'Gestão de documentos fiscais',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">{children}</body>
    </html>
  )
}
