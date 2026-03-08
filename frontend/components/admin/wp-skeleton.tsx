const shimmer = 'animate-pulse bg-gray-800 rounded'

function Row({ widths }: { widths: string[] }) {
  return (
    <div className="flex items-center gap-3 py-3">
      {widths.map((w, i) => (
        <div key={i} className={`${shimmer} h-4`} style={{ width: w }} />
      ))}
    </div>
  )
}

export function PostsSkeleton() {
  return (
    <div className="divide-y divide-gray-800">
      {Array.from({ length: 5 }).map((_, i) => (
        <Row key={i} widths={['55%', '60px', '80px']} />
      ))}
    </div>
  )
}

export function PagesSkeleton() {
  return (
    <div className="divide-y divide-gray-800">
      {Array.from({ length: 5 }).map((_, i) => (
        <Row key={i} widths={['50%', '60px', '70px']} />
      ))}
    </div>
  )
}

export function MediaSkeleton() {
  return (
    <div className="grid grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className={`${shimmer} aspect-square`} />
      ))}
    </div>
  )
}

export function CategoriesSkeleton() {
  return (
    <div className="divide-y divide-gray-800">
      {Array.from({ length: 8 }).map((_, i) => (
        <Row key={i} widths={['40%', '40px']} />
      ))}
    </div>
  )
}

export function TagsSkeleton() {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className={`${shimmer} h-6 rounded-full`} style={{ width: `${60 + (i % 4) * 20}px` }} />
      ))}
    </div>
  )
}

export function UsersSkeleton() {
  return (
    <div className="divide-y divide-gray-800">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 py-3">
          <div className={`${shimmer} h-8 w-8 rounded-full`} />
          <div className={`${shimmer} h-4`} style={{ width: '35%' }} />
          <div className={`${shimmer} h-4`} style={{ width: '60px' }} />
        </div>
      ))}
    </div>
  )
}
