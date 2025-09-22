import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.REACT_APP_BACKEND_URL ||
  '/api';

const LuxuryThemeBuilder = () => {
  const [themeElements, setThemeElements] = useState({});
  const [brandAssets, setBrandAssets] = useState({});
  const [pageLayouts, setPageLayouts] = useState([]);
  const [, setLoading] = useState(true);
  const [selectedLayout, setSelectedLayout] = useState('homepage');

  // Brand asset URLs from uploaded files
  const brandUrls = {
    headerLogo:
      'https://customer-assets.emergentagent.com/job_site-sentinel-1/artifacts/ieondban_TSRC.gif',
    standingLogo:
      'https://customer-assets.emergentagent.com/job_site-sentinel-1/artifacts/vwd7nlws_Photoroom_20240919_094026.jpeg',
    loveHurtsLogo:
      'https://customer-assets.emergentagent.com/job_site-sentinel-1/artifacts/mzvfqfnz_Photo%20Dec%2008%202023%2C%2012%2037%2003%20PM%20%282%29.png',
    signatureLogo:
      'https://customer-assets.emergentagent.com/job_site-sentinel-1/artifacts/mlwkd86t_Photo%20Dec%2008%202023%2C%2012%2038%2031%20PM.jpg',
  };

  useEffect(() => {
    fetchThemeData();
  }, []);

  const fetchThemeData = async () => {
    try {
      setLoading(true);

      // Mock luxury theme elements based on brand identity
      setThemeElements({
        colors: {
          primary: '#E8B4B8', // Rose gold
          secondary: '#FFD700', // Luxury gold
          accent: '#C0C0C0', // Elegant silver
          text: '#1A1A1A', // Rich black
          background: '#FFFFFF', // Pure white
          streetwear: '#FF0000', // Bold red for streetwear elements
          luxury: '#8B4513', // Rich brown for luxury elements
        },
        typography: {
          heading: 'Playfair Display', // Luxury serif
          body: 'Inter', // Clean modern sans-serif
          accent: 'Dancing Script', // Elegant script for special elements
        },
        components: {
          headers: 12,
          footers: 8,
          hero_sections: 15,
          product_grids: 10,
          galleries: 8,
          testimonials: 6,
          contact_forms: 5,
          checkout_flows: 4,
        },
      });

      setBrandAssets({
        logos: {
          header: brandUrls.headerLogo,
          standing: brandUrls.standingLogo,
          loveHurts: brandUrls.loveHurtsLogo,
          signature: brandUrls.signatureLogo,
        },
        style: 'luxury_streetwear',
        theme: 'bold_elegant_fusion',
      });

      setPageLayouts([
        {
          id: 'homepage',
          name: 'Luxury Homepage',
          type: 'landing',
          sections: [
            'hero',
            'featured_collections',
            'about',
            'testimonials',
            'instagram_feed',
          ],
          conversion_rate: '8.7%',
          status: 'active',
        },
        {
          id: 'love_hurts_collection',
          name: 'Love Hurts Collection',
          type: 'collection',
          sections: ['hero_video', 'product_grid', 'story', 'gallery', 'cta'],
          conversion_rate: '12.4%',
          status: 'active',
        },
        {
          id: 'signature_series',
          name: 'Signature Series',
          type: 'collection',
          sections: [
            'parallax_hero',
            'product_showcase',
            'behind_scenes',
            'reviews',
          ],
          conversion_rate: '10.1%',
          status: 'active',
        },
        {
          id: 'about_brand',
          name: 'Brand Story',
          type: 'about',
          sections: ['founder_story', 'brand_values', 'process', 'team'],
          conversion_rate: '5.8%',
          status: 'active',
        },
        {
          id: 'shop_all',
          name: 'Shop All Products',
          type: 'shop',
          sections: [
            'filter_sidebar',
            'product_grid',
            'quick_view',
            'wishlist',
          ],
          conversion_rate: '15.2%',
          status: 'active',
        },
      ]);
    } catch (error) {
      console.error('Failed to fetch theme data:', error);
    } finally {
      setLoading(false);
    }
  };

  const deployTheme = async layoutId => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/wordpress/theme/deploy`,
        {
          layout_id: layoutId,
          brand_assets: brandAssets,
          theme_elements: themeElements,
          style: 'luxury_streetwear_fusion',
        }
      );

      alert(`✅ ${response.data.message || 'Theme deployed successfully!'}`);
    } catch (error) {
      console.error('Failed to deploy theme:', error);
      alert('❌ Theme deployment failed. Please try again.');
    }
  };

  const createCustomSection = async sectionData => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/wordpress/section/create`,
        {
          ...sectionData,
          brand_style: 'luxury_streetwear',
          assets: brandAssets,
        }
      );

      fetchThemeData();
    } catch (error) {
      console.error('Failed to create section:', error);
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
          Luxury WordPress Theme Builder
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-4xl mx-auto">
          Create premium WordPress themes with Divi integration, optimized for
          luxury streetwear brands with high-converting layouts and stunning
          design elements.
        </p>
      </motion.div>

      {/* Brand Assets Preview */}
      <motion.div
        className="bg-gradient-to-br from-luxury-gold/10 to-rose-gold/10 rounded-3xl p-8 shadow-luxury border border-luxury-gold/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          Your Brand Assets
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-elegant text-center">
            <div className="h-24 flex items-center justify-center mb-4 bg-black rounded-xl">
              <img
                src={brandUrls.headerLogo}
                alt="Header Logo"
                className="max-h-16 max-w-full object-contain"
              />
            </div>
            <h4 className="font-semibold text-gray-800">Header Logo</h4>
            <p className="text-sm text-gray-600">Main navigation logo</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant text-center">
            <div className="h-24 flex items-center justify-center mb-4 bg-gray-50 rounded-xl">
              <img
                src={brandUrls.standingLogo}
                alt="Standing Logo"
                className="max-h-20 max-w-full object-contain"
              />
            </div>
            <h4 className="font-semibold text-gray-800">Standing Logo</h4>
            <p className="text-sm text-gray-600">Hero sections & footer</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant text-center">
            <div className="h-24 flex items-center justify-center mb-4 bg-gray-50 rounded-xl">
              <img
                src={brandUrls.loveHurtsLogo}
                alt="Love Hurts Collection"
                className="max-h-20 max-w-full object-contain"
              />
            </div>
            <h4 className="font-semibold text-gray-800">
              Love Hurts Collection
            </h4>
            <p className="text-sm text-gray-600">Collection page branding</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant text-center">
            <div className="h-24 flex items-center justify-center mb-4 bg-gray-50 rounded-xl">
              <img
                src={brandUrls.signatureLogo}
                alt="Signature Collection"
                className="max-h-20 max-w-full object-contain"
              />
            </div>
            <h4 className="font-semibold text-gray-800">
              Signature Collection
            </h4>
            <p className="text-sm text-gray-600">Premium line branding</p>
          </div>
        </div>
      </motion.div>

      {/* Color Palette & Typography */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          Brand Identity System
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Color Palette */}
          <div>
            <h4 className="text-lg font-semibold text-gray-800 mb-4">
              Color Palette
            </h4>
            <div className="space-y-3">
              {Object.entries(themeElements.colors || {}).map(
                ([name, color]) => (
                  <div key={name} className="flex items-center space-x-4">
                    <div
                      className="w-12 h-12 rounded-xl shadow-lg border-2 border-gray-200"
                      style={{ backgroundColor: color }}
                    ></div>
                    <div>
                      <div className="font-medium text-gray-800 capitalize">
                        {name.replace('_', ' ')}
                      </div>
                      <div className="text-sm text-gray-600 font-mono">
                        {color}
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Typography */}
          <div>
            <h4 className="text-lg font-semibold text-gray-800 mb-4">
              Typography
            </h4>
            <div className="space-y-4">
              <div>
                <div
                  className="text-3xl mb-2"
                  style={{ fontFamily: 'Playfair Display' }}
                >
                  Luxury Heading Font
                </div>
                <div className="text-sm text-gray-600">
                  Playfair Display - Premium serifs
                </div>
              </div>
              <div>
                <div className="text-lg mb-2" style={{ fontFamily: 'Inter' }}>
                  Modern body text for readability and clean aesthetics
                </div>
                <div className="text-sm text-gray-600">
                  Inter - Clean & modern
                </div>
              </div>
              <div>
                <div
                  className="text-2xl mb-2"
                  style={{ fontFamily: 'Dancing Script' }}
                >
                  Elegant Script Accents
                </div>
                <div className="text-sm text-gray-600">
                  Dancing Script - Special elements
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Page Layouts */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-fashion font-semibold text-gray-800">
            Premium Page Layouts
          </h3>
          <button
            onClick={() => deployTheme('complete_site')}
            className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-6 py-3 rounded-2xl font-semibold hover:shadow-gold-glow transition-all duration-300"
          >
            🚀 Deploy Complete Theme
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {pageLayouts.map(layout => (
            <div
              key={layout.id}
              className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 shadow-elegant hover:shadow-gold-glow transition-all duration-300"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-xl font-semibold text-gray-800 mb-2">
                    {layout.name}
                  </h4>
                  <span className="text-gray-600 text-sm capitalize">
                    {layout.type} page
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-emerald-600">
                    {layout.conversion_rate}
                  </div>
                  <div className="text-xs text-gray-600">Conversion Rate</div>
                </div>
              </div>

              <div className="mb-4">
                <h5 className="text-sm font-medium text-gray-700 mb-2">
                  Sections Included:
                </h5>
                <div className="flex flex-wrap gap-2">
                  {layout.sections.map(section => (
                    <span
                      key={section}
                      className="bg-luxury-gold/20 text-luxury-gold px-2 py-1 rounded-lg text-xs font-medium"
                    >
                      {section.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => deployTheme(layout.id)}
                  className="flex-1 bg-gradient-to-r from-rose-gold to-luxury-gold text-white py-2 rounded-xl text-sm font-semibold hover:shadow-lg transition-all duration-300"
                >
                  Deploy Layout
                </button>
                <button
                  onClick={() => setSelectedLayout(layout.id)}
                  className="px-4 py-2 border border-luxury-gold text-luxury-gold rounded-xl text-sm font-semibold hover:bg-luxury-gold/10 transition-all duration-300"
                >
                  Preview
                </button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Component Library */}
      <motion.div
        className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          Luxury Component Library
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {Object.entries(themeElements.components || {}).map(
            ([component, count]) => (
              <div
                key={component}
                className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 text-center shadow-elegant hover:shadow-gold-glow transition-all duration-300"
              >
                <div className="text-3xl mb-3">
                  {component === 'headers' && '🎯'}
                  {component === 'footers' && '📍'}
                  {component === 'hero_sections' && '🌟'}
                  {component === 'product_grids' && '🛍️'}
                  {component === 'galleries' && '🖼️'}
                  {component === 'testimonials' && '💬'}
                  {component === 'contact_forms' && '📞'}
                  {component === 'checkout_flows' && '💳'}
                </div>
                <div className="text-2xl font-bold text-luxury-gold mb-1">
                  {count}
                </div>
                <div className="text-sm text-gray-600 capitalize">
                  {component.replace('_', ' ')}
                </div>
                <button
                  onClick={() =>
                    createCustomSection({
                      type: component,
                      style: 'luxury_streetwear',
                    })
                  }
                  className="mt-3 bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-3 py-1 rounded-lg text-xs font-semibold hover:shadow-lg transition-all duration-300"
                >
                  Add Custom
                </button>
              </div>
            )
          )}
        </div>
      </motion.div>

      {/* E-commerce Integration */}
      <motion.div
        className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-3xl p-8 shadow-luxury border border-emerald-200"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
          WooCommerce Integration
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">🛒</div>
            <h4 className="text-lg font-semibold mb-2">Luxury Checkout</h4>
            <p className="text-gray-600 text-sm mb-4">
              Premium checkout experience with luxury branding
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ One-click checkout</li>
              <li>✅ Guest checkout option</li>
              <li>✅ Multiple payment methods</li>
              <li>✅ Mobile optimized</li>
            </ul>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">📦</div>
            <h4 className="text-lg font-semibold mb-2">Product Showcase</h4>
            <p className="text-gray-600 text-sm mb-4">
              Stunning product displays with zoom and gallery
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ 360° product views</li>
              <li>✅ High-res image zoom</li>
              <li>✅ Video integration</li>
              <li>✅ AR try-on ready</li>
            </ul>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-elegant">
            <div className="text-3xl mb-4">📊</div>
            <h4 className="text-lg font-semibold mb-2">
              Analytics Integration
            </h4>
            <p className="text-gray-600 text-sm mb-4">
              Advanced tracking and conversion optimization
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ GA4 integration</li>
              <li>✅ Facebook Pixel</li>
              <li>✅ Conversion tracking</li>
              <li>✅ Heat mapping</li>
            </ul>
          </div>
        </div>
      </motion.div>

      {/* Live Preview */}
      {selectedLayout && (
        <motion.div
          className="bg-white rounded-3xl p-8 shadow-luxury border border-gray-100"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <h3 className="text-2xl font-fashion font-semibold text-gray-800 mb-6">
            Live Preview: {pageLayouts.find(l => l.id === selectedLayout)?.name}
          </h3>

          <div className="bg-gray-100 rounded-2xl p-8 min-h-96 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🎨</div>
              <h4 className="text-2xl font-semibold text-gray-800 mb-4">
                Preview Coming Soon
              </h4>
              <p className="text-gray-600 mb-6">
                Live preview of your luxury theme will be displayed here
              </p>
              <button
                onClick={() => deployTheme(selectedLayout)}
                className="bg-gradient-to-r from-rose-gold to-luxury-gold text-white px-8 py-3 rounded-2xl font-semibold hover:shadow-gold-glow transition-all duration-300"
              >
                Deploy This Layout
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default LuxuryThemeBuilder;
