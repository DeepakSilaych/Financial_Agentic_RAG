import React, { useState, useEffect } from 'react';
import { FileText, MessageSquare, History, Plus, Loader2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { chatApi } from '../../utils/api';

const Sidebar = () => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadChats();
  }, []);

  const loadChats = async () => {
    try {
      const allChats = await chatApi.getAllChats();
      setChats(allChats);
      setError(null);
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
      const newChat = await chatApi.createChat();
      setChats(prevChats => [newChat, ...prevChats]);
      navigate(`/chat/${newChat.id}`);
    } catch (err) {
      setError('Failed to create new chat');
      console.error('Error creating new chat:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='w-72 h-screen p-4 bg-bluecolor text-white'>
      <div className="flex flex-col h-full">
        <h1 className="text-2xl font-bold mb-6">FinSight</h1>
        
        <nav className="flex flex-col mb-6">
          <Link to="/storage" className="flex items-center space-x-3 p-3 hover:bg-blue-600 rounded-lg transition-colors duration-200">
            <FileText size={20} />
            <span>File storage</span>
          </Link>
          
          <button
            onClick={handleNewChat}
            disabled={loading}
            className="w-full flex items-center space-x-3 p-3 hover:bg-blue-600 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Plus size={20} />}
            <span>New chat</span>
          </button>
        </nav>
        
        <div className="flex-grow overflow-hidden">
          <div className="flex items-center space-x-3 p-3 mb-2">
            <History size={20} />
            <span className="font-semibold">Recent Chats</span>
          </div>

          {error && (
            <div className="text-red-400 text-sm p-3 mb-2">
              {error}
            </div>
          )}

          <div className="space-y-2 max-h-[calc(100%-3rem)] overflow-y-auto pr-2" style={{scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.3) transparent'}}>
            {chats.map(chat => (
              <Link
                key={chat.id}
                to={`/chat/${chat.id}`}
                className="flex items-center space-x-3 pl-3  pt-3 hover:bg-blue-600 rounded-lg transition-colors duration-200"
              >
                {/* <MessageSquare size={16} /> */}
                <span className="truncate">Chat {chat.id}</span>
              </Link>
            ))}
          </div>
        </div>
        
        <div className="mt-auto pt-4 border-t border-graycolor">
          <div className="flex items-center space-x-3 p-3 hover:bg-blue-600 rounded-lg transition-colors duration-200">
            <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center font-semibold">
              A
            </div>
            <span>Abcd</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;