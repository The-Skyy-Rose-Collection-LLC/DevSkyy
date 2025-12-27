/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.googleusercontent.com',
      },
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com',
      },
      {
        protocol: 'https',
        hostname: '*.huggingface.co',
      },
      {
        protocol: 'https',
        hostname: 'skyyrose.co',
      },
    ],
  },
  // Environment variables for client-side
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api',
  },
  async rewrites() {
    // In development, proxy to local Python backend
    // In production (Vercel), /api routes go directly to Python serverless functions
    const isDev = process.env.NODE_ENV === 'development';

    if (isDev) {
      return [
        {
          source: '/api/:path*',
          destination: process.env.BACKEND_URL
            ? `${process.env.BACKEND_URL}/:path*`
            : 'http://localhost:8000/:path*',
        },
      ];
    }

    // In production, no rewrites needed - Vercel handles /api routes
    return [];
  },
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

module.exports = nextConfig;
