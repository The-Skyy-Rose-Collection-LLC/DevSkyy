'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { TopBar } from '@/components/console/TopBar';
import { ConsoleCard } from '@/components/console/Card';
import { StatusDot } from '@/components/console/StatusPill';
import { agentStatusColor } from '@/lib/console/agents';

/** Real `/api/v1/agents` roster. The handoff's mockup used five fictional
 *  names (Atelier/Concierge/Curator/Scout/Ledger) with per-agent task prose
 *  that has no backing field in the real API — this renders whatever the
 *  platform actually reports, with the fields that actually exist. */
export default function AgentsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['console-agents-page'],
    queryFn: () => api.agents.list(),
    staleTime: 30_000,
    refetchInterval: 30_000,
  });

  return (
    <>
      <TopBar title="DevSkyy Agents" />
      <div className="px-9 py-8 max-w-[1320px]">
        {isLoading && <div className="font-mono text-[11px] text-[#7A7A82]">Loading agent roster…</div>}
        {error && (
          <ConsoleCard className="p-5 mb-6">
            <span className="font-mono text-[11px] text-[#E5A85C]">Couldn&apos;t reach the agents API.</span>
          </ConsoleCard>
        )}
        {data && (
          <div className="mb-6 font-mono text-[10px] tracking-[0.1em] text-[#7A7A82] uppercase">
            {data.total_agents} total · {data.active_agents} active
          </div>
        )}
        <div className="grid grid-cols-2 gap-[18px]">
          {data?.agents.map((agent) => {
            const color = agentStatusColor(agent.status);
            return (
              <ConsoleCard key={agent.name} className="p-[22px] flex gap-4 items-start">
                <div className="mt-1.5">
                  <StatusDot color={color} glow={`${color}99`} size={12} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center gap-2.5">
                    <span
                      className="text-[17px] tracking-[0.06em] text-white uppercase"
                      style={{ fontFamily: 'var(--font-cinzel)' }}
                    >
                      {agent.name}
                    </span>
                    <span className="font-mono text-[9px] tracking-[0.14em] uppercase flex-none" style={{ color }}>
                      {agent.status}
                    </span>
                  </div>
                  <div className="text-[12.5px] text-[#9A9AA2] mt-2">
                    {agent.category} · v{agent.version}
                  </div>
                  {agent.capabilities.length > 0 && (
                    <div className="italic text-[13px] text-[#C8C8C8] leading-[1.4] mt-2.5 border-l-2 pl-3" style={{ borderColor: 'var(--acc)', fontFamily: 'var(--font-playfair)' }}>
                      {agent.capabilities.slice(0, 3).join(' · ')}
                    </div>
                  )}
                  {agent.last_execution && (
                    <div className="font-mono text-[9px] tracking-[0.1em] text-[#7A7A82] uppercase mt-2.5">
                      Last run {new Date(agent.last_execution).toLocaleString()}
                    </div>
                  )}
                </div>
              </ConsoleCard>
            );
          })}
        </div>
      </div>
    </>
  );
}
