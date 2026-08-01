// Same feTurbulence technique already used in HomePage.tsx / CollectionHero.tsx,
// scoped as a standalone component for the console shell.
export function GrainOverlay() {
  return (
    <div className="pointer-events-none fixed inset-0 z-[9500] opacity-[0.035] mix-blend-overlay">
      <svg width="100%" height="100%">
        <filter id="console-grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves={3} stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter="url(#console-grain)" />
      </svg>
    </div>
  );
}
