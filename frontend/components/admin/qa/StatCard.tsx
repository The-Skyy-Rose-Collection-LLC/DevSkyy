import { Card, CardContent } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color: 'amber' | 'green' | 'red' | 'purple';
    onClick?: () => void;
    active?: boolean;
}

export function StatCard({
    title,
    value,
    icon: Icon,
    color,
    onClick,
    active,
}: StatCardProps) {
    const colorMap = {
        amber: 'from-amber-500 to-orange-500',
        green: 'from-green-500 to-emerald-500',
        red: 'from-red-500 to-rose-500',
        purple: 'from-purple-500 to-pink-500',
    };

    return (
        <Card
            className={`bg-gray-900/80 border-gray-700 overflow-hidden cursor-pointer transition-all ${active ? 'ring-1 ring-rose-500' : ''
                }`}
            onClick={onClick}
        >
            <div className={`h-1 bg-gradient-to-r ${colorMap[color]}`} />
            <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-gray-400">{title}</p>
                        <p className="text-2xl font-bold text-white mt-1">{value}</p>
                    </div>
                    <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${colorMap[color]} flex items-center justify-center`}>
                        <Icon className="h-5 w-5 text-white" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
