import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  MessageSquare,
  FileText,
  Settings,
  Search,
  Plus,
  BotMessageSquare as BotMessageSquareIcon,
  History,
  Loader2,
  AlertTriangle,
  User
} from 'lucide-react';
import { chatApi } from '../../utils/api';
import { useUser } from '../../context/UserContext';

const Sidebar = ({ isCollapsed }) => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { currentSpace } = useUser();

  useEffect(() => {
    if (currentSpace?.id) {
      loadChats();
    }
  }, [currentSpace, location.pathname]);

  const loadChats = async () => {
    if (!currentSpace?.id) return;
    
    try {
      setLoading(true);
      const response = await chatApi.getAllChats(currentSpace.id);
      setChats(response.reverse());
      setError(null);
    } catch (err) {
      setError('Failed to load chats');
      console.error('Error loading chats:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderChatTitle = (chat) => {
    if (chat.title && chat.title.trim()) {
      const maxLength = 35;
      return chat.title.length > maxLength 
        ? chat.title.substring(0, maxLength) + '...'
        : chat.title;
    }
    return `Chat ${chat.id}`;
  };

  const filteredChats = chats.filter(chat =>
    chat.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isActiveRoute = (path) => location.pathname === path;

  const navItems = [
    { path: '/app/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/app/storage', icon: FileText, label: 'Storage' },
    { path: '/app/settings', icon: Settings, label: 'Settings' },
  ];

  const sidebarClasses = `
    h-full text-gray-700 flex flex-col
    transition-all duration-300 ease-in-out
    ${isCollapsed ? 'w-20' : 'w-72'}
  `;

  return (
    <div className={sidebarClasses}>
      <div className={`
        pt-6 flex items-center
        transition-all duration-300 ease-in-out
        px-6
        ${isCollapsed ? '' : 'space-x-3'}
      `}>
        <BotMessageSquareIcon
          size={30}
          className={`
            text-blue-600 transition-transform duration-300
            ${isCollapsed ? 'transform scale-90' : ''}
          `}
        />
        <h1 className={`
          text-2xl font-extrabold text-blue-600
          transition-all duration-300 ease-in-out
          origin-left whitespace-nowrap
          ${isCollapsed ? 'opacity-0 scale-0 w-0' : 'opacity-100 scale-100'}
        `}>
          Pathway
        </h1>
      </div>

      <div className={`
        flex transition-all duration-300 ease-in-out overflow-hidden rounded-lg border border-gray-300 m-4
        ${isCollapsed ? 'opacity-0' : 'opacity-100'}
      `}>
        <div className="relative flex-grow">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-black" />
          <input
            type="text"
            placeholder="Search chats..."
            className={`
              w-full bg-gray-200 text-gray-800 pl-10 pr-4 py-2 rounded-md
              focus:outline-none focus:ring-2 focus:ring-blue-500
              transition-all duration-200 ease-in-out 
              ${isSearchOpen ? 'opacity-100' : 'opacity-80 hover:opacity-100'}
            `}
            onFocus={() => setIsSearchOpen(true)}
            onBlur={() => setIsSearchOpen(false)}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <nav className={`flex-1 overflow-y-auto px-2 ${!isCollapsed && 'mr-10'} py-4`}>
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = isActiveRoute(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center px-3 py-2 rounded-lg
                  transition-all duration-200 ease-in-out
                  ${isActive
                    ? 'bg-blue-300 bg-opacity-80 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }
                  ${isCollapsed ? 'pl-2 pr-0' : 'space-x-2'}
                `}
              >
                <Icon size={20} className={`
                  transition-transform duration-200
                  ${isCollapsed ? 'transform scale-110' : ''}
                `} />
                <span className={`
                  transition-all duration-300 ease-in-out
                  ${isCollapsed ? 'opacity-0 w-0' : 'opacity-100'}
                `}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>

        <hr className="my-4 border-gray-300" />

        <div className="space-y-2">
          <div
            className={`
              flex items-center px-3 py-2 rounded-lg
              transition-all duration-200 ease-in-out
              ${isActiveRoute('/app/history')
                ? 'bg-blue-300 bg-opacity-80 text-blue-600'
                : 'text-gray-600 hover:bg-gray-100 hover:text-blue-600'
              }
              ${isCollapsed ? 'pl-2 pr-0' : 'space-x-2'}
            `}
          >
            <span className={`
              transition-all duration-300 ease-in-out
              ${isCollapsed ? 'opacity-0 w-0' : 'opacity-100'}
            `}>
              Past Chats
            </span>
          </div>
          
        </div>

        {!isCollapsed && (
          <div className="mt-4 space-y-2">
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="flex items-center gap-2 text-red-500 px-3 py-2">
                <AlertTriangle size={16} />
                <span className="text-sm">{error}</span>
              </div>
            ) : (
              filteredChats.map((chat) => (
                <Link
                  key={chat.id}
                  to={`/app/chat/${chat.id}`}
                  className={`
                    flex space-x-2 items-center px-3 py-2 rounded-lg text-sm
                    ${location.pathname === `/app/chat/${chat.id}`
                      ? 'bg-blue-100 text-blue-600'
                      : 'text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
            <History size={15} className={`transition-transform duration-200 transform scale-110`} />                  
            <span className="truncate">{renderChatTitle(chat)}</span>
                </Link>
              ))
            )}
          </div>
        )}
      </nav>
    </div>
  );
};

export default Sidebar;
