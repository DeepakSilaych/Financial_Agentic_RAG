import React, { useState, useRef, useEffect } from 'react';
import { Building2, Plus, ChevronDown, X, Settings, Trash2 } from 'lucide-react';
import { useUser } from '../../context/UserContext';
import { spaceApi } from '../../utils/api';

function SpaceSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const [isCreateSpaceOpen, setIsCreateSpaceOpen] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState('');
  const [newSpaceDescription, setNewSpaceDescription] = useState('');
  const [isCreatingSpace, setIsCreatingSpace] = useState(false);
  const [error, setError] = useState('');
  const dropdownRef = useRef(null);
  
  const {
    spaces,
    currentSpace,
    setCurrentSpace,
    fetchSpaces,
  } = useUser();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCreateSpace = async (e) => {
    e.preventDefault();
    if (!newSpaceName.trim()) {
      setError('Space name is required');
      return;
    }

    setIsCreatingSpace(true);
    setError('');
    
    try {
      await spaceApi.createSpace({
        name: newSpaceName.trim(),
        description: newSpaceDescription.trim() || null,
        // Add new schema fields here
        // For example:
        // type: 'public', // or 'private'
        // tags: ['tag1', 'tag2'],
      });
      setNewSpaceName('');
      setNewSpaceDescription('');
      setIsCreateSpaceOpen(false);
      await fetchSpaces();
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create space');
      console.error('Error creating space:', error);
    } finally {
      setIsCreatingSpace(false);
    }
  };

  const handleDeleteSpace = async (spaceId) => {
    if (!window.confirm('Are you sure you want to delete this space?')) return;
    
    try {
      await spaceApi.deleteSpace(spaceId);
      await fetchSpaces();
      if (currentSpace?.id === spaceId) {
        setCurrentSpace(spaces[0] || null);
      }
    } catch (error) {
      console.error('Error deleting space:', error);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-md bg-white hover:bg-gray-100"
      >
        <Building2 className="w-4 h-4" />
        <span className="max-w-[150px] truncate">{currentSpace?.name || "Select Space"}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
          {spaces.map((space) => (
            <div
              key={space.id}
              className="group relative"
            >
              <button
                onClick={() => {
                  setCurrentSpace(space);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center justify-between ${
                  currentSpace?.id === space.id ? 'bg-gray-100' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4" />
                  <span className="truncate">{space.name}</span>
                </div>
                <div className="hidden group-hover:flex items-center gap-2">
                  <Settings className="w-4 h-4 text-gray-500 hover:text-gray-700 cursor-pointer" />
                  <Trash2 
                    className="w-4 h-4 text-red-500 hover:text-red-700 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSpace(space.id);
                    }}
                  />
                </div>
              </button>
            </div>
          ))}
          
          <div className="border-t border-gray-200 mt-2 pt-2">
            <button
              onClick={() => {
                setIsCreateSpaceOpen(true);
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-blue-600"
            >
              <Plus className="w-4 h-4" />
              <span>Create new space</span>
            </button>
          </div>
        </div>
      )}

      {isCreateSpaceOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Create New Space</h2>
              <button
                onClick={() => {
                  setIsCreateSpaceOpen(false);
                  setError('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={20} />
              </button>
            </div>
            {error && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 rounded">
                {error}
              </div>
            )}
            <form onSubmit={handleCreateSpace}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Space Name
                  </label>
                  <input
                    type="text"
                    value={newSpaceName}
                    onChange={(e) => setNewSpaceName(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                    placeholder="Enter space name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description (optional)
                  </label>
                  <textarea
                    value={newSpaceDescription}
                    onChange={(e) => setNewSpaceDescription(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                    placeholder="Enter space description"
                    rows={3}
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreateSpaceOpen(false);
                      setError('');
                    }}
                    className="px-4 py-2 text-sm rounded-md border border-gray-300 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreatingSpace || !newSpaceName.trim()}
                    className="px-4 py-2 text-sm text-white rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isCreatingSpace ? 'Creating...' : 'Create Space'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default SpaceSwitcher;