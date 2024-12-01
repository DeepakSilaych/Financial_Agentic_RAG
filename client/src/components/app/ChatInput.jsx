import React, { useState } from 'react';
import { Paperclip, ArrowUp, Zap, Sparkles, Target } from 'lucide-react';

const ChatInput = ({ ws, setError }) => {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState('fast');
  const [researchMode, setResearchMode] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (message.trim()) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          message: message,
          mode: mode,
          research_mode: researchMode
        }));
        setMessage('');
      } else {
        setError('Connection lost. Please refresh the page.');
      }
    }
  };

  const getModeIcon = (modeType) => {
    switch (modeType) {
      case 'fast':
        return <Zap size={16} className="text-yellow-500" />;
      case 'creative':
        return <Sparkles size={16} className="text-purple-500" />;
      case 'precise':
        return <Target size={16} className="text-blue-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="w-full relative mb-6">
      <form onSubmit={handleSendMessage} className="p-4 py-3 max-w-5xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200">
        <div className="w-full flex flex-col space-y-3">
          <textarea
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
              setIsTyping(e.target.value.length > 0);
            }}
            placeholder="Ask me anything..."
            className="w-full p-3 bg-gray-50 rounded-xl border-none outline-none text-gray-800 placeholder:text-gray-400 resize-none transition-all duration-200 focus:bg-gray-100"
            rows="1"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(e);
              }
            }}
          />
          
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="relative">
                <select
                  value={mode}
                  className="pl-8 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 appearance-none cursor-pointer"
                  onChange={(e) => setMode(e.target.value)}
                >
                  <option value="fast">Fast</option>
                  <option value="creative">Creative</option>
                  <option value="precise">Precise</option>
                </select>
                <div className="absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none">
                  {getModeIcon(mode)}
                </div>
              </div>

              <button
                type="button"
                className="flex items-center px-4 py-2 text-sm text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-pink-500"
              >
                <Paperclip size={16} className="mr-2" />
                Attach
              </button>
            </div>

            <div className="flex items-center gap-4">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={researchMode}
                  onChange={(e) => setResearchMode(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-pink-300 rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-pink-600" />
                <span className="ml-3 text-sm font-medium text-gray-700">Research Mode</span>
              </label>

              <button
                type="submit"
                disabled={!isTyping}
                className={`p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-500 transition-all duration-200 ${
                  isTyping
                    ? 'bg-pink-600 text-white hover:bg-pink-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                <ArrowUp size={20} />
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;