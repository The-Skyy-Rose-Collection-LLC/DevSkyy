import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const CreateTaskModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    agent_type: 'brand_intelligence',
    category: 'performance',
    priority: 'medium',
    effort: 'medium',
    completion_time: '1 week',
    urgency: 'medium',
    revenue_impact: 'medium',
    customer_impact: 'medium',
    pros: [''],
    cons: [''],
    business_justification: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const agentTypes = [
    { id: 'brand_intelligence', name: 'Brand Oracle', icon: '👑' },
    { id: 'inventory', name: 'Asset Curator', icon: '💎' },
    { id: 'financial', name: 'Wealth Advisor', icon: '💰' },
    { id: 'ecommerce', name: 'Experience Guru', icon: '🛍️' },
    { id: 'wordpress', name: 'Design Virtuoso', icon: '🎨' },
    { id: 'web_development', name: 'Performance Expert', icon: '⚡' },
    { id: 'customer_service', name: 'Service Concierge', icon: '💝' },
    { id: 'seo_marketing', name: 'Marketing Maven', icon: '📈' },
    { id: 'security', name: 'Brand Guardian', icon: '🛡️' },
    { id: 'performance', name: 'Speed Specialist', icon: '⚡' },
  ];

  const categories = [
    { id: 'website_stability', name: 'Website Stability', icon: '🏛️' },
    { id: 'revenue_impact', name: 'Revenue Impact', icon: '💰' },
    { id: 'security', name: 'Security', icon: '🔒' },
    { id: 'customer_experience', name: 'Customer Experience', icon: '💝' },
    { id: 'compliance', name: 'Compliance', icon: '📋' },
    { id: 'performance', name: 'Performance', icon: '⚡' },
    { id: 'brand_protection', name: 'Brand Protection', icon: '🛡️' },
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayChange = (field, index, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => (i === index ? value : item)),
    }));
  };

  const addArrayItem = field => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], ''],
    }));
  };

  const removeArrayItem = (field, index) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Clean up empty array items
      const cleanedData = {
        ...formData,
        pros: formData.pros.filter(item => item.trim() !== ''),
        cons: formData.cons.filter(item => item.trim() !== ''),
      };

      await onSubmit(cleanedData);
      onClose();

      // Reset form
      setFormData({
        title: '',
        description: '',
        agent_type: 'brand_intelligence',
        category: 'performance',
        priority: 'medium',
        effort: 'medium',
        completion_time: '1 week',
        urgency: 'medium',
        revenue_impact: 'medium',
        customer_impact: 'medium',
        pros: [''],
        cons: [''],
        business_justification: '',
      });
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="bg-white rounded-3xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-luxury"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-fashion font-bold bg-gradient-to-r from-rose-gold via-luxury-gold to-elegant-silver bg-clip-text text-transparent">
                Create New Task
              </h2>
              <button
                onClick={onClose}
                className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Task Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={e => handleInputChange('title', e.target.value)}
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                    placeholder="Enter a compelling task title..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Assign to Agent *
                  </label>
                  <select
                    value={formData.agent_type}
                    onChange={e =>
                      handleInputChange('agent_type', e.target.value)
                    }
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    {agentTypes.map(agent => (
                      <option key={agent.id} value={agent.id}>
                        {agent.icon} {agent.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  required
                  value={formData.description}
                  onChange={e =>
                    handleInputChange('description', e.target.value)
                  }
                  rows={3}
                  className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  placeholder="Describe the task in detail..."
                />
              </div>

              {/* Category and Priority */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={e =>
                      handleInputChange('category', e.target.value)
                    }
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>
                        {category.icon} {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={e =>
                      handleInputChange('priority', e.target.value)
                    }
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    <option value="low">🟢 Low</option>
                    <option value="medium">🟡 Medium</option>
                    <option value="high">🟠 High</option>
                    <option value="urgent">🔴 Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Effort Level
                  </label>
                  <select
                    value={formData.effort}
                    onChange={e => handleInputChange('effort', e.target.value)}
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Timeline
                  </label>
                  <select
                    value={formData.completion_time}
                    onChange={e =>
                      handleInputChange('completion_time', e.target.value)
                    }
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    <option value="1 day">1 Day</option>
                    <option value="1 week">1 Week</option>
                    <option value="2 weeks">2 Weeks</option>
                    <option value="1 month">1 Month</option>
                    <option value="3 months">3 Months</option>
                  </select>
                </div>
              </div>

              {/* Impact Assessment */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Revenue Impact
                  </label>
                  <select
                    value={formData.revenue_impact}
                    onChange={e =>
                      handleInputChange('revenue_impact', e.target.value)
                    }
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Customer Impact
                  </label>
                  <select
                    value={formData.customer_impact}
                    onChange={e =>
                      handleInputChange('customer_impact', e.target.value)
                    }
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Urgency
                  </label>
                  <select
                    value={formData.urgency}
                    onChange={e => handleInputChange('urgency', e.target.value)}
                    className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              {/* Pros and Cons */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-green-700 mb-2">
                    ✅ Benefits & Advantages
                  </label>
                  {formData.pros.map((pro, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-2 mb-2"
                    >
                      <input
                        type="text"
                        value={pro}
                        onChange={e =>
                          handleArrayChange('pros', index, e.target.value)
                        }
                        className="flex-1 px-4 py-2 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all"
                        placeholder="Enter a benefit..."
                      />
                      {formData.pros.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeArrayItem('pros', index)}
                          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('pros')}
                    className="text-green-600 hover:text-green-700 font-medium"
                  >
                    + Add another benefit
                  </button>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-red-700 mb-2">
                    ⚠️ Risks & Considerations
                  </label>
                  {formData.cons.map((con, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-2 mb-2"
                    >
                      <input
                        type="text"
                        value={con}
                        onChange={e =>
                          handleArrayChange('cons', index, e.target.value)
                        }
                        className="flex-1 px-4 py-2 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
                        placeholder="Enter a risk or consideration..."
                      />
                      {formData.cons.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeArrayItem('cons', index)}
                          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('cons')}
                    className="text-red-600 hover:text-red-700 font-medium"
                  >
                    + Add another consideration
                  </button>
                </div>
              </div>

              {/* Business Justification */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Business Justification
                </label>
                <textarea
                  value={formData.business_justification}
                  onChange={e =>
                    handleInputChange('business_justification', e.target.value)
                  }
                  rows={2}
                  className="w-full px-4 py-3 border border-rose-gold/30 rounded-lg focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all"
                  placeholder="Why is this task important for the business?"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="luxury-button disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <span className="mr-2">⏳</span>
                      Creating...
                    </>
                  ) : (
                    <>
                      <span className="mr-2">✨</span>
                      Create Task
                    </>
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default CreateTaskModal;
