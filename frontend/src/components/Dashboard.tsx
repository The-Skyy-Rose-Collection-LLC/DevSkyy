import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await axios.get('http://localhost:8000/health');
        setHealth(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch health status:', error);
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600 mb-4">
            DevSkyy Enterprise Platform
          </h1>
          <p className="text-gray-300 text-lg">
            AI-Powered Luxury E-Commerce Platform
          </p>
        </div>

        {/* Status Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-purple-900/50 to-pink-900/30 backdrop-blur-lg border border-purple-500/30 rounded-2xl p-8 mb-8"
        >
          <h2 className="text-2xl font-semibold text-white mb-6 flex items-center">
            <span className="mr-3">🚀</span>
            System Status
          </h2>
          {health ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Status</div>
                <div className="text-green-400 text-2xl font-bold">{health.status || 'Healthy'}</div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Version</div>
                <div className="text-purple-400 text-2xl font-bold">{health.version || '1.0.0'}</div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Environment</div>
                <div className="text-blue-400 text-2xl font-bold">{health.environment || 'Development'}</div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Timestamp</div>
                <div className="text-pink-400 text-xl font-mono">{new Date().toLocaleTimeString()}</div>
              </div>
            </div>
          ) : (
            <div className="text-red-400">Unable to connect to backend</div>
          )}
        </motion.div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            icon="🤖"
            title="AI Agents"
            description="57+ specialized AI agents for luxury e-commerce"
            delay={0.3}
          />
          <FeatureCard
            icon="🔒"
            title="Enterprise Security"
            description="SOC2, GDPR, and PCI-DSS compliant"
            delay={0.4}
          />
          <FeatureCard
            icon="⚡"
            title="Real-time Processing"
            description="FastAPI backend with async support"
            delay={0.5}
          />
        </div>

        {/* Quick Links */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-12 text-center"
        >
          <div className="flex justify-center gap-4 flex-wrap">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
            >
              API Documentation
            </a>
            <a
              href="http://localhost:8000/health"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 bg-pink-600 hover:bg-pink-700 text-white rounded-lg font-semibold transition-colors"
            >
              Health Check
            </a>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

interface FeatureCardProps {
  icon: string;
  title: string;
  description: string;
  delay: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, delay }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="bg-gradient-to-br from-purple-900/40 to-pink-900/20 backdrop-blur-lg border border-purple-500/20 rounded-xl p-6 hover:border-purple-500/50 transition-all"
    >
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </motion.div>
  );
};

export default Dashboard;
