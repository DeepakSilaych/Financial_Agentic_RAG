import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({
    theme: {
      mode: 'dark',
      accentColor: 'pink',
    },
    chat: {
      defaultMode: 'creative',
      fontSize: 'medium',
      showTimestamps: true,
      enableSounds: false,
    },
    notifications: {
      enabled: true,
      sound: true,
      desktop: true,
    },
    privacy: {
      saveHistory: true,
      shareAnalytics: false,
    },
    accessibility: {
      highContrast: false,
      reducedMotion: false,
      fontSize: 'medium',
    }
  });

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (error) {
        console.error('Failed to parse saved settings:', error);
      }
    }
  }, []);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('appSettings', JSON.stringify(settings));
  }, [settings]);

  const updateSettings = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const resetSettings = () => {
    const defaultSettings = {
      theme: {
        mode: 'dark',
        accentColor: 'pink',
      },
      chat: {
        defaultMode: 'creative',
        fontSize: 'medium',
        showTimestamps: true,
        enableSounds: false,
      },
      notifications: {
        enabled: true,
        sound: true,
        desktop: true,
      },
      privacy: {
        saveHistory: true,
        shareAnalytics: false,
      },
      accessibility: {
        highContrast: false,
        reducedMotion: false,
        fontSize: 'medium',
      }
    };
    setSettings(defaultSettings);
  };

  const value = {
    settings,
    updateSettings,
    resetSettings
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};
