import { File, Clock, Calendar, ExternalLink } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { fileApi } from '../../utils/api';
import { format } from 'date-fns';
import { motion } from 'framer-motion';

const RecentFiles = () => {
  const [recentFiles, setRecentFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentFiles();
  }, []);

  const loadRecentFiles = async () => {
    try {
      setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
  };

  return (
    <div className="p-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center mb-8"
      >
        <div className="bg-blue-100 p-2 rounded-xl mr-3">
          <Clock className="w-5 h-5 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-blue-800 text-transparent bg-clip-text">
          Recent Files
        </h2>
      </motion.div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
      >
        {recentFiles.map((file) => (
          <motion.div
            key={file.id || file.name}
            variants={item}
            whileHover={{ y: -8, transition: { type: "spring", stiffness: 300 } }}
            className="relative group"
          >
            <motion.div
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 300 }}
              className="bg-gradient-to-br from-white to-gray-50 p-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100"
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="bg-blue-100 p-2 rounded-lg mr-3">
                    <File className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-800 truncate">{file.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {file.size.toLocaleString()} KB
                    </p>
                  </div>
                </div>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ExternalLink size={16} className="text-gray-400" />
                </motion.button>
              </div>

              <div className="aspect-video rounded-xl overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 group-hover:shadow-md transition-shadow duration-300">
                {file.thumbnail ? (
                  <img
                    src={file.thumbnail}
                    alt={file.name}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <File className="w-12 h-12 text-gray-300" />
                  </div>
                )}
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center text-gray-500">
                  <Calendar className="w-4 h-4 mr-2" />
                  <span className="text-xs font-medium">{file.lastModified}</span>
                </div>
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
              </div>
            </motion.div>
          </motion.div>
        ))}
      </motion.div>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="space-y-3">
            <div className="flex space-x-4">
              <div className="h-3 w-32 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="h-3 w-24 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="h-3 w-28 bg-gray-200 rounded-full animate-pulse"></div>
            </div>
            <div className="flex space-x-4">
              <div className="h-3 w-28 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="h-3 w-32 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="h-3 w-24 bg-gray-200 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentFiles;
