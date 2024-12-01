import React, { createContext, useContext, useState } from 'react';

const TeamContext = createContext();

export const useTeam = () => {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error('useTeam must be used within a TeamProvider');
  }
  return context;
};

export const TeamProvider = ({ children }) => {
  const [currentTeam, setCurrentTeam] = useState({
    id: '1',
    name: 'Pathway Team',
    type: 'team'
  });
  
  const [teams, setTeams] = useState([
    {
      id: '1',
      name: 'Pathway Team',
      type: 'team',
      members: [
        { id: '1', name: 'John Doe', avatar: 'J', role: 'admin' },
        { id: '2', name: 'Jane Smith', avatar: 'J', role: 'member' },
      ]
    },
    {
      id: '2',
      name: 'Personal Space',
      type: 'personal'
    }
  ]);

  const [teamMembers, setTeamMembers] = useState([
    { id: '1', name: 'John Doe', avatar: 'J', role: 'admin', status: 'online' },
    { id: '2', name: 'Jane Smith', avatar: 'J', role: 'member', status: 'offline' },
  ]);

  const createTeam = (teamData) => {
    const newTeam = {
      id: Date.now().toString(),
      ...teamData,
      members: [{ id: '1', name: 'You', avatar: 'Y', role: 'admin' }]
    };
    setTeams(prev => [...prev, newTeam]);
    return newTeam;
  };

  const switchTeam = (teamId) => {
    const team = teams.find(t => t.id === teamId);
    if (team) {
      setCurrentTeam(team);
    }
  };

  const value = {
    currentTeam,
    teams,
    teamMembers,
    createTeam,
    switchTeam,
  };

  return (
    <TeamContext.Provider value={value}>
      {children}
    </TeamContext.Provider>
  );
};
