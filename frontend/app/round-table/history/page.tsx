/**
 * Round Table History Page
 * ========================
 * Historical view of all LLM competitions.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Trophy,
  ArrowLeft,
  Calendar,
  Download,
  Filter,
  Crown,
  Search,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
} from '@/components/ui';
import { useRoundTableHistory } from '@/lib/hooks';
import {
  formatRelativeTime,
  formatDuration,
  formatCurrency,
  getProviderDisplayName,
} from '@/lib/utils';
import type { LLMProvider } from '@/lib/types';

export default function RoundTableHistoryPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: history, isLoading } = useRoundTableHistory({ limit: 100 });

  const filteredHistory = history?.filter((entry) =>
    entry.prompt.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const paginatedHistory = filteredHistory?.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const totalPages = Math.ceil((filteredHistory?.length || 0) / pageSize);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/round-table">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Calendar className="h-8 w-8" />
              Competition History
            </h1>
            <p className="text-gray-500 mt-1">
              View all past LLM Round Table competitions
            </p>
          </div>
        </div>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by prompt..."
          className="w-full pl-10 pr-4 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-brand-primary"
        />
      </div>

      {/* Results */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50 dark:bg-gray-900">
                <th className="text-left py-3 px-4 text-sm font-medium">Date</th>
                <th className="text-left py-3 px-4 text-sm font-medium">Prompt</th>
                <th className="text-left py-3 px-4 text-sm font-medium">Winner</th>
                <th className="text-left py-3 px-4 text-sm font-medium">Participants</th>
                <th className="text-left py-3 px-4 text-sm font-medium">Duration</th>
                <th className="text-left py-3 px-4 text-sm font-medium">Cost</th>
                <th className="text-left py-3 px-4 text-sm font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b">
                    <td colSpan={7} className="py-4 px-4">
                      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : paginatedHistory?.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    No competitions found
                  </td>
                </tr>
              ) : (
                paginatedHistory?.map((entry) => (
                  <tr
                    key={entry.id}
                    className="border-b hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                  >
                    <td className="py-3 px-4 text-sm">
                      {formatRelativeTime(entry.createdAt)}
                    </td>
                    <td className="py-3 px-4 text-sm max-w-[300px] truncate">
                      {entry.prompt}
                    </td>
                    <td className="py-3 px-4">
                      {entry.winner ? (
                        <Badge variant={entry.winner.provider as LLMProvider}>
                          <Crown className="mr-1 h-3 w-3" />
                          {getProviderDisplayName(entry.winner.provider)}
                        </Badge>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {entry.participants.length}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {entry.totalDurationMs
                        ? formatDuration(entry.totalDurationMs)
                        : '-'}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {entry.totalCostUsd
                        ? formatCurrency(entry.totalCostUsd)
                        : '-'}
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          entry.status === 'completed'
                            ? 'success'
                            : entry.status === 'failed'
                              ? 'destructive'
                              : 'warning'
                        }
                        className="text-xs"
                      >
                        {entry.status}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, filteredHistory?.length || 0)} of{' '}
            {filteredHistory?.length || 0} results
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
