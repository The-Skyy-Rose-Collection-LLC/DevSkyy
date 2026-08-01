interface RevenueChartProps {
  current: number[];
  prior: number[];
  labels: string[];
  gradientId: string;
}

function toPath(values: number[], width: number, height: number, pad = 20): string {
  if (values.length === 0) return '';
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = max - min || 1;
  const step = width / Math.max(1, values.length - 1);
  return values
    .map((v, i) => {
      const x = i * step;
      const y = pad + (height - pad * 1.5) * (1 - (v - min) / range);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

/** Matches the handoff's `viewBox 0 0 600 200` revenue chart: 3 gridlines, a
 *  dimmed prior-period line, a filled current-period area, and the current line. */
export function RevenueChart({ current, prior, labels, gradientId }: RevenueChartProps) {
  const revPath = toPath(current, 600, 200);
  const priorPath = toPath(prior, 600, 200);
  const revArea = revPath ? `${revPath} 600,200 0,200` : '';

  return (
    <div>
      <svg viewBox="0 0 600 200" preserveAspectRatio="none" className="w-full h-[200px] overflow-visible">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--acc,#B76E79)" stopOpacity="0.28" />
            <stop offset="100%" stopColor="var(--acc,#B76E79)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1="0" y1="50" x2="600" y2="50" stroke="rgba(255,255,255,.05)" strokeWidth="1" />
        <line x1="0" y1="100" x2="600" y2="100" stroke="rgba(255,255,255,.05)" strokeWidth="1" />
        <line x1="0" y1="150" x2="600" y2="150" stroke="rgba(255,255,255,.05)" strokeWidth="1" />
        {priorPath && (
          <polyline points={priorPath} fill="none" stroke="#3A3A42" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        )}
        {revArea && <polygon points={revArea} fill={`url(#${gradientId})`} />}
        {revPath && (
          <polyline
            points={revPath}
            fill="none"
            stroke="var(--acc,#B76E79)"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
      </svg>
      <div className="flex justify-between font-mono text-[9.5px] tracking-[0.1em] text-[#7A7A82] mt-2.5">
        {labels.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
    </div>
  );
}
