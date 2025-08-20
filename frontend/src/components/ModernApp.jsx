import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ModernWordPressDashboard from './ModernWordPressDashboard'
import AutomationDashboard from './AutomationDashboard'
import AgentDashboard from './AgentDashboard'
import FrontendAgentManager from './FrontendAgentManager'
import TaskManager from './TaskManager'
import RiskDashboard from './RiskDashboard'

const ModernApp = () => {
  const [currentView, setCurrentView] = useState('agents')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [systemStatus, setSystemStatus] = useState({
    health: 96.2,
    activeAgents: 10,
    uptime: '99.9%'
  })

  // Developer mode navigation items
  const navItems = [
    {
      id: 'agents',
      label: 'AI Agents',
      icon: '🤖',
      gradient: 'from-blue-500 to-cyan-500',
      description: 'Agent Control Center'
    },
    {
      id: 'automation',
      label: 'Automation',
      icon: '⚡',
      gradient: 'from-purple-500 to-pink-500',
      description: 'Marketing Automation'
    },
    {
      id: 'wordpress',
      label: 'WordPress',
      icon: '🌐',
      gradient: 'from-emerald-500 to-blue-500',
      description: 'Site Management'
    },
    {
      id: 'frontend',
      label: 'Frontend',
      icon: '🎨',
      gradient: 'from-orange-500 to-red-500',
      description: 'UI Development'
    },
    {
      id: 'tasks',
      label: 'Tasks',
      icon: '📋',
      gradient: 'from-indigo-500 to-purple-500',
      description: 'Task Management'
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: '📊',
      gradient: 'from-green-500 to-emerald-500',
      description: 'System Health'
    }
  ]

  const renderCurrentView = () => {
    switch (currentView) {
      case 'agents':
        return <AgentDashboard />
      case 'automation':
        return <AutomationDashboard />
      case 'wordpress':
        return <ModernWordPressDashboard />
      case 'frontend':
        return <FrontendAgentManager />
      case 'tasks':
        return <TaskManager />
      case 'monitoring':
        return <RiskDashboard />
      default:
        return <AgentDashboard />
    }
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
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-sm font-bold">SR</span>
            </div>
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-lg font-bold">Skyy Rose</h1>
                <p className="text-xs text-gray-400">Developer Console</p>
              </div>
            )}
          </div>
          
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute top-4 -right-3 w-6 h-6 bg-gray-800 border border-gray-700 rounded-full flex items-center justify-center hover:bg-gray-700 transition-colors"
          >
            <span className="text-xs text-gray-400">
              {sidebarCollapsed ? '→' : '←'}
            </span>
          </button>
        </div>

        {/* System Status */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-gray-800">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">System Health</span>
                <span className="text-emerald-400 text-xs">●</span>
              </div>
              <div className="text-sm font-semibold text-white">{systemStatus.health}%</div>
              <div className="text-xs text-gray-500">
                {systemStatus.activeAgents} agents • {systemStatus.uptime} uptime
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
                  currentView === item.id
                    ? 'bg-gradient-to-r ' + item.gradient + ' text-white shadow-lg'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="text-lg">{item.icon}</span>
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
              <div>v2.1.0 • Developer Mode</div>
              <div className="mt-1">Last sync: Just now</div>
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
              <h1 className="text-xl font-bold capitalize">
                {navItems.find(item => item.id === currentView)?.label} Console
              </h1>
              <p className="text-sm text-gray-400">
                {navItems.find(item => item.id === currentView)?.description}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Status Indicators */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-400">Live</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span className="text-xs text-gray-400">Connected</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                  <span className="text-xs text-gray-400">AI Active</span>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex items-center space-x-2">
                <button className="bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-lg transition-colors text-xs">
                  ⚙️ Settings
                </button>
                <button className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded-lg transition-colors text-xs">
                  🚀 Deploy
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto">
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
    </div>
  )
}

export default ModernApp