import { withSentryConfig } from '@sentry/nextjs';
import withBundleAnalyzer from '@next/bundle-analyzer';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Base settings
  reactStrictMode: true,
  swcMinify: true,

  // Experimental features - MERGED
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },

  // Image optimization - MERGED ALL DOMAINS
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 7, // 7 days
    remotePatterns: [
      // Google services
      { protocol: 'https', hostname: '*.googleusercontent.com' },
      { protocol: 'https', hostname: 'storage.googleapis.com' },
      // HuggingFace
      { protocol: 'https', hostname: '*.huggingface.co' },
      // SkyyRose domains
      { protocol: 'https', hostname: 'skyyrose.co' },
      { protocol: 'https', hostname: 'skyyrose.com', pathname: '/wp-content/uploads/**' },
      { protocol: 'https', hostname: '**.skyyrose.com', pathname: '/**' },
    ],
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api',
  },

  // CRITICAL: Root redirect
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard',
        permanent: false,
      },
    ];
  },

  // CRITICAL: API proxy rewrites
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL ||
                      process.env.NEXT_PUBLIC_API_URL ||
                      'http://localhost:8000';

    return [
      {
        source: '/api/backend/:path*',
        destination: 'https://api.devskyy.app/:path*',
      },
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  // CRITICAL: CORS headers
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,DELETE,OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'X-Requested-With, Content-Type, Authorization' },
        ],
      },
    ];
  },
};

// Compose: Bundle Analyzer + Sentry
const configWithBundleAnalyzer = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})(nextConfig);

export default withSentryConfig(
  configWithBundleAnalyzer,
  {
    org: 'skyyrose',
    project: 'devskyy-frontend',
    silent: true,
  },
  {
    widenClientFileUpload: true,
    transpileClientSDK: true,
    tunnelRoute: '/monitoring',
    hideSourceMaps: true,
    disableLogger: true,
  }
);
