/**
 * AI Tools Page Tests
 * ====================
 * Tests for HuggingFace Spaces integration page.
 */

import { describe, it, expect } from '@jest/globals';
import { HF_SPACES, getSpacesByCategory, searchSpaces } from '@/lib/hf-spaces';

describe('AI Tools Page - HF Spaces', () => {
  describe('HF_SPACES Configuration', () => {
    it('should have exactly 5 spaces configured', () => {
      expect(HF_SPACES).toHaveLength(5);
    });

    it('should have all required fields for each space', () => {
      HF_SPACES.forEach((space) => {
        expect(space).toHaveProperty('id');
        expect(space).toHaveProperty('name');
        expect(space).toHaveProperty('description');
        expect(space).toHaveProperty('url');
        expect(space).toHaveProperty('icon');
        expect(space).toHaveProperty('category');
        expect(space).toHaveProperty('tags');
        expect(Array.isArray(space.tags)).toBe(true);
      });
    });

    it('should have valid HuggingFace URLs', () => {
      HF_SPACES.forEach((space) => {
        expect(space.url).toContain('huggingface.co/spaces');
        expect(space.url).toMatch(/^https:\/\//);
      });
    });

    it('should have unique IDs', () => {
      const ids = HF_SPACES.map((space) => space.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });
  });

  describe('Category Filtering', () => {
    it('should return all spaces for "all" category', () => {
      const spaces = getSpacesByCategory('all');
      expect(spaces).toHaveLength(5);
    });

    it('should filter generation spaces correctly', () => {
      const spaces = getSpacesByCategory('generation');
      expect(spaces.length).toBeGreaterThan(0);
      spaces.forEach((space) => {
        expect(space.category).toBe('generation');
      });
    });

    it('should filter analysis spaces correctly', () => {
      const spaces = getSpacesByCategory('analysis');
      expect(spaces.length).toBeGreaterThan(0);
      spaces.forEach((space) => {
        expect(space.category).toBe('analysis');
      });
    });

    it('should filter training spaces correctly', () => {
      const spaces = getSpacesByCategory('training');
      expect(spaces.length).toBeGreaterThan(0);
      spaces.forEach((space) => {
        expect(space.category).toBe('training');
      });
    });

    it('should filter conversion spaces correctly', () => {
      const spaces = getSpacesByCategory('conversion');
      expect(spaces.length).toBeGreaterThan(0);
      spaces.forEach((space) => {
        expect(space.category).toBe('conversion');
      });
    });
  });

  describe('Search Functionality', () => {
    it('should find spaces by name', () => {
      const results = searchSpaces('converter');
      expect(results.length).toBeGreaterThan(0);
      expect(results.some((space) => space.name.toLowerCase().includes('converter'))).toBe(true);
    });

    it('should find spaces by description', () => {
      const results = searchSpaces('upscaling');
      expect(results.length).toBeGreaterThan(0);
    });

    it('should find spaces by tags', () => {
      const results = searchSpaces('3D');
      expect(results.length).toBeGreaterThan(0);
    });

    it('should be case-insensitive', () => {
      const resultsLower = searchSpaces('flux');
      const resultsUpper = searchSpaces('FLUX');
      expect(resultsLower).toEqual(resultsUpper);
    });

    it('should return empty array for no matches', () => {
      const results = searchSpaces('nonexistent-query-xyz');
      expect(results).toHaveLength(0);
    });
  });

  describe('Space Data Validation', () => {
    it('should have all 5 expected spaces', () => {
      const expectedSpaces = [
        '3d-converter',
        'flux-upscaler',
        'lora-training-monitor',
        'product-analyzer',
        'product-photography',
      ];

      expectedSpaces.forEach((id) => {
        const space = HF_SPACES.find((s) => s.id === id);
        expect(space).toBeDefined();
      });
    });

    it('should have emojis as icons', () => {
      HF_SPACES.forEach((space) => {
        expect(space.icon).toBeTruthy();
        expect(space.icon.length).toBeGreaterThan(0);
      });
    });

    it('should have non-empty descriptions', () => {
      HF_SPACES.forEach((space) => {
        expect(space.description).toBeTruthy();
        expect(space.description.length).toBeGreaterThan(10);
      });
    });

    it('should have at least one tag per space', () => {
      HF_SPACES.forEach((space) => {
        expect(space.tags.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Categories', () => {
    it('should have all 4 categories represented', () => {
      const categories = new Set(HF_SPACES.map((space) => space.category));
      expect(categories.has('generation')).toBe(true);
      expect(categories.has('analysis')).toBe(true);
      expect(categories.has('training')).toBe(true);
      expect(categories.has('conversion')).toBe(true);
    });

    it('should have valid category values', () => {
      const validCategories = ['generation', 'analysis', 'training', 'conversion'];
      HF_SPACES.forEach((space) => {
        expect(validCategories).toContain(space.category);
      });
    });
  });
});
