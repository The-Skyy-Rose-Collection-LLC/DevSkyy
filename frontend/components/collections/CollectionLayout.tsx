/**
 * CollectionLayout - Base layout for SkyyRose collection pages
 *
 * Provides the foundational structure for interactive collection experiences
 * combining Three.js 3D scenes, product grids, and luxury animations.
 *
 * @component
 */

import React, { ReactNode, useEffect, useState } from 'react';
import type { Collection } from '../../types/collections';

export interface CollectionLayoutProps {
  /** Collection data (BLACK_ROSE, SIGNATURE, LOVE_HURTS) */
  collection: Collection;

  /** Three.js experience component */
  experienceComponent: ReactNode;

  /** Product grid component */
  productGridComponent: ReactNode;

  /** Optional featured product section */
  featuredSection?: ReactNode;

  /** Loading state */
  loading?: boolean;
}

/**
 * Main collection page layout with hero, 3D experience, and product sections
 */
export const CollectionLayout: React.FC<CollectionLayoutProps> = ({
  collection,
  experienceComponent,
  productGridComponent,
  featuredSection,
  loading = false,
}) => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  const styles = {
    layout: {
      minHeight: '100vh',
      background: collection.theme.backgroundColor,
      color: collection.theme.textColor,
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    hero: {
      height: '100vh',
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      position: 'relative' as const,
      overflow: 'hidden',
    },
    heroBackground: {
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(135deg, ${collection.theme.primaryColor}15, ${collection.theme.backgroundColor})`,
      transform: `translateY(${scrollY * 0.5}px)`,
      willChange: 'transform',
    },
    heroPattern: {
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      opacity: 0.05,
      backgroundImage: `radial-gradient(circle at 20% 50%, ${collection.theme.primaryColor} 1px, transparent 1px),
                        radial-gradient(circle at 80% 80%, ${collection.theme.accentColor || collection.theme.primaryColor} 1px, transparent 1px)`,
      backgroundSize: '100px 100px, 150px 150px',
      transform: `translateY(${scrollY * 0.3}px)`,
      willChange: 'transform',
    },
    heroContent: {
      maxWidth: '800px',
      textAlign: 'center' as const,
      zIndex: 10,
    },
    title: {
      fontSize: 'clamp(3rem, 8vw, 6rem)',
      fontWeight: 800,
      letterSpacing: '-0.03em',
      margin: '0 0 1rem 0',
      background: `linear-gradient(135deg, ${collection.theme.primaryColor}, ${collection.theme.accentColor || collection.theme.primaryColor})`,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
    },
    tagline: {
      fontSize: 'clamp(1.25rem, 3vw, 1.75rem)',
      fontWeight: 500,
      margin: '0 0 1.5rem 0',
      opacity: 0.9,
    },
    description: {
      fontSize: 'clamp(1rem, 2vw, 1.125rem)',
      lineHeight: 1.7,
      opacity: 0.75,
      maxWidth: '600px',
      margin: '0 auto',
    },
    scrollIndicator: {
      position: 'absolute' as const,
      bottom: '2rem',
      left: '50%',
      transform: 'translateX(-50%)',
      opacity: 0.6,
    },
    experience: {
      minHeight: '100vh',
      position: 'relative' as const,
      background: collection.theme.backgroundColor,
    },
    experienceLoading: {
      height: '100vh',
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      justifyContent: 'center',
      gap: '1rem',
    },
    products: {
      padding: '4rem 2rem',
      background: `linear-gradient(to bottom, ${collection.theme.backgroundColor}, ${collection.theme.primaryColor}05)`,
    },
    productsHeader: {
      textAlign: 'center' as const,
      maxWidth: '800px',
      margin: '0 auto 3rem auto',
    },
    productsTitle: {
      fontSize: 'clamp(2rem, 5vw, 3rem)',
      fontWeight: 700,
      margin: '0 0 1rem 0',
    },
    productsSubtitle: {
      fontSize: '1.125rem',
      opacity: 0.75,
    },
    story: {
      padding: '6rem 2rem',
      background: `${collection.theme.primaryColor}08`,
    },
    storyContent: {
      maxWidth: '900px',
      margin: '0 auto',
      textAlign: 'center' as const,
    },
    storyTitle: {
      fontSize: 'clamp(2rem, 5vw, 3rem)',
      fontWeight: 700,
      margin: '0 0 2rem 0',
    },
    storyText: {
      fontSize: '1.25rem',
      lineHeight: 1.8,
      opacity: 0.85,
    },
    featured: {
      padding: '4rem 2rem',
    },
  };

  return (
    <div style={styles.layout}>
      {/* Hero Section */}
      <header style={styles.hero}>
        {/* Parallax Background Layers */}
        <div style={styles.heroBackground} />
        <div style={styles.heroPattern} />

        <div style={styles.heroContent}>
          <h1 style={styles.title}>{collection.name}</h1>
          <p style={styles.tagline}>{collection.tagline}</p>
          <p style={styles.description}>{collection.description}</p>
        </div>

        {/* Scroll indicator */}
        <div style={styles.scrollIndicator} aria-label="Scroll down">
          <div style={{
            width: '24px',
            height: '24px',
            borderRight: '2px solid currentColor',
            borderBottom: '2px solid currentColor',
            transform: 'rotate(45deg)',
          }} />
        </div>
      </header>

      {/* 3D Experience Section */}
      <section style={styles.experience} aria-label="Interactive 3D Experience">
        {loading ? (
          <div style={styles.experienceLoading}>
            <div style={{
              width: '48px',
              height: '48px',
              border: `4px solid ${collection.theme.primaryColor}30`,
              borderTopColor: collection.theme.primaryColor,
              borderRadius: '50%',
            }}>
              {/* Spinner animation handled by CSS */}
            </div>
            <p>Loading experience...</p>
          </div>
        ) : (
          experienceComponent
        )}
      </section>

      {/* Featured Product Section (optional) */}
      {featuredSection && (
        <section style={styles.featured} aria-label="Featured Products">
          {featuredSection}
        </section>
      )}

      {/* Product Grid Section */}
      <section style={styles.products} aria-label="Collection Products">
        <div style={styles.productsHeader}>
          <h2 style={styles.productsTitle}>Explore the Collection</h2>
          <p style={styles.productsSubtitle}>Handcrafted luxury streetwear where art meets rebellion</p>
        </div>

        {productGridComponent}
      </section>

      {/* Collection Story Section */}
      <section style={styles.story} aria-label="Collection Story">
        <div style={styles.storyContent}>
          <h2 style={styles.storyTitle}>The Story</h2>
          <p style={styles.storyText}>{collection.story}</p>
        </div>
      </section>
    </div>
  );
};

export default CollectionLayout;
