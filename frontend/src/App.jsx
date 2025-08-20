import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import AgentDashboard from './components/AgentDashboard'
import TaskManager from './components/TaskManager'
import RiskDashboard from './components/RiskDashboard'
import Header from './components/Header'
import Navigation from './components/Navigation'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [agents, setAgents] = useState({})
  const [tasks, setTasks] = useState([])
  const [risks, setRisks] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Fetch initial data
  useEffect(() => {
    fetchAllData()
    // Setup polling for real-time updates
    const interval = setInterval(fetchAllData, 30000) // Every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      
      // Fetch agents status
      const agentsResponse = await axios.get(`${API_BASE_URL}/agents/status`)
      setAgents(agentsResponse.data)

      // Fetch prioritized tasks
      const tasksResponse = await axios.get(`${API_BASE_URL}/tasks/prioritized`)
      setTasks(tasksResponse.data)

      // Fetch risk dashboard
      const risksResponse = await axios.get(`${API_BASE_URL}/risks/dashboard`)
      setRisks(risksResponse.data)

      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to fetch data:', error)
      // Use mock data for development
      setAgents(getMockAgents())
      setTasks(getMockTasks())
      setRisks(getMockRisks())
    } finally {
      setLoading(false)
    }
  }

  const getMockAgents = () => ({
    total_agents: 10,
    average_health: 96,
    total_active_tasks: 32,
    total_completed_today: 128,
    agents: {
      brand_intelligence: {
        status: "analyzing_trends",
        health: 98,
        styling: { color: "#E8B4B8", icon: "👑", personality: "visionary_fashion_oracle" },
        current_tasks: 3,
        completed_today: 12,
        expertise_focus: "luxury_brand_positioning"
      },
      inventory: {
        status: "optimizing_assets", 
        health: 94,
        styling: { color: "#C0C0C0", icon: "💎", personality: "detail_oriented_curator" },
        current_tasks: 2,
        completed_today: 8,
        expertise_focus: "asset_optimization"
      },
      financial: {
        status: "processing_transactions",
        health: 96,
        styling: { color: "#FFD700", icon: "💰", personality: "strategic_wealth_advisor" },
        current_tasks: 4,
        completed_today: 15,
        expertise_focus: "luxury_commerce_finance"
      }
    }
  })

  const getMockTasks = () => ({
    total_tasks: 23,
    high_risk_tasks: 5,
    urgent_tasks: 3,
    tasks: [
      {
        id: "1",
        title: "Optimize Fashion Week Keywords",
        description: "Target high-volume fashion week related keywords",
        priority: "urgent",
        risk_level: "high",
        agent_type: "seo_marketing",
        estimated_completion_time: "2 weeks",
        pros: ["High search volume during fashion weeks", "Positions brand as industry authority"],
        cons: ["Highly competitive keywords", "Seasonal fluctuations in traffic"]
      },
      {
        id: "2", 
        title: "Implement AI Styling Chatbot",
        description: "Deploy 24/7 AI styling assistant",
        priority: "high",
        risk_level: "medium", 
        agent_type: "customer_service",
        estimated_completion_time: "3 months",
        pros: ["24/7 availability", "Scalable solution"],
        cons: ["High development cost", "Training complexity"]
      }
    ]
  })

  const getMockRisks = () => ({
    risk_summary: {
      overall_risk_level: "MEDIUM",
      critical_risks: 0,
      high_risks: 3,
      medium_risks: 8,
      low_risks: 12
    }
  })

  const handleTaskUpdate = async (taskId, updates) => {
    try {
      await axios.put(`${API_BASE_URL}/tasks/${taskId}/status`, updates)
      fetchAllData() // Refresh data
    } catch (error) {
      console.error('Failed to update task:', error)
    }
  }

  const createNewTask = async (taskData) => {
    try {
      await axios.post(`${API_BASE_URL}/tasks/create`, taskData)
      fetchAllData() // Refresh data
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  return (
    <div className="min-h-screen bg-luxury-gradient">
      <Header 
        lastUpdate={lastUpdate}
        totalAgents={agents.total_agents || 0}
        averageHealth={agents.average_health || 0}
      />
      
      <Navigation 
        currentView={currentView}
        onViewChange={setCurrentView}
        taskCounts={{
          active: agents.total_active_tasks || 0,
          completed: agents.total_completed_today || 0,
          high_risk: tasks.high_risk_tasks || 0
        }}
      />

      <main className="container mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {currentView === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            >
              <AgentDashboard 
                agents={agents.agents || {}}
                loading={loading}
                onRefresh={fetchAllData}
              />
            </motion.div>
          )}

          {currentView === 'tasks' && (
            <motion.div
              key="tasks"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            >
              <TaskManager
                tasks={tasks.tasks || []}
                loading={loading}
                onTaskUpdate={handleTaskUpdate}
                onCreateTask={createNewTask}
                onRefresh={fetchAllData}
              />
            </motion.div>
          )}

          {currentView === 'risks' && (
            <motion.div
              key="risks"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            >
              <RiskDashboard
                risks={risks.risk_summary || {}}
                loading={loading}
                onRefresh={fetchAllData}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Floating Action Button for Quick Actions */}
      <motion.button
        className="fixed bottom-8 right-8 w-16 h-16 bg-luxury-gradient rounded-full shadow-luxury flex items-center justify-center text-2xl hover:shadow-gold-glow transition-all duration-300"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={fetchAllData}
      >
        🔄
      </motion.button>
    </div>
  )
}

export default App