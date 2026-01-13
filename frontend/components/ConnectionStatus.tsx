/**
 * Connection Status Component
 * ============================
 * Displays real-time connection status for backend API and WebSocket.
 */

'use client';

import { useEffect, useState } from 'react';
import { Activity, Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { Badge } from './ui';
import { apiClient, type WebSocketStatus } from '@/lib/api-client';

export interface ConnectionStatusProps {
  showDetails?: boolean;
  compact?: boolean;
}

interface ConnectionState {
  api: 'online' | 'offline' | 'checking';
  websocket: WebSocketStatus;
  lastCheck: Date;
}

export function ConnectionStatus({ showDetails = false, compact = false }: ConnectionStatusProps) {
  const [state, setState] = useState<ConnectionState>({
    api: 'checking',
    websocket: 'disconnected',
    lastCheck: new Date(),
  });

  useEffect(() => {
    // Check API health
    const checkAPI = async () => {
      try {
        await apiClient.healthCheck();
        setState((prev) => ({ ...prev, api: 'online', lastCheck: new Date() }));
      } catch (error) {
        setState((prev) => ({ ...prev, api: 'offline', lastCheck: new Date() }));
      }
    };

    // Initial check
    checkAPI();

    // Periodic health checks every 30 seconds
    const interval = setInterval(checkAPI, 30000);

    // Monitor WebSocket status for metrics channel
    const metricsWS = apiClient.websocket('metrics');
    const handleWSStatus = (status: WebSocketStatus) => {
      setState((prev) => ({ ...prev, websocket: status }));
    };
    metricsWS.onStatus(handleWSStatus);

    return () => {
      clearInterval(interval);
      metricsWS.offStatus(handleWSStatus);
    };
  }, []);

  const isOnline = state.api === 'online' && state.websocket === 'connected';
  const isChecking = state.api === 'checking' || state.websocket === 'connecting';
  const hasError = state.api === 'offline' || state.websocket === 'error';

  if (compact) {
    return (
      <Badge
        variant={isOnline ? 'success' : hasError ? 'destructive' : 'warning'}
        className="animate-pulse-glow"
      >
        <Activity className="mr-1 h-3 w-3" />
        {isOnline ? 'Online' : isChecking ? 'Connecting' : 'Offline'}
      </Badge>
    );
  }

  return (
    <div className="flex items-center gap-4">
      {/* Overall Status */}
      <div className="flex items-center gap-2">
        {isOnline ? (
          <Wifi className="h-5 w-5 text-green-500" />
        ) : hasError ? (
          <WifiOff className="h-5 w-5 text-red-500" />
        ) : (
          <AlertCircle className="h-5 w-5 text-yellow-500" />
        )}
        <div>
          <div className="text-sm font-medium">
            {isOnline ? 'Connected' : isChecking ? 'Connecting' : 'Disconnected'}
          </div>
          {showDetails && (
            <div className="text-xs text-gray-500">
              Last check: {state.lastCheck.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {/* Detailed Status */}
      {showDetails && (
        <div className="flex gap-2">
          <Badge
            variant={state.api === 'online' ? 'success' : state.api === 'offline' ? 'destructive' : 'secondary'}
            className="text-xs"
          >
            API: {state.api}
          </Badge>
          <Badge
            variant={
              state.websocket === 'connected'
                ? 'success'
                : state.websocket === 'error'
                  ? 'destructive'
                  : 'secondary'
            }
            className="text-xs"
          >
            WS: {state.websocket}
          </Badge>
        </div>
      )}
    </div>
  );
}

export default ConnectionStatus;
