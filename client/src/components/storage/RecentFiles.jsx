import { File, Clock } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { fileApi } from '../../utils/api';
import { format } from 'date-fns';

const RecentFiles = () => {
  const [recentFiles, setRecentFiles] = useState([]);

  useEffect(() => {
    loadRecentFiles();
  }, []);

  const loadRecentFiles = async () => {
    try {
      const files = await fileApi.listFiles();
      const sortedFiles = files
        .sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified))
        .slice(0, 3)
        .map(file => ({
          ...file,
          name: file.name.length > 20 ? file.name.substring(0, 17) + '...' : file.name,
          lastModified: format(new Date(file.lastModified), 'MMM d, yyyy')
        }));
      setRecentFiles(sortedFiles);
    } catch (error) {
      console.error('Error loading recent files:', error);
    }
  };

  return (
    <div className="p-4">
      <div className="flex items-center mb-4">
        <h2 className="text-xl font-semibold text-blackcolor">Recent Files</h2>
      </div>
      <div className="flex flex-row space-x-6">
        {recentFiles.map((file) => (
          <div key={file.id || file.name} className="relative group cursor-pointer w-64">
            <div className="mb-2 flex items-center justify-between">
              <div className="flex items-center">
                <File className="w-4 h-4 text-gray-500 mr-2" />
                <p className="text-sm text-gray-700 font-medium truncate">{file.name}</p>
              </div>
              <span className="text-xs text-gray-500">{file.size.toLocaleString()} KB</span>
            </div>
            <div className="aspect-video rounded-lg overflow-hidden shadow-lg group-hover:shadow-xl transition-shadow duration-200">
              {file.thumbnail ? (
                <img
                  src={file.thumbnail}
                  alt={file.name}
                  className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                />
              ) : (
                <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                  <File className="w-12 h-12 text-gray-400" />
                </div>
              )}
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-500">{file.lastModified}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentFiles;
