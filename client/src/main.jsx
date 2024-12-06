import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './pages/App';
import Chat from './pages/Chat';
import FileStorage from './pages/FileStorage';
import Settings from './pages/Settings';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import { UserProvider } from './context/UserContext';
import { SettingsProvider } from './context/SettingsContext';
import { useUser } from './context/UserContext';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import Help from './pages/Help';
import Documentation from './pages/Documentation';
import Notifications from './pages/Notifications';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import './index.css';
import Navbar from './components/Navbar';
import Blank from './pages/Blank';
import PDFChat from './pages/PDFChat';

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
        <SettingsProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={
              <>
                <Navbar />
                <LandingPage />
              </>
            } />
            
            <Route path="/login" element={
              <PublicRoute>
                <Navbar />
                <LoginPage />
              </PublicRoute>
            } />
            
            <Route path="/signup" element={
              <PublicRoute>
                <Navbar />
                <SignupPage />
              </PublicRoute>
            } />

            {/* Protected App Routes */}
            <Route path="/app" element={
              <ProtectedRoute>
                <Layout>
                  <Outlet />
                </Layout>
              </ProtectedRoute>
            }>
              <Route index element={<App />} />
              <Route path="chat" element={<App />} />
              <Route path="storage" element={<FileStorage />} />
							<Route path="storage/pdf" element={<PDFChat />} />
              <Route path="chat/:id" element={<Chat />} />
              <Route path="settings" element={<Settings />} />
              <Route path="help" element={<Help />} />
              <Route path="documentation" element={<Documentation />} />
              <Route path="notifications" element={<Notifications />} />
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </SettingsProvider>
      </UserProvider>
    </Router>
  </React.StrictMode>
);
