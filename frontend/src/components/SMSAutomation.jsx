import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.REACT_APP_BACKEND_URL ||
  '/api';

const SMSAutomation = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [subscribers, setSubscribers] = useState({
    total: 0,
    opt_in_rate: 0,
    growth: 0,
  });
  const [automationFlows, setAutomationFlows] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [, setLoading] = useState(true);

  useEffect(() => {
    fetchSMSData();
  }, []);

  const fetchSMSData = async () => {
    try {
      setLoading(true);

      // Mock data for luxury SMS automation
      setCampaigns([
        {
          id: 1,
          name: 'Love Hurts Drop Alert 💔',
          type: 'product_drop',
          status: 'sent',
          sent: 5600,
          delivered: 5580,
          clicked: 890,
          revenue: 18400,
          delivery_rate: 99.6,
          click_rate: 15.9,
        },
        {
          id: 2,
          name: 'VIP Exclusive Access 👑',
          type: 'vip_alert',
          status: 'scheduled',
          sent: 1200,
          delivered: 1196,
          clicked: 340,
          revenue: 12800,
          delivery_rate: 99.7,
          click_rate: 28.4,
        },
        {
          id: 3,
          name: 'Flash Sale - 2 Hours Only ⚡',
          type: 'flash_sale',
          status: 'sent',
          sent: 8900,
          delivered: 8845,
          clicked: 1560,
          revenue: 28600,
          delivery_rate: 99.4,
          click_rate: 17.6,
        },
      ]);

      setSubscribers({
        total: 18450,
        opt_in_rate: 3.2,
        growth: 18.7,
      });

      setAutomationFlows([
        {
          id: 1,
          name: 'Welcome Series - Street Luxury',
          trigger: 'SMS opt-in',
          messages: 3,
          active_subscribers: 1240,
          conversion_rate: 22.8,
          status: 'active',
        },
        {
          id: 2,
          name: 'Abandoned Cart Recovery',
          trigger: 'Cart abandonment (30min)',
          messages: 2,
          active_subscribers: 890,
          conversion_rate: 41.5,
          status: 'active',
        },
        {
          id: 3,
          name: 'VIP Birthday Drops',
          trigger: 'Customer birthday',
          messages: 1,
          active_subscribers: 340,
          conversion_rate: 68.2,
          status: 'active',
        },
        {
          id: 4,
          name: 'Restock Notifications',
          trigger: 'Back in stock',
          messages: 1,
          active_subscribers: 2100,
          conversion_rate: 35.7,
          status: 'active',
        },
        {
          id: 5,
          name: 'Win-Back Series',
          trigger: 'Inactive 45 days',
          messages: 2,
          active_subscribers: 450,
          conversion_rate: 18.3,
          status: 'paused',
        },
      ]);

      setTemplates([
        {
          id: 1,
          name: 'Product Drop Alert',
          type: 'product_launch',
          preview:
            "🔥 NEW DROP ALERT 🔥\nLove Hurts Collection is LIVE!\nGet yours before they're gone: [LINK]",
          click_rate: 16.8,
          conversion_rate: 4.2,
        },
        {
          id: 2,
          name: 'VIP Exclusive Access',
          type: 'vip_access',
          preview:
            '👑 VIP EXCLUSIVE 👑\nYour early access starts NOW!\n24hrs before everyone else: [LINK]',
          click_rate: 28.5,
          conversion_rate: 8.7,
        },
        {
          id: 3,
          name: 'Flash Sale Alert',
          type: 'flash_sale',
          preview:
            '⚡ FLASH SALE ⚡\n50% OFF everything!\n2 HOURS ONLY: [LINK]\nHurry, limited stock!',
          click_rate: 22.1,
          conversion_rate: 6.3,
        },
        {
          id: 4,
          name: 'Abandoned Cart',
          type: 'cart_recovery',
          preview:
            'You left something amazing behind 💔\nYour cart is waiting...\nComplete your order: [LINK]',
          click_rate: 35.4,
          conversion_rate: 12.8,
        },
      ]);
    } catch (error) {
      console.error('Failed to fetch SMS data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCampaign = async campaignData => {
    try {
      await axios.post(
        `${API_BASE_URL}/marketing/sms-campaign`,
        {
          ...campaignData,
          brand_voice: 'luxury_streetwear',
          compliance: 'TCPA_compliant',
        }
      );
      fetchSMSData();
    } catch (error) {
      console.error('Failed to create SMS campaign:', error);
    }
  };

  const getStatusColor = status => {
    switch (status) {
      case 'sent':
        return 'bg-emerald-100 text-emerald-700';
      case 'scheduled':
        return 'bg-blue-100 text-blue-700';
      case 'active':
        return 'bg-purple-100 text-purple-700';
      case 'paused':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

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
          SMS Marketing Empire
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-4xl mx-auto">
          Direct-to-customer luxury SMS automation with instant engagement and
          premium conversion rates for your streetwear empire.
        </p>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: { staggerChildren: 0.1 },
        }}
      >
        <motion.div
          className="bg-gradient-to-br from-rose-gold/20 to-luxury-gold/20 rounded-3xl p-6 shadow-luxury border border-rose-gold/30"
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">📱</div>
            <div className="text-3xl font-bold text-gray-800">
              {subscribers.total.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">SMS Subscribers</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              ↗️ +{subscribers.growth}% this month
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-blue-100 to-indigo-100 rounded-3xl p-6 shadow-luxury border border-blue-200"
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">✅</div>
            <div className="text-3xl font-bold text-gray-800">99.5%</div>
            <div className="text-sm text-gray-600">Delivery Rate</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              Industry avg: 94.7%
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-3xl p-6 shadow-luxury border border-purple-200"
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">👆</div>
            <div className="text-3xl font-bold text-gray-800">21.3%</div>
            <div className="text-sm text-gray-600">Avg Click Rate</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              Industry avg: 6.2%
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-br from-emerald-100 to-green-100 rounded-3xl p-6 shadow-luxury border border-emerald-200"
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">💰</div>
            <div className="text-3xl font-bold text-gray-800">$59K</div>
            <div className="text-sm text-gray-600">Monthly Revenue</div>
            <div className="text-emerald-600 text-sm font-semibold mt-1">
              ↗️ +32% this month
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
          <h3 className="text-2xl font-fashion font-semibold text-gray-800">
            Recent SMS Campaigns
          </h3>
          <button
            onClick={() =>
              createCampaign({
                name: 'New Luxury Drop Alert',
                type: 'product_drop',
                message: '🔥 NEW DROP 🔥 Exclusive luxury streetwear is here!',
              })
            }
            className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-6 py-3 rounded-2xl font-semibold hover:shadow-gold-glow transition-all duration-300"
          >
            📱 Create SMS Campaign
          </button>
        </div>

        <div className="space-y-4">
          {campaigns.map(campaign => (
            <div
              key={campaign.id}
              className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-6 border border-gray-200 hover:shadow-elegant transition-all duration-300"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-xl font-semibold text-gray-800 mb-2">
                    {campaign.name}
                  </h4>
                  <div className="flex items-center space-x-4">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(campaign.status)}`}
                    >
                      {campaign.status.charAt(0).toUpperCase() +
                        campaign.status.slice(1)}
                    </span>
                    <span className="text-gray-600 text-sm">
                      {campaign.type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-600">
                    ${campaign.revenue.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Revenue</div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center bg-gray-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-gray-800">
                    {campaign.sent.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-600">Sent</div>
                </div>
                <div className="text-center bg-blue-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-blue-600">
                    {campaign.delivered.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-600">
                    Delivered ({campaign.delivery_rate}%)
                  </div>
                </div>
                <div className="text-center bg-purple-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-purple-600">
                    {campaign.clicked.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-600">
                    Clicked ({campaign.click_rate}%)
                  </div>
                </div>
                <div className="text-center bg-emerald-100 rounded-xl p-3">
                  <div className="text-lg font-bold text-emerald-600">
                    ${(campaign.revenue / campaign.sent).toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-600">Revenue per SMS</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* SMS Templates */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          High-Converting SMS Templates
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {templates.map(template => (
            <div
              key={template.id}
              className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 shadow-elegant hover:shadow-gold-glow transition-all duration-300"
            >
              <div className="flex justify-between items-start mb-4">
                <h4 className="text-lg font-semibold text-gray-800">
                  {template.name}
                </h4>
                <div className="text-right text-sm">
                  <div className="text-purple-600 font-semibold">
                    {template.click_rate}% CTR
                  </div>
                  <div className="text-emerald-600 font-semibold">
                    {template.conversion_rate}% CVR
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 text-white p-4 rounded-xl mb-4 font-mono text-sm leading-relaxed">
                {template.preview}
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600 text-sm capitalize">
                  {template.type.replace('_', ' ')}
                </span>
                <button className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-4 py-2 rounded-xl text-sm font-semibold hover:shadow-lg transition-all duration-300">
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
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          SMS Automation Flows
        </h3>

        <div className="space-y-4">
          {automationFlows.map(flow => (
            <div
              key={flow.id}
              className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-6 border border-gray-200"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-2">
                    {flow.name}
                  </h4>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>📱 {flow.messages} messages</span>
                    <span>👥 {flow.active_subscribers} active</span>
                    <span>💰 {flow.conversion_rate}% conversion</span>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    Trigger: {flow.trigger}
                  </div>
                </div>

                <div className="text-right">
                  <div
                    className={`px-4 py-2 rounded-full text-sm font-semibold mb-3 ${
                      flow.status === 'active'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
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

      {/* Compliance & Best Practices */}
      <motion.div
        className="bg-gradient-to-br from-luxury-gold/10 to-rose-gold/10 rounded-3xl p-8 shadow-luxury border border-luxury-gold/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          SMS Compliance & Optimization
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">⚖️</div>
            <h4 className="text-lg font-semibold mb-2">TCPA Compliance</h4>
            <p className="text-gray-600 text-sm mb-4">
              Fully compliant with SMS marketing regulations
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ Opt-in verification</li>
              <li>✅ Easy opt-out process</li>
              <li>✅ Consent management</li>
            </ul>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">🎯</div>
            <h4 className="text-lg font-semibold mb-2">Optimization Tools</h4>
            <p className="text-gray-600 text-sm mb-4">
              AI-powered send time and content optimization
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ Send time optimization</li>
              <li>✅ A/B testing tools</li>
              <li>✅ Engagement tracking</li>
            </ul>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">📊</div>
            <h4 className="text-lg font-semibold mb-2">Analytics</h4>
            <p className="text-gray-600 text-sm mb-4">
              Advanced SMS performance analytics
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ Real-time metrics</li>
              <li>✅ Revenue attribution</li>
              <li>✅ Customer journey tracking</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SMSAutomation;
