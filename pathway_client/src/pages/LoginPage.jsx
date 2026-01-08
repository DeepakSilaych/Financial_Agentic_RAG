import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { motion } from 'framer-motion';
import { LogIn, Sparkles } from 'lucide-react';

const LoginPage = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useUser();
  const navigate = useNavigate();

  const handleDemoLogin = async () => {
    setError('');
    setLoading(true);

    const result = await login('demo@finsight.ai', 'demo123');
    if (result.success) {
      navigate('/app');
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl border border-gray-100"
      >
        <div className="text-center">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-6"
          >
            <Sparkles className="w-8 h-8 text-blue-600" />
          </motion.div>
          <h2 className="text-3xl font-bold text-gray-900">
            Welcome to FinSight
          </h2>
          <p className="mt-3 text-gray-500">
            AI-powered financial document analysis
          </p>
        </div>

        <div className="space-y-4">
          {error && (
            <div className="text-red-600 text-sm text-center bg-red-50 py-2 px-4 rounded-lg">{error}</div>
          )}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 py-4 px-6 border border-transparent text-base font-semibold rounded-xl text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LogIn className="w-5 h-5" />
            {loading ? 'Signing in...' : 'Use Demo Account'}
          </motion.button>

          <p className="text-center text-sm text-gray-400 mt-6">
            Click to sign in with demo credentials
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;
