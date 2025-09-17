import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const IntegrationDashboard = ({ selectedAgent, onClose }) => {
  const [integrations, setIntegrations] = useState([]);
  const [availableServices, setAvailableServices] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState({});

  useEffect(() => {
    if (selectedAgent) {
      fetchAgentIntegrations();
      fetchAvailableServices();
    }
  }, [selectedAgent]);

  const fetchAgentIntegrations = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/integrations/agent/${selectedAgent}`
      );
      setIntegrations(response.data.integrations || []);
    } catch (error) {
      console.error('Failed to fetch integrations:', error);
      setIntegrations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableServices = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/integrations/services`);
      setAvailableServices(response.data.supported_services || {});
    } catch (error) {
      console.error('Failed to fetch services:', error);
    }
  };

  const handleSync = async integrationId => {
    setSyncing(prev => ({ ...prev, [integrationId]: true }));
    try {
      await axios.post(`${API_BASE_URL}/integrations/${integrationId}/sync`);
      await fetchAgentIntegrations(); // Refresh data
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(prev => ({ ...prev, [integrationId]: false }));
    }
  };

  const getStatusColor = status => {
    const colors = {
      active: 'bg-green-500',
      pending: 'bg-yellow-500',
      error: 'bg-red-500',
      inactive: 'bg-gray-500',
    };
    return colors[status] || colors.inactive;
  };

  const getServiceIcon = (serviceType, serviceName) => {
    const icons = {
      banking: { chase: '🏦', bank_of_america: '🏛️', wells_fargo: '🏪' },
      social_media: {
        facebook: '📘',
        instagram: '📸',
        twitter: '🐦',
        linkedin: '💼',
        tiktok: '📱',
        youtube: '📺',
      },
      payment_processors: { stripe: '💳', paypal: '💰', square: '⬜' },
      websites: { wordpress: '🌐', shopify: '🛍️', custom_site: '⚡' },
      accounting_software: { quickbooks: '📊', xero: '📈' },
      analytics: { google_analytics: '📊' },
    };
    return icons[serviceType]?.[serviceName] || '🔗';
  };

  const agentNames = {
    brand_intelligence: 'Brand Oracle',
    financial: 'Wealth Advisor',
    ecommerce: 'Experience Guru',
    seo_marketing: 'Marketing Maven',
    customer_service: 'Service Concierge',
  };

  if (loading) {
    return (
      <motion.div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <div className="bg-white rounded-3xl p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-rose-gold border-t-luxury-gold rounded-full animate-spin mb-4 mx-auto"></div>
            <p className="text-gray-600 font-elegant">
              Loading integrations...
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="bg-white rounded-3xl p-8 max-w-6xl w-full max-h-[90vh] overflow-y-auto shadow-luxury"
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-fashion font-bold bg-gradient-to-r from-rose-gold via-luxury-gold to-elegant-silver bg-clip-text text-transparent mb-2">
              Integration Hub
            </h2>
            <p className="text-gray-600">
              Connect {agentNames[selectedAgent] || selectedAgent} to external
              services
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Integration Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-green-50 p-4 rounded-xl border border-green-200">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {integrations.filter(i => i.status === 'active').length}
            </div>
            <div className="text-sm text-gray-600">Active</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200">
            <div className="text-2xl font-bold text-yellow-600 mb-1">
              {integrations.filter(i => i.status === 'pending').length}
            </div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
          <div className="bg-red-50 p-4 rounded-xl border border-red-200">
            <div className="text-2xl font-bold text-red-600 mb-1">
              {integrations.filter(i => i.status === 'error').length}
            </div>
            <div className="text-sm text-gray-600">Errors</div>
          </div>
          <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {Object.keys(availableServices).length}
            </div>
            <div className="text-sm text-gray-600">Available Services</div>
          </div>
        </div>

        {/* Current Integrations */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-fashion font-bold text-gray-800">
              Current Integrations
            </h3>
            <button
              className="luxury-button"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="mr-2">➕</span>
              Add Integration
            </button>
          </div>

          {integrations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {integrations.map(integration => (
                <motion.div
                  key={integration.id}
                  className="fashion-card"
                  whileHover={{ y: -2 }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="text-3xl">
                        {getServiceIcon(
                          integration.service_type,
                          integration.service_name
                        )}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-800 capitalize">
                          {integration.service_name.replace(/_/g, ' ')}
                        </h4>
                        <p className="text-sm text-gray-600 capitalize">
                          {integration.service_type.replace(/_/g, ' ')}
                        </p>
                      </div>
                    </div>
                    <div
                      className={`w-3 h-3 rounded-full ${getStatusColor(integration.status)}`}
                    ></div>
                  </div>

                  <div className="mb-3">
                    <div className="text-xs text-gray-500 mb-1">
                      Capabilities
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {integration.capabilities
                        ?.slice(0, 2)
                        .map((capability, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-rose-gold/20 text-rose-gold rounded text-xs"
                          >
                            {capability.replace(/_/g, ' ')}
                          </span>
                        ))}
                      {integration.capabilities?.length > 2 && (
                        <span className="text-xs text-gray-500">
                          +{integration.capabilities.length - 2} more
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                    <span>
                      Last sync:{' '}
                      {integration.last_sync
                        ? new Date(integration.last_sync).toLocaleDateString()
                        : 'Never'}
                    </span>
                    <span className="capitalize">
                      {integration.sync_frequency}
                    </span>
                  </div>

                  <div className="flex space-x-2">
                    <button
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                        integration.status === 'active'
                          ? 'bg-luxury-gradient text-white hover:shadow-gold-glow'
                          : 'bg-gray-100 text-gray-500 cursor-not-allowed'
                      }`}
                      onClick={() =>
                        integration.status === 'active' &&
                        handleSync(integration.id)
                      }
                      disabled={
                        integration.status !== 'active' ||
                        syncing[integration.id]
                      }
                    >
                      {syncing[integration.id] ? '⏳' : '🔄'} Sync
                    </button>
                    <button className="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm hover:bg-gray-200 transition-colors">
                      ⚙️
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-xl">
              <div className="text-4xl mb-4">🔗</div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Integrations Yet
              </h3>
              <p className="text-gray-500 mb-4">
                Connect your first service to get started
              </p>
              <button
                className="luxury-button"
                onClick={() => setShowCreateModal(true)}
              >
                <span className="mr-2">➕</span>
                Add Your First Integration
              </button>
            </div>
          )}
        </div>

        {/* Available Services Preview */}
        <div>
          <h3 className="text-xl font-fashion font-bold text-gray-800 mb-4">
            Available Services
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Object.entries(availableServices).map(([serviceType, services]) =>
              Object.entries(services).map(([serviceName, serviceInfo]) => (
                <motion.div
                  key={`${serviceType}-${serviceName}`}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-center hover:bg-rose-gold/10 hover:border-rose-gold/30 transition-all cursor-pointer"
                  whileHover={{ scale: 1.05 }}
                  onClick={() => setShowCreateModal(true)}
                >
                  <div className="text-2xl mb-2">
                    {getServiceIcon(serviceType, serviceName)}
                  </div>
                  <div className="text-sm font-medium text-gray-800 capitalize">
                    {serviceName.replace(/_/g, ' ')}
                  </div>
                  <div className="text-xs text-gray-500 capitalize">
                    {serviceType.replace(/_/g, ' ')}
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Create Integration Modal */}
        <CreateIntegrationModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          agentType={selectedAgent}
          availableServices={availableServices}
          onIntegrationCreated={fetchAgentIntegrations}
        />
      </motion.div>
    </motion.div>
  );
};

const CreateIntegrationModal = ({
  isOpen,
  onClose,
  agentType,
  availableServices,
  onIntegrationCreated,
}) => {
  const [selectedServiceType, setSelectedServiceType] = useState('');
  const [selectedService, setSelectedService] = useState('');
  const [credentials, setCredentials] = useState({});
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!selectedServiceType || !selectedService) return;

    setCreating(true);
    try {
      await axios.post(`${API_BASE_URL}/integrations/create`, {
        agent_type: agentType,
        service_type: selectedServiceType,
        service_name: selectedService,
        credentials,
      });

      onIntegrationCreated();
      onClose();

      // Reset form
      setSelectedServiceType('');
      setSelectedService('');
      setCredentials({});
    } catch (error) {
      console.error('Failed to create integration:', error);
    } finally {
      setCreating(false);
    }
  };

  const serviceInfo =
    selectedServiceType && selectedService
      ? availableServices[selectedServiceType]?.[selectedService]
      : null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="bg-white rounded-2xl p-6 max-w-md w-full"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-xl font-fashion font-bold text-gray-800 mb-4">
              Add New Integration
            </h3>

            {/* Service Type Selection */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Service Category
              </label>
              <select
                value={selectedServiceType}
                onChange={e => {
                  setSelectedServiceType(e.target.value);
                  setSelectedService('');
                  setCredentials({});
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold"
              >
                <option value="">Select a category...</option>
                {Object.keys(availableServices).map(serviceType => (
                  <option key={serviceType} value={serviceType}>
                    {serviceType.replace(/_/g, ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            {/* Service Selection */}
            {selectedServiceType && (
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Service
                </label>
                <select
                  value={selectedService}
                  onChange={e => {
                    setSelectedService(e.target.value);
                    setCredentials({});
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold"
                >
                  <option value="">Select a service...</option>
                  {Object.entries(
                    availableServices[selectedServiceType] || {}
                  ).map(([serviceName, info]) => (
                    <option key={serviceName} value={serviceName}>
                      {info.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Credentials Form */}
            {serviceInfo && (
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Credentials
                </label>
                {serviceInfo.required_fields.map(field => (
                  <div key={field} className="mb-3">
                    <input
                      type={
                        field.toLowerCase().includes('secret') ||
                        field.toLowerCase().includes('key')
                          ? 'password'
                          : 'text'
                      }
                      placeholder={field.replace(/_/g, ' ').toUpperCase()}
                      value={credentials[field] || ''}
                      onChange={e =>
                        setCredentials(prev => ({
                          ...prev,
                          [field]: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold text-sm"
                    />
                  </div>
                ))}
                <div className="text-xs text-gray-500 mb-2">
                  Auth Type:{' '}
                  {serviceInfo.auth_type.replace(/_/g, ' ').toUpperCase()}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!selectedServiceType || !selectedService || creating}
                className="flex-1 luxury-button disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? '⏳ Creating...' : '✨ Create'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default IntegrationDashboard;
