import React, { useState, useEffect } from 'react';
import { X, File, Folder, ChevronLeft, Loader2, AlertCircle, Image, FileText, Music, Video, Archive, Search } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { format } from 'date-fns';

// Utility functions
export const getFileIcon = (fileName) => {
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

export const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDate = (dateString) => {
  return format(new Date(dateString), 'MMM d, yyyy HH:mm');
};

const FileSelector = ({ 
  isOpen, 
  onClose, 
  onFileSelect, 
  selectedFiles = [], 
  spaceId,
  title = "Select Files"
}) => {
  const [currentPath, setCurrentPath] = useState('');
  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadFiles = async (path = '') => {
    if (!spaceId) {
      setError('No space selected');
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`http://localhost:8000/spaces/${spaceId}/files/${path}`);
      if (!response.ok) {
        throw new Error('Failed to load files');
      }
      const data = await response.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading files:', error);
      setError('Failed to load files');
      setFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadFiles(currentPath);
    } else {
      setFiles([]);
      setError(null);
      setCurrentPath('');
      setSearchQuery('');
    }
  }, [isOpen, currentPath, spaceId]);

  const handleFileSelect = (file) => {
    if (!file || !file.name || file.type !== 'file') return;
    const filePath = currentPath ? `${currentPath}/${file.name}` : file.name;
    onFileSelect(filePath);
  };

  const handleFolderClick = (folderName) => {
    const newPath = currentPath ? `${currentPath}/${folderName}` : folderName;
    setCurrentPath(newPath);
  };

  const handleNavigateUp = () => {
    if (!currentPath) return;
    const newPath = currentPath.split('/').slice(0, -1).join('/');
    setCurrentPath(newPath);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-xl shadow-xl p-6 w-[800px] max-h-[80vh] flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-4">
              <Dialog.Title className="text-lg font-semibold">{title}</Dialog.Title>
              {currentPath && (
                <button
                  onClick={handleNavigateUp}
                  className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 flex items-center gap-1"
                >
                  <ChevronLeft size={20} />
                  Back
                </button>
              )}
              <div className="text-sm text-gray-500">
                {currentPath || 'Root'}
              </div>
            </div>
            <Dialog.Close className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <X size={20} />
            </Dialog.Close>
          </div>

          <div className="mb-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                <Search size={18} />
              </div>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto min-h-[400px] border rounded-lg">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center h-full text-red-500 gap-2">
                <AlertCircle size={24} />
                <p>{error}</p>
              </div>
            ) : (
              <div className="divide-y">
                {Array.isArray(files) && files.length > 0 ? (
                  files
                    .filter(item => 
                      item.name.toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    .map((item, index) => (
                      <div
                        key={index}
                        onClick={() => item.type === 'folder' ? handleFolderClick(item.name) : handleFileSelect(item)}
                        className={`flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer ${
                          item.type === 'file' && selectedFiles.includes(currentPath ? `${currentPath}/${item.name}` : item.name)
                            ? 'bg-blue-50'
                            : ''
                        }`}
                      >
                        <div className="flex items-center gap-3 flex-1">
                          {item.type === 'folder' ? (
                            <Folder className="text-blue-500" size={20} />
                          ) : (
                            getFileIcon(item.name)
                          )}
                          <span className="text-sm text-gray-700">{item.name}</span>
                        </div>
                        {item.type === 'file' && selectedFiles.includes(currentPath ? `${currentPath}/${item.name}` : item.name) && (
                          <div className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Selected</div>
                        )}
                      </div>
                    ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                    <File size={40} className="mb-2 opacity-50" />
                    <p>No files found</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default FileSelector;
