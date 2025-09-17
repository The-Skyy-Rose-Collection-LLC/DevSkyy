import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.REACT_APP_BACKEND_URL ||
  '/api';

const SocialMediaAutomation = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [platforms, setPlatforms] = useState({
    instagram: { connected: false, followers: 0, engagement: 0 },
    tiktok: { connected: false, followers: 0, engagement: 0 },
    facebook: { connected: false, followers: 0, engagement: 0 },
    twitter: { connected: false, followers: 0, engagement: 0 },
  });
  const [automationRules, setAutomationRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlatform, setSelectedPlatform] = useState('instagram');

  useEffect(() => {
    fetchSocialData();
  }, []);

  const fetchSocialData = async () => {
    try {
      setLoading(true);
      // Fetch campaign data
      const campaignsResponse = await axios.get(
        `${API_BASE_URL}/marketing/social-campaigns`
      );
      setCampaigns(campaignsResponse.data.campaigns || []);

      // Fetch platform connections
      const platformsResponse = await axios.get(
        `${API_BASE_URL}/integrations/social-platforms`
      );
      setPlatforms(platformsResponse.data.platforms || platforms);

      setAutomationRules([
        {
          id: 1,
          name: 'Streetwear Drop Alert',
          trigger: 'New product launch',
          platforms: ['instagram', 'tiktok'],
          status: 'active',
          engagement_rate: '8.7%',
        },
        {
          id: 2,
          name: 'Luxury Collection Showcase',
          trigger: 'Weekly collection feature',
          platforms: ['instagram', 'facebook'],
          status: 'active',
          engagement_rate: '12.4%',
        },
        {
          id: 3,
          name: 'Behind the Scenes Content',
          trigger: 'Daily brand story',
          platforms: ['instagram', 'tiktok'],
          status: 'paused',
          engagement_rate: '6.2%',
        },
      ]);
    } catch (error) {
      console.error('Failed to fetch social data:', error);
      // Mock data for development
      setCampaigns([
        {
          id: 1,
          name: 'Love Hurts Collection Launch',
          platform: 'instagram',
          status: 'active',
          reach: 45600,
          engagement: 3890,
          clicks: 1240,
          budget: 2500,
        },
        {
          id: 2,
          name: 'Signature Series Drop',
          platform: 'tiktok',
          status: 'scheduled',
          reach: 78300,
          engagement: 12400,
          clicks: 2890,
          budget: 3500,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const createCampaign = async campaignData => {
    try {
      const response = await axios.post(`${API_BASE_URL}/marketing/campaign`, {
        ...campaignData,
        type: 'social_media_luxury',
      });
      fetchSocialData();
    } catch (error) {
      console.error('Failed to create campaign:', error);
    }
  };

  const connectPlatform = async platform => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/integrations/social-connect`,
        {
          platform: platform,
          brand_style: 'luxury_streetwear',
        }
      );

      if (response.data.auth_url) {
        window.open(response.data.auth_url, '_blank', 'width=600,height=700');
      }

      fetchSocialData();
    } catch (error) {
      console.error('Failed to connect platform:', error);
    }
  };

  const platformColors = {
    instagram: 'from-pink-500 to-purple-600',
    tiktok: 'from-gray-800 to-red-600',
    facebook: 'from-blue-600 to-indigo-700',
    twitter: 'from-blue-400 to-blue-600',
  };

  const platformIcons = {
    instagram: '📸',
    tiktok: '🎵',
    facebook: '👥',
    twitter: '🐦',
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
          Social Media Empire
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-4xl mx-auto">
          Automate your luxury streetwear brand across all social platforms with
          AI-powered content creation, scheduling, and engagement optimization.
        </p>
      </motion.div>

      {/* Platform Connections */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: { staggerChildren: 0.1 },
        }}
      >
        {Object.entries(platforms).map(([platform, data]) => (
          <motion.div
            key={platform}
            className={`bg-gradient-to-br ${platformColors[platform]} p-6 rounded-3xl text-white shadow-luxury hover:shadow-gold-glow transition-all duration-300`}
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0 },
            }}
            whileHover={{ scale: 1.05 }}
          >
            <div className="text-center">
              <div className="text-4xl mb-3">{platformIcons[platform]}</div>
              <h3 className="text-xl font-fashion font-semibold capitalize mb-2">
                {platform}
              </h3>

              {data.connected ? (
                <div className="space-y-2">
                  <div className="bg-white/20 rounded-xl p-3">
                    <div className="text-sm opacity-80">Followers</div>
                    <div className="text-2xl font-bold">
                      {data.followers.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-white/20 rounded-xl p-3">
                    <div className="text-sm opacity-80">Engagement</div>
                    <div className="text-xl font-bold">{data.engagement}%</div>
                  </div>
                  <div className="bg-emerald-500 text-white px-3 py-1 rounded-full text-sm">
                    ✅ Connected
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => connectPlatform(platform)}
                  className="bg-white text-gray-800 px-4 py-2 rounded-xl font-semibold hover:bg-gray-100 transition-colors w-full"
                >
                  Connect {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Active Campaigns */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-fashion font-semibold text-gray-800">
            Active Campaigns
          </h3>
          <button
            onClick={() =>
              createCampaign({
                name: 'New Luxury Drop',
                platform: selectedPlatform,
                budget: 2000,
                target_audience: 'luxury_streetwear_enthusiasts',
              })
            }
            className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-6 py-3 rounded-2xl font-semibold hover:shadow-gold-glow transition-all duration-300"
          >
            🚀 Launch Campaign
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {campaigns.map(campaign => (
            <div
              key={campaign.id}
              className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-6 border border-gray-200"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-xl font-semibold text-gray-800 mb-1">
                    {campaign.name}
                  </h4>
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl">
                      {platformIcons[campaign.platform]}
                    </span>
                    <span className="capitalize text-gray-600">
                      {campaign.platform}
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        campaign.status === 'active'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}
                    >
                      {campaign.status}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-luxury-gold">
                    ${campaign.budget}
                  </div>
                  <div className="text-sm text-gray-600">Budget</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-800">
                    {campaign.reach.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Reach</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-rose-gold">
                    {campaign.engagement.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Engagement</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-emerald-600">
                    {campaign.clicks.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Clicks</div>
                </div>
              </div>

              <div className="mt-4 bg-gray-100 rounded-xl p-3">
                <div className="text-sm text-gray-600 mb-1">Performance</div>
                <div className="flex justify-between text-sm">
                  <span>
                    CTR: {((campaign.clicks / campaign.reach) * 100).toFixed(2)}
                    %
                  </span>
                  <span>
                    Engagement Rate:{' '}
                    {((campaign.engagement / campaign.reach) * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Automation Rules */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          Automation Rules
        </h3>

        <div className="space-y-4">
          {automationRules.map(rule => (
            <div
              key={rule.id}
              className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-6 border border-gray-200"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-2">
                    {rule.name}
                  </h4>
                  <p className="text-gray-600 mb-3">{rule.trigger}</p>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {rule.platforms.map(platform => (
                        <span key={platform} className="text-lg">
                          {platformIcons[platform]}
                        </span>
                      ))}
                    </div>
                    <div className="text-sm text-gray-500">
                      Engagement: {rule.engagement_rate}
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div
                    className={`px-4 py-2 rounded-full text-sm font-semibold mb-3 ${
                      rule.status === 'active'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {rule.status === 'active' ? '🟢 Active' : '⏸️ Paused'}
                  </div>
                  <button className="text-luxury-gold hover:text-rose-gold transition-colors">
                    ⚙️ Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Content Creation Studio */}
      <motion.div
        className="bg-gradient-to-br from-luxury-gold/10 to-rose-gold/10 rounded-3xl p-8 shadow-luxury border border-luxury-gold/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          AI Content Studio
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">🎨</div>
            <h4 className="text-lg font-semibold mb-2">Visual Content</h4>
            <p className="text-gray-600 text-sm mb-4">
              AI-generated luxury streetwear visuals
            </p>
            <button className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-4 py-2 rounded-xl text-sm font-semibold w-full">
              Generate Visuals
            </button>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">✍️</div>
            <h4 className="text-lg font-semibold mb-2">Copy Writing</h4>
            <p className="text-gray-600 text-sm mb-4">
              Luxury brand captions and hashtags
            </p>
            <button className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-4 py-2 rounded-xl text-sm font-semibold w-full">
              Generate Copy
            </button>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">📅</div>
            <h4 className="text-lg font-semibold mb-2">Auto Scheduling</h4>
            <p className="text-gray-600 text-sm mb-4">
              Optimal posting times across platforms
            </p>
            <button className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-4 py-2 rounded-xl text-sm font-semibold w-full">
              Schedule Posts
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SocialMediaAutomation;
