'use client';

import { useEffect, useState } from 'react';
import type { AgentInfo } from '@/lib/api';
import { agentGradient, agentInitials, agentStatusColor } from '@/lib/console/agents';

interface RoundtableDiagramProps {
  agents: AgentInfo[];
  accent?: string;
  onActiveChange?: (agent: AgentInfo) => void;
}

const R = 124;
const CX = 170;
const CY = 170;
const CYCLE_MS = 2600;

/** Cycles through the REAL agent roster (not the mockup's fixed 6 fictional
 *  seats) — N seats laid out on a radius-124 circle, one highlighted at a time.
 *  Per the handoff: "In production, drive activeIdx from the actual
 *  'currently working' agent event instead of a timer" — no such event stream
 *  exists yet, so this stays an honest interim timer, not a fabricated feed. */
export function RoundtableDiagram({ agents, accent = '#B76E79', onActiveChange }: RoundtableDiagramProps) {
  const [activeIdx, setActiveIdx] = useState(0);
  const seatCount = agents.length;

  useEffect(() => {
    if (seatCount === 0) return;
    const timer = setInterval(() => setActiveIdx((i) => (i + 1) % seatCount), CYCLE_MS);
    return () => clearInterval(timer);
  }, [seatCount]);

  useEffect(() => {
    if (seatCount > 0) onActiveChange?.(agents[activeIdx % seatCount]);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- notify on index/roster change only, not on a new onActiveChange identity each render
  }, [activeIdx, agents]);

  if (seatCount === 0) {
    return (
      <div className="relative w-[340px] h-[340px] mx-auto flex items-center justify-center">
        <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#7A7A82]">No agents reporting</span>
      </div>
    );
  }

  const active = agents[activeIdx];
  const beamAngleDeg = -90 + activeIdx * (360 / seatCount);

  return (
    <div className="relative w-[340px] h-[340px] mx-auto">
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] rounded-full pointer-events-none animate-[dsh-spin_16s_linear_infinite]"
        style={{ background: 'conic-gradient(from 0deg,transparent,rgba(183,110,121,.22),transparent 42%)' }}
      />
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[276px] h-[276px] rounded-full border border-dashed border-white/[0.08] pointer-events-none" />
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[210px] h-[210px] rounded-full border border-white/[0.05] pointer-events-none" />
      <div
        className="absolute pointer-events-none z-[2] rounded-[40px] blur-[2px] transition-transform duration-[800ms]"
        style={{
          left: CX,
          top: CY - 24,
          width: R,
          height: 48,
          transformOrigin: '0 50%',
          transform: `rotate(${beamAngleDeg}deg)`,
          background: `linear-gradient(90deg,${accent} -10%,transparent 78%)`,
          opacity: 0.42,
        }}
      />
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[3] w-[104px] h-[104px] rounded-full flex flex-col items-center justify-center border"
        style={{
          background: 'radial-gradient(circle at 32% 28%,#1c1519,#0d0b0d)',
          borderColor: 'rgba(183,110,121,.4)',
          boxShadow: '0 0 44px rgba(183,110,121,.22), inset 0 0 28px rgba(0,0,0,.6)',
        }}
      >
        <span className="font-serif text-[7.5px] tracking-[0.2em] uppercase" style={{ fontFamily: 'var(--font-cinzel)', color: accent }}>
          Roundtable
        </span>
      </div>

      {agents.map((agent, i) => {
        const angle = ((-90 + i * (360 / seatCount)) * Math.PI) / 180;
        const isActive = i === activeIdx;
        const size = isActive ? 56 : 46;
        return (
          <div
            key={agent.name}
            className="absolute flex flex-col items-center gap-1.5 w-[84px] z-[4] -translate-x-1/2 -translate-y-1/2"
            style={{ left: CX + R * Math.cos(angle), top: CY + R * Math.sin(angle) }}
          >
            <div className="relative flex items-center justify-center">
              {isActive && (
                <span
                  className="absolute w-full h-full rounded-full pointer-events-none animate-[dsh-ring_1.6s_ease-out_infinite]"
                  style={{ border: `2px solid ${accent}` }}
                />
              )}
              <div
                className="rounded-full flex items-center justify-center font-semibold transition-all duration-500"
                style={{
                  width: size,
                  height: size,
                  background: agentGradient(agent.name),
                  color: '#0A0A0A',
                  fontFamily: 'var(--font-cinzel)',
                  fontSize: isActive ? 16 : 14,
                  boxShadow: isActive
                    ? `0 0 0 3px rgba(183,110,121,.85), 0 0 28px rgba(183,110,121,.65)`
                    : '0 0 0 2px rgba(255,255,255,.08)',
                }}
              >
                {agentInitials(agent.name)}
              </div>
            </div>
            <div
              className="font-mono text-[8.5px] tracking-[0.1em] uppercase whitespace-nowrap transition-colors duration-500"
              style={{ color: isActive ? accent : agentStatusColor(agent.status) === '#5FBF7F' ? '#5FBF7F' : '#8A8A92' }}
            >
              {agent.name}
            </div>
          </div>
        );
      })}
      <span className="sr-only" role="status" aria-live="polite">
        Now calling {active.name}
      </span>
    </div>
  );
}
