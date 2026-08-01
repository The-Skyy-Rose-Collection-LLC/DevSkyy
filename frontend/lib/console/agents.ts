/**
 * Real-agent display helpers for the Hub/Agents/Overview screens.
 * `/api/v1/agents` (lib/api/endpoints/agents.ts) returns
 * { name, version, category, status, capabilities[], endpoints[], last_execution }.
 * There is no "current task" prose, "model" chip, or "commits today" field on
 * the real API — the mockup's fictional roster (Atelier/Concierge/Curator/
 * Scout/Ledger, Architect/Couturier/Lapidary/Sentinel/Scribe/Cartographer)
 * invented those. This module only maps fields that actually exist.
 */
import type { AgentInfo } from '@/lib/api';
import { STATUS_AMBER, STATUS_GREEN, STATUS_GREY } from './brand';

export function agentStatusColor(status: string): string {
  const s = status.toLowerCase();
  if (['active', 'working', 'running', 'building'].includes(s)) return STATUS_GREEN;
  if (['reviewing', 'busy', 'processing'].includes(s)) return STATUS_AMBER;
  return STATUS_GREY;
}

export function agentInitials(name: string): string {
  const parts = name.trim().split(/[\s_-]+/).filter(Boolean);
  if (parts.length === 0) return '??';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

const GRADIENTS = [
  'linear-gradient(135deg,#B76E79,#D4AF37)',
  'linear-gradient(135deg,#DC143C,#B76E79)',
  'linear-gradient(135deg,#C0C0C0,#B76E79)',
  'linear-gradient(135deg,#8A6A3E,#D4AF37)',
  'linear-gradient(135deg,#D4AF37,#F5E6D3)',
  'linear-gradient(135deg,#6A6A72,#C0C0C0)',
];

/** Deterministic (not random — Date.now/Math.random-free) gradient per agent, by name hash. */
export function agentGradient(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return GRADIENTS[hash % GRADIENTS.length];
}

export function activeAgentCount(agents: AgentInfo[]): number {
  return agents.filter((a) => agentStatusColor(a.status) === STATUS_GREEN).length;
}
