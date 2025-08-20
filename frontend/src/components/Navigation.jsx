import React from 'react'
import { motion } from 'framer-motion'

const Navigation = ({ currentView, onViewChange, taskCounts }) => {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Agent Gallery',
      icon: '👑',
      description: 'Fashion Guru Showcase',
      gradient: 'from-rose-gold to-luxury-gold'
    },
    {
      id: 'frontend',
      label: 'Frontend Elite',
      icon: '🎨',
      description: 'Frontend Specialists',
      gradient: 'from-purple-500 to-pink-500',
      badge: 'LIVE'
    },
    {
      id: 'tasks',
      label: 'Task Atelier',
      icon: '📋',
      description: 'Priority Workshop',
      gradient: 'from-luxury-gold to-elegant-silver',
      badge: taskCounts.active
    },
    {
      id: 'risks',
      label: 'Risk Boutique',
      icon: '⚠️',
      description: 'Protection Suite', 
      gradient: 'from-elegant-silver to-rose-gold',
      badge: taskCounts.high_risk
    }
  ]

  return (
    <nav className="bg-white/90 backdrop-blur-md shadow-elegant border-b border-rose-gold/20">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-center space-x-2">
          {navItems.map((item, index) => (
            <motion.button
              key={item.id}
              className={`relative px-8 py-4 rounded-t-2xl font-semibold transition-all duration-300 ${
                currentView === item.id
                  ? `bg-gradient-to-r ${item.gradient} text-white shadow-luxury`
                  : 'text-gray-600 hover:text-gray-800 hover:bg-rose-gold/10'
              }`}
              onClick={() => onViewChange(item.id)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
            >
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{item.icon}</span>
                <div className="text-left">
                  <div className="font-fashion font-semibold">{item.label}</div>
                  <div className="text-xs opacity-80">{item.description}</div>
                </div>
              </div>
              
              {/* Badge for counts */}
              {item.badge > 0 && (
                <motion.div
                  className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full min-w-[24px] text-center"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {item.badge}
                </motion.div>
              )}

              {/* Active indicator */}
              {currentView === item.id && (
                <motion.div
                  className="absolute bottom-0 left-1/2 w-12 h-1 bg-white rounded-full"
                  layoutId="activeTab"
                  initial={{ x: '-50%' }}
                  style={{ x: '-50%' }}
                />
              )}
            </motion.button>
          ))}
        </div>

        {/* Quick Action Bar */}
        <motion.div 
          className="flex items-center justify-center py-2 space-x-6 border-t border-rose-gold/10"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span>Active Tasks: {taskCounts.active}</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span className="w-2 h-2 bg-luxury-gold rounded-full animate-pulse"></span>
            <span>Completed Today: {taskCounts.completed}</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            <span>High Risk: {taskCounts.high_risk}</span>
          </div>
        </motion.div>
      </div>
    </nav>
  )
}

export default Navigation