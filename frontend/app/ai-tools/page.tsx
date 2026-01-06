/**
 * AI Tools & HuggingFace Spaces Page
 * ===================================
 * Interactive page for testing and using HuggingFace Spaces.
 * Provides tab navigation, fullscreen mode, and category filtering.
 */

'use client';

import { useState } from 'react';
import { Sparkles, Search, Grid, Maximize2 } from 'lucide-react';
import { HFSpaceCard } from '@/components/HFSpaceCard';
import { Card, CardContent, Badge } from '@/components/ui';
import {
  HF_SPACES,
  SPACE_CATEGORIES,
  getSpacesByCategory,
  searchSpaces,
  type HFSpace,
} from '@/lib/hf-spaces';

export default function AIToolsPage() {
  const [selectedSpace, setSelectedSpace] = useState<HFSpace>(HF_SPACES[0]);
  const [fullscreen, setFullscreen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  // Filter spaces based on search and category
  const filteredSpaces = searchQuery
    ? searchSpaces(searchQuery)
    : getSpacesByCategory(categoryFilter);

  // Update selected space if it's filtered out
  const visibleSelectedSpace = filteredSpaces.find(
    (space) => space.id === selectedSpace.id
  );
  const displaySpace = visibleSelectedSpace || filteredSpaces[0] || HF_SPACES[0];

  return (
    <div className="container mx-auto p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold flex items-center gap-3">
            <Sparkles className="h-8 w-8 lg:h-10 lg:w-10 text-brand-primary" />
            AI Tools & Spaces
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Explore and use {HF_SPACES.length} powerful AI tools powered by HuggingFace
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Search Bar */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search spaces by name, description, or tags..."
            className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-primary transition-all"
          />
        </div>

        {/* Category Filters */}
        <div className="flex gap-2 overflow-x-auto pb-2 lg:pb-0">
          {SPACE_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                setCategoryFilter(cat.id);
                setSearchQuery('');
              }}
              className={`px-4 py-2 rounded-lg whitespace-nowrap font-medium transition-all ${
                categoryFilter === cat.id
                  ? 'bg-brand-primary text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <span className="mr-2">{cat.icon}</span>
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {filteredSpaces.map((space) => (
            <button
              key={space.id}
              onClick={() => setSelectedSpace(space)}
              className={`px-4 py-3 rounded-t-lg whitespace-nowrap font-medium transition-all border-b-2 ${
                selectedSpace.id === space.id
                  ? 'bg-white dark:bg-gray-900 border-brand-primary text-brand-primary'
                  : 'bg-gray-50 dark:bg-gray-800 border-transparent hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <span className="text-xl mr-2">{space.icon}</span>
              <span className="hidden sm:inline">{space.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Active Space */}
      <HFSpaceCard
        space={displaySpace}
        fullscreen={fullscreen}
        onToggleFullscreen={() => setFullscreen(!fullscreen)}
      />

      {/* Grid View (when not fullscreen) */}
      {!fullscreen && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Grid className="h-5 w-5 text-gray-600" />
            <h2 className="text-xl font-bold">All Spaces</h2>
            <Badge variant="secondary">{filteredSpaces.length}</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSpaces.map((space) => (
              <Card
                key={space.id}
                className={`cursor-pointer transition-all hover:shadow-lg hover:scale-105 ${
                  selectedSpace.id === space.id
                    ? 'ring-2 ring-brand-primary'
                    : ''
                }`}
                onClick={() => setSelectedSpace(space)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <span className="text-4xl">{space.icon}</span>
                    <Badge variant="outline" className="text-xs">
                      {space.category}
                    </Badge>
                  </div>
                  <h3 className="text-lg font-bold mb-2">{space.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {space.description}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {space.tags.slice(0, 3).map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="text-xs"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredSpaces.length === 0 && (
            <Card className="p-12 text-center">
              <Search className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No spaces found matching your search
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
