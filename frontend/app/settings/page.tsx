/**
 * Settings Page
 * =============
 * Main settings hub with navigation to different settings sections.
 */

'use client';

import Link from 'next/link';
import { Settings, Palette, User, Bell, Shield, Database } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui';

const settingsSections = [
  {
    href: '/settings/brand',
    title: 'Brand Settings',
    description: 'Configure your brand identity, colors, and style',
    icon: Palette,
  },
  {
    href: '/settings/profile',
    title: 'Profile',
    description: 'Manage your account and profile information',
    icon: User,
    disabled: true,
  },
  {
    href: '/settings/notifications',
    title: 'Notifications',
    description: 'Configure notification preferences',
    icon: Bell,
    disabled: true,
  },
  {
    href: '/settings/security',
    title: 'Security',
    description: 'Security settings and API keys',
    icon: Shield,
    disabled: true,
  },
  {
    href: '/settings/integrations',
    title: 'Integrations',
    description: 'Manage third-party integrations',
    icon: Database,
    disabled: true,
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Settings className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-gray-500 mt-1">
          Manage your account, brand, and preferences
        </p>
      </div>

      {/* Settings Sections Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {settingsSections.map((section) => {
          const Icon = section.icon;

          if (section.disabled) {
            return (
              <div key={section.href} className="cursor-not-allowed">
                <Card className="h-full opacity-50">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-brand-primary/10 flex items-center justify-center">
                        <Icon className="h-5 w-5 text-brand-primary" />
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-lg">{section.title}</CardTitle>
                        <span className="text-xs text-gray-500">Coming Soon</span>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{section.description}</CardDescription>
                  </CardContent>
                </Card>
              </div>
            );
          }

          return (
            <Link key={section.href} href={section.href}>
              <Card className="h-full transition-all hover:shadow-md hover:border-brand-primary cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-brand-primary/10 flex items-center justify-center">
                      <Icon className="h-5 w-5 text-brand-primary" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{section.title}</CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription>{section.description}</CardDescription>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Info Section */}
      <Card className="bg-gray-50 dark:bg-gray-900">
        <CardContent className="pt-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Note:</strong> Additional settings sections are coming soon.
            Currently, you can configure your brand settings including colors,
            logos, and style preferences.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
