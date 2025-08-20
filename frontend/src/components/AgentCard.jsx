import React from 'react'
import { motion } from 'framer-motion'

const AgentCard = ({ agentId, agentData, isSelected, isExpanded, showDetails, onClick }) => {
  const getHealthColor = (health) => {
    if (health >= 95) return 'text-green-600'
    if (health >= 90) return 'text-luxury-gold'
    if (health >= 80) return 'text-orange-500'
    return 'text-red-500'
  }

  const getHealthBadge = (health) => {
    if (health >= 95) return { text: 'Excellent', bg: 'bg-green-100', color: 'text-green-800' }
    if (health >= 90) return { text: 'Good', bg: 'bg-yellow-100', color: 'text-yellow-800' }
    if (health >= 80) return { text: 'Fair', bg: 'bg-orange-100', color: 'text-orange-800' }
    return { text: 'Needs Attention', bg: 'bg-red-100', color: 'text-red-800' }
  }

  const healthBadge = getHealthBadge(agentData.health)

  const agentPersonalities = {
    brand_intelligence: {
      title: "Brand Oracle & Trend Visionary",
      specialties: ["Luxury Brand Positioning", "Market Trend Analysis", "Competitive Intelligence", "Brand Evolution"],
      currentFocus: "Analyzing Spring 2025 fashion trends and competitor positioning",
      achievements: ["Predicted 3 major trend shifts", "Increased brand visibility by 45%", "Optimized luxury positioning"]
    },
    inventory: {
      title: "Digital Asset Curator", 
      specialties: ["Asset Optimization", "Duplicate Detection", "Storage Efficiency", "Quality Assurance"],
      currentFocus: "Optimizing 10,000+ fashion assets with AI-powered categorization",
      achievements: ["Saved 2.3TB storage space", "Improved asset retrieval by 60%", "Implemented smart tagging"]
    },
    financial: {
      title: "Luxury Commerce Strategist",
      specialties: ["Transaction Processing", "Fraud Prevention", "Revenue Optimization", "Financial Analytics"],
      currentFocus: "Processing high-value transactions with advanced security protocols", 
      achievements: ["Blocked 156 fraud attempts", "Maintained 0.5% chargeback rate", "Increased revenue by 28%"]
    },
    ecommerce: {
      title: "Customer Experience Architect",
      specialties: ["Conversion Optimization", "Personalization", "User Journey Design", "A/B Testing"],
      currentFocus: "Enhancing luxury customer journey with AI-powered recommendations",
      achievements: ["Boosted conversion rate by 35%", "Reduced cart abandonment", "Increased AOV by 42%"]
    },
    wordpress: {
      title: "Divi5 Design Virtuoso",
      specialties: ["Divi5 Mastery", "WordPress Optimization", "WooCommerce Integration", "Performance Tuning"],
      currentFocus: "Crafting pixel-perfect luxury layouts with Divi5 advanced features",
      achievements: ["Created 15+ premium layouts", "Improved page speed by 40%", "Enhanced mobile experience"]
    },
    web_development: {
      title: "Universal Web Development Guru",
      specialties: ["Multi-Language Mastery", "Full-Stack Optimization", "Universal Debugging", "Performance Engineering"],
      currentFocus: "Analyzing and optimizing code across all programming languages with AI-powered solutions",
      achievements: ["Fixed 500+ cross-language issues", "Achieved 95+ PageSpeed scores", "Reduced load time by 65%", "Mastered 20+ programming languages"]
    },
    performance: {
      title: "Universal Code & Performance Guru",
      specialties: ["Multi-Language Code Analysis", "Universal Debugging", "Full-Stack Optimization", "Performance Engineering"],
      currentFocus: "Providing comprehensive code analysis and optimization for any programming language",
      achievements: ["Mastered 20+ programming languages", "Fixed critical security vulnerabilities", "Achieved 44% performance improvements", "Implemented automated debugging systems"]
    },
    customer_service: {
      title: "Luxury Service Concierge",
      specialties: ["VIP Experience Design", "Service Excellence", "Customer Satisfaction", "Support Automation"],
      currentFocus: "Designing white-glove service experience for high-value customers",
      achievements: ["Maintained 4.8/5 satisfaction", "Reduced response time by 70%", "Improved retention by 25%"]
    },
    seo_marketing: {
      title: "Fashion Marketing Maven",
      specialties: ["SEO Strategy", "Content Marketing", "Social Media", "Influencer Relations"],
      currentFocus: "Optimizing for fashion week keywords and seasonal trends",
      achievements: ["Increased organic traffic by 120%", "Improved keyword rankings", "Built 500+ quality backlinks"]
    },
    security: {
      title: "Brand Protection Guardian",
      specialties: ["Cybersecurity", "Fraud Detection", "Brand Monitoring", "Compliance"],
      currentFocus: "Protecting luxury brand assets with advanced threat intelligence",
      achievements: ["Zero security incidents", "94.5% security score", "Blocked 23 brand impersonation attempts"]
    }
  }

  const agentProfile = agentPersonalities[agentId] || {
    title: "Fashion Specialist",
    specialties: ["General Expertise"],
    currentFocus: "Working on various fashion-related tasks",
    achievements: ["Consistent performance"]
  }

  return (
    <motion.div
      className={`fashion-card cursor-pointer transition-all duration-300 ${
        isSelected ? 'ring-2 ring-luxury-gold shadow-gold-glow' : ''
      } ${isExpanded ? 'max-w-none' : 'max-w-sm'}`}
      whileHover={{ y: -5, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      style={{ 
        background: isSelected 
          ? `linear-gradient(135deg, ${agentData.styling.color}20, white)` 
          : undefined 
      }}
    >
      {/* Agent Header */}
      <div className="flex items-start space-x-4 mb-4">
        <motion.div
          className="agent-avatar"
          style={{ backgroundColor: agentData.styling.color }}
          animate={{ rotate: [0, 5, -5, 0] }}
          transition={{ duration: 4, repeat: Infinity }}
        >
          {agentData.styling.icon}
        </motion.div>
        
        <div className="flex-1">
          <h3 className="text-xl font-fashion font-bold text-gray-800 mb-1">
            {agentProfile.title}
          </h3>
          <p className="text-sm text-gray-600 mb-2 capitalize">
            {agentData.status.replace(/_/g, ' ')}
          </p>
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${healthBadge.bg} ${healthBadge.color}`}>
            <div className="w-2 h-2 bg-current rounded-full mr-2 animate-pulse"></div>
            {healthBadge.text}
          </div>
        </div>

        <div className="text-right">
          <div className={`text-2xl font-bold ${getHealthColor(agentData.health)}`}>
            {agentData.health}%
          </div>
          <div className="text-xs text-gray-500">Health Score</div>
        </div>
      </div>

      {/* Current Focus */}
      <div className="mb-4 p-3 bg-rose-gold/10 rounded-xl border border-rose-gold/20">
        <h4 className="font-semibold text-gray-800 mb-1 flex items-center">
          <span className="mr-2">🎯</span>
          Current Focus
        </h4>
        <p className="text-sm text-gray-600">
          {agentProfile.currentFocus}
        </p>
      </div>

      {/* Task Statistics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-luxury-gold/10 rounded-xl">
          <div className="text-2xl font-bold text-luxury-gold">
            {agentData.current_tasks}
          </div>
          <div className="text-xs text-gray-600">Active Tasks</div>
        </div>
        <div className="text-center p-3 bg-green-100 rounded-xl">
          <div className="text-2xl font-bold text-green-600">
            {agentData.completed_today}
          </div>
          <div className="text-xs text-gray-600">Completed Today</div>
        </div>
      </div>

      {/* Expanded Details */}
      {(showDetails || isExpanded) && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.3 }}
          className="border-t border-gray-200 pt-4"
        >
          {/* Specialties */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
              <span className="mr-2">💎</span>
              Specialties
            </h4>
            <div className="flex flex-wrap gap-2">
              {agentProfile.specialties.map((specialty, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-elegant-silver/20 text-gray-700 rounded-full text-sm border border-elegant-silver/30"
                >
                  {specialty}
                </span>
              ))}
            </div>
          </div>

          {/* Recent Achievements */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
              <span className="mr-2">🏆</span>
              Recent Achievements
            </h4>
            <ul className="space-y-1">
              {agentProfile.achievements.map((achievement, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-luxury-gold mr-2 mt-1">•</span>
                  {achievement}
                </li>
              ))}
            </ul>
          </div>

          {/* Expertise Focus */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
              <span className="mr-2">🎨</span>
              Expertise Focus
            </h4>
            <div className="p-3 bg-gradient-to-r from-rose-gold/10 to-luxury-gold/10 rounded-xl border border-rose-gold/20">
              <p className="text-sm text-gray-700 font-medium">
                {agentData.expertise_focus.replace(/_/g, ' ').toUpperCase()}
              </p>
            </div>
          </div>

          {/* Personality Traits */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
              <span className="mr-2">✨</span>
              Personality
            </h4>
            <p className="text-sm text-gray-600 italic">
              "{agentData.styling.personality.replace(/_/g, ' ').toLowerCase()}"
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <button className="flex-1 bg-luxury-gradient text-white py-2 px-4 rounded-lg font-medium hover:shadow-gold-glow transition-all duration-300">
              View Tasks
            </button>
            <button 
              className="flex-1 bg-white border border-rose-gold text-rose-gold py-2 px-4 rounded-lg font-medium hover:bg-rose-gold hover:text-white transition-all duration-300"
              onClick={(e) => {
                e.stopPropagation()
                if (onClick) onClick('integrations')
              }}
            >
              🔗 Integrations
            </button>
          </div>
        </motion.div>
      )}

      {/* Hover Indicator */}
      {!isExpanded && (
        <div className="text-center mt-4 text-xs text-gray-500">
          Click to view detailed profile
        </div>
      )}
    </motion.div>
  )
}

export default AgentCard