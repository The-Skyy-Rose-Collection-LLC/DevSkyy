/**
 * Agents API Route Handler
 * Returns mock agent data for the frontend dashboard
 */

import { NextResponse } from 'next/server';

// Mock agent data matching the Python backend structure
const AGENTS = [
  {
    type: 'commerce',
    name: 'Commerce Agent',
    description: 'E-commerce operations: products, orders, inventory, pricing optimization',
    status: 'active',
    llmProvider: 'openai',
    capabilities: ['product_management', 'order_processing', 'inventory_tracking', 'pricing_optimization'],
    tools: [
      { name: 'manage_products', description: 'Create/update products', category: 'commerce', parameters: [] },
      { name: 'dynamic_pricing', description: 'ML-based pricing', category: 'commerce', parameters: [] },
    ],
    stats: { tasksCompleted: 1247, successRate: 0.98, avgLatencyMs: 450, totalCostUsd: 12.50 }
  },
  {
    type: 'creative',
    name: 'Creative Agent',
    description: 'Visual content: 3D assets (Tripo3D), images (Imagen/FLUX), virtual try-on (FASHN)',
    status: 'active',
    llmProvider: 'google',
    capabilities: ['image_generation', 'video_generation', '3d_modeling', 'virtual_tryon'],
    tools: [
      { name: 'generate_3d_asset', description: '3D model generation', category: 'visual', parameters: [] },
      { name: 'generate_image', description: 'AI image generation', category: 'visual', parameters: [] },
    ],
    stats: { tasksCompleted: 523, successRate: 0.95, avgLatencyMs: 2100, totalCostUsd: 45.30 }
  },
  {
    type: 'marketing',
    name: 'Marketing Agent',
    description: 'Marketing & content: SEO, social media, email campaigns, trend analysis',
    status: 'active',
    llmProvider: 'anthropic',
    capabilities: ['seo_optimization', 'content_creation', 'campaign_management', 'trend_analysis'],
    tools: [
      { name: 'marketing_campaign', description: 'Campaign management', category: 'marketing', parameters: [] },
    ],
    stats: { tasksCompleted: 892, successRate: 0.97, avgLatencyMs: 680, totalCostUsd: 8.90 }
  },
  {
    type: 'support',
    name: 'Support Agent',
    description: 'Customer support: tickets, FAQs, escalation, intent classification',
    status: 'active',
    llmProvider: 'anthropic',
    capabilities: ['ticket_management', 'faq_generation', 'intent_classification', 'escalation'],
    tools: [
      { name: 'handle_ticket', description: 'Process support tickets', category: 'support', parameters: [] },
    ],
    stats: { tasksCompleted: 2156, successRate: 0.99, avgLatencyMs: 320, totalCostUsd: 15.20 }
  },
  {
    type: 'operations',
    name: 'Operations Agent',
    description: 'DevOps & deployment: WordPress, Elementor, monitoring, deployment',
    status: 'active',
    llmProvider: 'openai',
    capabilities: ['wordpress_management', 'elementor_theming', 'deployment', 'monitoring'],
    tools: [
      { name: 'generate_wordpress_theme', description: 'WordPress theme generation', category: 'wordpress', parameters: [] },
      { name: 'system_monitoring', description: 'System health monitoring', category: 'monitoring', parameters: [] },
    ],
    stats: { tasksCompleted: 743, successRate: 0.99, avgLatencyMs: 890, totalCostUsd: 5.60 }
  },
  {
    type: 'analytics',
    name: 'Analytics Agent',
    description: 'Data & insights: reports, forecasting, clustering, anomaly detection',
    status: 'active',
    llmProvider: 'openai',
    capabilities: ['report_generation', 'forecasting', 'clustering', 'anomaly_detection'],
    tools: [
      { name: 'ml_prediction', description: 'ML predictions', category: 'analytics', parameters: [] },
    ],
    stats: { tasksCompleted: 412, successRate: 0.96, avgLatencyMs: 1500, totalCostUsd: 22.40 }
  }
];

export async function GET() {
  return NextResponse.json(AGENTS);
}
