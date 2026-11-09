import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Search, Bell, Sparkles, LogOut, Shield } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Search Bar */}
      <div className="flex items-center gap-3 w-96">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search projects, claims, tasks, decisions..."
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 focus:bg-white text-slate-900 placeholder:text-slate-400 transition-all"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Verification Status Pill */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-teal-50 border border-teal-200 rounded-full text-xs font-medium text-teal-800">
          <Sparkles className="w-3.5 h-3.5 text-teal-600" />
          <span>Continuous Verification Active</span>
        </div>

        {/* Notifications */}
        <button className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full absolute top-1.5 right-1.5"></span>
        </button>

        <div className="h-4 w-px bg-slate-200"></div>

        {/* User Info & Role */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-semibold">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-slate-900 leading-none">{user?.name || 'User'}</div>
            <div className="text-[10px] text-slate-500 font-mono mt-0.5">{user?.role || 'MEMBER'}</div>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

