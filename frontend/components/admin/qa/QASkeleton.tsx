import { Skeleton } from '@/components/ui/skeleton';

export function QASkeleton() {
    return (
        <div className="space-y-6">
            <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
            <div className="grid gap-4 md:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                    <Skeleton key={i} className="h-24 bg-gray-800" />
                ))}
            </div>
            <div className="grid gap-6 lg:grid-cols-3">
                <Skeleton className="h-96 bg-gray-800" />
                <Skeleton className="h-96 bg-gray-800 lg:col-span-2" />
            </div>
        </div>
    );
}
