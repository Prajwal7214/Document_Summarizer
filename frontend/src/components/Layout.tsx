import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, FileText, Files, MessageSquare, LogOut, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/summary', label: 'Summary', icon: FileText },
    { path: '/documents', label: 'Documents', icon: Files },
    { path: '/chat', label: 'Chat', icon: MessageSquare },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Generate initials from name
  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <div className="flex h-screen bg-gray-100 text-gray-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-black border-r border-white/10 flex flex-col shadow-lg">
        {/* Brand */}
        <div className="p-6 flex items-center gap-3 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
            <span className="text-black font-bold text-xl">S</span>
          </div>
          <h1 className="text-xl font-bold tracking-wide text-white">Summarix</h1>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-6 px-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path));

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-white/10 text-white font-medium'
                    : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
                }`}
              >
                <Icon size={20} className={isActive ? 'text-white' : ''} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Profile Section */}
        <div className="p-4 border-t border-white/10 relative">
          {showProfileMenu && (
            <div className="absolute bottom-full left-4 right-4 mb-2 bg-[#111] border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-fade-in-up">
              <div className="px-4 py-3 border-b border-white/10">
                <p className="text-white text-sm font-medium truncate">{user?.name}</p>
                <p className="text-white/40 text-xs truncate mt-0.5">{user?.email}</p>
              </div>
              <button
                id="logout-btn"
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-white/5 hover:text-red-300 transition-colors"
              >
                <LogOut size={16} />
                Sign out
              </button>
            </div>
          )}

          <button
            id="profile-menu-btn"
            onClick={() => setShowProfileMenu((v) => !v)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-all group"
          >
            {/* Avatar */}
            <div className="w-9 h-9 rounded-full bg-white/10 border border-white/20 flex items-center justify-center flex-shrink-0 text-white text-xs font-bold group-hover:border-white/30 transition-colors">
              {initials}
            </div>
            {/* Info */}
            <div className="flex-1 min-w-0 text-left">
              <p className="text-white text-sm font-medium truncate leading-tight">{user?.name || 'User'}</p>
              <p className="text-white/40 text-xs truncate mt-0.5">{user?.email || ''}</p>
            </div>
            {/* Icon */}
            <User size={14} className="text-white/30 flex-shrink-0 group-hover:text-white/50 transition-colors" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-100">
        <div className="h-full p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
