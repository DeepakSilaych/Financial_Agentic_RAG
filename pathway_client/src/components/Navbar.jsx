import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import Logo from "../assets/logo.svg";

const Navbar = () => {
  const navigate = useNavigate();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <img src={Logo} alt="FinSight" className="h-10" />
          </Link>

          <button
            onClick={() => navigate("/login")}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-all duration-200"
          >
            <LogIn size={18} />
            Sign In
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
