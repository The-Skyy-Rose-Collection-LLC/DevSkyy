/**
 * ModernApp.jsx - Main UI Shell
 * High-level dashboard UI for DevSkyy with lazy-loaded sections and animations
 */
import React, { useState, useEffect, Suspense, lazy } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
// Lazy load components for better performance
const ModernWordPressDashboard = lazy(() => import('./ModernWordPressDashboard'))
const AutomationDashboard = lazy(() => import('./AutomationDashboard'))
const StreetAgentDashboard = lazy(() => import('./StreetAgentDashboard'))
const FrontendAgentManager = lazy(() => import('./FrontendAgentManager'))
const TaskManager = lazy(() => import('./TaskManager'))
const RiskDashboard = lazy(() => import('./RiskDashboard'))
// Loading component for Suspense fallback
const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-64">
    <motion.div
      className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  </div>
)
const ModernApp = () => {
  const [currentView, setCurrentView] = useState('agents')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [systemStatus, setSystemStatus] = useState({
    health: 96.2,
    activeAgents: 10,
    uptime: '99.9%'
  })
  // Developer mode navigation items with streetwear aesthetic
  const navItems = [
    {
      id: 'agents',
      label: 'Street Gurus',
      icon: '👾',
      gradient: 'from-purple-500 via-pink-500 to-cyan-500',
      description: 'Animated AI Agents'
    },
    {
      id: 'automation',
      label: 'Automation',
      icon: '⚡',
      gradient: 'from-yellow-500 via-orange-500 to-red-500',
      description: 'Marketing Empire'
    },
    {
      id: 'wordpress',
      label: 'WordPress',
      icon: '🌐',
      gradient: 'from-emerald-500 to-blue-500',
      description: 'Site Command'
    },
    {
      id: 'frontend',
      label: 'Frontend',
      icon: '🎨',
      gradient: 'from-indigo-500 to-purple-500',
      description: 'UI Studio'
    },
    {
      id: 'tasks',
      label: 'Tasks',
      icon: '📋',
      gradient: 'from-teal-500 to-cyan-500',
      description: 'Mission Control'
    },
    {
      id: 'monitoring',
      label: 'Analytics',
      icon: '📊',
      gradient: 'from-green-500 to-emerald-500',
      description: 'Performance Hub'
    }
  ]
  const renderCurrentView = () => {
    const components = {
      agents: StreetAgentDashboard,
      automation: AutomationDashboard,
      wordpress: ModernWordPressDashboard,
      frontend: FrontendAgentManager,
      tasks: TaskManager,
      monitoring: RiskDashboard
    }
    const Component = components[currentView] || StreetAgentDashboard
    return (
      <Suspense fallback={<LoadingSpinner />}>
        <Component />
      </Suspense>
    )
  }
  return (
    <div className="min-h-screen bg-gray-900 text-white flex">
      {/* Sidebar */}
      <motion.div
        className={`bg-gray-900/95 backdrop-blur-xl border-r border-gray-800 flex flex-col ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        } transition-all duration-300`}
        initial={{ x: -100 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Logo/Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <motion.div
              className="w-8 h-8 bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-500 rounded-lg flex items-center justify-center"
              animate={{ rotate: [0, 360], scale: [1, 1.1, 1] }}
              transition={{ rotate: { duration: 20, repeat: Infinity, ease: 'linear' }, scale: { duration: 2, repeat: Infinity } }}
            >
              <span className="text-sm font-bold">SR</span>
            </motion.div>
            {!sidebarCollapsed && (
              <div>
                <motion.h1
                  className="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent"
                  animate={{ opacity: [0.8, 1, 0.8] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  Skyy Rose
                </motion.h1>
                <p className="text-xs text-gray-400">Fashion AI Platform</p>
              </div>
            )}
          </div>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute top-4 -right-3 w-6 h-6 bg-gray-800 border border-gray-700 rounded-full flex items-center justify-center hover:bg-gray-700 transition-colors"
          >
            <span className="text-xs text-gray-400">{sidebarCollapsed ? '→' : '←'}</span>
          </button>
        </div>
        {/* System Status */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-gray-800">
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">Platform Status</span>
                <motion.span className="text-emerald-400 text-xs" animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1, repeat: Infinity }}>
                  ● LIVE
                </motion.span>
              </div>
              <div className="text-sm font-semibold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                {systemStatus.health}% GOD MODE
              </div>
              <div className="text-xs text-gray-500">
                {systemStatus.activeAgents} street gurus • {systemStatus.uptime} uptime
              </div>
            </div>
          </div>
        )}
        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            {navItems.map((item) => (
              <motion.button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-3 rounded-lg transition-all duration-300 ${
                  currentView === item.id ? 'bg-gradient-to-r ' + item.gradient + ' text-white shadow-lg' : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`}
                whileHover={{ scale: 1.02, x: 2 }}
                whileTap={{ scale: 0.98 }}
              >
                <motion.span
                  className="text-lg"
                  animate={currentView === item.id ? { scale: [1, 1.2, 1], rotate: [0, 10, -10, 0] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {item.icon}
                </motion.span>
                {!sidebarCollapsed && (
                  <div className="text-left">
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs opacity-70">{item.description}</div>
                  </div>
                )}
              </motion.button>
            ))}
          </div>
        </nav>
        {/* Footer */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-800">
            <div className="text-xs text-gray-500">
              <div className="flex items-center space-x-2">
                <motion.div className="w-2 h-2 bg-purple-500 rounded-full" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity }} />
                v3.0.0 • Fashion GOD MODE
              </div>
              <div className="mt-1">Dominating since 2025</div>
            </div>
          </div>
        )}
      </motion.div>
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-gray-900/95 backdrop-blur-xl border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <motion.h1
                className="text-xl font-bold capitalize bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent"
                key={currentView}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                {navItems.find((item) => item.id === currentView)?.label} Console
              </motion.h1>
              <p className="text-sm text-gray-400">{navItems.find((item) => item.id === currentView)?.description}</p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Status Indicators */}
              <div className="flex items-center space-x-3">
                <motion.div className="flex items-center space-x-2" animate={{ scale: [1, 1.05, 1] }} transition={{ duration: 2, repeat: Infinity }}>
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-400">Street Mode</span>
                </motion.div>
                <motion.div className="flex items-center space-x-2" animate={{ scale: [1, 1.05, 1] }} transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}>
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span className="text-xs text-gray-400">Connected</span>
                </motion.div>
                <motion.div className="flex items-center space-x-2" animate={{ scale: [1, 1.05, 1] }} transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}>
                  <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                  <span className="text-xs text-gray-400">GOD MODE</span>
                </motion.div>
              </div>
              {/* Actions */}
              <div className="flex items-center space-x-2">
                <motion.button className="bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-lg transition-colors text-xs" whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  ⚙️ Settings
                </motion.button>
                <motion.button
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 px-3 py-2 rounded-lg transition-colors text-xs font-semibold"
                  whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(168, 85, 247, 0.4)' }}
                  whileTap={{ scale: 0.95 }}
                >
                  🚀 Deploy
                </motion.button>
              </div>
            </div>
          </div>
        </div>
        {/* Main Content Area */}
        <div className="flex-1 overflow-auto bg-gradient-to-br from-gray-900 via-gray-900 to-purple-900/20">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentView}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              {renderCurrentView()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
      {/* Floating particles for extra flair */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-purple-400 rounded-full opacity-30"
            animate={{
              x: [Math.random() * window.innerWidth, Math.random() * window.innerWidth],
              y: [Math.random() * window.innerHeight, Math.random() * window.innerHeight],
              opacity: [0, 0.3, 0]
            }}
            transition={{ duration: 10 + Math.random() * 10, repeat: Infinity, delay: i * 2 }}
          />
        ))}
      </div>
    </div>
  )
}
export default ModernApp
