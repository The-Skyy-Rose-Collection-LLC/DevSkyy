import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { Provider3D } from '@/lib/api';

interface ProviderCardProps {
    provider: Provider3D;
    isExpanded: boolean;
    onToggle: () => void;
    activeJobs: number;
}

export function ProviderCard({
    provider,
    isExpanded,
    onToggle,
    activeJobs,
}: ProviderCardProps) {
    const statusColors = {
        online: 'bg-green-500',
        offline: 'bg-red-500',
        busy: 'bg-yellow-500',
    };

    return (
        <Card
            className={`bg-gray-800 border-gray-700 cursor-pointer transition-all ${isExpanded ? 'ring-1 ring-rose-500' : ''
                }`}
            onClick={onToggle}
        >
            <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <div className={`h-2.5 w-2.5 rounded-full ${statusColors[provider.status]}`} />
                        <span className="text-white font-medium">{provider.name}</span>
                    </div>
                    {activeJobs > 0 && (
                        <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                            {activeJobs} active
                        </Badge>
                    )}
                </div>

                <div className="text-sm text-gray-400 space-y-1">
                    <div className="flex justify-between">
                        <span>Type:</span>
                        <span className="text-white capitalize">{provider.type}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Avg Time:</span>
                        <span className="text-white">{provider.avg_generation_time_s}s</span>
                    </div>
                </div>

                {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                        <p className="text-xs text-gray-500 mb-2">Capabilities</p>
                        <div className="flex flex-wrap gap-1">
                            {provider.capabilities.map((cap) => (
                                <Badge key={cap} variant="secondary" className="bg-gray-700 text-gray-300 text-xs">
                                    {cap}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}

                <div className="flex justify-center mt-3">
                    {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-gray-500" />
                    ) : (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
