'use client';

import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import type { CreativeOperation } from '@/lib/elite-studio-client';

interface OperationStatusBadgeProps {
  status: CreativeOperation['status'];
  className?: string;
}

const STATUS_CONFIG: Record<
  CreativeOperation['status'],
  { label: string; className: string; icon: React.ComponentType<{ className?: string }> }
> = {
  queued: {
    label: 'Queued',
    className: 'border-gray-600 bg-gray-800 text-gray-300',
    icon: Clock,
  },
  running: {
    label: 'Running',
    className: 'border-blue-500/50 bg-blue-500/10 text-blue-400',
    icon: Loader2,
  },
  completed: {
    label: 'Completed',
    className: 'border-green-500/50 bg-green-500/10 text-green-400',
    icon: CheckCircle2,
  },
  failed: {
    label: 'Failed',
    className: 'border-red-500/50 bg-red-500/10 text-red-400',
    icon: XCircle,
  },
};

export function OperationStatusBadge({ status, className = '' }: OperationStatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  const isSpinning = status === 'running';

  return (
    <Badge
      variant="outline"
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 font-medium ${config.className} ${className}`}
    >
      <Icon
        className={`h-3 w-3 flex-shrink-0 ${isSpinning ? 'animate-spin' : ''}`}
        aria-hidden="true"
      />
      <span>{config.label}</span>
    </Badge>
  );
}
