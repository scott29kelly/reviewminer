'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  MessageSquareText,
  AlertTriangle,
  Play,
  Settings,
  Moon,
  Sun,
  Menu,
  Search,
  LogOut,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTheme } from 'next-themes';
import { signOut } from 'next-auth/react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useState } from 'react';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/reviews', label: 'Reviews', icon: MessageSquareText },
  { href: '/pain-points', label: 'Pain Points', icon: AlertTriangle },
  { href: '/jobs', label: 'Scrape Jobs', icon: Play },
  { href: '/settings', label: 'Settings', icon: Settings },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1.5">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              'group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200',
              isActive
                ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/25'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
            )}
          >
            <Icon className={cn(
              'h-[18px] w-[18px] transition-transform duration-200',
              !isActive && 'group-hover:scale-110'
            )} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-2 p-1 rounded-lg bg-muted">
      <button
        onClick={() => setTheme('light')}
        className={cn(
          'flex items-center justify-center h-8 w-8 rounded-md transition-all',
          theme === 'light' 
            ? 'bg-background shadow-sm text-foreground' 
            : 'text-muted-foreground hover:text-foreground'
        )}
      >
        <Sun className="h-4 w-4" />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={cn(
          'flex items-center justify-center h-8 w-8 rounded-md transition-all',
          theme === 'dark' 
            ? 'bg-background shadow-sm text-foreground' 
            : 'text-muted-foreground hover:text-foreground'
        )}
      >
        <Moon className="h-4 w-4" />
      </button>
    </div>
  );
}

function SearchTrigger() {
  const handleClick = () => {
    // Dispatch keyboard event to open command palette
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      metaKey: true,
      bubbles: true,
    });
    document.dispatchEvent(event);
  };

  return (
    <button
      onClick={handleClick}
      className="flex w-full items-center gap-3 rounded-xl border border-border/50 bg-muted/50 px-3.5 py-2.5 text-sm text-muted-foreground transition-all hover:bg-muted hover:border-border"
    >
      <Search className="h-4 w-4" />
      <span className="flex-1 text-left">Search...</span>
      <kbd className="pointer-events-none hidden select-none items-center gap-0.5 rounded-md border border-border/50 bg-background px-1.5 py-0.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex">
        <span className="text-xs">⌘</span>K
      </kbd>
    </button>
  );
}

function Logo() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white font-bold text-lg shadow-lg shadow-indigo-500/25">
        R
        <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 transition-opacity hover:opacity-100" />
      </div>
      <div className="flex flex-col">
        <span className="text-base font-bold tracking-tight">ReviewMiner</span>
        <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Analytics</span>
      </div>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden lg:flex h-screen w-[280px] flex-col border-r border-border/50 bg-card/50 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex h-[72px] items-center px-6 border-b border-border/50">
        <Logo />
      </div>

      {/* Search */}
      <div className="p-4 pb-2">
        <SearchTrigger />
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <NavLinks />
      </div>

      {/* Footer */}
      <div className="border-t border-border/50 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">Theme</span>
          <ThemeToggle />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => signOut({ callbackUrl: '/login' })}
          className="w-full justify-start text-muted-foreground hover:text-foreground hover:bg-destructive/10 hover:text-destructive"
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </Button>
      </div>
    </aside>
  );
}

export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[280px] p-0 border-border/50">
        <div className="flex h-[72px] items-center px-6 border-b border-border/50">
          <Logo />
        </div>
        <div className="p-4">
          <NavLinks onNavigate={() => setOpen(false)} />
        </div>
        <div className="absolute bottom-0 left-0 right-0 border-t border-border/50 p-4 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Theme</span>
            <ThemeToggle />
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => signOut({ callbackUrl: '/login' })}
            className="w-full justify-start text-muted-foreground hover:text-foreground"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign out
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export function Header() {
  return (
    <header className="flex h-[72px] items-center gap-4 border-b border-border/50 bg-card/50 backdrop-blur-xl px-6 lg:hidden">
      <MobileNav />
      <Logo />
    </header>
  );
}
