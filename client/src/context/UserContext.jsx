import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [teams, setTeams] = useState([]);
  const [currentTeam, setCurrentTeam] = useState(null);
  const [spaces, setSpaces] = useState([]);
  const [currentSpace, setCurrentSpace] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // For development, using hardcoded user
      setUser({
        id: 1,
        name: "deepak",
        email: "deepak@example.com"
      });
      setLoading(false);
    } catch (error) {
      console.error('Auth check failed:', error);
      setLoading(false);
    }
  };

  const fetchTeams = async () => {
    if (!user) return;
    
    try {
      const response = await fetch('/api/teams');
      if (response.ok) {
        const teamsData = await response.json();
        setTeams(teamsData);
        if (teamsData.length > 0 && !currentTeam) {
          setCurrentTeam(teamsData[0]);
          await fetchSpaces(teamsData[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch teams:', error);
    }
  };

  const fetchSpaces = async (teamId) => {
    if (!user || !teamId) return;
    
    try {
      const response = await fetch(`/api/teams/${teamId}/spaces`);
      if (response.ok) {
        const spacesData = await response.json();
        setSpaces(spacesData);
        if (spacesData.length > 0 && !currentSpace) {
          setCurrentSpace(spacesData[0]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch spaces:', error);
    }
  };

  const login = async (credentials) => {
    try {
      // Implement actual login logic here
      await checkAuth();
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setTeams([]);
    setCurrentTeam(null);
    setSpaces([]);
    setCurrentSpace(null);
  };

  const value = {
    user,
    teams,
    currentTeam,
    spaces,
    currentSpace,
    loading,
    setCurrentTeam,
    setCurrentSpace,
    login,
    logout,
    checkAuth,
    fetchTeams,
    fetchSpaces
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
