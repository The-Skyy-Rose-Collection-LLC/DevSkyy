'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, XCircle, RefreshCw, Globe } from 'lucide-react';
import { getWordPressSyncService } from '@/lib/wordpress/sync-service';

interface WordPressSyncPanelProps {
  result: any;
  onSyncComplete?: (postId: number) => void;
}

export function WordPressSyncPanel({ result, onSyncComplete }: WordPressSyncPanelProps) {
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<{
    synced: boolean;
    postId?: number;
    error?: string;
  } | null>(null);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus(null);

    try {
      const syncService = getWordPressSyncService();
      if (!syncService) {
        setSyncStatus({
          synced: false,
          error: 'WordPress credentials not configured',
        });
        return;
      }

      const response = await syncService.syncRoundTableResult(result);

      setSyncStatus({
        synced: response.success,
        postId: response.postId,
        error: response.error,
      });

      if (response.success && response.postId && onSyncComplete) {
        onSyncComplete(response.postId);
      }
    } catch (error) {
      setSyncStatus({
        synced: false,
        error: error instanceof Error ? error.message : 'Sync failed',
      });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <Card className="border-rose-500/20 bg-gradient-to-br from-gray-900 to-gray-800">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-rose-500/10 rounded-lg">
            <Globe className="w-5 h-5 text-rose-400" />
          </div>
          <div>
            <CardTitle className="text-white">WordPress Sync</CardTitle>
            <CardDescription>Publish results to your WordPress site</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {syncStatus === null && (
          <div className="text-gray-400 text-sm">
            <p>Click sync to publish this Round Table result as a WordPress post (draft).</p>
          </div>
        )}

        {syncStatus && (
          <div
            className={`p-4 rounded-lg border ${
              syncStatus.synced
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}
          >
            <div className="flex items-start gap-3">
              {syncStatus.synced ? (
                <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                {syncStatus.synced ? (
                  <>
                    <p className="text-green-400 font-medium">Synced successfully!</p>
                    {syncStatus.postId && (
                      <p className="text-green-300/70 text-sm mt-1">
                        WordPress Post ID: {syncStatus.postId}
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p className="text-red-400 font-medium">Sync failed</p>
                    {syncStatus.error && (
                      <p className="text-red-300/70 text-sm mt-1">{syncStatus.error}</p>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <Button
            onClick={handleSync}
            disabled={syncing}
            className="flex-1 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600"
          >
            {syncing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Sync to WordPress
              </>
            )}
          </Button>

          {syncStatus?.synced && syncStatus.postId && (
            <Button
              variant="outline"
              className="border-rose-500/30 text-rose-400 hover:bg-rose-500/10"
              onClick={() => {
                const wpUrl = process.env.NEXT_PUBLIC_WORDPRESS_URL;
                if (wpUrl) {
                  window.open(`${wpUrl}/wp-admin/post.php?post=${syncStatus.postId}&action=edit`, '_blank');
                }
              }}
            >
              View in WP
            </Button>
          )}
        </div>

        <div className="text-xs text-gray-500 pt-2 border-t border-gray-700">
          <p>
            Posts are created as <Badge variant="outline" className="text-xs">draft</Badge> for review before publishing.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
