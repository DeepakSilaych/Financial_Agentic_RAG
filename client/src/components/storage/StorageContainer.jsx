import React from 'react';
import RecentFiles from './RecentFiles';
import FileTable from './FileTable';

const StorageContainer = () => {
  return (
    <div className="w-full pt-10 flex-1 flex flex-col h-screen bg-gray-50">


      <div className="flex-1 mx-10 overflow-y-auto">
        <RecentFiles />
        <FileTable />
      </div>
    </div>
  );
};

export default StorageContainer;
