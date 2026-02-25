/**
 * Unit Tests for Collection Types and Constants
 */

import { COLLECTIONS } from '../collections';
import type { Collection, CollectionTheme } from '../collections';

describe('COLLECTIONS', () => {
  it('should define exactly 3 collections', () => {
    expect(Object.keys(COLLECTIONS)).toHaveLength(3);
  });

  it('should contain BLACK_ROSE, SIGNATURE, and LOVE_HURTS', () => {
    expect(COLLECTIONS).toHaveProperty('BLACK_ROSE');
    expect(COLLECTIONS).toHaveProperty('SIGNATURE');
    expect(COLLECTIONS).toHaveProperty('LOVE_HURTS');
  });

  describe.each(Object.entries(COLLECTIONS))('%s', (key, collection) => {
    it('should have an id matching the key', () => {
      expect(collection.id).toBe(key);
    });

    it('should have required string fields', () => {
      expect(typeof collection.name).toBe('string');
      expect(collection.name.length).toBeGreaterThan(0);
      expect(typeof collection.tagline).toBe('string');
      expect(collection.tagline.length).toBeGreaterThan(0);
      expect(typeof collection.description).toBe('string');
      expect(collection.description.length).toBeGreaterThan(0);
      expect(typeof collection.story).toBe('string');
      expect(collection.story.length).toBeGreaterThan(0);
    });

    it('should have a valid theme with required colors', () => {
      const theme: CollectionTheme = collection.theme;
      expect(theme.primaryColor).toMatch(/^#[0-9a-fA-F]{6}$/);
      expect(theme.backgroundColor).toMatch(/^#[0-9a-fA-F]{6}$/);
      expect(theme.textColor).toMatch(/^#[0-9a-fA-F]{6}$/);
    });

    it('should have a categorySlug', () => {
      expect(typeof collection.categorySlug).toBe('string');
      expect(collection.categorySlug.length).toBeGreaterThan(0);
    });

    it('should have a valid experienceType', () => {
      const validTypes = ['black-rose', 'signature', 'love-hurts', 'showroom', 'runway'];
      expect(validTypes).toContain(collection.experienceType);
    });
  });

  describe('BLACK_ROSE', () => {
    const col = COLLECTIONS['BLACK_ROSE'];

    it('should have gothic dark theme', () => {
      expect(col.theme.primaryColor).toBe('#1a1a1a');
      expect(col.theme.backgroundColor).toBe('#0a0a0a');
      expect(col.theme.textColor).toBe('#ffffff');
      expect(col.theme.accentColor).toBe('#8b0000');
    });

    it('should have black-rose experience type', () => {
      expect(col.experienceType).toBe('black-rose');
    });

    it('should have black-rose category slug', () => {
      expect(col.categorySlug).toBe('black-rose');
    });
  });

  describe('SIGNATURE', () => {
    const col = COLLECTIONS['SIGNATURE'];

    it('should have classic gold theme', () => {
      expect(col.theme.primaryColor).toBe('#d4af37');
      expect(col.theme.backgroundColor).toBe('#f5f5f0');
      expect(col.theme.textColor).toBe('#2a2a2a');
      expect(col.theme.accentColor).toBe('#8b7355');
    });

    it('should have signature experience type', () => {
      expect(col.experienceType).toBe('signature');
    });
  });

  describe('LOVE_HURTS', () => {
    const col = COLLECTIONS['LOVE_HURTS'];

    it('should have rose gold primary (brand color)', () => {
      expect(col.theme.primaryColor).toBe('#b76e79');
    });

    it('should have dark background', () => {
      expect(col.theme.backgroundColor).toBe('#1a0a0a');
    });

    it('should have crimson accent', () => {
      expect(col.theme.accentColor).toBe('#dc143c');
    });

    it('should have love-hurts experience type', () => {
      expect(col.experienceType).toBe('love-hurts');
    });
  });
});
