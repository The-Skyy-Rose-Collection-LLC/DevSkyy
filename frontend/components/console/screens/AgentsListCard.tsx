'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { ConsoleCard, ConsoleRow } from '../Card';
import { StatusDot } from '../StatusPill';
import { agentStatusColor, activeAgentCount } from '@/lib/console/agents';

/** Overview's "DevSkyy Agents" card — real `/api/v1/agents` data. The mockup's
 *  per-agent "task" line and glow color don't exist on the real API, so this
 *  shows what's real: name, category (as a subtitle), and status. */
export function AgentsListCard() {
  const { data, isLoading } = useQuery({
    queryKey: ['console-agents-list'],
    queryFn: () => api.agents.list(),
    staleTime: 30_000,
    refetchInterval: 30_000,
  });

  const agents = data?.agents ?? [];
  const active = data ? activeAgentCount(data.agents) : 0;

  return (
    <ConsoleCard className="p-6 flex flex-col">
      <div className="flex justify-between items-center mb-[18px]">
        <span className="font-mono text-[10px] tracking-[0.18em] uppercase" style={{ color: 'var(--acc)' }}>
          DevSkyy Agents
        </span>
        {data && <span className="font-mono text-[10px] tracking-[0.1em]" style={{ color: '#5FBF7F' }}>{active} active</span>}
      </div>
      <div className="flex flex-col gap-0.5">
        {isLoading && <div className="font-mono text-[10px] text-[#7A7A82] py-2">Loading agents…</div>}
        {!isLoading && agents.length === 0 && (
          <div className="font-mono text-[10px] text-[#7A7A82] py-2">No agents reporting.</div>
        )}
        {agents.slice(0, 6).map((agent) => {
          const color = agentStatusColor(agent.status);
          return (
            <ConsoleRow key={agent.name} className="flex items-center gap-[13px] px-1.5 py-[11px]">
              <StatusDot color={color} glow={`${color}99`} />
              <div className="flex-1 min-w-0">
                <div className="text-[13.5px] text-[#E0E0E0] font-semibold">{agent.name}</div>
                <div className="text-[11px] text-[#8A8A92] truncate">{agent.category}</div>
              </div>
              <span className="font-mono text-[9px] tracking-[0.14em] uppercase flex-none" style={{ color }}>
                {agent.status}
              </span>
            </ConsoleRow>
          );
        })}
      </div>
    </ConsoleCard>
  );
}
