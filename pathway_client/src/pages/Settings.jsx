import React, { useState } from 'react';
import {
  Palette,
  MessageSquare,
  Bell,
  Lock,
  Eye,
  RotateCcw,
  Accessibility,
  Volume2,
  Type,
  Cloud,
  CheckCircle
} from 'lucide-react';
import { useSettings } from '../context/SettingsContext';

const SettingSection = ({ title, icon: Icon, children }) => (
  <div className="mb-8">
    <div className="flex items-center space-x-2 mb-4">
      <Icon className="text-gray-400" size={20} />
      <h2 className="text-lg font-semibold text-gray-700">{title}</h2>
    </div>
    <div className="space-y-4">
      {children}
    </div>
  </div>
);

const ToggleSwitch = ({ checked, onChange, label }) => (
  <label className="flex items-center cursor-pointer">
    <div className="relative">
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={onChange}
      />
      <div className={`block w-10 h-6 rounded-full transition-colors duration-200 ${checked ? 'bg-blue-500' : 'bg-gray-400'
        }`} />
      <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform duration-200 transform ${checked ? 'translate-x-4' : 'translate-x-0'
        }`} />
    </div>
    <span className="ml-3 text-sm font-medium text-gray-700">{label}</span>
  </label>
);

const Select = ({ value, onChange, options, label }) => (
  <div className="flex items-center justify-between">
    <span className="text-sm font-medium text-gray-700">{label}</span>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="ml-3 block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
    >
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </div>
);

const Settings = () => {
  const { settings, updateSettings, resetSettings } = useSettings();
  const [googleDriveApiKey, setGoogleDriveApiKey] = useState('');
  const [isGoogleDriveConnected, setIsGoogleDriveConnected] = useState(false);

  const fontSizeOptions = [
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium' },
    { value: 'large', label: 'Large' },
  ];

  const chatModeOptions = [
    { value: 'creative', label: 'Creative' },
    { value: 'precise', label: 'Precise' },
    { value: 'balanced', label: 'Balanced' },
  ];

  const accentColorOptions = [
    { value: 'pink', label: 'Pink' },
    { value: 'blue', label: 'Blue' },
    { value: 'green', label: 'Green' },
    { value: 'purple', label: 'Purple' },
  ];

  const themeOptions = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
  ];

  const handleSubmitGoogleDriveApiKey = (e) => {
    e.preventDefault();
    // TODO: Implement API call to backend to save Google Drive API key
    console.log('Submitting Google Drive API Key:', googleDriveApiKey);
    // Simulate API call
    setTimeout(() => {
      setIsGoogleDriveConnected(true);
      setGoogleDriveApiKey('');
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <button
          onClick={resetSettings}
          className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <RotateCcw size={16} className="mr-2" />
          Reset to Defaults
        </button>
      </div>

      <div className="space-y-6 bg-white shadow rounded-lg p-6">
        <SettingSection title="Google Drive Integration" icon={Cloud}>
          {isGoogleDriveConnected ? (
            <div className="flex items-center text-green-600">
              <CheckCircle size={20} className="mr-2" />
              <span>Google Drive Connected Successfully</span>
            </div>
          ) : (
            <form onSubmit={handleSubmitGoogleDriveApiKey} className="space-y-4">
              <div>
                <label htmlFor="googleDriveApiKey" className="block text-sm font-medium text-gray-700">
                  Google Drive API Key
                </label>
                <input
                  type="text"
                  id="googleDriveApiKey"
                  value={googleDriveApiKey}
                  onChange={(e) => setGoogleDriveApiKey(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter your Google Drive API Key"
                />
              </div>
              <button
                type="submit"
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Connect Google Drive
              </button>
            </form>
          )}
        </SettingSection>
        <SettingSection title="Theme" icon={Palette}>
          <Select
            value={settings.theme.mode}
            onChange={(value) => updateSettings('theme', 'mode', value)}
            options={themeOptions}
            label="Theme Mode"
          />
          <Select
            value={settings.theme.accentColor}
            onChange={(value) => updateSettings('theme', 'accentColor', value)}
            options={accentColorOptions}
            label="Accent Color"
          />
        </SettingSection>

        <SettingSection title="Chat" icon={MessageSquare}>
          <Select
            value={settings.chat.defaultMode}
            onChange={(value) => updateSettings('chat', 'defaultMode', value)}
            options={chatModeOptions}
            label="Default Mode"
          />
          <ToggleSwitch
            checked={settings.chat.showTimestamps}
            onChange={() => updateSettings('chat', 'showTimestamps', !settings.chat.showTimestamps)}
            label="Show Timestamps"
          />
          <ToggleSwitch
            checked={settings.chat.enableSounds}
            onChange={() => updateSettings('chat', 'enableSounds', !settings.chat.enableSounds)}
            label="Enable Sound Effects"
          />
        </SettingSection>

        <SettingSection title="Notifications" icon={Bell}>
          <ToggleSwitch
            checked={settings.notifications.enabled}
            onChange={() => updateSettings('notifications', 'enabled', !settings.notifications.enabled)}
            label="Enable Notifications"
          />
          <ToggleSwitch
            checked={settings.notifications.sound}
            onChange={() => updateSettings('notifications', 'sound', !settings.notifications.sound)}
            label="Notification Sounds"
          />
          <ToggleSwitch
            checked={settings.notifications.desktop}
            onChange={() => updateSettings('notifications', 'desktop', !settings.notifications.desktop)}
            label="Desktop Notifications"
          />
        </SettingSection>

        <SettingSection title="Privacy" icon={Lock}>
          <ToggleSwitch
            checked={settings.privacy.saveHistory}
            onChange={() => updateSettings('privacy', 'saveHistory', !settings.privacy.saveHistory)}
            label="Save Chat History"
          />
          <ToggleSwitch
            checked={settings.privacy.shareAnalytics}
            onChange={() => updateSettings('privacy', 'shareAnalytics', !settings.privacy.shareAnalytics)}
            label="Share Analytics"
          />
        </SettingSection>

        <SettingSection title="Accessibility" icon={Accessibility}>
          <ToggleSwitch
            checked={settings.accessibility.highContrast}
            onChange={() => updateSettings('accessibility', 'highContrast', !settings.accessibility.highContrast)}
            label="High Contrast"
          />
          <ToggleSwitch
            checked={settings.accessibility.reducedMotion}
            onChange={() => updateSettings('accessibility', 'reducedMotion', !settings.accessibility.reducedMotion)}
            label="Reduced Motion"
          />
          <Select
            value={settings.accessibility.fontSize}
            onChange={(value) => updateSettings('accessibility', 'fontSize', value)}
            options={fontSizeOptions}
            label="Font Size"
          />
        </SettingSection>
      </div>
    </div>
  );
};

export default Settings;
