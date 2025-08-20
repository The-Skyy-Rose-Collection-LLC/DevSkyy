import React, { useState } from 'react'
import { motion } from 'framer-motion'

const TaskCard = ({ task, onUpdate, onClick, isExpanded, showDetails }) => {
  const [isUpdating, setIsUpdating] = useState(false)

  const getRiskColor = (riskLevel) => {
    const colors = {
      critical: 'border-red-500 bg-red-50',
      high: 'border-orange-500 bg-orange-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-green-500 bg-green-50'
    }
    return colors[riskLevel] || colors.medium
  }

  const getPriorityColor = (priority) => {
    const colors = {
      urgent: 'bg-red-500',
      high: 'bg-orange-500', 
      medium: 'bg-yellow-500',
      low: 'bg-green-500'
    }
    return colors[priority] || colors.medium
  }

  const getAgentInfo = (agentType) => {
    const agentMap = {
      brand_intelligence: { name: 'Brand Oracle', icon: '👑', color: '#E8B4B8' },
      inventory: { name: 'Asset Curator', icon: '💎', color: '#C0C0C0' },
      financial: { name: 'Wealth Advisor', icon: '💰', color: '#FFD700' },
      ecommerce: { name: 'Experience Guru', icon: '🛍️', color: '#E8B4B8' },
      wordpress: { name: 'Design Virtuoso', icon: '🎨', color: '#FFD700' },
      web_development: { name: 'Performance Expert', icon: '⚡', color: '#C0C0C0' },
      customer_service: { name: 'Service Concierge', icon: '💝', color: '#E8B4B8' },
      seo_marketing: { name: 'Marketing Maven', icon: '📈', color: '#FFD700' },
      security: { name: 'Brand Guardian', icon: '🛡️', color: '#000000' },
      performance: { name: 'Speed Specialist', icon: '⚡', color: '#C0C0C0' }
    }
    return agentMap[agentType] || { name: 'Fashion Specialist', icon: '🤖', color: '#E8B4B8' }
  }

  const handleStatusUpdate = async (newStatus) => {
    setIsUpdating(true)
    try {
      await onUpdate({ status: newStatus })
    } catch (error) {
      console.error('Failed to update task:', error)
    } finally {
      setIsUpdating(false)
    }
  }

  const agentInfo = getAgentInfo(task.agent_type)

  return (
    <motion.div
      className={`fashion-card cursor-pointer transition-all duration-300 border-l-4 ${getRiskColor(task.risk_level)}`}
      whileHover={{ y: -3, scale: 1.02 }}
      onClick={onClick}
      layout
    >
      {/* Task Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span
              className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-elegant"
              style={{ backgroundColor: agentInfo.color }}
            >
              {agentInfo.icon}
            </span>
            <span className="text-sm text-gray-600">{agentInfo.name}</span>
          </div>
          
          <h3 className="text-lg font-fashion font-bold text-gray-800 mb-2 line-clamp-2">
            {task.title}
          </h3>
          
          <p className="text-sm text-gray-600 line-clamp-2">
            {task.description}
          </p>
        </div>

        {/* Priority Badge */}
        <div className={`px-3 py-1 rounded-full text-white text-xs font-bold uppercase tracking-wide ${getPriorityColor(task.priority)}`}>
          {task.priority}
        </div>
      </div>

      {/* Risk and Timeline */}
      <div className="flex items-center justify-between mb-4">
        <div className={`risk-indicator risk-${task.risk_level}`}>
          <span className="mr-1">
            {task.risk_level === 'critical' ? '🚨' : 
             task.risk_level === 'high' ? '⚠️' : 
             task.risk_level === 'medium' ? '📊' : '✅'}
          </span>
          {task.risk_level} risk
        </div>
        
        <div className="text-sm text-gray-500">
          <span className="mr-1">⏰</span>
          {task.estimated_completion_time}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>Progress</span>
          <span>{task.status === 'completed' ? '100%' : task.status === 'in_progress' ? '60%' : '0%'}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className={`h-2 rounded-full ${
              task.status === 'completed' ? 'bg-green-500' :
              task.status === 'in_progress' ? 'bg-luxury-gold' : 'bg-gray-400'
            }`}
            initial={{ width: 0 }}
            animate={{ 
              width: task.status === 'completed' ? '100%' : 
                     task.status === 'in_progress' ? '60%' : '10%' 
            }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Pros and Cons Preview */}
      {(task.pros || task.cons) && (
        <div className="mb-4 space-y-2">
          {task.pros && task.pros.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-green-700 mb-1">✓ Key Benefits</div>
              <div className="text-xs text-gray-600">
                {task.pros.slice(0, 2).join(' • ')}
                {task.pros.length > 2 && '...'}
              </div>
            </div>
          )}
          
          {task.cons && task.cons.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-red-700 mb-1">⚠ Considerations</div>
              <div className="text-xs text-gray-600">
                {task.cons.slice(0, 2).join(' • ')}
                {task.cons.length > 2 && '...'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Expanded Details */}
      {(showDetails || isExpanded) && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.3 }}
          className="border-t border-gray-200 pt-4 mt-4"
        >
          {/* Full Pros and Cons */}
          {task.pros && task.pros.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-green-700 mb-2 flex items-center">
                <span className="mr-2">✅</span>
                Advantages
              </h4>
              <ul className="space-y-1">
                {task.pros.map((pro, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-green-500 mr-2 mt-1">+</span>
                    {pro}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {task.cons && task.cons.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-red-700 mb-2 flex items-center">
                <span className="mr-2">⚠️</span>
                Risks & Considerations
              </h4>
              <ul className="space-y-1">
                {task.cons.map((con, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-red-500 mr-2 mt-1">-</span>
                    {con}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risk Factors */}
          {task.risk_factors && task.risk_factors.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-orange-700 mb-2 flex items-center">
                <span className="mr-2">🎯</span>
                Risk Factors
              </h4>
              <div className="flex flex-wrap gap-2">
                {task.risk_factors.map((factor, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs border border-orange-200"
                  >
                    {factor.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Mitigation Strategies */}
          {task.mitigation_strategies && task.mitigation_strategies.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-blue-700 mb-2 flex items-center">
                <span className="mr-2">🛡️</span>
                Mitigation Strategies
              </h4>
              <ul className="space-y-2">
                {task.mitigation_strategies.map((strategy, index) => (
                  <li key={index} className="text-sm">
                    <div className="font-medium text-gray-800">{strategy.strategy}</div>
                    <div className="text-gray-600">{strategy.description}</div>
                    <div className="flex space-x-4 text-xs text-gray-500 mt-1">
                      <span>Effectiveness: {strategy.effectiveness}</span>
                      <span>Time: {strategy.implementation_time}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-2 mt-4">
        {task.status === 'pending' && (
          <button
            className="flex-1 bg-luxury-gradient text-white py-2 px-4 rounded-lg font-medium hover:shadow-gold-glow transition-all duration-300 disabled:opacity-50"
            onClick={(e) => {
              e.stopPropagation()
              handleStatusUpdate('in_progress')
            }}
            disabled={isUpdating}
          >
            {isUpdating ? '⏳' : '▶️'} Start Task
          </button>
        )}
        
        {task.status === 'in_progress' && (
          <button
            className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-600 transition-all duration-300 disabled:opacity-50"
            onClick={(e) => {
              e.stopPropagation()
              handleStatusUpdate('completed')
            }}
            disabled={isUpdating}
          >
            {isUpdating ? '⏳' : '✅'} Complete
          </button>
        )}

        {task.status === 'completed' && (
          <div className="flex-1 bg-green-100 text-green-800 py-2 px-4 rounded-lg font-medium text-center border border-green-200">
            ✅ Completed
          </div>
        )}

        <button
          className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all duration-300"
          onClick={(e) => {
            e.stopPropagation()
            // Handle edit or more options
          }}
        >
          ⚙️
        </button>
      </div>

      {/* Click hint for non-expanded cards */}
      {!isExpanded && !showDetails && (
        <div className="text-center mt-3 text-xs text-gray-500">
          Click for detailed analysis
        </div>
      )}
    </motion.div>
  )
}

export default TaskCard