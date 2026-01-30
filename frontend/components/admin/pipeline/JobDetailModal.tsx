import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Box, RotateCcw, XCircle } from 'lucide-react';
import { ModelViewerFallback } from '@/components/three-viewer';
import type { Job3D } from '@/lib/api';

interface JobDetailModalProps {
    job: Job3D;
    onClose: () => void;
}

export function JobDetailModal({
    job,
    onClose,
}: JobDetailModalProps) {
    return (
        <div className="fixed inset-0 z-50 bg-gray-900/95 flex items-center justify-center p-4">
            <Card className="w-full max-w-4xl bg-gray-900 border-gray-700 max-h-[90vh] overflow-auto">
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-white">Job Details</CardTitle>
                        <CardDescription className="text-gray-400">
                            {job.id}
                        </CardDescription>
                    </div>
                    <Button variant="ghost" onClick={onClose}>
                        <XCircle className="h-5 w-5" />
                    </Button>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Model Preview */}
                    {job.status === 'completed' && job.output_url && (
                        <div className="aspect-video rounded-lg overflow-hidden">
                            <ModelViewerFallback
                                modelUrl={job.output_url}
                                height="100%"
                                arEnabled
                            />
                        </div>
                    )}

                    {/* Job Info */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <p className="text-gray-500 text-sm">Provider</p>
                            <p className="text-white">{job.provider}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-gray-500 text-sm">Input Type</p>
                            <p className="text-white capitalize">{job.input_type}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-gray-500 text-sm">Status</p>
                            <Badge
                                className={
                                    job.status === 'completed'
                                        ? 'bg-green-500/10 text-green-400'
                                        : job.status === 'failed'
                                            ? 'bg-red-500/10 text-red-400'
                                            : 'bg-blue-500/10 text-blue-400'
                                }
                            >
                                {job.status}
                            </Badge>
                        </div>
                        <div className="space-y-1">
                            <p className="text-gray-500 text-sm">Created</p>
                            <p className="text-white">{new Date(job.created_at).toLocaleString()}</p>
                        </div>
                    </div>

                    {/* Input */}
                    <div className="space-y-1">
                        <p className="text-gray-500 text-sm">Input</p>
                        <p className="text-white bg-gray-800 rounded-lg p-3 text-sm break-all">
                            {job.input}
                        </p>
                    </div>

                    {/* Error */}
                    {job.error && (
                        <div className="space-y-1">
                            <p className="text-red-400 text-sm flex items-center gap-2">
                                <AlertCircle className="h-4 w-4" />
                                Error
                            </p>
                            <p className="text-red-300 bg-red-500/10 rounded-lg p-3 text-sm">
                                {job.error}
                            </p>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 pt-4">
                        {job.status === 'completed' && job.output_url && (
                            <Button
                                className="bg-rose-500 hover:bg-rose-600"
                                onClick={() => window.open(job.output_url, '_blank')}
                            >
                                <Box className="mr-2 h-4 w-4" />
                                View 3D Model
                            </Button>
                        )}
                        {job.status === 'failed' && (
                            <Button className="bg-amber-500 hover:bg-amber-600">
                                <RotateCcw className="mr-2 h-4 w-4" />
                                Retry
                            </Button>
                        )}
                        <Button variant="outline" className="border-gray-700" onClick={onClose}>
                            Close
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
