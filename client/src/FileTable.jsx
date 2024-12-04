import React, { useState, useRef, useEffect } from 'react';
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
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const fileList = await fileApi.listFiles();
      setFiles(fileList);
    } catch (error) {
      console.error('Error loading files:', error);
    }
  };

  const handleFileUpload = async (files) => {
    for (const file of files) {
      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        await fileApi.uploadFile(file);
        setUploadProgress(prev => ({ ...prev, [file.name]: 100 }));
        loadFiles();
      } catch (error) {
        console.error('Error uploading file:', error);
        setUploadProgress(prev => ({ ...prev, [file.name]: -1 }));
      }
    }
  };

  const handleDelete = async (filename) => {
    try {
      await fileApi.deleteFile(filename);
      loadFiles();
    } catch (error) {
      console.error('Error deleting file:', error);
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

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-blackcolor">All Files</h2>
        <div className="flex items-center space-x-4">
          <div className="relative w-96">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-offset-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search files, tags, or owners..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Upload className="h-5 w-5 mr-2" />
            Upload
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

      <div
        className={`overflow-x-auto bg-white rounded-lg shadow transition-all ${isDragging ? 'border-2 border-blue-500 border-dashed' : ''
          }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragging && (
          <div className="absolute inset-0 bg-blue-50 bg-opacity-50 flex items-center justify-center">
            <div className="text-center">
              <Plus className="h-12 w-12 text-blue-500 mx-auto" />
              <p className="mt-2 text-sm text-blue-600">Drop files here to upload</p>
            </div>
          </div>
        )}

        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tag</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Modified</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {Object.entries(uploadProgress).map(([fileName, progress]) => (
              <tr key={fileName} className="bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap" colSpan="7">
                  <div className="flex items-center">
                    <Upload className="h-5 w-5 text-gray-400 mr-2 animate-pulse" />
                    <div className="flex-1">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-900">{fileName}</span>
                        <span className="text-sm text-gray-500">{progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            ))}

            {filteredFiles.map((file) => (
              <tr key={file.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getFileIcon(file.name)}
                    <span className="ml-2 text-sm text-gray-900">{file.name.length > 20 ? file.name.substring(0, 17) + '...' : file.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {file.tag}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatFileSize(file.size)}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(file.created)}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{file.owner}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(file.lastModified)}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex items-center justify-center">
                  <LucideTrash2
                    onClick={() => handleDelete(file.name)}
                    className="text-black-900 text-black cursor-pointer font-thin"
                    title="Delete"
                    size={20}
                    strokeWidth={1.5}
                  />
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
