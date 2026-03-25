import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Clock, Loader2, Play, Pause, XCircle } from 'lucide-react';
import type { BatchJob } from '@/lib/api';

interface BatchJobCardProps {
    batch: BatchJob;
}

export function BatchJobCard({ batch }: BatchJobCardProps) {
    const statusColors = {
        pending: 'text-gray-400 bg-gray-500/10',
        processing: 'text-blue-400 bg-blue-500/10',
        completed: 'text-green-400 bg-green-500/10',
        failed: 'text-red-400 bg-red-500/10',
        paused: 'text-yellow-400 bg-yellow-500/10',
    };

    return (
        <div className="flex items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
            <div className="flex-shrink-0">
                {batch.status === 'processing' ? (
                    <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />
                ) : batch.status === 'completed' ? (
                    <CheckCircle2 className="h-8 w-8 text-green-400" />
                ) : batch.status === 'failed' ? (
                    <XCircle className="h-8 w-8 text-red-400" />
                ) : (
                    <Clock className="h-8 w-8 text-gray-400" />
                )}
            </div>

            <div className="flex-1">
                <div className="flex items-center gap-2">
                    <span className="text-white font-medium">Batch #{batch.id.slice(0, 8)}</span>
                    <Badge className={statusColors[batch.status]} variant="secondary">
                        {batch.status}
                    </Badge>
                </div>
                <p className="text-gray-400 text-sm mt-1">
                    {batch.processed_assets} / {batch.total_assets} assets
                    {batch.failed_assets > 0 && (
                        <span className="text-red-400 ml-2">({batch.failed_assets} failed)</span>
                    )}
                </p>
            </div>

            <div className="flex-shrink-0 w-32">
                <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-500">Progress</span>
                    <span className="text-white">{batch.progress_percentage.toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-rose-500 to-purple-600 transition-all duration-300"
                        style={{ width: `${batch.progress_percentage}%` }}
                    />
                </div>
            </div>

            {batch.status === 'processing' && (
                <Button size="sm" variant="outline" className="border-gray-700">
                    <Pause className="h-4 w-4" />
                </Button>
            )}
            {batch.status === 'paused' && (
                <Button size="sm" variant="outline" className="border-gray-700">
                    <Play className="h-4 w-4" />
                </Button>
            )}
        </div>
    );
}
