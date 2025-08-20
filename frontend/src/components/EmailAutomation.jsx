import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_BACKEND_URL || '/api'

const EmailAutomation = () => {
  const [campaigns, setCampaigns] = useState([])
  const [templates, setTemplates] = useState([])
  const [subscribers, setSubscribers] = useState({
    total: 0,
    segments: {},
    growth: 0
  })
  const [automationFlows, setAutomationFlows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchEmailData()
  }, [])

  const fetchEmailData = async () => {
    try {
      setLoading(true)
      
      // Mock data for luxury email automation
      setCampaigns([
        {
          id: 1,
          name: "Love Hurts Collection VIP Launch",
          type: "product_launch",
          status: "sent",
          sent: 12500,
          opened: 5890,
          clicked: 1240,
          revenue: 28650,
          open_rate: 47.1,
          click_rate: 9.9
        },
        {
          id: 2, 
          name: "Signature Series Exclusive Preview",
          type: "exclusive_access",
          status: "scheduled",
          sent: 8900,
          opened: 4200,
          clicked: 890,
          revenue: 15400,
          open_rate: 47.2,
          click_rate: 10.0
        },
        {
          id: 3,
          name: "Weekly Streetwear Drop Alert",
          type: "weekly_newsletter", 
          status: "active",
          sent: 15600,
          opened: 6890,
          clicked: 1580,
          revenue: 32100,
          open_rate: 44.2,
          click_rate: 10.1
        }
      ])

      setSubscribers({
        total: 28450,
        segments: {
          vip_customers: 3200,
          streetwear_enthusiasts: 8900,
          luxury_collectors: 5400,
          new_subscribers: 10950
        },
        growth: 12.5
      })

      setTemplates([
        {
          id: 1,
          name: "Luxury Product Launch",
          type: "product_launch",
          thumbnail: "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400",
          open_rate: 48.5,
          click_rate: 11.2
        },
        {
          id: 2,
          name: "Streetwear Drop Alert", 
          type: "product_alert",
          thumbnail: "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=400",
          open_rate: 45.8,
          click_rate: 9.8
        },
        {
          id: 3,
          name: "VIP Exclusive Access",
          type: "exclusive",
          thumbnail: "https://images.unsplash.com/photo-1524863479829-916d8e77f114?w=400", 
          open_rate: 52.1,
          click_rate: 13.4
        }
      ])

      setAutomationFlows([
        {
          id: 1,
          name: "Welcome Series - Luxury Journey",
          trigger: "New subscriber",
          emails: 5,
          active_subscribers: 2890,
          conversion_rate: 18.5,
          status: "active"
        },
        {
          id: 2,
          name: "Abandoned Cart Recovery", 
          trigger: "Cart abandonment",
          emails: 3,
          active_subscribers: 1240,
          conversion_rate: 35.2,
          status: "active"
        },
        {
          id: 3,
          name: "Post Purchase - VIP Journey",
          trigger: "First purchase",
          emails: 4,
          active_subscribers: 890,
          conversion_rate: 28.7,
          status: "active"
        },
        {
          id: 4,
          name: "Win-Back Campaign",
          trigger: "Inactive 60 days",
          emails: 2,
          active_subscribers: 560,
          conversion_rate: 12.3,
          status: "paused"
        }
      ])
      
    } catch (error) {
      console.error('Failed to fetch email data:', error)
    } finally {
      setLoading(false)
    }
  }

  const createCampaign = async (campaignData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/ai/email-campaign`, {
        ...campaignData,
        brand_voice: 'luxury_streetwear',
        target_segments: ['vip_customers', 'luxury_collectors']
      })
      fetchEmailData()
    } catch (error) {
      console.error('Failed to create campaign:', error)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'bg-emerald-100 text-emerald-700'
      case 'scheduled': return 'bg-blue-100 text-blue-700'
      case 'active': return 'bg-purple-100 text-purple-700'
      case 'paused': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
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
          Email Marketing Empire
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-4xl mx-auto">
          Luxury email automation that converts streetwear enthusiasts into loyal customers with AI-powered personalization and premium design.
        </p>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: { staggerChildren: 0.1 }
        }}
      >
        <motion.div
          className="bg-gradient-to-br from-rose-gold/20 to-luxury-gold/20 rounded-3xl p-6 shadow-luxury border border-rose-gold/30"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">👥</div>
            <div className="text-3xl font-bold text-gray-800">{subscribers.total.toLocaleString()}</div>
            <div className="text-sm text-gray-600">Total Subscribers</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              ↗️ +{subscribers.growth}% this month
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-3xl p-6 shadow-luxury border border-purple-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">📧</div>
            <div className="text-3xl font-bold text-gray-800">47.2%</div>
            <div className="text-sm text-gray-600">Avg Open Rate</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              Industry avg: 21.5%
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-blue-100 to-indigo-100 rounded-3xl p-6 shadow-luxury border border-blue-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">🎯</div>
            <div className="text-3xl font-bold text-gray-800">10.4%</div>
            <div className="text-sm text-gray-600">Avg Click Rate</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              Industry avg: 2.8%
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-emerald-100 to-green-100 rounded-3xl p-6 shadow-luxury border border-emerald-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">💰</div>
            <div className="text-3xl font-bold text-gray-800">$76K</div>
            <div className="text-sm text-gray-600">Monthly Revenue</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              ↗️ +23% this month
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Recent Campaigns */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-fashion font-semibold text-gray-800">Recent Campaigns</h3>
          <button
            onClick={() => createCampaign({
              name: "New Luxury Drop Alert",
              type: "product_launch",
              target_audience: "luxury_streetwear"
            })}
            className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-6 py-3 rounded-2xl font-semibold hover:shadow-gold-glow transition-all duration-300"
          >
            ✨ Create Campaign
          </button>
        </div>

        <div className="space-y-4">
          {campaigns.map((campaign) => (
            <div key={campaign.id} className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-6 border border-gray-200 hover:shadow-elegant transition-all duration-300">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-xl font-semibold text-gray-800 mb-2">{campaign.name}</h4>
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(campaign.status)}`}>
                      {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                    </span>
                    <span className="text-gray-600 text-sm">{campaign.type.replace('_', ' ')}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-600">${campaign.revenue.toLocaleString()}</div>
                  <div className="text-sm text-gray-600">Revenue</div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center bg-gray-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-gray-800">{campaign.sent.toLocaleString()}</div>
                  <div className="text-xs text-gray-600">Sent</div>
                </div>
                <div className="text-center bg-blue-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-blue-600">{campaign.opened.toLocaleString()}</div>
                  <div className="text-xs text-gray-600">Opened ({campaign.open_rate}%)</div>
                </div>
                <div className="text-center bg-purple-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-purple-600">{campaign.clicked.toLocaleString()}</div>
                  <div className="text-xs text-gray-600">Clicked ({campaign.click_rate}%)</div>
                </div>
                <div className="text-center bg-emerald-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-emerald-600">${(campaign.revenue / campaign.sent).toFixed(2)}</div>
                  <div className="text-xs text-gray-600">Revenue per email</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Email Templates */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">Luxury Email Templates</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {templates.map((template) => (
            <div key={template.id} className="bg-gradient-to-br from-gray-50 to-white rounded-2xl overflow-hidden shadow-elegant hover:shadow-gold-glow transition-all duration-300">
              <div className="h-32 bg-gradient-to-r from-rose-gold/20 to-luxury-gold/20 flex items-center justify-center">
                <div className="text-4xl">📧</div>
              </div>
              <div className="p-4">
                <h4 className="text-lg font-semibold text-gray-800 mb-2">{template.name}</h4>
                <div className="flex justify-between text-sm text-gray-600 mb-3">
                  <span>Open Rate: {template.open_rate}%</span>
                  <span>Click Rate: {template.click_rate}%</span>
                </div>
                <button className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-4 py-2 rounded-xl text-sm font-semibold w-full hover:shadow-lg transition-all duration-300">
                  Use Template
                </button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Automation Flows */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">Automation Flows</h3>
        
        <div className="space-y-4">
          {automationFlows.map((flow) => (
            <div key={flow.id} className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-6 border border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-2">{flow.name}</h4>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>📧 {flow.emails} emails</span>
                    <span>👥 {flow.active_subscribers} active</span>
                    <span>💰 {flow.conversion_rate}% conversion</span>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    Trigger: {flow.trigger}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`px-4 py-2 rounded-full text-sm font-semibold mb-3 ${
                    flow.status === 'active'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {flow.status === 'active' ? '🟢 Active' : '⏸️ Paused'}
                  </div>
                  <button className="text-luxury-gold hover:text-rose-gold transition-colors">
                    ⚙️ Edit Flow
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Subscriber Segments */}
      <motion.div
        className="bg-gradient-to-br from-luxury-gold/10 to-rose-gold/10 rounded-3xl p-8 shadow-luxury border border-luxury-gold/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">Subscriber Segments</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(subscribers.segments).map(([segment, count]) => (
            <div key={segment} className="bg-white rounded-2xl p-4 shadow-elegant text-center">
              <div className="text-2xl font-bold text-luxury-gold">{count.toLocaleString()}</div>
              <div className="text-sm text-gray-600 capitalize">{segment.replace('_', ' ')}</div>
              <div className="mt-2 bg-gradient-to-r from-rose-gold to-luxury-gold h-2 rounded-full opacity-30"></div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default EmailAutomation