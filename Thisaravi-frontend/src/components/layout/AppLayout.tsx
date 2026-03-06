import { Outlet } from 'react-router-dom';
import { NavLink } from 'react-router-dom';
import { BarChart3, MessageSquare, Sparkles, Settings, Menu, History } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import type { UserType } from '@/context/AuthContext';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

interface NavItem {
  to: string;
  label: string;
  icon: typeof BarChart3;
  allowedRoles: UserType[];
}

const navItems: NavItem[] = [
  { to: '/', label: 'Analysis', icon: BarChart3, allowedRoles: ['student'] },
  { to: '/history', label: 'History', icon: History, allowedRoles: ['student'] },
  { to: '/feedback', label: 'Feedback', icon: MessageSquare, allowedRoles: ['expert'] },
  { to: '/evolution', label: 'Evolution', icon: Sparkles, allowedRoles: ['expert'] },
  { to: '/settings', label: 'Settings', icon: Settings, allowedRoles: ['expert'] },
];

function MobileNav() {
  const { user } = useAuth();
  const userType = user?.userType ?? 'student';
  const visibleItems = navItems.filter(item => item.allowedRoles.includes(userType));
  return (
    <div className="flex md:hidden items-center gap-2 border-b bg-sidebar-background px-4 py-3">
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-56 p-4 bg-sidebar-background border-sidebar-border">
          <div className="mb-6 px-2">
            <div className="flex items-center gap-2 mb-1">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <BarChart3 className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-sidebar-primary-foreground">UpSkill</h2>
                <p className="text-[10px] text-sidebar-foreground/60 leading-none">Skill Gap Analyzer</p>
              </div>
            </div>
          </div>
          <nav className="flex flex-col gap-1">
            {visibleItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground',
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>
        </SheetContent>
      </Sheet>
      <span className="text-sm font-semibold text-sidebar-primary-foreground">UpSkill</span>
    </div>
  );
}

export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <MobileNav />
        <TopBar />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
