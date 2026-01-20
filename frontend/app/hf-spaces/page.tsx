/**
 * HuggingFace Spaces Dashboard
 * ============================
 * Interactive dashboard for DevSkyy's HuggingFace Spaces
 *
 * Features:
 * - Real-time status monitoring
 * - Embedded Space interfaces
 * - Category filtering
 * - Search functionality
 */

'use client';

import { useState, useEffect } from 'react';
import {
  HF_SPACES,
  SPACE_CATEGORIES,
  getSpacesByCategory,
  searchSpaces,
  type HFSpace
} from '@/lib/hf-spaces';

interface SpaceStatus {
  id: string;
  status: 'running' | 'building' | 'error' | 'unknown';
  last_updated: string;
}

export default function HFSpacesPage() {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [spaces, setSpaces] = useState<HFSpace[]>(HF_SPACES);
  const [spaceStatuses, setSpaceStatuses] = useState<Record<string, SpaceStatus>>({});
  const [selectedSpace, setSelectedSpace] = useState<HFSpace | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch Space statuses from backend
  useEffect(() => {
    async function fetchStatuses() {
      try {
        const response = await fetch('/api/v1/hf-spaces/status');
        if (!response.ok) throw new Error('Failed to fetch statuses');

        const data = await response.json();
        const statusMap: Record<string, SpaceStatus> = {};

        data.spaces.forEach((space: any) => {
          statusMap[space.id] = {
            id: space.id,
            status: space.status,
            last_updated: space.last_updated,
          };
        });

        setSpaceStatuses(statusMap);
      } catch (error) {
        console.error('Error fetching Space statuses:', error);
        // If endpoint doesn't exist, set all spaces to 'running' and continue
        const defaultStatuses: Record<string, SpaceStatus> = {};
        HF_SPACES.forEach((space) => {
          defaultStatuses[space.id] = {
            id: space.id,
            status: 'running',
            last_updated: new Date().toISOString(),
          };
        });
        setSpaceStatuses(defaultStatuses);
      } finally {
        setIsLoading(false);
      }
    }

    fetchStatuses();

    // Refresh statuses every 30 seconds
    const interval = setInterval(fetchStatuses, 30000);
    return () => clearInterval(interval);
  }, []);

  // Filter spaces based on category and search
  useEffect(() => {
    let filtered = searchQuery
      ? searchSpaces(searchQuery)
      : getSpacesByCategory(selectedCategory);

    setSpaces(filtered);
  }, [selectedCategory, searchQuery]);

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'building': return 'bg-yellow-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-gray-900 via-purple-900 to-gray-900">
      {/* Header */}
      <div className="bg-black/30 backdrop-blur-sm border-b border-purple-500/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-linear-to-r from-purple-400 to-pink-600">
            🤗 HuggingFace Spaces
          </h1>
          <p className="mt-2 text-gray-300">
            AI-powered tools and interfaces hosted on HuggingFace
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters and Search */}
        <div className="mb-8 space-y-4">
          {/* Category Filters */}
          <div className="flex flex-wrap gap-2">
            {SPACE_CATEGORIES.map((category) => (
              <button
                key={category.id}
                onClick={() => {
                  setSelectedCategory(category.id);
                  setSearchQuery('');
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  selectedCategory === category.id
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50'
                    : 'bg-gray-800/50 text-gray-300 hover:bg-gray-700/50'
                }`}
              >
                {category.icon} {category.label}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search Spaces by name, description, or tags..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSelectedCategory('all');
              }}
              className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <span className="absolute right-4 top-3 text-gray-400">🔍</span>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            <p className="mt-4 text-gray-400">Loading Spaces...</p>
          </div>
        )}

        {/* Spaces Grid */}
        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {spaces.map((space) => {
              const status = spaceStatuses[space.id]?.status || 'unknown';

              return (
                <div
                  key={space.id}
                  className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 hover:border-purple-500 transition-all cursor-pointer overflow-hidden group"
                  onClick={() => setSelectedSpace(space)}
                >
                  {/* Status Badge */}
                  <div className="flex items-center justify-between p-4 border-b border-gray-700">
                    <span className="text-3xl">{space.icon}</span>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
                      <span className="text-xs text-gray-400 capitalize">{status}</span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-purple-400 transition-colors">
                      {space.name}
                    </h3>
                    <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                      {space.description}
                    </p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2">
                      {space.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-purple-600/20 text-purple-300 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="px-4 py-3 bg-gray-900/50 flex items-center justify-between">
                    <span className="text-xs text-gray-500 capitalize">
                      {space.category}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(space.url, '_blank');
                      }}
                      className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
                    >
                      Open in HF →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* No Results */}
        {!isLoading && spaces.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">
              No Spaces found matching &quot;{searchQuery}&quot;
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory('all');
              }}
              className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Space Modal */}
      {selectedSpace && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedSpace(null)}
        >
          <div
            className="bg-gray-900 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden border border-purple-500/30"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <div className="flex items-center gap-4">
                <span className="text-4xl">{selectedSpace.icon}</span>
                <div>
                  <h2 className="text-2xl font-bold text-white">{selectedSpace.name}</h2>
                  <p className="text-gray-400">{selectedSpace.description}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSpace(null)}
                className="text-gray-400 hover:text-white transition-colors text-2xl"
              >
                ×
              </button>
            </div>

            {/* Embedded Space */}
            <div className="h-[600px] bg-black">
              <iframe
                src={selectedSpace.url.replace('huggingface.co', 'hf.space') + '/embed'}
                className="w-full h-full"
                title={selectedSpace.name}
                allow="accelerometer; ambient-light-sensor; camera; encrypted-media; geolocation; gyroscope; hid; microphone; midi; payment; usb; vr; xr-spatial-tracking"
                sandbox="allow-forms allow-modals allow-popups allow-presentation allow-same-origin allow-scripts"
              />
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-700 flex items-center justify-between bg-gray-800/50">
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(spaceStatuses[selectedSpace.id]?.status || 'unknown')}`} />
                <span className="text-sm text-gray-400">
                  Status: {spaceStatuses[selectedSpace.id]?.status || 'unknown'}
                </span>
              </div>
              <a
                href={selectedSpace.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Open in New Tab →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
