import path from 'path'
import type { NextConfig } from 'next'

// On Vercel, rootDirectory=frontend so only this dir is uploaded; the
// repo-root lockfile isn't in build scope and there's no ambiguous-root
// warning to suppress. Setting outputFileTracingRoot above the project
// root on Vercel causes a doubled-path bug in the post-build trace step
// (looks for .next/routes-manifest.json at /vercel/path1/path1/.next/...
// and crashes with ENOENT).
//
// Locally, both lockfiles are present, so we still set the override —
// but only when not running on Vercel.
const isVercel = !!process.env.VERCEL
const tracingRoot = isVercel ? undefined : path.resolve(__dirname, '..')

const nextConfig: NextConfig = {
  reactStrictMode: true,
  ...(tracingRoot && { outputFileTracingRoot: tracingRoot }),
  ...(tracingRoot && { turbopack: { root: tracingRoot } }),
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
  cacheComponents: true,
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
}

export default nextConfig
