import React from 'react';
import { motion } from 'framer-motion';
import RecentFiles from './RecentFiles';
import FileTable from './FileTable';

const StorageContainer = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full flex-1 flex flex-col min-h-screen bg-gradient-to-br from-gray-50 to-blue-50"
    >
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex-1 container mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6"
      >
        <motion.div 
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 overflow-hidden hover:shadow-xl transition-shadow duration-300"
        >
          <RecentFiles />
        </motion.div>
        
        <motion.div 
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 overflow-hidden hover:shadow-xl transition-shadow duration-300"
        >
          <FileTable />
        </motion.div>
      </motion.div>
    </motion.div>
  );
};

export default StorageContainer;
