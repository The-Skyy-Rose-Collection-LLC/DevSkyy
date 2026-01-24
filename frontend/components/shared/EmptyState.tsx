'use client';

import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  /** Icon component */
  icon?: React.ComponentType<{ className?: string }>;
  /** Title */
  title: string;
  /** Description */
  description?: string;
  /** Action button text */
  actionText?: string;
  /** Action callback */
  onAction?: () => void;
  /** Custom children */
  children?: ReactNode;
}

/**
 * Reusable empty state component for lists and tables.
 *
 * @example
 * <EmptyState
 *   icon={FolderOpen}
 *   title="No assets found"
 *   description="Upload your first asset to get started."
 *   actionText="Upload Asset"
 *   onAction={() => setShowUpload(true)}
 * />
 */
export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionText,
  onAction,
  children,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-gray-800 p-4 mb-4">
        <Icon className="h-8 w-8 text-gray-500" />
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-gray-400 max-w-sm">{description}</p>
      )}
      {actionText && onAction && (
        <Button
          onClick={onAction}
          className="mt-4 bg-rose-500 hover:bg-rose-600"
        >
          {actionText}
        </Button>
      )}
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}

export default EmptyState;
