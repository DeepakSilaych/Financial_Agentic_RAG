import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, ArrowUp, Zap, Sparkles, Target, X, Loader2, Image, File, FileText, Music, Video, Archive } from 'lucide-react';
import { chatApi, fileApi, autoCompleteApi } from '../../utils/api';
import * as Dialog from '@radix-ui/react-dialog';
import { useUser } from '../../context/UserContext';
import FileSelector from '../shared/FileSelector';

const getFileIcon = (fileName) => {
  const extension = fileName.split('.').pop().toLowerCase();
  switch (extension) {
    case 'jpg':
    case 'png':
    case 'gif':
    case 'jpeg':
    case 'webp':
      return <Image className="text-green-500" />;
    case 'pdf':
    case 'doc':
    case 'docx':
    case 'txt':
    case 'md':
      return <FileText className="text-yellow-500" />;
    case 'mp3':
    case 'wav':
    case 'ogg':
      return <Music className="text-purple-500" />;
    case 'mp4':
    case 'mov':
    case 'avi':
    case 'webm':
      return <Video className="text-red-500" />;
    case 'zip':
    case 'rar':
    case '7z':
      return <Archive className="text-orange-500" />;
    default:
      return <File className="text-gray-500" />;
  }
};

const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateString) => {
  return format(new Date(dateString), 'MMM d, yyyy HH:mm');
};

const ChatInput = ({ 
  setError: setParentError, 
  chatId, 
  messages, 
  onSendMessage,
  isDialog = false,
  onSend
}) => {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState('fast');
  const [researchMode, setResearchMode] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isFileDialogOpen, setIsFileDialogOpen] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const componentRef = useRef(null);
  const textareaRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const { currentSpace } = useUser();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (componentRef.current && !componentRef.current.contains(event.target)) {
        setIsExpanded(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (isExpanded && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isExpanded]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    try {
      if (isDialog) {
        const newChat = await chatApi.createChat(currentSpace.id);
        await onSendMessage({
          content: message,
          mode,
          research_mode: researchMode,
          is_user: true
        }, newChat.id);
        onSend?.();
      } else {
        await onSendMessage({
          content: message,
          mode,
          research_mode: researchMode,
          is_user: true
        });
      }
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      setParentError?.(error.message);
    }
  };

  const handleFileSelect = (filePath) => {
    setSelectedFiles(prev => {
      const isAlreadySelected = prev.includes(filePath);
      if (isAlreadySelected) {
        return prev.filter(path => path !== filePath);
      } else {
        return [...prev, filePath];
      }
    });
  };

  const handleRemoveFile = (filePath) => {
    setSelectedFiles(prev => prev.filter(path => path !== filePath));
  };

  const fetchSuggestions = async (query) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    
    try {
      setIsLoadingSuggestions(true);
      const response = await autoCompleteApi.getSuggestions(query);
      setSuggestions(response.suggestions || []);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleMessageChange = (e) => {
    const newMessage = e.target.value;
    setMessage(newMessage);
    setIsTyping(newMessage.length > 0);
    
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    debounceTimerRef.current = setTimeout(() => {
      fetchSuggestions(newMessage);
    }, 300);
  };

  // Clear suggestions when component unmounts
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const getModeIcon = (modeType) => {
    switch (modeType) {
      case 'fast': return <Zap size={16} className="text-yellow-500" />;
      case 'creative': return <Sparkles size={16} className="text-purple-500" />;
      case 'precise': return <Target size={16} className="text-blue-500" />;
      default: return null;
    }
  };

  return (
    <div ref={componentRef} className="relative">
      {/* File selection dialog */}
      <FileSelector
        isOpen={isFileDialogOpen}
        onClose={() => setIsFileDialogOpen(false)}
        onFileSelect={handleFileSelect}
        selectedFiles={selectedFiles}
        spaceId={currentSpace?.id}
        title="Select Files"
      />

      {/* Suggestions dropdown */}
      {suggestions.length > 0 && suggestions.length[0] !== '' && (
        <div className="absolute bottom-full w-full max-w-5xl translate-x-[-50%] left-1/2 mb-2 bg-white rounded-lg shadow-lg border  max-h-48 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 text-sm text-gray-700"
              onClick={() => {
                setMessage(suggestion);
                setSuggestions([]);
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
      {isLoadingSuggestions && (
        <div className="absolute bottom-full left-0 w-full mb-2 p-2 text-center text-black-500 ">
          <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
          Loading suggestions...
        </div>
      )}
      <div 
        className={`w-full relative mb-4 transition-all duration-500 ease-in-out ${isExpanded ? 'h-48' : selectedFiles.length > 0 ? 'h-28' : 'h-16'}`}
        onClick={() => setIsExpanded(true)}
      >
        <form onSubmit={handleSubmit} className="p-3 max-w-5xl mx-auto bg-white border-2 border-gray-300 rounded-2xl shadow-sm hover:shadow-md transition-all duration-500 h-full">
          <div className="w-full flex flex-col space-y-2 h-full">
            {selectedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 px-2">
                {selectedFiles.map((filePath, index) => (
                  <div key={index} className="flex items-center gap-1 bg-blue-50 text-blue-700 text-sm px-2 py-1 rounded-lg">
                    <File size={14} />
                    <span>{filePath.split('/').pop()}</span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFile(filePath);
                      }}
                      className="ml-1 hover:bg-blue-100 rounded-full p-1"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleMessageChange}
              onFocus={() => setIsExpanded(true)}
              placeholder="Ask me anything..."
              className="w-full p-2 bg-gray-50 rounded-xl border-none outline-none text-gray-800 placeholder:text-gray-400 resize-none transition-all duration-500 focus:bg-gray-100"
              style={{ height: isExpanded ? '100px' : '40px' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />

            <div className={`flex items-center justify-between gap-2 transition-all duration-500 ${isExpanded ? 'opacity-100 max-h-20' : 'opacity-0 max-h-0 overflow-hidden'}`}>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <select
                    value={mode}
                    className="pl-7 pr-3 py-1.5 bg-blue-50 border-2 border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none cursor-pointer transition-all duration-300"
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
                  onClick={() => setIsFileDialogOpen(true)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2 text-gray-600 text-sm"
                >
                  <Paperclip size={18} />
                  {selectedFiles.length > 0 && (
                    <span className="text-blue-600 font-medium">{selectedFiles.length} file(s)</span>
                  )}
                </button>
              </div>

              <div className="flex items-center gap-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={researchMode}
                    onChange={(e) => setResearchMode(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
                  <span className="ml-2 text-sm font-medium text-gray-700">Research Mode</span>
                </label>
                <button
                  type="submit"
                  disabled={!isTyping || isLoading}
                  className={`p-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300 ${
                    isTyping && !isLoading
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : isLoading
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                > 
                  {isLoading ? (
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <ArrowUp size={20} />
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>

      </div>

    </div>
  );
};

export default ChatInput; 