interface SparklineProps {
  values: number[];
  color?: string;
}

/** Matches the handoff's `viewBox 0 0 120 32` KPI-card sparkline exactly. */
export function Sparkline({ values, color = 'var(--acc,#B76E79)' }: SparklineProps) {
  if (values.length === 0) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = 120 / Math.max(1, values.length - 1);

  const points = values
    .map((v, i) => {
      const x = i * step;
      const y = 30 - ((v - min) / range) * 28;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg viewBox="0 0 120 32" preserveAspectRatio="none" className="w-full h-8 mt-3.5 overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.85"
      />
    </svg>
  );
}
