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
    ],
  },
  async rewrites() {
    // In development, proxy to local Python server
    // In production (Vercel), Python functions are at /api automatically
    return process.env.NODE_ENV === 'development'
      ? [
          {
            source: '/api/:path*',
            destination: 'http://127.0.0.1:8000/api/:path*',
          },
        ]
      : [];
  },
};

module.exports = nextConfig;
