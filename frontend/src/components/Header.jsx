import React from 'react'
import { motion } from 'framer-motion'

const Header = ({ lastUpdate, totalAgents, averageHealth }) => {
  return (
    <header className="bg-white/95 backdrop-blur-md shadow-elegant border-b border-rose-gold/20">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Brand Section */}
          <motion.div 
            className="flex items-center space-x-4"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="w-12 h-12 bg-rose-gold-gradient rounded-full flex items-center justify-center shadow-elegant">
              <span className="text-2xl">👑</span>
            </div>
            <div>
              <h1 className="text-3xl font-fashion font-bold bg-gradient-to-r from-rose-gold via-luxury-gold to-elegant-silver bg-clip-text text-transparent">
                The Skyy Rose Collection
              </h1>
              <p className="text-gray-600 font-elegant">AI Fashion Guru Dashboard</p>
            </div>
          </motion.div>

          {/* Status Section */}
          <motion.div 
            className="flex items-center space-x-8"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {/* System Health */}
            <div className="text-center">
              <div className="flex items-center space-x-2 mb-1">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700">System Health</span>
              </div>
              <div className="text-2xl font-bold text-green-600">{averageHealth}%</div>
            </div>

            {/* Active Agents */}
            <div className="text-center">
              <div className="text-sm font-medium text-gray-700 mb-1">Fashion Gurus</div>
              <div className="text-2xl font-bold text-rose-gold">{totalAgents}</div>
            </div>

            {/* Last Update */}
            <div className="text-center">
              <div className="text-sm font-medium text-gray-700 mb-1">Last Update</div>
              <div className="text-sm text-gray-500">
                {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '--:--'}
              </div>
            </div>

            {/* Luxury Status Indicator */}
            <motion.div 
              className="px-4 py-2 bg-luxury-gradient rounded-full text-white font-semibold text-sm shadow-elegant"
              animate={{ 
                boxShadow: ['0 0 20px rgba(255, 215, 0, 0.3)', '0 0 30px rgba(232, 180, 184, 0.5)', '0 0 20px rgba(255, 215, 0, 0.3)'] 
              }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              ✨ LUXURY MODE ACTIVE
            </motion.div>
          </motion.div>
        </div>

        {/* Quick Stats Bar */}
        <motion.div 
          className="mt-4 flex items-center justify-center space-x-8 py-3 bg-rose-gold/10 rounded-xl border border-rose-gold/20"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🎯</span>
            <span className="font-medium text-gray-700">Trend Analysis: Active</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">💎</span>
            <span className="font-medium text-gray-700">Asset Optimization: Running</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🛡️</span>
            <span className="font-medium text-gray-700">Brand Protection: Secured</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">⚡</span>
            <span className="font-medium text-gray-700">Performance: Optimal</span>
          </div>
        </motion.div>
      </div>
    </header>
  )
}

export default Header