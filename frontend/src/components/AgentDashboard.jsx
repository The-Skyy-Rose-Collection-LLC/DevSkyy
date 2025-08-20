import React, { useState } from 'react'
import { motion } from 'framer-motion'
import AgentCard from './AgentCard'
import IntegrationDashboard from './IntegrationDashboard'

const AgentDashboard = ({ agents, loading, onRefresh }) => {
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [showIntegrations, setShowIntegrations] = useState(false)
  const [selectedAgentForIntegration, setSelectedAgentForIntegration] = useState(null)
  const [filterBy, setFilterBy] = useState('all') // all, high_performance, needs_attention

  const getFilteredAgents = () => {
    if (!agents) return []
    
    const agentList = Object.entries(agents)
    
    switch (filterBy) {
      case 'high_performance':
        return agentList.filter(([_, agent]) => agent.health > 95)
      case 'needs_attention':
        return agentList.filter(([_, agent]) => agent.health < 90)
      default:
        return agentList
    }
  }

  const filteredAgents = getFilteredAgents()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-16 h-16 border-4 border-rose-gold border-t-luxury-gold rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-gray-600 font-elegant">Consulting with Fashion Gurus...</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Dashboard Header */}
      <motion.div
        className="text-center"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="text-4xl font-fashion font-bold bg-gradient-to-r from-rose-gold via-luxury-gold to-elegant-silver bg-clip-text text-transparent mb-4">
          Fashion Guru Collective
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-2xl mx-auto">
          Meet your elite team of AI fashion specialists, each expertly crafted to elevate your luxury e-commerce experience with unmatched sophistication and style.
        </p>
      </motion.div>

      {/* Filter Controls */}
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <div className="flex space-x-2">
          {[
            { id: 'all', label: 'All Gurus', icon: '👑' },
            { id: 'high_performance', label: 'Star Performers', icon: '⭐' },
            { id: 'needs_attention', label: 'Needs Attention', icon: '🎯' }
          ].map((filter) => (
            <button
              key={filter.id}
              className={`px-4 py-2 rounded-full font-medium transition-all duration-300 ${
                filterBy === filter.id
                  ? 'bg-luxury-gradient text-white shadow-elegant'
                  : 'bg-white/80 text-gray-700 hover:bg-rose-gold/20'
              }`}
              onClick={() => setFilterBy(filter.id)}
            >
              <span className="mr-2">{filter.icon}</span>
              {filter.label}
            </button>
          ))}
        </div>

        <button
          className="luxury-button"
          onClick={onRefresh}
        >
          <span className="mr-2">🔄</span>
          Refresh Gallery
        </button>
      </motion.div>

      {/* Agents Grid */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
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
        {filteredAgents.map(([agentId, agentData], index) => (
          <motion.div
            key={agentId}
            variants={{
              hidden: { opacity: 0, y: 30, scale: 0.9 },
              visible: { 
                opacity: 1, 
                y: 0, 
                scale: 1,
                transition: {
                  duration: 0.5,
                  ease: "easeOut"
                }
              }
            }}
          >
            <AgentCard
              agentId={agentId}
              agentData={agentData}
              isSelected={selectedAgent === agentId}
              onClick={() => setSelectedAgent(selectedAgent === agentId ? null : agentId)}
            />
          </motion.div>
        ))}
      </motion.div>

      {/* Empty State */}
      {filteredAgents.length === 0 && (
        <motion.div
          className="text-center py-16"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-fashion font-semibold text-gray-700 mb-2">
            No Gurus Found
          </h3>
          <p className="text-gray-500">
            Try adjusting your filters to see more fashion specialists.
          </p>
        </motion.div>
      )}

      {/* Selected Agent Details Modal */}
      {selectedAgent && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSelectedAgent(null)}
        >
          <motion.div
            className="bg-white rounded-3xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-luxury"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={(e) => e.stopPropagation()}
          >
            <AgentCard
              agentId={selectedAgent}
              agentData={agents[selectedAgent]}
              isExpanded={true}
              showDetails={true}
            />
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}

export default AgentDashboard