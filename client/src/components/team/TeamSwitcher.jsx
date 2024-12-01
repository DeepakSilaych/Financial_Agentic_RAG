import React, { useState } from 'react';
import { Building2, Users, Plus, ChevronDown } from 'lucide-react';
import { useTeam } from '../../context/TeamContext';

const TeamSwitcher = () => {
  const { currentTeam, teams, createTeam, switchTeam } = useTeam();
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');

  const handleCreateTeam = () => {
    if (newTeamName.trim()) {
      const newTeam = createTeam({
        name: newTeamName.trim(),
        type: 'team'
      });
      switchTeam(newTeam.id);
      setNewTeamName('');
      setIsCreating(false);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
      >
        {currentTeam.type === 'team' ? (
          <Building2 size={20} />
        ) : (
          <Users size={20} />
        )}
        <span className="font-medium">{currentTeam.name}</span>
        <ChevronDown size={16} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
          <div className="px-4 py-2 text-xs font-medium text-gray-500">
            Your spaces
          </div>

          {teams.map(team => (
            <button
              key={team.id}
              onClick={() => {
                switchTeam(team.id);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2 ${
                currentTeam.id === team.id ? 'text-pink-600' : 'text-gray-700'
              }`}
            >
              {team.type === 'team' ? (
                <Building2 size={16} />
              ) : (
                <Users size={16} />
              )}
              <span>{team.name}</span>
            </button>
          ))}

          <div className="border-t border-gray-200 my-1"></div>

          {isCreating ? (
            <div className="px-4 py-2">
              <input
                type="text"
                placeholder="Enter team name..."
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateTeam();
                  } else if (e.key === 'Escape') {
                    setIsCreating(false);
                  }
                }}
                autoFocus
              />
              <div className="flex justify-end space-x-2 mt-2">
                <button
                  onClick={() => setIsCreating(false)}
                  className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTeam}
                  className="px-2 py-1 text-xs text-pink-600 hover:text-pink-800"
                >
                  Create
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsCreating(true)}
              className="w-full text-left px-4 py-2 text-sm text-pink-600 hover:bg-gray-100 flex items-center space-x-2"
            >
              <Plus size={16} />
              <span>Create new space</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default TeamSwitcher;
