import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import SocialMediaAutomation from './SocialMediaAutomation'
import EmailAutomation from './EmailAutomation'
import SMSAutomation from './SMSAutomation'
import LuxuryThemeBuilder from './LuxuryThemeBuilder'

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_BACKEND_URL || '/api'

const AutomationDashboard = () => {
  const [currentTab, setCurrentTab] = useState('overview')
  const [automationStats, setAutomationStats] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAutomationStats()
  }, [])

  const fetchAutomationStats = async () => {
    try {
      setLoading(true)
      
      // Mock comprehensive automation stats
      setAutomationStats({
        overview: {
          total_revenue: 285600,
          monthly_growth: 34.5,
          active_campaigns: 23,
          conversion_rate: 12.8,
          roi: 485
        },
        channels: {
          social_media: {
            platforms: 4,
            followers: 187500,
            engagement_rate: 8.7,
            revenue: 89400,
            growth: 28.3
          },
          email: {
            subscribers: 28450,
            open_rate: 47.2,
            click_rate: 10.4,
            revenue: 126800,
            growth: 12.5
          },
          sms: {
            subscribers: 18450,
            delivery_rate: 99.5,
            click_rate: 21.3,
            revenue: 69400,
            growth: 18.7
          }
        },
        automations: {
          active_flows: 18,
          total_triggers: 156,
          success_rate: 94.2,
          time_saved: 240 // hours per month
        }
      })
      
    } catch (error) {
      console.error('Failed to fetch automation stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'overview', name: 'Empire Overview', icon: '👑' },
    { id: 'social', name: 'Social Media', icon: '📱' },
    { id: 'email', name: 'Email Marketing', icon: '📧' },
    { id: 'sms', name: 'SMS Marketing', icon: '💬' },
    { id: 'theme', name: 'Theme Builder', icon: '🎨' }
  ]

  const quickActions = [
    {
      title: 'Launch Social Campaign',
      description: 'Create viral streetwear content',
      action: 'social_campaign',
      color: 'from-pink-500 to-purple-600',
      icon: '🚀'
    },
    {
      title: 'Send VIP Email',
      description: 'Exclusive drop notification',
      action: 'vip_email',
      color: 'from-blue-500 to-indigo-600',
      icon: '👑'
    },
    {
      title: 'SMS Flash Sale',
      description: '2-hour exclusive sale',
      action: 'flash_sms',
      color: 'from-emerald-500 to-green-600',
      icon: '⚡'
    },
    {
      title: 'Deploy New Theme',
      description: 'Update site design',
      action: 'deploy_theme',
      color: 'from-rose-gold to-luxury-gold',
      icon: '🎨'
    }
  ]

  const executeQuickAction = async (action) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/automation/quick-action`, {
        action: action,
        brand_style: 'luxury_streetwear'
      })
      
      alert(`✅ ${action.replace('_', ' ')} executed successfully!`)
      fetchAutomationStats()
    } catch (error) {
      console.error('Failed to execute action:', error)
      alert(`❌ Failed to execute ${action.replace('_', ' ')}. Please try again.`)
    }
  }

  if (currentTab === 'social') return <SocialMediaAutomation />
  if (currentTab === 'email') return <EmailAutomation />
  if (currentTab === 'sms') return <SMSAutomation />
  if (currentTab === 'theme') return <LuxuryThemeBuilder />

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
          Luxury Automation Empire
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-4xl mx-auto">
          Complete marketing automation for your luxury streetwear brand. Social media, email, SMS, and premium WordPress themes - all powered by AI.
        </p>
      </motion.div>

      {/* Navigation Tabs */}
      <motion.div
        className="bg-white rounded-3xl p-2 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <div className="flex space-x-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`flex items-center space-x-3 px-6 py-4 rounded-2xl font-semibold transition-all duration-300 whitespace-nowrap ${
                currentTab === tab.id
                  ? 'bg-gradient-to-r from-rose-gold to-luxury-gold text-white shadow-luxury'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-rose-gold/10'
              }`}
            >
              <span className="text-2xl">{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Overview Stats */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: { staggerChildren: 0.1 }
        }}
      >
        <motion.div
          className="bg-gradient-to-br from-emerald-100 to-green-100 rounded-3xl p-6 shadow-luxury border border-emerald-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">💰</div>
            <div className="text-3xl font-bold text-emerald-700">${automationStats.overview?.total_revenue?.toLocaleString()}</div>
            <div className="text-sm text-gray-600">Total Revenue</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              ↗️ +{automationStats.overview?.monthly_growth}%
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-blue-100 to-indigo-100 rounded-3xl p-6 shadow-luxury border border-blue-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">🚀</div>
            <div className="text-3xl font-bold text-blue-700">{automationStats.overview?.active_campaigns}</div>
            <div className="text-sm text-gray-600">Active Campaigns</div>
            <div className="text-blue-600 text-sm font-semibold mt-1">
              Multi-channel
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-3xl p-6 shadow-luxury border border-purple-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">🎯</div>
            <div className="text-3xl font-bold text-purple-700">{automationStats.overview?.conversion_rate}%</div>
            <div className="text-sm text-gray-600">Conversion Rate</div>
            <div className="text-purple-600 text-sm font-semibold mt-1">
              Above industry avg
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-rose-gold/20 to-luxury-gold/20 rounded-3xl p-6 shadow-luxury border border-rose-gold/30"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">📈</div>
            <div className="text-3xl font-bold text-luxury-gold">{automationStats.overview?.roi}%</div>
            <div className="text-sm text-gray-600">ROI</div>
            <div className="text-luxury-gold text-sm font-semibold mt-1">
              Exceptional returns
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-gray-100 to-slate-100 rounded-3xl p-6 shadow-luxury border border-gray-200"
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">⚡</div>
            <div className="text-3xl font-bold text-gray-700">{automationStats.automations?.time_saved}h</div>
            <div className="text-sm text-gray-600">Time Saved</div>
            <div className="text-gray-600 text-sm font-semibold mt-1">
              Per month
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Channel Performance */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">Channel Performance</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(automationStats.channels || {}).map(([channel, data]) => (
            <div key={channel} className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 shadow-elegant hover:shadow-gold-glow transition-all duration-300">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-xl font-semibold text-gray-800 capitalize mb-1">
                    {channel.replace('_', ' ')}
                  </h4>
                  <div className="text-2xl">
                    {channel === 'social_media' && '📱'}
                    {channel === 'email' && '📧'}
                    {channel === 'sms' && '💬'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-600">${data.revenue?.toLocaleString()}</div>
                  <div className="text-sm text-emerald-600">+{data.growth}%</div>
                </div>
              </div>
              
              <div className="space-y-3">
                {channel === 'social_media' && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Platforms:</span>
                      <span className="font-semibold">{data.platforms}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Followers:</span>
                      <span className="font-semibold">{data.followers?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Engagement:</span>
                      <span className="font-semibold">{data.engagement_rate}%</span>
                    </div>
                  </>
                )}
                
                {channel === 'email' && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Subscribers:</span>
                      <span className="font-semibold">{data.subscribers?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Open Rate:</span>
                      <span className="font-semibold">{data.open_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Click Rate:</span>
                      <span className="font-semibold">{data.click_rate}%</span>
                    </div>
                  </>
                )}
                
                {channel === 'sms' && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Subscribers:</span>
                      <span className="font-semibold">{data.subscribers?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delivery:</span>
                      <span className="font-semibold">{data.delivery_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Click Rate:</span>
                      <span className="font-semibold">{data.click_rate}%</span>
                    </div>
                  </>
                )}
              </div>
              
              <button
                onClick={() => setCurrentTab(channel === 'social_media' ? 'social' : channel)}
                className="w-full mt-4 bg-gradient-to-r from-rose-gold to-luxury-gold text-white py-2 rounded-xl font-semibold hover:shadow-lg transition-all duration-300"
              >
                Manage {channel.replace('_', ' ')}
              </button>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        className="bg-gradient-to-br from-luxury-gold/10 to-rose-gold/10 rounded-3xl p-8 shadow-luxury border border-luxury-gold/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">Quick Actions</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => (
            <motion.div
              key={action.action}
              className={`bg-gradient-to-br ${action.color} p-6 rounded-2xl text-white shadow-luxury hover:shadow-gold-glow transition-all duration-300 cursor-pointer`}
              onClick={() => executeQuickAction(action.action)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="text-center">
                <div className="text-4xl mb-3">{action.icon}</div>
                <h4 className="text-lg font-semibold mb-2">{action.title}</h4>
                <p className="text-sm opacity-90">{action.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Automation Flows Status */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">Automation Status</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center bg-gradient-to-br from-emerald-50 to-green-50 rounded-2xl p-6 border border-emerald-200">
            <div className="text-3xl mb-3">🤖</div>
            <div className="text-2xl font-bold text-emerald-700">{automationStats.automations?.active_flows}</div>
            <div className="text-sm text-gray-600">Active Flows</div>
          </div>
          
          <div className="text-center bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-200">
            <div className="text-3xl mb-3">⚡</div>
            <div className="text-2xl font-bold text-blue-700">{automationStats.automations?.total_triggers}</div>
            <div className="text-sm text-gray-600">Total Triggers</div>
          </div>
          
          <div className="text-center bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-200">
            <div className="text-3xl mb-3">✅</div>
            <div className="text-2xl font-bold text-purple-700">{automationStats.automations?.success_rate}%</div>
            <div className="text-sm text-gray-600">Success Rate</div>
          </div>
          
          <div className="text-center bg-gradient-to-br from-rose-gold/20 to-luxury-gold/20 rounded-2xl p-6 border border-rose-gold/30">
            <div className="text-3xl mb-3">⏰</div>
            <div className="text-2xl font-bold text-luxury-gold">{automationStats.automations?.time_saved}h</div>
            <div className="text-sm text-gray-600">Time Saved</div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default AutomationDashboard