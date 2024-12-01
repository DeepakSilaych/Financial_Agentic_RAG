import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { 
  Menu, 
  PanelLeftClose, 
  PanelLeft, 
  Search,
  Bell,
  HelpCircle,
  FileText,
  MessageSquare,
  ChevronRight,
  UserCircle
} from 'lucide-react';
import Sidebar from './app/Sidebar';
import TeamSwitcher from './team/TeamSwitcher';
import TeamMembers from './team/TeamMembers';
import { TeamProvider } from '../context/TeamContext';

const getBreadcrumbs = (pathname) => {
  const parts = pathname.split('/').filter(Boolean);
  if (parts.length === 0) return [{ name: 'Chat', path: '/chat' }];
  
  return parts.map((part, index) => {
    const path = '/' + parts.slice(0, index + 1).join('/');
    let name = part.charAt(0).toUpperCase() + part.slice(1);
    if (name.length === 24 && /^[0-9a-f]{24}$/.test(part)) {
      name = 'Chat Session';
    }
    return { name, path };
  });
};

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const location = useLocation();
  const breadcrumbs = getBreadcrumbs(location.pathname);

  return (
    <TeamProvider>
      <div className="h-screen flex bg-graycolor overflow-hidden bg-custom-gray">
        {/* Sidebar Container */}
        <aside 
          className={`
            fixed lg:relative inset-y-0 left-0 z-30
            transform transition-all duration-300 ease-in-out
            ${isSidebarOpen ? 'translate-x-0 w-72' : '-translate-x-full lg:translate-x-0 lg:w-20'}
          `}
        >
          <Sidebar isCollapsed={!isSidebarOpen} />
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col mt-4 mr-4 bg-white shadow-xl border-2 border-gray-200 rounded-t-xl min-w-0 relative">
          {/* Top Bar */}
          <div className="h-16 border-b flex items-center justify-between px-4">
            <div className="flex items-center space-x-4">
              {/* Mobile Toggle */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="lg:hidden text-gray-500 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-pink-500 p-2 rounded-md"
              >
                <Menu size={20} className="transition-transform duration-200 ease-in-out" />
              </button>

              {/* Desktop Toggle */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className={`
                  hidden lg:flex items-center justify-center w-8 h-8 rounded-lg
                  text-gray-500 hover:text-gray-600 hover:bg-gray-100
                  focus:outline-none focus:ring-2 focus:ring-pink-500
                  transition-all duration-200 ease-in-out
                  ${isSidebarOpen ? 'transform rotate-0' : 'transform rotate-180'}
                `}
                title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              >
                {isSidebarOpen ? (
                  <PanelLeftClose size={18} className="transition-transform duration-200" />
                ) : (
                  <PanelLeft size={18} className="transition-transform duration-200" />
                )}
              </button>

              {/* Breadcrumbs */}
              <nav className="hidden md:flex items-center space-x-1">
                {breadcrumbs.map((crumb, index) => (
                  <React.Fragment key={crumb.path}>
                    {index > 0 && <ChevronRight size={16} className="text-gray-400" />}
                    <a
                      href={crumb.path}
                      className="text-sm text-gray-600 hover:text-pink-600 font-medium"
                    >
                      {crumb.name}
                    </a>
                  </React.Fragment>
                ))}
              </nav>
            </div>

            {/* Right Section */}
            <div className="flex items-center space-x-3">
              {/* Quick Actions */}
              <button
                onClick={() => setIsSearchOpen(true)}
                className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                title="Quick search"
              >
                <Search size={18} />
              </button>

              <button
                className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                title="Documentation"
              >
                <FileText size={18} />
              </button>

              <button
                className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                title="Help & Support"
              >
                <HelpCircle size={18} />
              </button>

              {/* Notifications */}
              <div className="relative">
                <button
                  className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  title="Notifications"
                >
                  <Bell size={18} />
                  {notifications.length > 0 && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-pink-500 rounded-full"></span>
                  )}
                </button>
              </div>

              {/* Team Switcher */}
              <TeamSwitcher />

              {/* Team Members */}
              <TeamMembers />

              {/* User Menu */}
              <button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-pink-500">
                <UserCircle size={20} className="text-gray-600" />
                <span className="text-sm font-medium text-gray-700 hidden md:inline-block">John Doe</span>
              </button>
            </div>
          </div>

          {/* Page Content */}
          <div className="flex-1 overflow-y-auto">
            <Outlet />
          </div>
        </main>

        {/* Mobile Overlay */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 lg:hidden z-20"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
      </div>
    </TeamProvider>
  );
};

export default Layout;
