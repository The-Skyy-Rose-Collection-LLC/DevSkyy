interface StatusPillProps {
  label: string;
  bg: string;
  color: string;
  className?: string;
}

export function StatusPill({ label, bg, color, className }: StatusPillProps) {
  return (
    <span
      className={`font-mono text-[9px] uppercase tracking-[0.1em] px-2.5 py-1 rounded ${className ?? ''}`}
      style={{ background: bg, color }}
    >
      {label}
    </span>
  );
}

interface StatusDotProps {
  color: string;
  glow?: string;
  pulse?: boolean;
  size?: number;
}

export function StatusDot({ color, glow, pulse, size = 8 }: StatusDotProps) {
  return (
    <span
      className={`inline-block flex-none rounded-full ${pulse ? 'animate-[dsh-pulse_2.4s_ease-in-out_infinite]' : ''}`}
      style={{
        width: size,
        height: size,
        background: color,
        boxShadow: glow ? `0 0 8px ${glow}` : undefined,
      }}
    />
  );
}
