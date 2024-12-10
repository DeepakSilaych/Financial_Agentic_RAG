import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import {
  BotMessageSquare,
  LogIn,
  UserPlus,
  LayoutDashboard,
  LogOut
} from 'lucide-react';

const NavButton = ({
  children,
  onClick,
  variant = 'default',
  className = '',
  icon: Icon
}) => {
  const variants = {
    default: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg',
    primary: 'bg-blue-600 text-white hover:bg-blue-700 rounded-lg',
    secondary: 'bg-gray-900 text-white hover:bg-gray-800 rounded-lg',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-100 rounded-lg'
  };

  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-3 py-2 text-sm font-medium 
        transition-all duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-blue-500
        ${variants[variant]}
        ${className}
      `}
    >
      {Icon && <Icon size={18} />}
      {children}
    </button>
  );
};

const Navbar = () => {
  const { user, logout } = useUser();
  const location = useLocation();
  const navigate = useNavigate();
  const isLandingPage = location.pathname === '/';

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-1 rounded-lg group-hover:bg-blue-50 transition-colors">
              <BotMessageSquare size={32} className="text-blue-600" />
            </div>
            <span className="text-xl font-bold text-gray-900">FinSight</span>
          </Link>

          {/* Auth Buttons */}
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <NavButton
                  icon={LayoutDashboard}
                  onClick={() => navigate('/app')}
                >
                  Dashboard
                </NavButton>
                <NavButton
                  icon={LogOut}
                  onClick={handleLogout}
                  variant="outline"
                >
                  Logout
                </NavButton>
              </>
            ) : (
              <>
                <NavButton
                  icon={LogIn}
                  onClick={() => navigate('/login')}
                >
                  Login
                </NavButton>
                <NavButton
                  icon={UserPlus}
                  onClick={() => navigate('/signup')}
                  variant={isLandingPage ? 'primary' : 'secondary'}
                >
                  Sign Up
                </NavButton>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
