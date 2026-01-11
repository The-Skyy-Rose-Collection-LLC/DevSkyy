/**
 * FilterDrawer Component
 *
 * Mobile filter drawer with:
 * - Slide-in animation from right
 * - Overlay with backdrop blur
 * - Same filter options as sidebar
 * - Apply/Close buttons
 *
 * @component
 */

import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { FilterSidebar } from './FilterSidebar';
import type { ProductFilters } from '../../hooks/useProductFilters';

export interface FilterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
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

export const FilterDrawer: React.FC<FilterDrawerProps> = ({
  isOpen,
  onClose,
  filters,
  availableFilters,
  onUpdateFilters,
  onClearFilters,
  hasActiveFilters,
  accentColor = '#B76E79',
}) => {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (!isOpen) return;

    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Close on ESC key
  useEffect(() => {
    if (!isOpen) return;

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const styles = {
    overlay: {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 999,
      animation: 'fadeIn 0.3s ease-out',
      backdropFilter: 'blur(4px)',
    },
    drawer: {
      position: 'fixed' as const,
      top: 0,
      right: 0,
      bottom: 0,
      width: '90%',
      maxWidth: '400px',
      backgroundColor: '#ffffff',
      zIndex: 1000,
      animation: 'slideInRight 0.3s ease-out',
      display: 'flex',
      flexDirection: 'column' as const,
      boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.2)',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '1.5rem',
      borderBottom: '1px solid #e5e5e5',
    },
    title: {
      fontSize: '1.25rem',
      fontWeight: 700,
      color: '#1a1a1a',
    },
    closeButton: {
      background: 'none',
      border: 'none',
      fontSize: '1.5rem',
      color: '#666',
      cursor: 'pointer',
      width: '40px',
      height: '40px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '50%',
      transition: 'background-color 0.2s ease',
    } as React.CSSProperties,
    content: {
      flex: 1,
      overflowY: 'auto' as const,
      padding: '0 0.5rem',
    },
    footer: {
      padding: '1.5rem',
      borderTop: '1px solid #e5e5e5',
      display: 'flex',
      gap: '1rem',
    },
    applyButton: {
      flex: 1,
      background: accentColor,
      color: '#ffffff',
      border: 'none',
      padding: '1rem',
      borderRadius: '8px',
      fontSize: '1rem',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'transform 0.2s ease',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.05em',
    } as React.CSSProperties,
    clearButton: {
      background: 'none',
      border: `2px solid ${accentColor}`,
      color: accentColor,
      padding: '1rem 1.5rem',
      borderRadius: '8px',
      fontSize: '1rem',
      fontWeight: 600,
      cursor: hasActiveFilters ? 'pointer' : 'not-allowed',
      opacity: hasActiveFilters ? 1 : 0.4,
      transition: 'all 0.2s ease',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.05em',
    } as React.CSSProperties,
  };

  const drawerContent = (
    <>
      <div style={styles.overlay} onClick={onClose} />
      <div ref={drawerRef} style={styles.drawer}>
        <div style={styles.header}>
          <div style={styles.title}>Filters</div>
          <button
            style={styles.closeButton}
            onClick={onClose}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f0f0f0';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            aria-label="Close filters"
          >
            ×
          </button>
        </div>

        <div style={styles.content}>
          <FilterSidebar
            filters={filters}
            availableFilters={availableFilters}
            onUpdateFilters={onUpdateFilters}
            onClearFilters={onClearFilters}
            hasActiveFilters={hasActiveFilters}
            accentColor={accentColor}
          />
        </div>

        <div style={styles.footer}>
          <button
            style={styles.clearButton}
            onClick={() => {
              onClearFilters();
              onClose();
            }}
            disabled={!hasActiveFilters}
          >
            Clear
          </button>
          <button
            style={styles.applyButton}
            onClick={onClose}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            Apply Filters
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  );

  return createPortal(drawerContent, document.body);
};

export default FilterDrawer;
