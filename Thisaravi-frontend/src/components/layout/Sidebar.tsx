import { NavLink } from 'react-router-dom';
import { BarChart3, MessageSquare, Sparkles, Settings, History } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import type { UserType } from '@/context/AuthContext';

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

export default function Sidebar() {
  const { user } = useAuth();
  const userType = user?.userType ?? 'student';
  const visibleItems = navItems.filter(item => item.allowedRoles.includes(userType));
  return (
    <aside className="hidden md:flex w-56 flex-col border-r bg-sidebar-background p-4">
      <div className="mb-6 px-2">
        <div className="flex items-center gap-2 mb-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
            <BarChart3 className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold tracking-tight text-sidebar-primary-foreground">UpSkill</h2>
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
    </aside>
  );
}
