import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { File, Image, FileText, Music, Video, Archive, Search, Upload, Plus, LucideTrash2 } from 'lucide-react';
import { fileApi } from '../../utils/api';
import { format } from 'date-fns';

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

const FileTable = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const response = await fileApi.listFiles();
      setFiles(response || []); 
    } catch (error) {
      console.error('Error loading files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    for (const file of files) {
      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        await fileApi.uploadFile(file);
        setUploadProgress(prev => ({ ...prev, [file.name]: 100 }));
        await loadFiles(); 
      } catch (error) {
        console.error(`Error uploading file ${file.name}:`, error);
        setUploadProgress(prev => ({ ...prev, [file.name]: -1 })); 
      }
    }
  };

  const handleDelete = async (filename) => {
    try {
      await fileApi.deleteFile(filename);
      await loadFiles(); 
    } catch (error) {
      console.error(`Error deleting file ${filename}:`, error);
    }
  };

  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.tag.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.owner.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDragOver = (e) => {
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
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFileUpload(droppedFiles);
  };

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFileUpload(selectedFiles);
  };

  const handleFileClick = (file) => {
    if (file.name.toLowerCase().endsWith('.pdf')) {
      const encodedPath = encodeURIComponent(file.name);
      navigate(`/pdf-preview/${encodedPath}`);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent w-64"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-2 px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 transition-colors duration-200"
            >
              <Upload size={16} />
              <span>Upload</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInput}
              className="hidden"
              multiple
            />
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-500 bg-gray-50">
              <th className="font-medium px-4 py-3">Name</th>
              <th className="font-medium px-4 py-3">Size</th>
              <th className="font-medium px-4 py-3">Modified</th>
              <th className="font-medium px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(uploadProgress).map(([fileName, progress]) => (
              <tr key={fileName} className="bg-gray-50">
                <td className="px-4 py-3" colSpan="4">
                  <div className="flex items-center">
                    <Upload className="h-5 w-5 text-gray-400 mr-2 animate-pulse" />
                    <div className="flex-1">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-900">{fileName}</span>
                        <span className="text-sm text-gray-500">{progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-pink-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            ))}
            {filteredFiles.map((file, index) => (
              <tr 
                key={file.id || file.name}
                className={`
                  text-sm border-t border-gray-100
                  ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                  hover:bg-gray-50 cursor-pointer
                `}
                onClick={() => handleFileClick(file)}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center space-x-3">
                    {getFileIcon(file.name)}
                    <span className="font-medium text-gray-700">{file.name.length > 20 ? file.name.substring(0, 17) + '...' : file.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-500">{formatFileSize(file.size)}</td>
                <td className="px-4 py-3 text-gray-500">{formatDate(file.lastModified)}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(file.name);
                    }}
                    className="text-gray-400 hover:text-red-500 focus:outline-none"
                    title="Delete file"
                  >
                    <LucideTrash2 size={16} />
                  </button>
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
