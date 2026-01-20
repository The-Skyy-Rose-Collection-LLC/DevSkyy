/**
 * Pre-Order Countdown Timer Component
 *
 * Displays a real-time countdown to product launch with server-synced timing.
 * Handles status transitions and sends notifications on launch.
 *
 * Features:
 * - Server time synchronization to prevent client clock drift
 * - Automatic status transitions (blooming_soon → now_blooming)
 * - Collection-aware color theming
 * - Responsive design (mobile → desktop)
 * - Error recovery with retry logic
 * - Email capture for "Notify Me" feature
 *
 * @component
 * @example
 * <PreorderCountdown
 *   productId={123}
 *   collectionSlug="signature"
 *   onLaunch={() => console.log('Product launched!')}
 * />
 */

'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';

// ============================================================================
// Types & Interfaces
// ============================================================================

interface CountdownConfig {
  product_id: number;
  product_name: string;
  launch_date_iso: string;
  launch_date_unix: number;
  server_time_unix: number;
  status: 'blooming_soon' | 'now_blooming' | 'available';
  ar_enabled: boolean;
  collection: string;
  time_remaining_seconds: number;
}

interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  total: number;
}

interface PreorderCountdownProps {
  productId: number;
  collectionSlug?: string;
  onLaunch?: () => void;
  onStatusChange?: (status: 'blooming_soon' | 'now_blooming' | 'available') => void;
  className?: string;
  variant?: 'minimal' | 'standard' | 'featured';
}

// ============================================================================
// Collection Colors
// ============================================================================

const COLLECTION_COLORS: Record<string, { primary: string; accent: string }> = {
  signature: {
    primary: '#D4AF37',
    accent: '#0D0D0D',
  },
  'black-rose': {
    primary: '#C0C0C0',
    accent: '#000000',
  },
  'love-hurts': {
    primary: '#B76E79',
    accent: '#0A0510',
  },
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Sync with server time and calculate time remaining
 */
async function fetchCountdownConfig(productId: number): Promise<CountdownConfig | null> {
  try {
    const response = await fetch(`/wp-json/skyyrose/v1/products/${productId}/countdown`);
    if (!response.ok) {
      console.warn(`Failed to fetch countdown config: ${response.status}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching countdown config:', error);
    return null;
  }
}

/**
 * Get current server time (with retry)
 */
async function getServerTime(retries = 3): Promise<number | null> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch('/wp-json/skyyrose/v1/server-time');
      if (!response.ok) {
        continue;
      }
      const data = await response.json();
      return data.timestamp;
    } catch (error) {
      if (i < retries - 1) {
        await new Promise((resolve) => setTimeout(resolve, 100 * (i + 1)));
        continue;
      }
      console.error('Failed to get server time:', error);
      return null;
    }
  }
  return null;
}

/**
 * Calculate time remaining
 */
function calculateTimeRemaining(launchUnix: number, currentUnix: number): TimeRemaining {
  const diff = Math.max(0, launchUnix - currentUnix);

  const days = Math.floor(diff / 86400);
  const hours = Math.floor((diff % 86400) / 3600);
  const minutes = Math.floor((diff % 3600) / 60);
  const seconds = diff % 60;

  return { days, hours, minutes, seconds, total: diff };
}

/**
 * Format time units with leading zeros
 */
function padTime(value: number): string {
  return String(value).padStart(2, '0');
}

// ============================================================================
// Component
// ============================================================================

export const PreorderCountdown: React.FC<PreorderCountdownProps> = ({
  productId,
  collectionSlug = 'signature',
  onLaunch,
  onStatusChange,
  className = '',
  variant = 'standard',
}) => {
  const [config, setConfig] = useState<CountdownConfig | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<TimeRemaining | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>('blooming_soon');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [emailSubmitted, setEmailSubmitted] = useState(false);
  const [timeDrift, setTimeDrift] = useState(0); // Client vs server time

  const animationFrameRef = useRef<number | undefined>(undefined);
  const serverTimeFetchRef = useRef<number>(Date.now());
  const launchNotifiedRef = useRef(false);

  // =========================================================================
  // Initialization & Setup
  // =========================================================================

  useEffect(() => {
    const initialize = async () => {
      try {
        // Fetch countdown configuration
        const cfg = await fetchCountdownConfig(productId);
        if (!cfg) {
          setError('Failed to load countdown information');
          setLoading(false);
          return;
        }

        setConfig(cfg);
        setCurrentStatus(cfg.status);

        // Calculate initial time drift
        const serverTime = cfg.server_time_unix;
        const clientTime = Math.floor(Date.now() / 1000);
        setTimeDrift(serverTime - clientTime);

        setLoading(false);
      } catch (err) {
        console.error('Error initializing countdown:', err);
        setError('Failed to initialize countdown');
        setLoading(false);
      }
    };

    initialize();
  }, [productId]);

  // =========================================================================
  // Countdown Animation
  // =========================================================================

  const updateCountdown = useCallback(() => {
    if (!config) return;

    // Use server-synced time
    const now = Math.floor(Date.now() / 1000) + timeDrift;
    const remaining = calculateTimeRemaining(config.launch_date_unix, now);

    setTimeRemaining(remaining);

    // Check if launched
    if (remaining.total <= 0 && !launchNotifiedRef.current) {
      launchNotifiedRef.current = true;
      setCurrentStatus('now_blooming');
      onStatusChange?.('now_blooming');
      onLaunch?.();
    }

    // Continue animation loop
    animationFrameRef.current = requestAnimationFrame(updateCountdown);
  }, [config, timeDrift, onLaunch, onStatusChange]);

  useEffect(() => {
    if (!loading && config) {
      // Initial update
      updateCountdown();

      // Periodically resync with server (every 5 minutes)
      const resyncInterval = setInterval(async () => {
        const serverTime = await getServerTime();
        if (serverTime) {
          const clientTime = Math.floor(Date.now() / 1000);
          setTimeDrift(serverTime - clientTime);
        }
      }, 5 * 60 * 1000);

      return () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        clearInterval(resyncInterval);
      };
    }
  }, [loading, config, updateCountdown]);

  // =========================================================================
  // Event Handlers
  // =========================================================================

  const handleNotifyMe = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      // In production, this would send to Klaviyo or email service
      // For now, we'll simulate the request
      const response = await fetch('/wp-json/skyyrose/v1/products/notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          email: email,
          collection: collectionSlug,
        }),
      });

      if (response.ok) {
        setEmailSubmitted(true);
        setEmail('');
        setTimeout(() => setEmailSubmitted(false), 3000);
      } else {
        setError('Failed to subscribe - please try again');
      }
    } catch (err) {
      console.error('Error submitting email:', err);
      setError('Failed to subscribe - please try again');
    }
  };

  // =========================================================================
  // Render
  // =========================================================================

  if (loading) {
    return (
      <div className={`preorder-countdown preorder-countdown--loading ${className}`}>
        <div className="countdown-skeleton">
          <div className="skeleton-bar"></div>
        </div>
      </div>
    );
  }

  if (error || !config || !timeRemaining) {
    return (
      <div className={`preorder-countdown preorder-countdown--error ${className}`}>
        <p className="error-message">{error || 'Unable to load countdown'}</p>
      </div>
    );
  }

  const colors = COLLECTION_COLORS[collectionSlug] || COLLECTION_COLORS.signature;
  const isLaunched = timeRemaining.total <= 0;
  const statusText =
    currentStatus === 'now_blooming'
      ? 'Now Blooming'
      : currentStatus === 'available'
        ? 'Available'
        : 'Blooming Soon';

  // =========================================================================
  // Minimal Variant
  // =========================================================================

  if (variant === 'minimal') {
    return (
      <div
        className={`preorder-countdown preorder-countdown--minimal ${className}`}
        style={{ '--primary-color': colors.primary } as React.CSSProperties}
      >
        <div className="countdown-status">{statusText}</div>
        {!isLaunched && (
          <div className="countdown-timer">
            <span className="time-value">{padTime(timeRemaining.days)}</span>
            <span className="time-label">d</span>
            <span className="time-value">{padTime(timeRemaining.hours)}</span>
            <span className="time-label">h</span>
            <span className="time-value">{padTime(timeRemaining.minutes)}</span>
            <span className="time-label">m</span>
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // Featured Variant
  // =========================================================================

  if (variant === 'featured') {
    return (
      <div
        className={`preorder-countdown preorder-countdown--featured ${className}`}
        style={
          {
            '--primary-color': colors.primary,
            '--accent-color': colors.accent,
          } as React.CSSProperties
        }
      >
        <div className="featured-content">
          <h3 className="countdown-title">{statusText}</h3>

          {!isLaunched && (
            <>
              <div className="countdown-display">
                <div className="time-unit">
                  <div className="time-value">{padTime(timeRemaining.days)}</div>
                  <div className="time-label">Days</div>
                </div>
                <div className="time-separator">:</div>
                <div className="time-unit">
                  <div className="time-value">{padTime(timeRemaining.hours)}</div>
                  <div className="time-label">Hours</div>
                </div>
                <div className="time-separator">:</div>
                <div className="time-unit">
                  <div className="time-value">{padTime(timeRemaining.minutes)}</div>
                  <div className="time-label">Minutes</div>
                </div>
                <div className="time-separator">:</div>
                <div className="time-unit">
                  <div className="time-value">{padTime(timeRemaining.seconds)}</div>
                  <div className="time-label">Seconds</div>
                </div>
              </div>

              {!emailSubmitted ? (
                <form onSubmit={handleNotifyMe} className="notify-form">
                  <input
                    type="email"
                    placeholder="Get notified at launch"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="notify-input"
                    disabled={emailSubmitted}
                  />
                  <button type="submit" className="notify-button" disabled={emailSubmitted}>
                    Notify Me
                  </button>
                </form>
              ) : (
                <div className="notify-success">✓ Check your email for updates</div>
              )}
            </>
          )}

          {isLaunched && (
            <button className="launch-cta">
              {config.ar_enabled ? 'View in AR' : 'View Collection'}
            </button>
          )}
        </div>
      </div>
    );
  }

  // =========================================================================
  // Standard Variant (Default)
  // =========================================================================

  return (
    <div
      className={`preorder-countdown preorder-countdown--standard ${className}`}
      style={{ '--primary-color': colors.primary } as React.CSSProperties}
    >
      <div className="countdown-header">
        <h4 className="product-name">{config.product_name}</h4>
        <span className="countdown-status">{statusText}</span>
      </div>

      {!isLaunched ? (
        <div className="countdown-body">
          <div className="countdown-timer">
            <div className="time-unit">
              <span className="time-value">{padTime(timeRemaining.days)}</span>
              <span className="time-label">Days</span>
            </div>
            <div className="time-unit">
              <span className="time-value">{padTime(timeRemaining.hours)}</span>
              <span className="time-label">Hours</span>
            </div>
            <div className="time-unit">
              <span className="time-value">{padTime(timeRemaining.minutes)}</span>
              <span className="time-label">Mins</span>
            </div>
            <div className="time-unit">
              <span className="time-value">{padTime(timeRemaining.seconds)}</span>
              <span className="time-label">Secs</span>
            </div>
          </div>

          {!emailSubmitted && (
            <form onSubmit={handleNotifyMe} className="notify-form">
              <input
                type="email"
                placeholder="Email to notify"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="notify-input"
              />
              <button type="submit" className="notify-button">
                Notify Me
              </button>
            </form>
          )}

          {emailSubmitted && <div className="notify-success">✓ Notification set!</div>}
        </div>
      ) : (
        <div className="countdown-launched">
          <p className="launch-message">Product is now available!</p>
          {config.ar_enabled && (
            <button className="ar-button">View in AR Quick Look →</button>
          )}
        </div>
      )}
    </div>
  );
};

export default PreorderCountdown;
