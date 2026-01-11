/**
 * FilterSidebar Component
 *
 * Desktop filter sidebar with:
 * - Size, color, and price range filters
 * - Sorting options
 * - Collapse/expand animations
 * - Clear all filters button
 *
 * @component
 */

import React, { useState } from 'react';
import type { ProductFilters, SortOption } from '../../hooks/useProductFilters';

export interface FilterSidebarProps {
  filters: ProductFilters;
  availableFilters: {
    sizes: string[];
    colors: string[];
    priceRange: [number, number];
  };
  onUpdateFilters: (updates: Partial<ProductFilters>) => void;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
  accentColor?: string;
}

interface FilterSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const FilterSection: React.FC<FilterSectionProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  const styles = {
    section: {
      borderBottom: '1px solid #e5e5e5',
      paddingBottom: '1rem',
      marginBottom: '1rem',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      cursor: 'pointer',
      padding: '0.75rem 0',
      userSelect: 'none' as const,
    },
    title: {
      fontSize: '0.95rem',
      fontWeight: 600,
      color: '#1a1a1a',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.05em',
    },
    icon: {
      fontSize: '1.2rem',
      color: '#666',
      transition: 'transform 0.3s ease',
      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
    },
    content: {
      maxHeight: isExpanded ? '1000px' : '0',
      overflow: 'hidden',
      transition: 'max-height 0.3s ease',
    },
    contentInner: {
      paddingTop: '0.5rem',
    },
  };

  return (
    <div style={styles.section}>
      <div style={styles.header} onClick={onToggle}>
        <div style={styles.title}>{title}</div>
        <div style={styles.icon}>▼</div>
      </div>
      <div style={styles.content}>
        <div style={styles.contentInner}>{children}</div>
      </div>
    </div>
  );
};

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  filters,
  availableFilters,
  onUpdateFilters,
  onClearFilters,
  hasActiveFilters,
  accentColor = '#B76E79',
}) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    sort: true,
    size: true,
    color: true,
    price: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleSizeToggle = (size: string) => {
    const newSizes = filters.sizes.includes(size)
      ? filters.sizes.filter((s) => s !== size)
      : [...filters.sizes, size];
    onUpdateFilters({ sizes: newSizes });
  };

  const handleColorToggle = (color: string) => {
    const newColors = filters.colors.includes(color)
      ? filters.colors.filter((c) => c !== color)
      : [...filters.colors, color];
    onUpdateFilters({ colors: newColors });
  };

  const handlePriceChange = (min: number, max: number) => {
    onUpdateFilters({ priceRange: [min, max] });
  };

  const handleSortChange = (sortBy: SortOption) => {
    onUpdateFilters({ sortBy });
  };

  const styles = {
    sidebar: {
      width: '280px',
      padding: '2rem 1.5rem',
      backgroundColor: '#ffffff',
      borderRight: '1px solid #e5e5e5',
      height: '100%',
      overflowY: 'auto' as const,
      position: 'sticky' as const,
      top: 0,
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '2rem',
    },
    title: {
      fontSize: '1.25rem',
      fontWeight: 700,
      color: '#1a1a1a',
    },
    clearButton: {
      background: 'none',
      border: 'none',
      color: accentColor,
      fontSize: '0.85rem',
      fontWeight: 600,
      cursor: hasActiveFilters ? 'pointer' : 'not-allowed',
      opacity: hasActiveFilters ? 1 : 0.4,
      textDecoration: 'underline',
      transition: 'opacity 0.2s ease',
    } as React.CSSProperties,
    checkbox: {
      marginRight: '0.5rem',
      accentColor: accentColor,
      cursor: 'pointer',
    } as React.CSSProperties,
    checkboxLabel: {
      display: 'flex',
      alignItems: 'center',
      padding: '0.5rem 0',
      cursor: 'pointer',
      fontSize: '0.9rem',
      color: '#333',
      transition: 'color 0.2s ease',
    },
    radioLabel: {
      display: 'flex',
      alignItems: 'center',
      padding: '0.5rem 0',
      cursor: 'pointer',
      fontSize: '0.9rem',
      color: '#333',
      transition: 'color 0.2s ease',
    },
    priceInputs: {
      display: 'flex',
      gap: '0.5rem',
      alignItems: 'center',
      marginTop: '0.5rem',
    },
    priceInput: {
      width: '100%',
      padding: '0.5rem',
      border: '1px solid #ddd',
      borderRadius: '4px',
      fontSize: '0.9rem',
    } as React.CSSProperties,
    priceSeparator: {
      color: '#999',
    },
    resultCount: {
      padding: '1rem 0',
      fontSize: '0.85rem',
      color: '#666',
      fontStyle: 'italic' as const,
      borderTop: '1px solid #e5e5e5',
      marginTop: '1rem',
    },
  };

  const sortOptions: { value: SortOption; label: string }[] = [
    { value: 'newest', label: 'Newest' },
    { value: 'price-low', label: 'Price: Low to High' },
    { value: 'price-high', label: 'Price: High to Low' },
    { value: 'popular', label: 'Most Popular' },
  ];

  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <div style={styles.title}>Filters</div>
        <button
          style={styles.clearButton}
          onClick={onClearFilters}
          disabled={!hasActiveFilters}
        >
          Clear All
        </button>
      </div>

      {/* Sort By */}
      <FilterSection
        title="Sort By"
        isExpanded={expandedSections.sort}
        onToggle={() => toggleSection('sort')}
      >
        {sortOptions.map((option) => (
          <label
            key={option.value}
            style={{
              ...styles.radioLabel,
              color: filters.sortBy === option.value ? accentColor : '#333',
            }}
          >
            <input
              type="radio"
              name="sortBy"
              value={option.value}
              checked={filters.sortBy === option.value}
              onChange={() => handleSortChange(option.value)}
              style={styles.checkbox}
            />
            {option.label}
          </label>
        ))}
      </FilterSection>

      {/* Size Filter */}
      {availableFilters.sizes.length > 0 && (
        <FilterSection
          title="Size"
          isExpanded={expandedSections.size}
          onToggle={() => toggleSection('size')}
        >
          {availableFilters.sizes.map((size) => (
            <label
              key={size}
              style={{
                ...styles.checkboxLabel,
                color: filters.sizes.includes(size) ? accentColor : '#333',
              }}
            >
              <input
                type="checkbox"
                checked={filters.sizes.includes(size)}
                onChange={() => handleSizeToggle(size)}
                style={styles.checkbox}
              />
              {size}
            </label>
          ))}
        </FilterSection>
      )}

      {/* Color Filter */}
      {availableFilters.colors.length > 0 && (
        <FilterSection
          title="Color"
          isExpanded={expandedSections.color}
          onToggle={() => toggleSection('color')}
        >
          {availableFilters.colors.map((color) => (
            <label
              key={color}
              style={{
                ...styles.checkboxLabel,
                color: filters.colors.includes(color) ? accentColor : '#333',
              }}
            >
              <input
                type="checkbox"
                checked={filters.colors.includes(color)}
                onChange={() => handleColorToggle(color)}
                style={styles.checkbox}
              />
              {color}
            </label>
          ))}
        </FilterSection>
      )}

      {/* Price Range Filter */}
      <FilterSection
        title="Price Range"
        isExpanded={expandedSections.price}
        onToggle={() => toggleSection('price')}
      >
        <div style={styles.priceInputs}>
          <input
            type="number"
            placeholder="Min"
            value={filters.priceRange[0] || ''}
            onChange={(e) =>
              handlePriceChange(
                parseFloat(e.target.value) || 0,
                filters.priceRange[1]
              )
            }
            style={styles.priceInput}
            min={availableFilters.priceRange[0]}
            max={availableFilters.priceRange[1]}
          />
          <span style={styles.priceSeparator}>—</span>
          <input
            type="number"
            placeholder="Max"
            value={
              filters.priceRange[1] === Infinity ? '' : filters.priceRange[1]
            }
            onChange={(e) =>
              handlePriceChange(
                filters.priceRange[0],
                parseFloat(e.target.value) || Infinity
              )
            }
            style={styles.priceInput}
            min={availableFilters.priceRange[0]}
            max={availableFilters.priceRange[1]}
          />
        </div>
        <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.5rem' }}>
          ${availableFilters.priceRange[0]} - ${availableFilters.priceRange[1]}
        </div>
      </FilterSection>
    </div>
  );
};

export default FilterSidebar;
