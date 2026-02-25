import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactStrictMode: true,
  turbopack: {
    root: '..',
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.skyyrose.co',
      },
      {
        protocol: 'https',
        hostname: '**.devskyy.app',
      },
    ],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
}

export default nextConfig
