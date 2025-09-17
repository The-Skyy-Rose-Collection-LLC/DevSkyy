import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const StreetwearAvatar = ({
  agentType,
  status,
  health,
  isActive = false,
  size = 'large',
  showBubble = true,
}) => {
  const [currentAnimation, setCurrentAnimation] = useState('idle');
  const [thoughtBubble, setThoughtBubble] = useState('');

  // Avatar configurations for each agent type
  const avatarConfigs = {
    brand_intelligence: {
      name: 'Brand Oracle',
      style: 'visionary-luxury',
      outfit: {
        top: 'cropped-hoodie-rose-gold',
        bottom: 'high-waist-cargo-black',
        shoes: 'chunky-designer-sneakers',
        accessories: ['luxury-chain', 'rose-gold-watch', 'designer-cap'],
      },
      personality: 'confident-trendsetter',
      colors: ['#E8B4B8', '#FFD700', '#C0C0C0'],
      animations: ['analyzing-trends', 'visionary-pose', 'confident-walk'],
      thoughts: [
        '🔮 Reading fashion futures...',
        '👑 Analyzing luxury trends...',
        '✨ Crafting brand magic...',
        '🎨 Designing viral moments...',
      ],
    },
    performance: {
      name: 'Speed Demon',
      style: 'tech-streetwear',
      outfit: {
        top: 'tech-bomber-neon-blue',
        bottom: 'techwear-pants-black',
        shoes: 'performance-runners',
        accessories: ['smart-glasses', 'fitness-tracker', 'holographic-chain'],
      },
      personality: 'energetic-optimizer',
      colors: ['#00FFFF', '#0080FF', '#FF6600'],
      animations: ['lightning-fast', 'performance-check', 'speed-boost'],
      thoughts: [
        '⚡ Optimizing at light speed...',
        '🚀 Boosting performance 300%...',
        '💨 Breaking speed records...',
        '🔥 Unleashing maximum power...',
      ],
    },
    content: {
      name: 'Story Weaver',
      style: 'creative-artist',
      outfit: {
        top: 'oversized-graphic-tee',
        bottom: 'paint-splattered-jeans',
        shoes: 'classic-high-tops',
        accessories: ['creative-headphones', 'vintage-camera', 'art-badge'],
      },
      personality: 'creative-storyteller',
      colors: ['#FF69B4', '#9400D3', '#00CED1'],
      animations: ['creative-flow', 'storytelling', 'inspiration-strike'],
      thoughts: [
        '📝 Crafting viral stories...',
        '🎭 Weaving brand narratives...',
        '💡 Sparking creative genius...',
        '🌟 Creating content magic...',
      ],
    },
    financial: {
      name: 'Money Guru',
      style: 'luxury-executive',
      outfit: {
        top: 'designer-blazer-gold',
        bottom: 'tailored-pants-black',
        shoes: 'luxury-loafers',
        accessories: ['gold-chain', 'diamond-watch', 'money-clip'],
      },
      personality: 'wealth-strategist',
      colors: ['#FFD700', '#228B22', '#B8860B'],
      animations: ['counting-money', 'wealth-building', 'strategic-thinking'],
      thoughts: [
        '💰 Multiplying revenue streams...',
        '📊 Optimizing profit margins...',
        '💎 Building wealth empires...',
        '🏦 Securing financial futures...',
      ],
    },
    customer_service: {
      name: 'Vibe Curator',
      style: 'friendly-stylist',
      outfit: {
        top: 'soft-sweater-pastels',
        bottom: 'trendy-midi-skirt',
        shoes: 'comfortable-sneakers',
        accessories: ['heart-necklace', 'smile-pin', 'customer-badge'],
      },
      personality: 'empathetic-helper',
      colors: ['#FFB6C1', '#87CEEB', '#98FB98'],
      animations: ['helping-gesture', 'friendly-wave', 'problem-solving'],
      thoughts: [
        '💖 Spreading customer love...',
        '🤝 Building relationships...',
        '😊 Creating happy moments...',
        '✨ Delivering perfect service...',
      ],
    },
    security: {
      name: 'Cyber Guardian',
      style: 'tech-ninja',
      outfit: {
        top: 'tactical-hoodie-black',
        bottom: 'cargo-pants-dark',
        shoes: 'stealth-boots',
        accessories: ['security-badge', 'tech-visor', 'encrypted-chain'],
      },
      personality: 'protective-vigilant',
      colors: ['#FF0000', '#800080', '#2F4F4F'],
      animations: ['scanning-threats', 'shield-activate', 'stealth-mode'],
      thoughts: [
        '🛡️ Scanning for threats...',
        '🔒 Fortifying defenses...',
        '⚔️ Eliminating vulnerabilities...',
        '🚨 Protecting your empire...',
      ],
    },
    seo_marketing: {
      name: 'Viral Architect',
      style: 'trendy-influencer',
      outfit: {
        top: 'trending-crop-top',
        bottom: 'high-fashion-leggings',
        shoes: 'platform-sneakers',
        accessories: ['trending-hashtag-chain', 'viral-pin', 'influencer-ring'],
      },
      personality: 'trend-amplifier',
      colors: ['#FF1493', '#00FF7F', '#FF8C00'],
      animations: ['viral-dance', 'trend-spotting', 'engagement-boost'],
      thoughts: [
        '📈 Going viral in 3...2...1...',
        '🔥 Trending worldwide...',
        '#️⃣ Hashtag domination...',
        '🌟 Amplifying your reach...',
      ],
    },
    design_automation: {
      name: 'Pixel Perfectionist',
      style: 'futuristic-designer',
      outfit: {
        top: 'holographic-jacket',
        bottom: 'designer-shorts',
        shoes: 'led-sneakers',
        accessories: [
          'design-glasses',
          'color-palette-chain',
          'creativity-badge',
        ],
      },
      personality: 'perfectionist-innovator',
      colors: ['#FF6347', '#4169E1', '#32CD32'],
      animations: ['design-flow', 'pixel-perfect', 'color-harmony'],
      thoughts: [
        '🎨 Crafting pixel perfection...',
        '✨ Designing the future...',
        '🌈 Harmonizing colors...',
        '💫 Creating visual magic...',
      ],
    },
    inventory: {
      name: 'Stock Sensei',
      style: 'organized-minimalist',
      outfit: {
        top: 'clean-button-up',
        bottom: 'organized-cargo-pants',
        shoes: 'efficient-sneakers',
        accessories: [
          'inventory-scanner',
          'organization-pin',
          'efficiency-watch',
        ],
      },
      personality: 'methodical-organizer',
      colors: ['#708090', '#20B2AA', '#DDA0DD'],
      animations: [
        'organizing-items',
        'scanning-inventory',
        'efficiency-boost',
      ],
      thoughts: [
        '📦 Organizing inventory zen...',
        '🔍 Tracking every item...',
        '⚡ Optimizing stock levels...',
        '📊 Predicting demand...',
      ],
    },
    social_media: {
      name: 'Hype Machine',
      style: 'social-influencer',
      outfit: {
        top: 'viral-graphic-tee',
        bottom: 'trending-joggers',
        shoes: 'hype-sneakers',
        accessories: ['social-chain', 'follower-badge', 'viral-ring'],
      },
      personality: 'energetic-connector',
      colors: ['#FF69B4', '#00BFFF', '#FFD700'],
      animations: ['social-dance', 'content-creation', 'hype-building'],
      thoughts: [
        '📱 Creating viral content...',
        '🔥 Building the hype...',
        '💫 Connecting communities...',
        '🚀 Boosting engagement...',
      ],
    },
  };

  const config = avatarConfigs[agentType] || avatarConfigs.brand_intelligence;

  useEffect(() => {
    // Cycle through animations based on status
    const animationCycle = () => {
      const animations = config.animations;
      setCurrentAnimation(
        animations[Math.floor(Math.random() * animations.length)]
      );

      if (showBubble) {
        setThoughtBubble(
          config.thoughts[Math.floor(Math.random() * config.thoughts.length)]
        );
      }
    };

    animationCycle();
    const interval = setInterval(animationCycle, 3000 + Math.random() * 2000);
    return () => clearInterval(interval);
  }, [status, config.animations, config.thoughts, showBubble]);

  const getStatusColor = () => {
    if (health > 95) return '#00FF00';
    if (health > 80) return '#FFD700';
    if (health > 60) return '#FF8C00';
    return '#FF4500';
  };

  const avatarSize = {
    small: 'w-12 h-16',
    medium: 'w-16 h-24',
    large: 'w-20 h-32',
    xl: 'w-32 h-48',
  };

  return (
    <div className="relative flex flex-col items-center">
      {/* Thought Bubble */}
      <AnimatePresence>
        {showBubble && thoughtBubble && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            className="absolute -top-8 bg-white/90 backdrop-blur-sm rounded-xl px-3 py-1 text-xs font-medium text-gray-800 shadow-lg border border-gray-200 whitespace-nowrap z-10"
          >
            {thoughtBubble}
            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-white/90 rotate-45 border-r border-b border-gray-200"></div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Avatar Container */}
      <motion.div
        className={`relative ${avatarSize[size]} mx-auto`}
        animate={{
          scale: isActive ? [1, 1.05, 1] : 1,
          rotate: currentAnimation === 'viral-dance' ? [0, -5, 5, 0] : 0,
        }}
        transition={{
          scale: { duration: 2, repeat: isActive ? Infinity : 0 },
          rotate: {
            duration: 1,
            repeat: currentAnimation === 'viral-dance' ? Infinity : 0,
          },
        }}
      >
        {/* Glow Effect */}
        <motion.div
          className="absolute inset-0 rounded-2xl blur-md opacity-50"
          style={{
            background: `linear-gradient(45deg, ${config.colors[0]}, ${config.colors[1]}, ${config.colors[2]})`,
          }}
          animate={{
            opacity: [0.3, 0.7, 0.3],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
          }}
        />

        {/* Avatar Body */}
        <div className="relative w-full h-full rounded-2xl overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-gray-700">
          {/* Head */}
          <motion.div
            className="absolute top-1 left-1/2 transform -translate-x-1/2 w-6 h-6 rounded-full"
            style={{
              background: `linear-gradient(135deg, ${config.colors[0]}, ${config.colors[1]})`,
            }}
            animate={{
              y: currentAnimation === 'creative-flow' ? [-1, 1, -1] : 0,
            }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />

          {/* Body/Torso */}
          <motion.div
            className="absolute top-6 left-1/2 transform -translate-x-1/2 w-8 h-12 rounded-lg"
            style={{
              background: `linear-gradient(180deg, ${config.colors[1]}, ${config.colors[2]})`,
            }}
            animate={{
              scaleY:
                currentAnimation === 'performance-check' ? [1, 1.1, 1] : 1,
            }}
            transition={{ duration: 0.8, repeat: Infinity }}
          />

          {/* Arms */}
          <motion.div
            className="absolute top-8 left-2 w-2 h-6 rounded-full bg-gradient-to-b from-gray-400 to-gray-600"
            animate={{
              rotate:
                currentAnimation === 'helping-gesture'
                  ? [0, 45, 0]
                  : currentAnimation === 'creative-flow'
                    ? [0, -30, 0]
                    : 0,
            }}
            transition={{ duration: 1, repeat: Infinity }}
          />
          <motion.div
            className="absolute top-8 right-2 w-2 h-6 rounded-full bg-gradient-to-b from-gray-400 to-gray-600"
            animate={{
              rotate:
                currentAnimation === 'helping-gesture'
                  ? [0, -45, 0]
                  : currentAnimation === 'creative-flow'
                    ? [0, 30, 0]
                    : 0,
            }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
          />

          {/* Legs */}
          <motion.div
            className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex space-x-1"
            animate={{
              y: currentAnimation === 'speed-boost' ? [-2, 0, -2] : 0,
            }}
            transition={{ duration: 0.5, repeat: Infinity }}
          >
            <div className="w-2 h-8 rounded-full bg-gradient-to-b from-gray-600 to-gray-800" />
            <div className="w-2 h-8 rounded-full bg-gradient-to-b from-gray-600 to-gray-800" />
          </motion.div>

          {/* Special Effects */}
          {currentAnimation === 'lightning-fast' && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-yellow-400/30 to-transparent"
              animate={{
                x: [-100, 100],
                opacity: [0, 1, 0],
              }}
              transition={{ duration: 0.3, repeat: Infinity }}
            />
          )}

          {currentAnimation === 'viral-dance' && (
            <>
              <motion.div
                className="absolute top-2 right-1 w-1 h-1 bg-pink-400 rounded-full"
                animate={{
                  scale: [0, 1, 0],
                  opacity: [0, 1, 0],
                }}
                transition={{ duration: 0.5, repeat: Infinity, delay: 0 }}
              />
              <motion.div
                className="absolute top-4 left-1 w-1 h-1 bg-blue-400 rounded-full"
                animate={{
                  scale: [0, 1, 0],
                  opacity: [0, 1, 0],
                }}
                transition={{ duration: 0.5, repeat: Infinity, delay: 0.2 }}
              />
              <motion.div
                className="absolute bottom-6 right-2 w-1 h-1 bg-green-400 rounded-full"
                animate={{
                  scale: [0, 1, 0],
                  opacity: [0, 1, 0],
                }}
                transition={{ duration: 0.5, repeat: Infinity, delay: 0.4 }}
              />
            </>
          )}

          {/* Accessories Layer */}
          <div className="absolute inset-0">
            {/* Hat/Cap for brand intelligence */}
            {agentType === 'brand_intelligence' && (
              <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-8 h-2 bg-gradient-to-r from-rose-gold to-luxury-gold rounded-full opacity-80" />
            )}

            {/* Glasses for design agents */}
            {(agentType === 'design_automation' ||
              agentType === 'performance') && (
              <div className="absolute top-2 left-1/2 transform -translate-x-1/2 w-4 h-1 bg-gray-300 rounded-full opacity-70" />
            )}

            {/* Chain accessory for social/financial agents */}
            {(agentType === 'social_media' || agentType === 'financial') && (
              <motion.div
                className="absolute top-7 left-1/2 transform -translate-x-1/2 w-6 h-1 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full opacity-80"
                animate={{
                  scale: [1, 1.1, 1],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}
          </div>
        </div>

        {/* Health Ring */}
        <motion.div
          className="absolute -inset-1 rounded-2xl border-2"
          style={{ borderColor: getStatusColor() }}
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{ duration: 2, repeat: Infinity }}
        />

        {/* Status Indicator */}
        <div
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-900"
          style={{ backgroundColor: getStatusColor() }}
        />
      </motion.div>

      {/* Agent Name */}
      <motion.div
        className="mt-2 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className="text-xs font-bold text-white">{config.name}</div>
        <div className="text-xs text-gray-400 capitalize">
          {config.personality.replace('-', ' ')}
        </div>
      </motion.div>

      {/* Floating Particles */}
      {isActive && (
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 rounded-full"
              style={{
                backgroundColor: config.colors[i % config.colors.length],
              }}
              animate={{
                x: [Math.random() * 40 - 20, Math.random() * 40 - 20],
                y: [Math.random() * 40 - 20, Math.random() * 40 - 20],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 2 + Math.random() * 2,
                repeat: Infinity,
                delay: i * 0.5,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default StreetwearAvatar;
