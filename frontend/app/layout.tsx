/**
 * Root Layout
 * ===========
 * The root layout for the DevSkyy Dashboard.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import Script from 'next/script';
import { SpeedInsights } from '@vercel/speed-insights/next';
import {
  LayoutDashboard,
  Bot,
  Trophy,
  FlaskConical,
  Wrench,
  Settings,
  Box,
} from 'lucide-react';
import './globals.css';

// Use CSS custom properties for fonts - defined in globals.css
// This avoids next/font build-time font fetching issues

export const metadata: Metadata = {
  title: 'DevSkyy Dashboard',
  description: '6 SuperAgents with 17 prompt techniques, ML, and LLM Round Table',
  icons: {
    icon: '/favicon.ico',
  },
};

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/3d-pipeline', label: '3D Pipeline', icon: Box },
  { href: '/round-table', label: 'Round Table', icon: Trophy },
  { href: '/ab-testing', label: 'A/B Testing', icon: FlaskConical },
  { href: '/tools', label: 'Tools', icon: Wrench },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 dark:bg-gray-950 font-sans antialiased">
        {/* Google Model Viewer for 3D assets */}
        <Script
          src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js"
          type="module"
          strategy="afterInteractive"
        />
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
            {/* Logo */}
            <div className="flex h-16 items-center border-b border-gray-200 px-6 dark:border-gray-800">
              <Link href="/" className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-brand-primary flex items-center justify-center">
                  <span className="text-white font-bold text-sm">DS</span>
                </div>
                <span className="font-bold text-lg">DevSkyy</span>
              </Link>
            </div>

            {/* Navigation */}
            <nav className="flex flex-col gap-1 p-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50"
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Bottom Section */}
            <div className="absolute bottom-0 left-0 right-0 border-t border-gray-200 p-4 dark:border-gray-800">
              <Link
                href="/settings"
                className="flex items-center gap-3 rounded-lg px-3 py-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50"
              >
                <Settings className="h-5 w-5" />
                Settings
              </Link>
              <div className="mt-4 rounded-lg bg-brand-primary/10 p-3">
                <p className="text-xs font-medium text-brand-primary">
                  SkyyRose AI
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Where Love Meets Luxury
                </p>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="ml-64 flex-1 p-8">{children}</main>
        </div>
        <SpeedInsights />
      </body>
    </html>
  );
}
