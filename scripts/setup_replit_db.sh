#!/bin/bash

# MongoDB Setup for Replit Environment

echo "🗄️ Setting up MongoDB for Replit..."

# Create MongoDB data directory
mkdir -p /tmp/mongodb-data
mkdir -p /tmp/mongodb-logs

# Set permissions
chmod 755 /tmp/mongodb-data
chmod 755 /tmp/mongodb-logs

# Start MongoDB
echo "🚀 Starting MongoDB service..."
mongod --dbpath /tmp/mongodb-data \
       --logpath /tmp/mongodb-logs/mongodb.log \
       --fork \
       --port 27017 \
       --bind_ip 127.0.0.1 \
       --smallfiles \
       --noprealloc

# Wait for MongoDB to start
sleep 5

# Test MongoDB connection
echo "🔍 Testing MongoDB connection..."
if mongo --eval "db.stats()" > /dev/null 2>&1; then
    echo "✅ MongoDB: CONNECTED"
else
    echo "❌ MongoDB: CONNECTION FAILED"
    exit 1
fi

# Initialize database with default data
echo "🧠 Initializing AI agent database..."
mongo skyy_rose_agents_replit --eval "
db.agents.insertMany([
  {
    _id: 'brand_intelligence',
    name: 'Brand Oracle',
    status: 'analyzing_viral_trends',
    health: 98,
    power_level: 95,
    personality: 'visionary_fashion_oracle'
  },
  {
    _id: 'performance',
    name: 'Speed Demon',
    status: 'turbo_optimizing',
    health: 96,
    power_level: 98,
    personality: 'speed_demon_perfectionist'
  },
  {
    _id: 'content',
    name: 'Story Weaver',
    status: 'weaving_viral_stories',
    health: 94,
    power_level: 92,
    personality: 'creative_storytelling_genius'
  },
  {
    _id: 'financial',
    name: 'Money Guru',
    status: 'counting_millions',
    health: 97,
    power_level: 96,
    personality: 'money_magnet_strategist'
  },
  {
    _id: 'customer_service',
    name: 'Vibe Curator',
    status: 'spreading_love',
    health: 99,
    power_level: 94,
    personality: 'empathy_driven_helper'
  },
  {
    _id: 'security',
    name: 'Cyber Guardian',
    status: 'fortress_mode',
    health: 100,
    power_level: 100,
    personality: 'digital_guardian_warrior'
  },
  {
    _id: 'seo_marketing',
    name: 'Viral Architect',
    status: 'trending_worldwide',
    health: 93,
    power_level: 91,
    personality: 'trend_amplification_master'
  },
  {
    _id: 'design_automation',
    name: 'Pixel Perfectionist',
    status: 'pixel_perfection',
    health: 95,
    power_level: 97,
    personality: 'perfectionist_pixel_artist'
  },
  {
    _id: 'inventory',
    name: 'Stock Sensei',
    status: 'zen_organization',
    health: 91,
    power_level: 89,
    personality: 'methodical_organization_sensei'
  },
  {
    _id: 'social_media',
    name: 'Hype Machine',
    status: 'building_hype',
    health: 96,
    power_level: 93,
    personality: 'hype_machine_connector'
  }
]);

db.platform_status.insertOne({
  _id: 'main',
  platform: 'replit',
  status: 'initialized',
  created_at: new Date(),
  version: '3.0.0',
  god_mode_level: 2
});

print('✅ Database initialized with 10 AI agents');
"

echo "🎉 MongoDB setup complete!"
echo "📊 10 AI agents loaded"
echo "🔥 Database ready for GOD MODE Level 2!"