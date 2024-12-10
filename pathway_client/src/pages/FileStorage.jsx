import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import FileTable from '../components/storage/FileTable';
import { useContext } from 'react';
import UserContext from '../context/UserContext';
import { fileApi, spaceApi } from '../utils/api';

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

// Inline Input component
const Input = ({ value, onChange, className = '', ...props }) => (
  <input
    value={value}
    onChange={onChange}
    className={`px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    {...props}
  />
);

const FileStorage = () => {
  const { spaceId } = useParams();
  const { currentSpace, setCurrentSpace } = useContext(UserContext);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [showNewFolderInput, setShowNewFolderInput] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    const loadSpace = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (spaceId) {
          const space = await spaceApi.getSpace(parseInt(spaceId));
          setCurrentSpace(space);
        }
        else if (!currentSpace) {
          const spaces = await spaceApi.getSpaces();
          if (spaces && spaces.length > 0) {
            setCurrentSpace(spaces[0]);
          }
        }
      } catch (error) {
        console.error('Error loading space:', error);
        setError('Failed to load space');
      } finally {
        setLoading(false);
      }
    };

    loadSpace();
  }, [spaceId]);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim() || !currentSpace?.id) return;
    
    try {
      await fileApi.createFolder(newFolderName.trim(), currentSpace.id);
      setNewFolderName('');
      setShowNewFolderInput(false);
      // Trigger refresh after folder creation
      setRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold">Loading...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center text-red-500">
          <h2 className="text-xl font-semibold">{error}</h2>
        </div>
      </div>
    );
  }

  if (!currentSpace) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold">No spaces available</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">
          Files - {currentSpace.name}
        </h1>
      </div>
      
      <FileTable 
        spaceId={currentSpace.id} 
        selectedFolder={selectedFolder}
        onFolderSelect={setSelectedFolder}
        showNewFolderInput={showNewFolderInput}
        setShowNewFolderInput={setShowNewFolderInput}
        newFolderName={newFolderName}
        setNewFolderName={setNewFolderName}
        onCreateFolder={handleCreateFolder}
        refreshTrigger={refreshTrigger}
      />
    </div>
  );
};

export default FileStorage;