import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_BACKEND_URL || '/api'

const WordPressConnection = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [authUrl, setAuthUrl] = useState('')
  const [siteInfo, setSiteInfo] = useState(null)
  const [agentStatus, setAgentStatus] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    checkConnectionStatus()
  }, [])

  const checkConnectionStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/wordpress/site/info`)
      if (response.data.site_info && !response.data.site_info.error) {
        setConnectionStatus('connected')
        setSiteInfo(response.data.site_info)
        setAgentStatus(response.data.performance_monitoring)
      }
    } catch (error) {
      // Not connected yet
      setConnectionStatus('disconnected')
    }
  }

  const getAuthUrl = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await axios.get(`${API_BASE_URL}/wordpress/auth-url`)
      setAuthUrl(response.data.auth_url)
      
      // Open WordPress authorization in new window
      const authWindow = window.open(
        response.data.auth_url,
        'wordpress_auth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      )
      
      // Listen for the auth completion
      const checkClosed = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkClosed)
          // Check if connection was successful
          setTimeout(() => {
            checkConnectionStatus()
          }, 2000)
        }
      }, 1000)
      
    } catch (error) {
      setError('Failed to get authorization URL')
      console.error('Auth URL error:', error)
    } finally {
      setLoading(false)
    }
  }

  const createCollectionPage = async (collectionType) => {
    try {
      setLoading(true)
      
      const collectionData = {
        title: `Luxury ${collectionType.replace('_', ' ')} Collection`,
        collection_type: collectionType,
        description: 'Exclusive luxury collection featuring premium items crafted for discerning customers.',
        featured_image: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800',
        hero_image: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200'
      }
      
      const response = await axios.post(`${API_BASE_URL}/wordpress/collection/create`, collectionData)
      
      if (response.data.collection_created.status === 'success') {
        // Show success message
        alert(`✅ Collection page created successfully!\nURL: ${response.data.page_url}`)
      }
      
    } catch (error) {
      console.error('Collection creation failed:', error)
      alert('❌ Failed to create collection page. Please try again.')
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
          WordPress Site Connection
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-3xl mx-auto">
          Connect your WordPress site to activate your 4 specialized luxury agents for 24/7 optimization and brand enhancement.
        </p>
      </motion.div>

      {/* Connection Status */}
      <motion.div
        className={`rounded-3xl p-8 border-2 ${
          connectionStatus === 'connected' 
            ? 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200' 
            : 'bg-gradient-to-r from-orange-50 to-amber-50 border-orange-200'
        }`}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-center">
          <div className={`text-6xl mb-4 ${
            connectionStatus === 'connected' ? 'text-emerald-500' : 'text-orange-500'
          }`}>
            {connectionStatus === 'connected' ? '✅' : '🔗'}
          </div>
          
          <h3 className={`text-2xl font-fashion font-semibold mb-3 ${
            connectionStatus === 'connected' ? 'text-emerald-700' : 'text-orange-700'
          }`}>
            {connectionStatus === 'connected' 
              ? 'WordPress Site Connected!' 
              : 'Connect Your WordPress Site'
            }
          </h3>
          
          {connectionStatus === 'connected' ? (
            <div className="space-y-4">
              <p className="text-emerald-600 text-lg">
                🎉 Your luxury agents are now actively working on your site!
              </p>
              
              {siteInfo && (
                <div className="bg-white rounded-2xl p-6 mt-6">
                  <h4 className="font-semibold text-gray-800 mb-4">Connected Site Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                    <div>
                      <span className="text-gray-600">Site Name:</span>
                      <div className="font-medium">{siteInfo.site_name}</div>
                    </div>
                    <div>
                      <span className="text-gray-600">Site URL:</span>
                      <div className="font-medium text-blue-600">
                        <a href={siteInfo.site_url} target="_blank" rel="noopener noreferrer">
                          {siteInfo.site_url}
                        </a>
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Site ID:</span>
                      <div className="font-medium">{siteInfo.site_id}</div>
                    </div>
                    <div>
                      <span className="text-gray-600">WordPress.com:</span>
                      <div className="font-medium">{siteInfo.is_wpcom ? 'Yes' : 'No'}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-orange-600 text-lg">
                Authorize access to activate your luxury brand agents
              </p>
              
              <button
                className="luxury-button px-8 py-4 text-lg"
                onClick={getAuthUrl}
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                    Connecting...
                  </span>
                ) : (
                  'Connect WordPress Site'
                )}
              </button>
            </div>
          )}
        </div>
      </motion.div>

      {/* Agent Capabilities */}
      {connectionStatus === 'connected' && (
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
          {[
            {
              name: 'Design Automation Agent',
              icon: '🎨',
              status: 'Active',
              capabilities: [
                'Divi Theme Optimization',
                'Luxury Color Schemes',
                'Mobile Responsiveness',
                'Brand Consistency'
              ]
            },
            {
              name: 'Performance Agent',
              icon: '⚡',
              status: 'Monitoring',
              capabilities: [
                'Speed Optimization',
                'Image Compression',
                'Caching Management',
                'Core Web Vitals'
              ]
            },
            {
              name: 'WordPress Specialist',
              icon: '🌐',
              status: 'Working',
              capabilities: [
                'Content Management',
                'Plugin Optimization',
                'Security Enhancement',
                'Database Cleanup'
              ]
            },
            {
              name: 'Brand Intelligence',
              icon: '👑',
              status: 'Analyzing',
              capabilities: [
                'Brand Guidelines',
                'Content Strategy',
                'Market Analysis',
                'Luxury Positioning'
              ]
            }
          ].map((agent, index) => (
            <motion.div
              key={index}
              className="bg-white rounded-3xl p-6 shadow-luxury border border-gray-100 hover:shadow-gold-glow transition-all duration-300"
              variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 }
              }}
            >
              <div className="text-center mb-4">
                <div className="text-4xl mb-2">{agent.icon}</div>
                <h4 className="font-fashion font-semibold text-gray-800 mb-2">
                  {agent.name}
                </h4>
                <div className="text-sm text-emerald-600 bg-emerald-50 rounded-full px-3 py-1 inline-block">
                  {agent.status}
                </div>
              </div>

              <div className="space-y-2">
                <h5 className="text-sm font-medium text-gray-700">Capabilities:</h5>
                {agent.capabilities.map((capability, capIndex) => (
                  <div key={capIndex} className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">
                    • {capability}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Collection Creation */}
      {connectionStatus === 'connected' && (
        <motion.div
          className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6 text-center">
            Create Luxury Collection Pages
          </h3>
          <p className="text-gray-600 text-center mb-8">
            Let your agents create high-converting collection pages with luxury aesthetics and Divi optimization.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { 
                type: 'rose_gold_collection', 
                name: 'Rose Gold Elegance', 
                color: 'from-pink-400 to-rose-400',
                description: 'Timeless elegance meets modern sophistication'
              },
              { 
                type: 'luxury_gold_collection', 
                name: 'Luxury Gold Statement', 
                color: 'from-yellow-400 to-amber-400',
                description: 'Bold statements for discerning connoisseurs'
              },
              { 
                type: 'elegant_silver_collection', 
                name: 'Elegant Silver', 
                color: 'from-gray-400 to-slate-400',
                description: 'Refined elegance for modern luxury lifestyle'
              }
            ].map((collection) => (
              <motion.div
                key={collection.type}
                className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-all duration-300"
                whileHover={{ scale: 1.02 }}
              >
                <div className={`w-full h-32 bg-gradient-to-r ${collection.color} rounded-xl mb-4 flex items-center justify-center text-white text-2xl font-bold`}>
                  {collection.name.split(' ')[0]}
                </div>
                <h4 className="font-fashion font-semibold text-gray-800 mb-2">
                  {collection.name}
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  {collection.description}
                </p>
                <button
                  className={`w-full py-3 rounded-xl bg-gradient-to-r ${collection.color} text-white font-medium hover:shadow-lg transition-all duration-300 disabled:opacity-50`}
                  onClick={() => createCollectionPage(collection.type)}
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Page'}
                </button>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="text-red-600 font-medium mb-2">Connection Error</div>
            <div className="text-red-500 text-sm">{error}</div>
            <button
              className="mt-4 px-6 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors"
              onClick={() => setError('')}
            >
              Dismiss
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default WordPressConnection