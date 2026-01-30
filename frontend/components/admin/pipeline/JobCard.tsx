import { Badge } from '@/components/ui/badge';
import { ArrowRight, CheckCircle2, Circle, Clock, Loader2, XCircle } from 'lucide-react';
import type { Job3D } from '@/lib/api';

interface JobCardProps {
    job: Job3D;
    isSelected: boolean;
    onSelect: () => void;
}

export function JobCard({
    job,
    isSelected,
    onSelect,
}: JobCardProps) {
    const statusConfig = {
        queued: { icon: Clock, bg: 'bg-gray-500/10', text: 'text-gray-400', label: 'Queued' },
        processing: { icon: Loader2, bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'Processing' },
        completed: { icon: CheckCircle2, bg: 'bg-green-500/10', text: 'text-green-400', label: 'Completed' },
        failed: { icon: XCircle, bg: 'bg-red-500/10', text: 'text-red-400', label: 'Failed' },
    };

    const config = statusConfig[job.status] || statusConfig.queued;
    const StatusIcon = config.icon;

    return (
        <div
            className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all ${isSelected
                    ? 'bg-gray-800 border-rose-500'
                    : 'bg-gray-900/80 border-gray-700 hover:border-gray-600'
                }`}
            onClick={onSelect}
        >
            <div className={`h-10 w-10 rounded-lg ${config.bg} flex items-center justify-center`}>
                <StatusIcon className={`h-5 w-5 ${config.text} ${job.status === 'processing' ? 'animate-spin' : ''}`} />
            </div>

            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="text-white font-medium truncate">{job.provider}</span>
                    <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
                        {job.input_type}
                    </Badge>
                </div>
                <p className="text-gray-500 text-sm truncate mt-0.5">{job.input}</p>
            </div>

            <Badge className={`${config.bg} ${config.text} border-0`}>
                {config.label}
            </Badge>

            <div className="text-right text-sm">
                <p className="text-gray-400">
                    {new Date(job.created_at).toLocaleTimeString()}
                </p>
                {job.completed_at && (
                    <p className="text-gray-500 text-xs">
                        {Math.round(
                            (new Date(job.completed_at).getTime() - new Date(job.created_at).getTime()) / 1000
                        )}s
                    </p>
                )}
            </div>

            <ArrowRight className="h-4 w-4 text-gray-500" />
        </div>
    );
}
