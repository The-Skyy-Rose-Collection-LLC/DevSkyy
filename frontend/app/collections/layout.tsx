/**
 * Collections Layout - Bypasses dashboard shell
 *
 * Provides clean layout for immersive collection experiences.
 */

export default function CollectionsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Preconnect to critical third-party origins */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="preconnect" href="https://skyyrose.com" />
        <link rel="dns-prefetch" href="https://skyyrose.com" />

        {/* Load critical fonts with display=swap for better LCP */}
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
