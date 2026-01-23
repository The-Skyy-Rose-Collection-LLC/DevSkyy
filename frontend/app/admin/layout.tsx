'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/dashboard/app-sidebar';
import { Separator } from '@/components/ui/separator';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    } else {
      setIsAuthenticated(true);
    }
  }, [router]);

  if (isAuthenticated === null) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-rose-500 border-t-transparent" />
          <p className="text-gray-400">Loading DevSkyy...</p>
        </div>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="bg-gray-950">
        <header className="flex h-14 shrink-0 items-center gap-2 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="text-gray-400 hover:text-white" />
            <Separator orientation="vertical" className="h-4 bg-gray-700" />
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-gray-400">System Online</span>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
