/**
 * Toast Provider Component
 * ========================
 * Client component wrapper for Sonner toaster and WebSocket toast notifications.
 */

'use client';

import { Toaster } from 'sonner';
import { useToastNotifications } from '@/lib/hooks/useToastNotifications';

export function ToastProvider() {
  useToastNotifications({
    showTaskToasts: true,
    showAgentToasts: true,
    showRoundTableToasts: true,
    showConnectionToasts: true,
    showErrorToasts: true,
    debounceMs: 5000,
  });

  return <Toaster position="bottom-right" expand={false} richColors closeButton duration={4000} />;
}
