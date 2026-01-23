'use client';

import { Sidebar, Header } from '@/components/sidebar';
import { CommandPalette } from '@/components/command-palette';
import { PageTransition } from '@/components/page-transition';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto">
          {/* Subtle gradient background */}
          <div className="relative min-h-full">
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-indigo-500/[0.03] to-violet-500/[0.03] rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
              <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-br from-violet-500/[0.03] to-pink-500/[0.03] rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
            </div>
            <div className="relative p-6 lg:p-8 max-w-[1600px] mx-auto">
              <PageTransition>{children}</PageTransition>
            </div>
          </div>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
