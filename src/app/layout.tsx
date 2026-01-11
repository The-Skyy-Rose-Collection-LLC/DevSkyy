/**
 * Root Layout for Next.js App Router
 *
 * Required for App Router to function.
 */

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SkyyRose Collections',
  description: 'Luxury streetwear collections with interactive 3D experiences',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ margin: 0, padding: 0, overflow: 'auto' }}>
        {children}
      </body>
    </html>
  );
}
