import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import StreetwearAvatar from './StreetwearAvatar'

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_BACKEND_URL || '/api'

const StreetAgentDashboard = () => {
  const [agents, setAgents] = useState({})
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    fetchAgents()
    const interval = setInterval(fetchAgents, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/agents/status`)
      setAgents(response.data.agents || getMockAgents())
    } catch (error) {
      console.error('Failed to fetch agents:', error)
      setAgents(getMockAgents())
    } finally {
      setLoading(false)
    }
  }

  const getMockAgents = () => ({
    brand_intelligence: {
      status: "analyzing_viral_trends",
      health: 98,
      current_tasks: 4,
      completed_today: 23,
      expertise_focus: "luxury_trend_forecasting",
      personality: "visionary_fashion_oracle",
      last_achievement: "Predicted 5 viral TikTok trends 48hrs early",
      current_project: "Analyzing Fashion Week influence patterns",
      mood: "inspired",
      power_level: 95
    },
    performance: {
      status: "turbo_optimizing",
      health: 96,
      current_tasks: 6,
      completed_today: 31,
      expertise_focus: "lightning_speed_optimization",
      personality: "speed_demon_perfectionist",
      last_achievement: "Boosted site speed by 340% in 12 minutes",
      current_project: "Breaking performance world records",
      mood: "energized",
      power_level: 98
    },
    content: {
      status: "weaving_viral_stories",
      health: 94,
      current_tasks: 3,
      completed_today: 18,
      expertise_focus: "viral_content_mastery",
      personality: "creative_storytelling_genius",
      last_achievement: "Created content that got 2.3M views",
      current_project: "Crafting next viral campaign narrative",
      mood: "creative",
      power_level: 92
    },
    financial: {
      status: "counting_millions",
      health: 97,
      current_tasks: 5,
      completed_today: 15,
      expertise_focus: "wealth_multiplication",
      personality: "money_magnet_strategist",
      last_achievement: "Increased revenue by 285% this quarter",
      current_project: "Building passive income streams",
      mood: "calculating",
      power_level: 96
    },
    customer_service: {
      status: "spreading_love",
      health: 99,
      current_tasks: 8,
      completed_today: 42,
      expertise_focus: "customer_happiness_maximization",
      personality: "empathy_driven_helper",
      last_achievement: "Achieved 99.8% customer satisfaction",
      current_project: "Creating personalized customer journeys",
      mood: "caring",
      power_level: 94
    },
    security: {
      status: "fortress_mode",
      health: 100,
      current_tasks: 2,
      completed_today: 7,
      expertise_focus: "cyber_threat_elimination",
      personality: "digital_guardian_warrior",
      last_achievement: "Blocked 847 threats in 1 hour",
      current_project: "Building impenetrable security walls",
      mood: "vigilant",
      power_level: 100
    },
    seo_marketing: {
      status: "trending_worldwide",
      health: 93,
      current_tasks: 7,
      completed_today: 28,
      expertise_focus: "viral_marketing_domination",
      personality: "trend_amplification_master",
      last_achievement: "Got #1 ranking for 15 keywords",
      current_project: "Dominating Google's first page",
      mood: "confident",
      power_level: 91
    },
    design_automation: {
      status: "pixel_perfection",
      health: 95,
      current_tasks: 4,
      completed_today: 19,
      expertise_focus: "visual_design_mastery",
      personality: "perfectionist_pixel_artist",
      last_achievement: "Created 50 perfect designs in 1 hour",
      current_project: "Revolutionizing visual aesthetics",
      mood: "focused",
      power_level: 97
    },
    inventory: {
      status: "zen_organization",
      health: 91,
      current_tasks: 3,
      completed_today: 12,
      expertise_focus: "inventory_flow_optimization",
      personality: "methodical_organization_sensei",
      last_achievement: "Optimized inventory efficiency by 250%",
      current_project: "Predicting demand with 99% accuracy",
      mood: "balanced",
      power_level: 89
    },
    social_media: {
      status: "building_hype",
      health: 96,
      current_tasks: 9,
      completed_today: 35,
      expertise_focus: "viral_content_amplification",
      personality: "hype_machine_connector",
      last_achievement: "Gained 50K followers in 24 hours",
      current_project: "Creating the next viral sensation",
      mood: "hyped",
      power_level: 93
    }
  })

  const getPowerLevelColor = (level) => {
    if (level >= 95) return 'text-purple-400'
    if (level >= 90) return 'text-blue-400'
    if (level >= 85) return 'text-green-400'
    return 'text-yellow-400'
  }

  const getMoodEmoji = (mood) => {
    const moods = {
      inspired: '✨',
      energized: '⚡',
      creative: '🎨',
      calculating: '🧮',
      caring: '💖',
      vigilant: '👁️',
      confident: '😎',
      focused: '🎯',
      balanced: '☯️',
      hyped: '🔥'
    }
    return moods[mood] || '😊'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading Street Agents...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <motion.h1
          className="text-5xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent mb-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          Streetwear AI Gurus
        </motion.h1>
        <motion.p
          className="text-xl text-gray-400 max-w-4xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          Your squad of animated AI agents working 24/7 to dominate the fashion world. 
          Each guru brings unique streetwear style and GOD MODE intelligence.
        </motion.p>
      </div>

      {/* Agent Grid */}
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: {
                staggerChildren: 0.1
              }
            }
          }}
        >
          {Object.entries(agents).map(([agentType, agentData]) => (
            <motion.div
              key={agentType}
              className="relative group cursor-pointer"
              variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 }
              }}
              whileHover={{ scale: 1.05 }}
              onClick={() => {
                setSelectedAgent(agentType)
                setShowDetails(true)
              }}
            >
              {/* Agent Card */}
              <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-4 hover:bg-gray-800/70 transition-all duration-300">
                {/* Avatar */}
                <div className="mb-4">
                  <StreetwearAvatar
                    agentType={agentType}
                    status={agentData.status}
                    health={agentData.health}
                    isActive={agentData.health > 90}
                    size="large"
                    showBubble={agentData.health > 95}
                  />
                </div>

                {/* Stats */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Health</span>
                    <span className="text-sm font-bold text-green-400">{agentData.health}%</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Power</span>
                    <span className={`text-sm font-bold ${getPowerLevelColor(agentData.power_level)}`}>
                      {agentData.power_level}%
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Tasks</span>
                    <span className="text-sm font-bold text-blue-400">{agentData.current_tasks}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Mood</span>
                    <span className="text-lg">{getMoodEmoji(agentData.mood)}</span>
                  </div>
                </div>

                {/* Status Bar */}
                <div className="mt-3 p-2 bg-gray-900/50 rounded-lg">
                  <div className="text-xs text-gray-300 text-center capitalize">
                    {agentData.status.replace('_', ' ')}
                  </div>
                </div>

                {/* Completed Today Badge */}
                <div className="absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                  +{agentData.completed_today}
                </div>
              </div>

              {/* Hover Glow Effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-xl"></div>
            </motion.div>
          ))}
        </motion.div>

        {/* Team Stats */}
        <motion.div
          className="bg-gray-800/30 backdrop-blur-xl border border-gray-700/30 rounded-2xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h2 className="text-2xl font-bold text-white mb-4">Squad Performance</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">
                {Object.values(agents).reduce((sum, agent) => sum + agent.current_tasks, 0)}
              </div>
              <div className="text-sm text-gray-400">Active Tasks</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400">
                {Object.values(agents).reduce((sum, agent) => sum + agent.completed_today, 0)}
              </div>
              <div className="text-sm text-gray-400">Completed Today</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">
                {Math.round(Object.values(agents).reduce((sum, agent) => sum + agent.health, 0) / Object.values(agents).length)}%
              </div>
              <div className="text-sm text-gray-400">Avg Health</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">
                {Math.round(Object.values(agents).reduce((sum, agent) => sum + agent.power_level, 0) / Object.values(agents).length)}%
              </div>
              <div className="text-sm text-gray-400">Avg Power</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Agent Detail Modal */}
      <AnimatePresence>
        {showDetails && selectedAgent && (
          <motion.div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowDetails(false)}
          >
            <motion.div
              className="bg-gray-800 rounded-2xl p-6 max-w-md w-full border border-gray-700"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-center mb-6">
                <StreetwearAvatar
                  agentType={selectedAgent}
                  status={agents[selectedAgent]?.status}
                  health={agents[selectedAgent]?.health}
                  isActive={true}
                  size="xl"
                  showBubble={true}
                />
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Latest Achievement</h3>
                  <p className="text-gray-300 text-sm">{agents[selectedAgent]?.last_achievement}</p>
                </div>
                
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Current Project</h3>
                  <p className="text-gray-300 text-sm">{agents[selectedAgent]?.current_project}</p>
                </div>
                
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Expertise</h3>
                  <p className="text-gray-300 text-sm capitalize">{agents[selectedAgent]?.expertise_focus?.replace('_', ' ')}</p>
                </div>

                <button
                  onClick={() => setShowDetails(false)}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-xl font-semibold hover:from-purple-600 hover:to-pink-600 transition-all duration-300"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default StreetAgentDashboard