import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './pages/App';
import Chat from './pages/Chat';
import FileStorage from './pages/FileStorage';
import Settings from './pages/Settings';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import { TeamProvider } from './context/TeamContext';
import { SettingsProvider } from './context/SettingsContext';
import { UserProvider } from './context/UserContext';
import { useUser } from './context/UserContext';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import './index.css';
import Navbar from './components/Navbar';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useUser();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

const PublicRoute = ({ children }) => {
  const { user, loading } = useUser();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (user) {
    return <Navigate to="/app" />;
  }
  
  return children;
};

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router>
      <UserProvider>
        <TeamProvider>
          <SettingsProvider>
            <Routes>
              {/* Landing Page */}
              <Route
                path="/"
                element={
                  <>
                    <Navbar />
                    <LandingPage />
                  </>
                }
              />
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <Navbar />
                    <LoginPage />
                  </PublicRoute>
                }
              />
              <Route
                path="/signup"
                element={
                  <PublicRoute>
                    <Navbar />
                    <SignupPage />
                  </PublicRoute>
                }
              />

              <Route
                path="/app"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/app/chat" replace />} />
                <Route path="chat" element={<App />} />
                <Route path="storage" element={<FileStorage />} />
                <Route path="chat/:id" element={<Chat />} />
                <Route path="settings" element={<Settings />} />
              </Route>

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </SettingsProvider>
        </TeamProvider>
      </UserProvider>
    </Router>
  </React.StrictMode>,
)
