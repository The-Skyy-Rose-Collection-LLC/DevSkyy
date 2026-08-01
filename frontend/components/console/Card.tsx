import { cn } from '@/lib/utils';

/** The console's `.dsh-card` primitive: bg #111, border #2A2A2A, radius 8, hover lift.
 *  Hover/transition rules live in app/admin/console.css (`.dsh-card`). */
export function ConsoleCard({ className, style, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('dsh-card rounded-lg border', className)}
      style={{ background: 'var(--console-card)', borderColor: 'var(--console-border)', ...style }}
      {...props}
    />
  );
}

/** The console's `.dsh-row` primitive: subtle hover background on list rows. */
export function ConsoleRow({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('dsh-row rounded-md', className)} {...props} />;
}
