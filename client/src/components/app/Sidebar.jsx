import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  History,
  Plus,
  Loader2,
  Search,
  ChevronDown,
  User,
  Settings,
  BotMessageSquareIcon,
  AlertTriangle
} from 'lucide-react';
import { chatApi } from '../../utils/api';

const Sidebar = ({ isCollapsed }) => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    loadChats();
  }, []);

  const loadChats = async () => {
    try {
      setLoading(true);
      const response = await chatApi.getAllChats();
      setChats(response);
    } catch (err) {
      setError('Failed to load chats');
      console.error('Error loading chats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      setLoading(true);
      const response = await chatApi.createChat();
      const newChat = response;
      setChats([newChat, ...chats]);
      navigate(`/app/chat/${newChat.id}`);
    } catch (err) {
      setError('Failed to create new chat');
      console.error('Error creating new chat:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredChats = chats.filter(chat =>
    chat.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isActiveRoute = (path) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/app/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/app/storage', icon: FileText, label: 'Storage' },
    { path: '/app/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className={`
      h-full text-gray-700 flex flex-col
      transition-all duration-300 ease-in-out
      ${isCollapsed ? 'w-20' : 'w-72'}
      relative
    `}>
      <div className={`
        px-4 pt-6 flex items-center
        transition-all duration-300 ease-in-out
        ${isCollapsed ? 'justify-center' : 'px-6 space-x-3'}
      `}>
        <BotMessageSquareIcon 
          size={30} 
          className={`
            text-pink-600 transition-transform duration-300
            ${isCollapsed ? 'transform scale-90' : ''}
          `}
        />
        <h1 className={`
          text-2xl font-extrabold text-pink-600
          transition-all duration-300 ease-in-out
          origin-left whitespace-nowrap
          ${isCollapsed ? 'opacity-0 scale-0 w-0' : 'opacity-100 scale-100'}
        `}>
          Pathway
        </h1>
      </div>

      <div className={`
        transition-all duration-300 ease-in-out overflow-hidden
        ${isCollapsed ? 'opacity-0 h-0' : 'opacity-100 p-4'}
      `}>
        <div className="relative border-2">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-black" />
          <input
            type="text"
            placeholder="Search chats..."
            className={`
              w-full bg-white text-black pl-10 pr-4 py-2 rounded-lg
              focus:outline-none focus:ring-2 focus:ring-pink-500
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

      <nav className={`flex-1 overflow-y-auto px-2 ${!isCollapsed && 'mr-10'} py-4`} >
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
                    ? 'bg-pink-600/10 text-pink-600' 
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }
                  ${isCollapsed ? 'justify-center' : 'space-x-3'}
                `}
              >
                <Icon size={20} className={`
                  transition-transform duration-200
                  ${isActive ? 'text-pink-600' : ''}
                  ${isCollapsed ? 'transform scale-110' : ''}
                `} />
                <span className={`
                  transition-all duration-300 ease-in-out
                  ${isCollapsed ? 'opacity-0 w-0' : 'opacity-100'}
                  whitespace-nowrap
                `}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>


        <button
          onClick={handleNewChat}
          disabled={loading}
          className={`
            w-full mt-4 flex items-center justify-center space-x-2
            px-4 py-2 rounded-lg font-medium
            bg-pink-600 text-white
            hover:bg-pink-700
            focus:outline-none focus:ring-2 focus:ring-pink-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors duration-200
          `}
        >
          {loading ? (
            <Loader2 className="animate-spin" size={20} />
          ) : (
            <>
              <Plus size={20} />
              {!isCollapsed && <span>New Chat</span>}
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertTriangle size={20} />
              <div className="text-sm font-medium">
                {error}
              </div>
            </div>
          </div>
        )}

        {!loading && !isCollapsed && (
          <div className="mt-4">
            <div className="space-y-1">
              {filteredChats.map(chat => (
                <Link
                  key={chat.id}
                  to={`/app/chat/${chat.id}`}
                  className={`
                    flex items-center space-x-3 p-2 rounded-lg text-sm
                    ${isActiveRoute(`/app/chat/${chat.id}`)
                      ? 'bg-pink-600 text-white'
                      : 'hover:bg-pink-100 hover:text-pink-600'}
                  `}
                >
                  <History size={18} />
                  <span className="truncate">{chat.title || 'New Chat'}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <button
          className={`
            flex items-center space-x-3 p-2 rounded-lg
            hover:bg-gray-100 transition-colors duration-200
            text-gray-700 w-full
          `}
        >
          <User size={20} />
          {!isCollapsed && <span className="font-medium">Profile</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;