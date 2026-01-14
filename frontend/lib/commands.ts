/**
 * Command Registry
 * ================
 * Central registry of all commands available in the command palette.
 */

export interface Command {
  id: string;
  label: string;
  description: string;
  category: 'Navigation' | 'Actions' | 'Agents' | 'Settings' | 'Data';
  icon: string;
  shortcut?: string;
  keywords?: string[];
  action: () => void | Promise<void>;
}

export const defaultCommands: Omit<Command, 'action'>[] = [
  // Navigation
  {
    id: 'nav-agents',
    label: 'Go to Agents',
    description: 'Navigate to SuperAgents section',
    category: 'Navigation',
    icon: '🤖',
    shortcut: '⌘1',
    keywords: ['navigate', 'agents', 'superagents'],
  },
  {
    id: 'nav-tasks',
    label: 'Go to Task History',
    description: 'Navigate to recent task history',
    category: 'Navigation',
    icon: '📋',
    shortcut: '⌘2',
    keywords: ['navigate', 'tasks', 'history'],
  },
  {
    id: 'nav-round-table',
    label: 'Go to Round Table',
    description: 'Navigate to LLM Round Table section',
    category: 'Navigation',
    icon: '🏆',
    shortcut: '⌘3',
    keywords: ['navigate', 'roundtable', 'llm', 'competition'],
  },
  {
    id: 'nav-metrics',
    label: 'Go to Metrics',
    description: 'Navigate to dashboard metrics',
    category: 'Navigation',
    icon: '📊',
    shortcut: '⌘4',
    keywords: ['navigate', 'metrics', 'stats'],
  },
  // Actions
  {
    id: 'action-execute-task',
    label: 'Execute Task',
    description: 'Open quick task executor',
    category: 'Actions',
    icon: '⚡',
    shortcut: '⌘E',
    keywords: ['execute', 'task', 'run'],
  },
  {
    id: 'action-refresh',
    label: 'Refresh Dashboard',
    description: 'Reload all dashboard data',
    category: 'Actions',
    icon: '🔄',
    shortcut: '⌘R',
    keywords: ['refresh', 'reload', 'update'],
  },
  {
    id: 'action-export-csv',
    label: 'Export Task History (CSV)',
    description: 'Download task history as CSV',
    category: 'Actions',
    icon: '📥',
    shortcut: '⌘S',
    keywords: ['export', 'download', 'csv', 'tasks'],
  },
  {
    id: 'action-export-json',
    label: 'Export Dashboard Data (JSON)',
    description: 'Download full dashboard state',
    category: 'Actions',
    icon: '💾',
    keywords: ['export', 'download', 'json', 'data'],
  },
  // Agents
  {
    id: 'agent-commerce',
    label: 'Commerce Agent',
    description: 'View Commerce SuperAgent',
    category: 'Agents',
    icon: '🛒',
    keywords: ['agent', 'commerce', 'shopping'],
  },
  {
    id: 'agent-creative',
    label: 'Creative Agent',
    description: 'View Creative SuperAgent',
    category: 'Agents',
    icon: '🎨',
    keywords: ['agent', 'creative', 'design'],
  },
  {
    id: 'agent-marketing',
    label: 'Marketing Agent',
    description: 'View Marketing SuperAgent',
    category: 'Agents',
    icon: '📢',
    keywords: ['agent', 'marketing', 'promotion'],
  },
  {
    id: 'agent-support',
    label: 'Support Agent',
    description: 'View Support SuperAgent',
    category: 'Agents',
    icon: '💬',
    keywords: ['agent', 'support', 'help'],
  },
  {
    id: 'agent-operations',
    label: 'Operations Agent',
    description: 'View Operations SuperAgent',
    category: 'Agents',
    icon: '⚙️',
    keywords: ['agent', 'operations', 'ops'],
  },
  {
    id: 'agent-analytics',
    label: 'Analytics Agent',
    description: 'View Analytics SuperAgent',
    category: 'Agents',
    icon: '📈',
    keywords: ['agent', 'analytics', 'data'],
  },
  // Settings
  {
    id: 'settings-dark-mode',
    label: 'Toggle Dark Mode',
    description: 'Switch between light and dark themes',
    category: 'Settings',
    icon: '🌙',
    shortcut: '⌘D',
    keywords: ['settings', 'theme', 'dark', 'light'],
  },
  {
    id: 'settings-time-range-1h',
    label: 'Set Time Range: 1 hour',
    description: 'Show data from last 1 hour',
    category: 'Settings',
    icon: '🕐',
    keywords: ['settings', 'time', 'range', '1h'],
  },
  {
    id: 'settings-time-range-24h',
    label: 'Set Time Range: 24 hours',
    description: 'Show data from last 24 hours',
    category: 'Settings',
    icon: '📅',
    keywords: ['settings', 'time', 'range', '24h'],
  },
  {
    id: 'settings-time-range-7d',
    label: 'Set Time Range: 7 days',
    description: 'Show data from last 7 days',
    category: 'Settings',
    icon: '📆',
    keywords: ['settings', 'time', 'range', '7d', 'week'],
  },
  {
    id: 'settings-time-range-30d',
    label: 'Set Time Range: 30 days',
    description: 'Show data from last 30 days',
    category: 'Settings',
    icon: '📊',
    keywords: ['settings', 'time', 'range', '30d', 'month'],
  },
];
