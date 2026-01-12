/**
 * Not Found Page
 * ==============
 * Custom 404 page for missing routes.
 */

import Link from 'next/link';
import { FileQuestion, Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-gray-100 dark:bg-gray-800 p-4">
            <FileQuestion className="h-12 w-12 text-gray-600 dark:text-gray-400" />
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-brand-primary">404</h1>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-50">
            Page Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:bg-brand-primary/90 transition-colors"
        >
          <Home className="h-4 w-4" />
          Return Home
        </Link>
      </div>
    </div>
  );
}
