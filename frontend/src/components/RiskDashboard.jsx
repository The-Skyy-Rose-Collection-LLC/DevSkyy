import React, { useState } from 'react'
import { motion } from 'framer-motion'

const RiskDashboard = ({ risks, loading, onRefresh }) => {
  const [selectedRiskCategory, setSelectedRiskCategory] = useState(null)

  const getRiskColor = (level) => {
    const colors = {
      CRITICAL: { bg: 'bg-red-500', text: 'text-red-600', light: 'bg-red-50' },
      HIGH: { bg: 'bg-orange-500', text: 'text-orange-600', light: 'bg-orange-50' },
      MEDIUM: { bg: 'bg-yellow-500', text: 'text-yellow-600', light: 'bg-yellow-50' },
      LOW: { bg: 'bg-green-500', text: 'text-green-600', light: 'bg-green-50' }
    }
    return colors[level] || colors.MEDIUM
  }

  const riskCategories = [
    {
      id: 'security',
      name: 'Brand Security',
      icon: '🛡️',
      description: 'Cybersecurity and brand protection',
      risk_level: 'LOW',
      impact: 'Brand reputation and customer trust',
      mitigation: 'Advanced threat detection active'
    },
    {
      id: 'performance',
      name: 'Site Performance', 
      icon: '⚡',
      description: 'Speed and user experience',
      risk_level: 'MEDIUM',
      impact: 'Customer satisfaction and conversions',
      mitigation: 'Performance monitoring and optimization'
    },
    {
      id: 'financial',
      name: 'Financial Operations',
      icon: '💰',
      description: 'Payment processing and fraud',
      risk_level: 'LOW',
      impact: 'Revenue and transaction security',
      mitigation: 'Multi-layer fraud protection'
    },
    {
      id: 'compliance',
      name: 'Regulatory Compliance',
      icon: '📋',
      description: 'GDPR, PCI DSS, and industry standards',
      risk_level: 'LOW', 
      impact: 'Legal and operational continuity',
      mitigation: 'Continuous compliance monitoring'
    },
    {
      id: 'customer',
      name: 'Customer Experience',
      icon: '💝',
      description: 'Service quality and satisfaction',
      risk_level: 'MEDIUM',
      impact: 'Customer retention and brand loyalty',
      mitigation: 'AI-powered service optimization'
    },
    {
      id: 'inventory',
      name: 'Asset Management',
      icon: '💎',
      description: 'Digital assets and inventory',
      risk_level: 'LOW',
      impact: 'Operational efficiency',
      mitigation: 'Automated asset optimization'
    }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-16 h-16 border-4 border-elegant-silver border-t-rose-gold rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-gray-600 font-elegant">Analyzing risk landscape...</p>
        </motion.div>
      </div>
    )
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
        <h2 className="text-4xl font-fashion font-bold bg-gradient-to-r from-elegant-silver via-rose-gold to-luxury-gold bg-clip-text text-transparent mb-4">
          Risk Protection Suite
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-2xl mx-auto">
          Your comprehensive risk management dashboard, designed to protect and preserve your luxury brand's integrity across all operational dimensions.
        </p>
      </motion.div>

      {/* Overall Risk Summary */}
      <motion.div
        className="fashion-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <div className="text-center mb-6">
          <h3 className="text-2xl font-fashion font-bold text-gray-800 mb-2">
            Overall Risk Status
          </h3>
          <div className={`inline-flex items-center px-6 py-3 rounded-full text-lg font-bold ${getRiskColor(risks.overall_risk_level || 'MEDIUM').bg} text-white shadow-elegant`}>
            <span className="mr-2">
              {risks.overall_risk_level === 'CRITICAL' ? '🚨' : 
               risks.overall_risk_level === 'HIGH' ? '⚠️' : 
               risks.overall_risk_level === 'MEDIUM' ? '📊' : '✅'}
            </span>
            {risks.overall_risk_level || 'MEDIUM'} RISK
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { label: 'Critical', value: risks.critical_risks || 0, color: 'text-red-600', bg: 'bg-red-100' },
            { label: 'High', value: risks.high_risks || 0, color: 'text-orange-600', bg: 'bg-orange-100' },
            { label: 'Medium', value: risks.medium_risks || 0, color: 'text-yellow-600', bg: 'bg-yellow-100' },
            { label: 'Low', value: risks.low_risks || 0, color: 'text-green-600', bg: 'bg-green-100' }
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              className={`text-center p-4 rounded-xl ${stat.bg} border border-gray-200`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
            >
              <div className={`text-3xl font-bold ${stat.color} mb-1`}>{stat.value}</div>
              <div className="text-sm font-medium text-gray-700">{stat.label} Risk</div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Risk Categories Grid */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
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
        {riskCategories.map((category, index) => (
          <motion.div
            key={category.id}
            className={`fashion-card cursor-pointer transition-all duration-300 border-l-4 ${getRiskColor(category.risk_level).light} hover:shadow-gold-glow ${
              selectedRiskCategory === category.id ? 'ring-2 ring-luxury-gold' : ''
            }`}
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
            whileHover={{ y: -5, scale: 1.02 }}
            onClick={() => setSelectedRiskCategory(
              selectedRiskCategory === category.id ? null : category.id
            )}
          >
            {/* Category Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-luxury-gradient rounded-full flex items-center justify-center text-2xl shadow-elegant">
                  {category.icon}
                </div>
                <div>
                  <h3 className="font-fashion font-bold text-gray-800 text-lg">
                    {category.name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {category.description}
                  </p>
                </div>
              </div>
              
              <div className={`px-3 py-1 rounded-full text-xs font-bold ${getRiskColor(category.risk_level).bg} text-white`}>
                {category.risk_level}
              </div>
            </div>

            {/* Risk Details */}
            <div className="space-y-3">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-1 flex items-center">
                  <span className="mr-2">💥</span>
                  Potential Impact
                </h4>
                <p className="text-sm text-gray-600">{category.impact}</p>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-1 flex items-center">
                  <span className="mr-2">🛡️</span>
                  Active Mitigation
                </h4>
                <p className="text-sm text-gray-600">{category.mitigation}</p>
              </div>
            </div>

            {/* Risk Health Bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>Risk Health</span>
                <span>{category.risk_level === 'LOW' ? '95%' : category.risk_level === 'MEDIUM' ? '75%' : '50%'}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <motion.div
                  className={`h-2 rounded-full ${
                    category.risk_level === 'LOW' ? 'bg-green-500' :
                    category.risk_level === 'MEDIUM' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ 
                    width: category.risk_level === 'LOW' ? '95%' : 
                           category.risk_level === 'MEDIUM' ? '75%' : '50%' 
                  }}
                  transition={{ duration: 1, delay: index * 0.1 }}
                />
              </div>
            </div>

            {/* Click hint */}
            <div className="text-center mt-3 text-xs text-gray-500">
              Click for detailed analysis
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Automated Risk Mitigation Status */}
      <motion.div
        className="fashion-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <h3 className="text-xl font-fashion font-bold text-gray-800 mb-6 flex items-center">
          <span className="mr-3">🤖</span>
          Automated Risk Response System
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-xl border border-green-200">
            <div className="text-3xl font-bold text-green-600 mb-2">12</div>
            <div className="text-sm font-medium text-gray-700">Active Mitigations</div>
            <div className="text-xs text-gray-500 mt-1">Running continuously</div>
          </div>

          <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-200">
            <div className="text-3xl font-bold text-blue-600 mb-2">5</div>
            <div className="text-sm font-medium text-gray-700">Scheduled Actions</div>
            <div className="text-xs text-gray-500 mt-1">Planned for execution</div>
          </div>

          <div className="text-center p-4 bg-luxury-gold/10 rounded-xl border border-luxury-gold/30">
            <div className="text-3xl font-bold text-luxury-gold mb-2">8</div>
            <div className="text-sm font-medium text-gray-700">Resolved Today</div>
            <div className="text-xs text-gray-500 mt-1">Successfully mitigated</div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-rose-gold/10 rounded-xl border border-rose-gold/20">
          <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
            <span className="mr-2">⚡</span>
            Recent Automated Actions
          </h4>
          <div className="space-y-2">
            {[
              { time: '2 min ago', action: 'Blocked suspicious IP attempting credential stuffing', status: 'resolved' },
              { time: '15 min ago', action: 'Optimized image compression for better page speed', status: 'completed' },
              { time: '1 hour ago', action: 'Updated security headers for enhanced protection', status: 'completed' },
              { time: '3 hours ago', action: 'Cleaned duplicate assets to improve storage efficiency', status: 'completed' }
            ].map((action, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-gray-700">{action.action}</span>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">{action.time}</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    action.status === 'resolved' ? 'bg-green-100 text-green-800' : 
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {action.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Risk Trends */}
      <motion.div
        className="fashion-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <h3 className="text-xl font-fashion font-bold text-gray-800 mb-6 flex items-center">
          <span className="mr-3">📈</span>
          Risk Trend Analysis
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-green-50 rounded-xl border border-green-200">
            <h4 className="font-semibold text-green-800 mb-2 flex items-center">
              <span className="mr-2">📉</span>
              Improving
            </h4>
            <div className="space-y-1">
              <div className="text-sm text-gray-700">• Site Performance</div>
              <div className="text-sm text-gray-700">• Security Posture</div>
              <div className="text-sm text-gray-700">• Compliance Status</div>
            </div>
          </div>

          <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
              <span className="mr-2">📊</span>
              Stable
            </h4>
            <div className="space-y-1">
              <div className="text-sm text-gray-700">• Customer Experience</div>
              <div className="text-sm text-gray-700">• Asset Management</div>
              <div className="text-sm text-gray-700">• Financial Operations</div>
            </div>
          </div>

          <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
            <h4 className="font-semibold text-yellow-800 mb-2 flex items-center">
              <span className="mr-2">👁️</span>
              Monitoring
            </h4>
            <div className="space-y-1">
              <div className="text-sm text-gray-700">• Market Competition</div>
              <div className="text-sm text-gray-700">• Revenue Optimization</div>
              <div className="text-sm text-gray-700">• Brand Positioning</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Refresh Button */}
      <motion.div
        className="text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.6 }}
      >
        <button
          className="luxury-button"
          onClick={onRefresh}
        >
          <span className="mr-2">🔄</span>
          Refresh Risk Analysis
        </button>
      </motion.div>
    </div>
  )
}

export default RiskDashboard