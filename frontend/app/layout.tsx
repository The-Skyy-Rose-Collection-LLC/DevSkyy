import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { playfair, cormorant, spaceMono } from '@/lib/fonts'
import { SyncStatusToast } from '@/components/wordpress/sync-status-toast'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DevSkyy Dashboard',
  description: 'AI-driven multi-agent orchestration platform for enterprise e-commerce automation',
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
        {children}
        <SyncStatusToast />
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
