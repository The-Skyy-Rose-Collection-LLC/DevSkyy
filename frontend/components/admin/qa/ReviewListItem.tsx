import { Badge } from '@/components/ui/badge';
import { ChevronRight } from 'lucide-react';
import type { QAReview } from '@/lib/api';

const FIDELITY_THRESHOLD = 98;

interface ReviewListItemProps {
    review: QAReview;
    isSelected: boolean;
    onClick: () => void;
}

export function ReviewListItem({
    review,
    isSelected,
    onClick,
}: ReviewListItemProps) {
    const statusColors = {
        pending: 'bg-amber-500/10 text-amber-400',
        approved: 'bg-green-500/10 text-green-400',
        rejected: 'bg-red-500/10 text-red-400',
        regenerating: 'bg-blue-500/10 text-blue-400',
    };

    return (
        <div
            className={`flex items-center gap-3 p-4 cursor-pointer border-b border-gray-800 transition-colors ${isSelected ? 'bg-gray-800' : 'hover:bg-gray-800/50'
                }`}
            onClick={onClick}
        >
            <div className="h-12 w-12 rounded-lg bg-gray-800 overflow-hidden flex-shrink-0">
                <img
                    src={review.reference_image_url}
                    alt=""
                    className="w-full h-full object-cover"
                />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="text-white text-sm font-medium truncate">
                        #{review.id.slice(0, 8)}
                    </span>
                    <Badge className={statusColors[review.status]} variant="secondary">
                        {review.status}
                    </Badge>
                </div>
                <div className="flex items-center gap-2 mt-1">
                    <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className={`h-full ${review.fidelity_score >= FIDELITY_THRESHOLD
                                    ? 'bg-green-500'
                                    : review.fidelity_score >= 90
                                        ? 'bg-yellow-500'
                                        : 'bg-red-500'
                                }`}
                            style={{ width: `${review.fidelity_score}%` }}
                        />
                    </div>
                    <span className="text-gray-500 text-xs">
                        {review.fidelity_score.toFixed(0)}%
                    </span>
                </div>
            </div>
            <ChevronRight className="h-4 w-4 text-gray-500 flex-shrink-0" />
        </div>
    );
}
