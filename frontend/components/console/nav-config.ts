export interface ConsoleNavItem {
  id: string;
  href: string;
  label: string;
}

export const CONSOLE_NAV_ITEMS: ConsoleNavItem[] = [
  { id: 'overview', href: '/admin', label: 'Overview' },
  { id: 'hub', href: '/admin/hub', label: 'The Hub' },
  { id: 'orders', href: '/admin/orders', label: 'Orders' },
  { id: 'products', href: '/admin/products', label: 'Products' },
  { id: 'collections', href: '/admin/collections', label: 'Collections' },
  { id: 'agents', href: '/admin/agents', label: 'Agents' },
  { id: 'customers', href: '/admin/customers', label: 'Customers' },
  { id: 'settings', href: '/admin/settings', label: 'Settings' },
];
