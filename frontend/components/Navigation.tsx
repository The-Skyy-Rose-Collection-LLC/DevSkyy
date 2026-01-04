/**
 * Navigation Component
 * ====================
 * Sidebar navigation with support for nested menu items.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  LayoutDashboard,
  Bot,
  Trophy,
  FlaskConical,
  Wrench,
  Box,
  Image,
  UserCircle,
  Sparkles,
  GalleryVertical,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

type NavItem = {
  href?: string;
  label: string;
  icon: any;
  items?: { label: string; href: string }[];
};

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/3d-pipeline', label: '3D Pipeline', icon: Box },
  { href: '/round-table', label: 'Round Table', icon: Trophy },
  { href: '/ab-testing', label: 'A/B Testing', icon: FlaskConical },
  { href: '/tools', label: 'Tools', icon: Wrench },
  {
    label: 'Collections',
    icon: GalleryVertical,
    items: [
      { label: 'Black Rose Garden', href: '/collections/black-rose' },
      { label: 'Signature', href: '/collections/signature' },
      { label: 'Love Hurts', href: '/collections/love-hurts' },
      { label: 'Showroom', href: '/collections/showroom' },
      { label: 'Runway', href: '/collections/runway' },
    ],
  },
  { href: '/visual', label: 'Visual Generation', icon: Image },
  { href: '/try-on', label: 'Virtual Try-On', icon: UserCircle },
  { href: '/brand', label: 'Brand DNA', icon: Sparkles },
];

function NavigationItem({ item }: { item: NavItem }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (item.items) {
    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50"
        >
          <item.icon className="h-5 w-5" />
          <span className="flex-1 text-left">{item.label}</span>
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
        {isExpanded && (
          <div className="ml-8 mt-1 flex flex-col gap-1">
            {item.items.map((subItem) => (
              <Link
                key={subItem.href}
                href={subItem.href}
                className="rounded-lg px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50"
              >
                {subItem.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <Link
      href={item.href!}
      className="flex items-center gap-3 rounded-lg px-3 py-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50"
    >
      <item.icon className="h-5 w-5" />
      {item.label}
    </Link>
  );
}

export function Navigation() {
  return (
    <nav className="flex flex-col gap-1 overflow-y-auto">
      {navItems.map((item, index) => (
        <NavigationItem key={item.label || index} item={item} />
      ))}
    </nav>
  );
}
