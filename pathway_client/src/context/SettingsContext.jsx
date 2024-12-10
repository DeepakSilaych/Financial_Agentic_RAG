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
      mode: 'light',
      accentColor: 'blue',
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

  // Apply theme changes
  useEffect(() => {
    const root = document.documentElement;
    const isDark = settings.theme.mode === 'dark';
    
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Set theme colors based on mode and accent color
    const colors = {
      blue: {
        primary: '#191E96',
        accent: '#2563eb',
      },
      pink: {
        primary: '#C5198D',
        accent: '#ec4899',
      },
      green: {
        primary: '#059669',
        accent: '#10b981',
      },
      purple: {
        primary: '#7c3aed',
        accent: '#8b5cf6',
      }
    };

    const selectedColors = colors[settings.theme.accentColor];

    // Light mode colors
    if (!isDark) {
      root.style.setProperty('--color-primary', selectedColors.primary);
      root.style.setProperty('--color-accent', selectedColors.accent);
      root.style.setProperty('--color-background', '#ffffff');
      root.style.setProperty('--color-surface', '#f3f4f6');
      root.style.setProperty('--color-text', '#111827');
      root.style.setProperty('--color-text-secondary', '#4b5563');
      root.style.setProperty('--color-border', '#e5e7eb');
    } 
    // Dark mode colors
    else {
      root.style.setProperty('--color-primary', selectedColors.primary);
      root.style.setProperty('--color-accent', selectedColors.accent);
      root.style.setProperty('--color-background', '#111827');
      root.style.setProperty('--color-surface', '#1f2937');
      root.style.setProperty('--color-text', '#f9fafb');
      root.style.setProperty('--color-text-secondary', '#9ca3af');
      root.style.setProperty('--color-border', '#374151');
    }
  }, [settings.theme]);

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
        mode: 'light',
        accentColor: 'blue',
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
