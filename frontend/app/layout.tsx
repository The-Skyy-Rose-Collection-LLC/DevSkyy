import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { playfair, cormorant, spaceMono } from '@/lib/fonts'
import { SyncStatusToast } from '@/components/wordpress/sync-status-toast'
import MascotBubble from '@/components/mascot/MascotBubble'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import { QueryProvider } from '@/lib/providers/query-provider'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://devskyy.app'),
  title: 'DevSkyy Dashboard',
  description: 'AI-driven multi-agent orchestration platform for enterprise e-commerce automation',
  openGraph: {
    siteName: 'DevSkyy',
    locale: 'en_US',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`dark ${playfair.variable} ${cormorant.variable} ${spaceMono.variable}`}
    >
      <body className={inter.className}>
        <QueryProvider>
          {children}
        </QueryProvider>
        <MascotBubble />
        <SyncStatusToast />
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
