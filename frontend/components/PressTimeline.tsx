/**
 * SkyyRose Press Timeline Component
 *
 * Displays press mentions and media coverage in an interactive timeline format.
 * Fetches data from wordpress/data/press_mentions.py via REST API.
 *
 * Features:
 * - Dynamic press mention loading via WordPress REST API
 * - Responsive grid layout (1-3 columns based on viewport)
 * - Publication logos with fallback text
 * - Click-through to full articles
 * - Impact score visualization
 * - Featured press highlighting
 * - Smooth animations and transitions
 *
 * Author: DevSkyy Platform Team
 * Version: 1.0.0
 */

import React, { useEffect, useState } from 'react';
import Link from 'next/link';

/**
 * Pydantic-validated press mention structure from WordPress
 */
interface PressMention {
  date: string; // ISO 8601 format
  publication: string;
  title: string;
  excerpt: string;
  link: string;
  logo_url: string;
  featured: boolean;
  impact_score: number; // 1-10 scale
}

interface PressTimelineProps {
  /**
   * Maximum number of press mentions to display
   * @default 6
   */
  limit?: number;

  /**
   * Show only featured press mentions
   * @default false
   */
  featuredOnly?: boolean;

  /**
   * Sort order of press mentions
   * @default 'newest'
   */
  sortBy?: 'newest' | 'oldest' | 'impact';

  /**
   * Collection slug for color theming
   * @default 'signature'
   */
  collectionSlug?: 'signature' | 'black-rose' | 'love-hurts';

  /**
   * Whether to show publication logos
   * @default true
   */
  showLogos?: boolean;

  /**
   * Whether to show impact score badges
   * @default false
   */
  showImpactScore?: boolean;

  /**
   * CSS class for root container
   */
  className?: string;

  /**
   * Callback when mention is clicked
   */
  onMentionClick?: (mention: PressMention) => void;
}

/**
 * Collection-specific color themes
 */
const COLLECTION_COLORS = {
  signature: {
    primary: '#D4AF37',
    accent: '#C9A962',
    background: '#F5F5F0',
  },
  'black-rose': {
    primary: '#C0C0C0',
    accent: '#E8E8E8',
    background: '#1A1A1A',
  },
  'love-hurts': {
    primary: '#B76E79',
    accent: '#E8B4BC',
    background: '#FFF5F7',
  },
};

/**
 * Press Timeline Component
 *
 * Renders press mentions in an interactive grid layout with optional
 * impact scoring and featured highlighting.
 *
 * Example usage:
 * ```tsx
 * <PressTimeline
 *   limit={6}
 *   collectionSlug="signature"
 *   sortBy="impact"
 *   showImpactScore={true}
 * />
 * ```
 */
export const PressTimeline: React.FC<PressTimelineProps> = ({
  limit = 6,
  featuredOnly = false,
  sortBy = 'newest',
  collectionSlug = 'signature',
  showLogos = true,
  showImpactScore = false,
  className = '',
  onMentionClick,
}) => {
  const [mentions, setMentions] = useState<PressMention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const colors = COLLECTION_COLORS[collectionSlug];

  /**
   * Fetch press mentions from WordPress REST API
   * Connected to wordpress/api/server_time_endpoint.php
   */
  useEffect(() => {
    const fetchPressMentions = async () => {
      try {
        setLoading(true);
        setError(null);

        // Endpoint provided by wordpress/api/server_time_endpoint.php
        const endpoint = `/wp-json/skyyrose/v1/press-mentions`;
        const params = new URLSearchParams();

        if (featuredOnly) {
          params.append('featured', 'true');
        }
        if (limit) {
          params.append('limit', limit.toString());
        }
        if (sortBy && sortBy !== 'newest') {
          params.append('sort', sortBy);
        }

        const response = await fetch(`${endpoint}?${params.toString()}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch press mentions: ${response.statusText}`);
        }

        const data = await response.json();
        setMentions(data.mentions || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        console.error('Failed to fetch press mentions:', errorMessage);
        setError(errorMessage);
        // Fallback: use empty array to prevent crash
        setMentions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPressMentions();
  }, [featuredOnly, limit, sortBy]);

  /**
   * Handle mention card click with optional callback
   */
  const handleMentionClick = (mention: PressMention) => {
    if (onMentionClick) {
      onMentionClick(mention);
    }
    // Open article in new tab
    window.open(mention.link, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
    return (
      <div
        className={`press-timeline press-timeline--loading ${className}`}
        style={{ textAlign: 'center', padding: '40px 0' }}
      >
        <div
          className="spinner"
          style={{
            width: '40px',
            height: '40px',
            border: `3px solid ${colors.accent}`,
            borderTop: `3px solid ${colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto',
          }}
        />
        <p style={{ marginTop: '16px', color: '#666' }}>Loading press coverage...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`press-timeline press-timeline--error ${className}`}>
        <div
          style={{
            padding: '24px',
            backgroundColor: '#FFF3CD',
            borderLeft: `4px solid ${colors.primary}`,
            borderRadius: '4px',
          }}
        >
          <p style={{ margin: 0, color: '#856404' }}>
            Unable to load press mentions. Please try again later.
          </p>
        </div>
      </div>
    );
  }

  if (mentions.length === 0) {
    return (
      <div className={`press-timeline press-timeline--empty ${className}`}>
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          <p>No press mentions available at this time.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`press-timeline ${className}`}>
      <style>{`
        .press-timeline {
          width: 100%;
        }

        .press-timeline__grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
          gap: 24px;
          margin: 0;
          padding: 0;
          list-style: none;
        }

        .press-timeline__item {
          position: relative;
          display: flex;
          flex-direction: column;
          background: white;
          border: 1px solid #eee;
          border-radius: 8px;
          padding: 24px;
          transition: all 0.3s ease;
          cursor: pointer;
          overflow: hidden;
        }

        .press-timeline__item::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, ${colors.primary}, ${colors.accent});
          transform: scaleX(0);
          transition: transform 0.3s ease;
          transform-origin: left;
        }

        .press-timeline__item:hover {
          border-color: ${colors.primary};
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        .press-timeline__item:hover::before {
          transform: scaleX(1);
        }

        .press-timeline__header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }

        .press-timeline__logo {
          flex-shrink: 0;
          width: 48px;
          height: 48px;
          background: #f5f5f5;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }

        .press-timeline__logo img {
          width: 100%;
          height: 100%;
          object-fit: contain;
          padding: 4px;
        }

        .press-timeline__logo-fallback {
          width: 100%;
          height: 100%;
          background: linear-gradient(135deg, ${colors.primary}, ${colors.accent});
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 12px;
          text-align: center;
          padding: 4px;
        }

        .press-timeline__publication {
          flex: 1;
        }

        .press-timeline__publication-name {
          font-size: 13px;
          font-weight: 600;
          color: ${colors.primary};
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin: 0;
        }

        .press-timeline__date {
          font-size: 12px;
          color: #999;
          margin: 4px 0 0 0;
        }

        .press-timeline__badge {
          display: inline-block;
          padding: 4px 8px;
          background: ${colors.background};
          color: ${colors.primary};
          font-size: 11px;
          font-weight: 600;
          border-radius: 3px;
          text-transform: uppercase;
          letter-spacing: 0.3px;
        }

        .press-timeline__title {
          font-size: 16px;
          font-weight: 700;
          line-height: 1.4;
          color: #1a1a1a;
          margin: 16px 0 12px 0;
          padding: 0;
        }

        .press-timeline__excerpt {
          font-size: 13px;
          line-height: 1.6;
          color: #666;
          margin: 0 0 16px 0;
          padding: 0;
          flex: 1;
        }

        .press-timeline__footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .press-timeline__impact {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .press-timeline__impact-star {
          color: ${colors.primary};
          font-size: 14px;
        }

        .press-timeline__impact-text {
          font-size: 12px;
          color: #999;
        }

        .press-timeline__link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: ${colors.primary};
          color: white;
          text-decoration: none;
          font-size: 12px;
          font-weight: 600;
          border-radius: 4px;
          transition: all 0.3s ease;
          white-space: nowrap;
        }

        .press-timeline__link:hover {
          background: ${colors.accent};
          transform: translateX(4px);
        }

        .press-timeline__link svg {
          width: 14px;
          height: 14px;
        }

        /* Featured press styling */
        .press-timeline__item--featured {
          position: relative;
          border: 2px solid ${colors.primary};
          background: ${colors.background};
        }

        .press-timeline__item--featured .press-timeline__badge {
          display: inline-block;
          background: ${colors.primary};
          color: white;
        }

        /* Responsive design */
        @media (max-width: 768px) {
          .press-timeline__grid {
            grid-template-columns: 1fr;
            gap: 16px;
          }

          .press-timeline__title {
            font-size: 14px;
          }

          .press-timeline__excerpt {
            font-size: 12px;
          }
        }

        /* Animation */
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .press-timeline__item {
          animation: fadeIn 0.4s ease forwards;
        }

        .press-timeline__item:nth-child(1) {
          animation-delay: 0.1s;
        }
        .press-timeline__item:nth-child(2) {
          animation-delay: 0.2s;
        }
        .press-timeline__item:nth-child(3) {
          animation-delay: 0.3s;
        }
        .press-timeline__item:nth-child(4) {
          animation-delay: 0.4s;
        }
        .press-timeline__item:nth-child(5) {
          animation-delay: 0.5s;
        }
        .press-timeline__item:nth-child(6) {
          animation-delay: 0.6s;
        }
      `}</style>

      <ul className="press-timeline__grid">
        {mentions.map((mention, index) => (
          <li
            key={`${mention.publication}-${mention.date}`}
            className={`press-timeline__item ${mention.featured ? 'press-timeline__item--featured' : ''}`}
          >
            {/* Header with logo and publication info */}
            <div className="press-timeline__header">
              {showLogos && (
                <div className="press-timeline__logo">
                  <img
                    src={mention.logo_url}
                    alt={mention.publication}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.parentElement!.innerHTML = `
                        <div class="press-timeline__logo-fallback">
                          ${mention.publication.substring(0, 2).toUpperCase()}
                        </div>
                      `;
                    }}
                  />
                </div>
              )}

              <div className="press-timeline__publication">
                <h4 className="press-timeline__publication-name">
                  {mention.publication}
                </h4>
                <p className="press-timeline__date">{mention.date}</p>
              </div>

              {mention.featured && (
                <span className="press-timeline__badge">Featured</span>
              )}
            </div>

            {/* Article title */}
            <h3 className="press-timeline__title">{mention.title}</h3>

            {/* Article excerpt */}
            {mention.excerpt && (
              <p className="press-timeline__excerpt">{mention.excerpt}</p>
            )}

            {/* Footer with impact score and read more link */}
            <div className="press-timeline__footer">
              {showImpactScore && (
                <div className="press-timeline__impact">
                  {Array.from({ length: mention.impact_score }).map((_, i) => (
                    <span key={i} className="press-timeline__impact-star">
                      ★
                    </span>
                  ))}
                  <span className="press-timeline__impact-text">
                    {mention.impact_score}/10
                  </span>
                </div>
              )}

              <a
                href={mention.link}
                target="_blank"
                rel="noopener noreferrer"
                className="press-timeline__link"
                onClick={() => handleMentionClick(mention)}
              >
                Read More
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PressTimeline;
