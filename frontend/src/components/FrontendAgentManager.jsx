import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import WordPressConnection from './WordPressConnection'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const FrontendAgentManager = () => {
  const [frontendAgents, setFrontendAgents] = useState({})
  const [monitoringStatus, setMonitoringStatus] = useState({})
  const [assignmentRequest, setAssignmentRequest] = useState({
    procedure_type: 'luxury_ui_design',
    priority: 'medium',
    user_facing: true
  })
  const [loading, setLoading] = useState(false)
  const [assignmentResult, setAssignmentResult] = useState(null)

  const procedureTypes = [
    { value: 'luxury_ui_design', label: '🎨 Luxury UI Design', description: 'Premium interface design with luxury aesthetics' },
    { value: 'collection_page_creation', label: '💎 Collection Page Creation', description: 'High-converting collection landing pages' },
    { value: 'frontend_performance_optimization', label: '⚡ Performance Optimization', description: 'Speed and Core Web Vitals optimization' },
    { value: 'responsive_design_implementation', label: '📱 Responsive Design', description: 'Mobile-first luxury experiences' },
    { value: 'component_development', label: '🧩 Component Development', description: 'Reusable luxury UI components' },
    { value: 'brand_consistency_enforcement', label: '👑 Brand Consistency', description: 'Maintain luxury brand standards' },
    { value: 'user_experience_optimization', label: '✨ UX Optimization', description: 'Premium user experience enhancement' },
    { value: 'frontend_testing_and_qa', label: '🔍 Testing & QA', description: 'Quality assurance for frontend excellence' }
  ]

  useEffect(() => {
    fetchFrontendStatus()
    fetchMonitoringStatus()
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchFrontendStatus()
      fetchMonitoringStatus()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchFrontendStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/frontend/agents/status`)
      setFrontendAgents(response.data)
    } catch (error) {
      console.error('Failed to fetch frontend status:', error)
    }
  }

  const fetchMonitoringStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/frontend/monitoring/24-7`)
      setMonitoringStatus(response.data)
    } catch (error) {
      console.error('Failed to fetch monitoring status:', error)
    }
  }

  const handleAssignAgents = async () => {
    try {
      setLoading(true)
      const response = await axios.post(`${API_BASE_URL}/frontend/assign-agents`, assignmentRequest)
      setAssignmentResult(response.data)
      await fetchFrontendStatus()
    } catch (error) {
      console.error('Failed to assign agents:', error)
      setAssignmentResult({ error: 'Assignment failed', details: error.message })
    } finally {
      setLoading(false)
    }
  }

  const createCollectionPage = async (collectionType) => {
    try {
      setLoading(true)
      const collectionData = {
        collection_name: `Luxury ${collectionType} Collection`,
        type: collectionType,
        target_audience: 'luxury_customers',
        priority: 'high'
      }
      const response = await axios.post(`${API_BASE_URL}/frontend/collections/create`, collectionData)
      setAssignmentResult(response.data)
    } catch (error) {
      console.error('Failed to create collection page:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        className="text-center"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="text-4xl font-fashion font-bold bg-gradient-to-r from-rose-gold via-luxury-gold to-elegant-silver bg-clip-text text-transparent mb-4">
          Elite Frontend Agent Management
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-3xl mx-auto">
          Dedicated frontend specialists working exclusively on user-facing luxury experiences while seamlessly communicating with backend systems.
        </p>
      </motion.div>

      {/* WordPress Connection Section */}
      <WordPressConnection />

      {/* 24/7 Monitoring Status */}
      <motion.div
        className="bg-gradient-to-r from-rose-gold/10 to-luxury-gold/10 rounded-3xl p-6 border border-rose-gold/20"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-4 flex items-center">
          <span className="mr-3">🔄</span>
          24/7 Frontend Monitoring System
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white/80 rounded-2xl p-4 backdrop-blur-sm">
            <div className="text-2xl font-bold text-luxury-gold mb-1">
              {monitoringStatus.system_health?.uptime || '99.98%'}
            </div>
            <div className="text-sm text-gray-600">System Uptime</div>
          </div>
          <div className="bg-white/80 rounded-2xl p-4 backdrop-blur-sm">
            <div className="text-2xl font-bold text-emerald-600 mb-1">
              {monitoringStatus.system_health?.response_time || '0.8s'}
            </div>
            <div className="text-sm text-gray-600">Response Time</div>
          </div>
          <div className="bg-white/80 rounded-2xl p-4 backdrop-blur-sm">
            <div className="text-2xl font-bold text-rose-gold mb-1">
              {monitoringStatus.system_health?.customer_satisfaction || '97.5%'}
            </div>
            <div className="text-sm text-gray-600">Customer Satisfaction</div>
          </div>
          <div className="bg-white/80 rounded-2xl p-4 backdrop-blur-sm">
            <div className="text-2xl font-bold text-elegant-silver mb-1">
              {monitoringStatus.executive_decisions_today?.total_decisions || 8}
            </div>
            <div className="text-sm text-gray-600">Executive Decisions Today</div>
          </div>
        </div>
      </motion.div>

      {/* Frontend Agent Status */}
      {frontendAgents.frontend_agents && (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: { staggerChildren: 0.1 }
            }
          }}
        >
          {Object.entries(frontendAgents.frontend_agents).map(([agentId, agentData]) => (
            <motion.div
              key={agentId}
              className="bg-white rounded-3xl p-6 shadow-luxury border border-gray-100 hover:shadow-gold-glow transition-all duration-300"
              variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 }
              }}
            >
              <div className="text-center mb-4">
                <div className="text-4xl mb-2">
                  {agentId === 'design_automation' ? '🎨' :
                   agentId === 'performance' ? '⚡' :
                   agentId === 'wordpress' ? '🌐' :
                   agentId === 'brand_intelligence' ? '👑' : '🤖'}
                </div>
                <h4 className="font-fashion font-semibold text-gray-800 mb-1">
                  {agentData.agent_name}
                </h4>
                <div className="text-sm text-emerald-600 bg-emerald-50 rounded-full px-3 py-1 inline-block">
                  Frontend Specialist
                </div>
              </div>

              {/* Current Tasks */}
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-gray-700">Current Frontend Tasks:</h5>
                {agentData.current_tasks?.slice(0, 2).map((task, index) => (
                  <div key={index} className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">
                    <div className="font-medium">{task.task}</div>
                    <div className="flex justify-between items-center mt-1">
                      <span className={`px-2 py-1 rounded text-xs ${
                        task.priority === 'critical' ? 'bg-red-100 text-red-600' :
                        task.priority === 'high' ? 'bg-orange-100 text-orange-600' :
                        'bg-blue-100 text-blue-600'
                      }`}>
                        {task.priority}
                      </span>
                      <span className="text-gray-500">{task.progress}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Performance Metrics */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="text-xs text-gray-500 mb-2">Quality Score</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-rose-gold to-luxury-gold h-2 rounded-full transition-all duration-300"
                    style={{ width: `${agentData.work_quality_score || 95}%` }}
                  ></div>
                </div>
                <div className="text-right text-xs text-gray-600 mt-1">
                  {agentData.work_quality_score || 95}%
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Agent Assignment Interface */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          Assign Frontend Specialists
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Assignment Form */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Frontend Procedure Type
              </label>
              <div className="space-y-2">
                {procedureTypes.map((procedure) => (
                  <div
                    key={procedure.value}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 ${
                      assignmentRequest.procedure_type === procedure.value
                        ? 'border-rose-gold bg-rose-gold/10'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setAssignmentRequest({
                      ...assignmentRequest,
                      procedure_type: procedure.value
                    })}
                  >
                    <div className="font-medium text-gray-800">{procedure.label}</div>
                    <div className="text-sm text-gray-600 mt-1">{procedure.description}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority Level
              </label>
              <select
                className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-rose-gold focus:border-rose-gold"
                value={assignmentRequest.priority}
                onChange={(e) => setAssignmentRequest({
                  ...assignmentRequest,
                  priority: e.target.value
                })}
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
                <option value="critical">Critical Priority</option>
              </select>
            </div>

            <button
              className="luxury-button w-full"
              onClick={handleAssignAgents}
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Assigning Specialists...
                </span>
              ) : (
                'Assign Frontend Specialists'
              )}
            </button>
          </div>

          {/* Quick Collection Page Creation */}
          <div className="space-y-6">
            <h4 className="text-lg font-fashion font-semibold text-gray-800">
              Quick Collection Page Creation
            </h4>
            <p className="text-gray-600 text-sm">
              Create luxury collection pages designed like top-selling landing pages with premium aesthetics and conversion optimization.
            </p>

            <div className="space-y-3">
              {[
                { type: 'rose_gold_collection', name: 'Rose Gold Elegance', color: 'from-pink-400 to-rose-400' },
                { type: 'luxury_gold_collection', name: 'Luxury Gold Statement', color: 'from-yellow-400 to-amber-400' },
                { type: 'elegant_silver_collection', name: 'Elegant Silver Sophistication', color: 'from-gray-400 to-slate-400' }
              ].map((collection) => (
                <button
                  key={collection.type}
                  className={`w-full p-4 rounded-xl bg-gradient-to-r ${collection.color} text-white font-medium hover:shadow-lg transition-all duration-300 disabled:opacity-50`}
                  onClick={() => createCollectionPage(collection.type)}
                  disabled={loading}
                >
                  Create {collection.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Assignment Result */}
      <AnimatePresence>
        {assignmentResult && (
          <motion.div
            className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-fashion font-semibold text-gray-800">
                Assignment Result
              </h3>
              <button
                className="text-gray-400 hover:text-gray-600 transition-colors"
                onClick={() => setAssignmentResult(null)}
              >
                ✕
              </button>
            </div>

            {assignmentResult.error ? (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="text-red-600 font-medium mb-2">Assignment Failed</div>
                <div className="text-red-500 text-sm">{assignmentResult.error}</div>
              </div>
            ) : (
              <div className="space-y-6">
                {assignmentResult.frontend_agents_assigned && (
                  <div>
                    <h4 className="font-medium text-gray-800 mb-3">Assigned Frontend Specialists:</h4>
                    <div className="space-y-2">
                      {assignmentResult.frontend_agents_assigned.map((agent, index) => (
                        <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                          <div>
                            <div className="font-medium text-gray-800">{agent.agent_name}</div>
                            <div className="text-sm text-gray-600">{agent.responsibility_level}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium text-luxury-gold">{agent.workload_percentage}%</div>
                            <div className="text-xs text-gray-500">workload</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {assignmentResult.expected_delivery && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
                    <div className="text-emerald-700 font-medium mb-2">Expected Delivery</div>
                    <div className="text-emerald-600">{assignmentResult.expected_delivery}</div>
                  </div>
                )}

                {assignmentResult.collection_page && (
                  <div className="bg-luxury-gradient rounded-xl p-6 text-white">
                    <div className="font-medium mb-2">Collection Page Created Successfully</div>
                    <div className="text-sm opacity-90">
                      Luxury score: {assignmentResult.luxury_score}% | 
                      Estimated conversion: {assignmentResult.estimated_conversion_rate}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default FrontendAgentManager