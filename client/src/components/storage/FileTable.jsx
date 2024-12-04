import React, { useState, useRef, useEffect } from 'react';
import { File, Image, FileText, Music, Video, Archive, Search, Upload, Folder, ArrowLeft, Trash2, Download, X } from 'lucide-react';
import { format } from 'date-fns';
import * as Dialog from '@radix-ui/react-dialog';

// Inline Button component
const Button = ({ children, onClick, variant = 'primary', className = '', ...props }) => {
  const baseStyle = "px-4 py-2 rounded-lg font-medium transition-colors duration-200";
  const variants = {
    primary: "bg-blue-500 text-white hover:bg-blue-600",
    secondary: "bg-gray-200 text-gray-700 hover:bg-gray-300",
    ghost: "bg-transparent text-gray-700 hover:bg-gray-100"
  };

  return (
    <button
      onClick={onClick}
      className={`${baseStyle} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

const getFileIcon = (fileName) => {
  const extension = fileName.split('.').pop().toLowerCase();
  switch (extension) {
    case 'pdf':
      return <FileText className="w-5 h-5 text-red-500" />;
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'webp':
      return <Image className="w-5 h-5 text-blue-500" />;
    case 'mp3':
    case 'wav':
    case 'ogg':
      return <Music className="w-5 h-5 text-purple-500" />;
    case 'mp4':
    case 'mov':
    case 'avi':
    case 'webm':
      return <Video className="w-5 h-5 text-green-500" />;
    case 'zip':
    case 'rar':
    case '7z':
      return <Archive className="w-5 h-5 text-yellow-500" />;
    default:
      return <File className="w-5 h-5 text-gray-500" />;
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

const NewFolderDialog = ({ isOpen, onClose, onCreateFolder, newFolderName, setNewFolderName }) => (
  <Dialog.Root open={isOpen} onOpenChange={onClose}>
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 bg-black/50" />
      <Dialog.Content className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-lg shadow-lg p-6 w-[400px]">
        <div className="flex justify-between items-center mb-4">
          <Dialog.Title className="text-lg font-semibold">Create New Folder</Dialog.Title>
          <Dialog.Close className="p-2 hover:bg-gray-100 rounded-full">
            <X size={20} />
          </Dialog.Close>
        </div>
        <div className="mb-4">
          <input
            type="text"
            placeholder="Folder name"
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && onCreateFolder()}
            autoFocus
          />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onCreateFolder}>
            Create Folder
          </Button>
        </div>
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>
);

const FileTable = ({ 
  spaceId, 
  selectedFolder, 
  onFolderSelect,
  showNewFolderInput,
  setShowNewFolderInput,
  newFolderName,
  setNewFolderName,
  onCreateFolder,
  refreshTrigger
}) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [currentPath, setCurrentPath] = useState('');
  const fileInputRef = useRef(null);

  const loadItems = async () => {
    if (!spaceId) return;

    try {
      setLoading(true);
      setError(null);
      console.log('Loading items for space:', spaceId, 'path:', currentPath);
      const response = await fetch(`http://localhost:8000/spaces/${spaceId}/files/${currentPath}`);
      const data = await response.json();
      console.log('Loaded items:', data);
      setItems(data || []);
    } catch (error) {
      console.error('Error loading files and folders:', error);
      setError('Failed to load files and folders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, [spaceId, currentPath, refreshTrigger]);

  const handleItemClick = (item) => {
    if (item.type === 'folder') {
      console.log('Clicking folder:', item);
      const newPath = currentPath ? `${currentPath}/${item.name}` : item.name;
      setCurrentPath(newPath);
    }
  };

  const handleNavigateUp = () => {
    if (!currentPath) return;
    const newPath = currentPath.split('/').slice(0, -1).join('/');
    setCurrentPath(newPath);
  };

  const handleFileUpload = async (files) => {
    for (const file of files) {
      try {
        console.log('Uploading file:', file.name, 'to space:', spaceId, 'path:', currentPath);
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`http://localhost:8000/spaces/${spaceId}/files/${currentPath}/upload`, {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`Upload failed with status: ${response.status}`);
        }
        
        setUploadProgress(prev => ({ ...prev, [file.name]: 100 }));
        await loadItems();
      } catch (error) {
        console.error(`Error uploading file ${file.name}:`, error);
        setUploadProgress(prev => ({ ...prev, [file.name]: -1 }));
      }
    }
  };

  const handleDelete = async (name, type) => {
    try {
      console.log('Deleting', type, 'with name:', name, 'at path:', currentPath);
      const response = await fetch(`http://localhost:8000/spaces/${spaceId}/files/${currentPath}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(name)
      });
      
      if (!response.ok) {
        throw new Error(`Delete failed with status: ${response.status}`);
      }
      
      await loadItems();
    } catch (error) {
      console.error(`Error deleting ${type}:`, error);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      console.log('Creating folder:', newFolderName, 'at path:', currentPath);
      const response = await fetch(`http://localhost:8000/spaces/${spaceId}/files/${currentPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newFolderName })
      });
      
      if (!response.ok) {
        throw new Error(`Create folder failed with status: ${response.status}`);
      }
      
      setNewFolderName('');
      setShowNewFolderInput(false);
      await loadItems();
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };

  const handleDownload = async (filename) => {
    try {
      const response = await fetch(`http://localhost:8000/spaces/${spaceId}/files/${currentPath}/download/${filename}`);
      
      if (!response.ok) {
        throw new Error(`Download failed with status: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  const handleFileClick = (file) => {
    if (file.type === 'pdf') {
      window.open(file.url, '_blank');
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) return <div className="text-center py-4">Loading...</div>;
  if (error) return <div className="text-center py-4 text-red-500">{error}</div>;

  return (
    <div
      className={`p-6 bg-gray-50 rounded-lg shadow-sm ${isDragging ? 'bg-blue-100 border-2 border-dashed border-blue-400' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 space-y-4 md:space-y-0">
        <div className="flex items-center gap-4 w-full md:w-auto">
          {currentPath && (
            <Button variant="outline" onClick={handleNavigateUp} className="flex items-center">
              <ArrowLeft size={18} className="mr-2" />
              Back
            </Button>
          )}
          <div className="relative flex-grow md:flex-grow-0">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search files..."
              className="w-full md:w-64 pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <Button onClick={() => setShowNewFolderInput(true)} className="flex items-center justify-center flex-1 md:flex-initial">
            <Folder className="mr-2" size={18} />
            New Folder
          </Button>
          <Button onClick={() => fileInputRef.current?.click()} className="flex items-center justify-center flex-1 md:flex-initial">
            <Upload className="mr-2" size={18} />
            Upload
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            multiple
            onChange={(e) => handleFileUpload(Array.from(e.target.files))}
          />
        </div>
      </div>

      <NewFolderDialog
        isOpen={showNewFolderInput}
        onClose={() => setShowNewFolderInput(false)}
        onCreateFolder={handleCreateFolder}
        newFolderName={newFolderName}
        setNewFolderName={setNewFolderName}
      />

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modified</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredItems.map((item, index) => (
              <tr
                key={index}
                className={`hover:bg-gray-50 transition-colors duration-150 ${item.type === 'folder' ? 'cursor-pointer' : ''}`}
                onClick={() => item.type === 'folder' ? handleItemClick(item) : handleFileClick(item)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {item.type === 'folder' ? (
                      <Folder className="text-blue-500 mr-3" size={20} />
                    ) : (
                      getFileIcon(item.name)
                    )}
                    <span className="ml-2 text-sm font-medium text-gray-900">{item.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.type === 'file' ? formatFileSize(item.size) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(item.lastModified)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-2">
                    {item.type === 'file' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(item.name);
                        }}
                        className="text-indigo-600 hover:text-indigo-900 p-2 hover:bg-indigo-50 rounded-full transition-colors duration-150"
                      >
                        <Download size={18} />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(item.name, item.type);
                      }}
                      className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-full transition-colors duration-150"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FileTable;
