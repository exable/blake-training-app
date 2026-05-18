import React, { useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Dumbbell, UtensilsCrossed, ClipboardCheck,
  LineChart, MessageCircle, Settings as SettingsIcon, LogOut,
} from 'lucide-react';
import { api, clearToken } from '../lib/api.js';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/workout', label: 'Workout', icon: Dumbbell },
  { to: '/nutrition', label: 'Nutrition', icon: UtensilsCrossed },
  { to: '/checkins', label: 'Check-ins', icon: ClipboardCheck },
  { to: '/progress', label: 'Progress', icon: LineChart },
  { to: '/chat', label: 'Ero', icon: MessageCircle },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export default function Layout() {
  const navigate = useNavigate();

  useEffect(() => {
    // Fire off pending weekly Ero responses on app load
    api.post('/api/checkins/weekly/process-pending').catch(() => {});
  }, []);

  function logout() {
    clearToken();
    navigate('/login');
  }

  return (
    <div className="min-h-screen flex md:flex-row flex-col bg-bg">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:flex-col w-60 border-r border-line bg-surface/40 backdrop-blur-sm">
        <div className="px-6 py-7 border-b border-line">
          <div className="text-xs uppercase tracking-[0.2em] text-textmuted">Blake's</div>
          <div className="text-xl font-bold text-white">Training App</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-accent/10 text-accent border border-accent/30'
                    : 'text-textmuted hover:bg-surface2 hover:text-white border border-transparent'
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-line">
          <button onClick={logout} className="btn btn-ghost w-full justify-start">
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 border-b border-line bg-surface/40 sticky top-0 z-30 backdrop-blur-sm">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-textmuted">Blake's</div>
          <div className="text-base font-bold">Training App</div>
        </div>
        <button onClick={logout} className="text-textmuted hover:text-white p-2">
          <LogOut size={18} />
        </button>
      </header>

      {/* Main */}
      <main className="flex-1 pb-24 md:pb-8 px-4 md:px-8 py-5 md:py-8 max-w-5xl mx-auto w-full">
        <Outlet />
      </main>

      {/* Mobile bottom tab nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-surface border-t border-line z-30">
        <div className="grid grid-cols-7">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 py-2.5 text-[10px] font-medium transition-colors ${
                  isActive ? 'text-accent' : 'text-textmuted hover:text-white'
                }`
              }
            >
              <item.icon size={20} />
              <span className="truncate w-full text-center px-0.5">{item.label === 'Dashboard' ? 'Home' : item.label}</span>
            </NavLink>
          ))}
        </div>
        <div className="h-[env(safe-area-inset-bottom)]" />
      </nav>
    </div>
  );
}
