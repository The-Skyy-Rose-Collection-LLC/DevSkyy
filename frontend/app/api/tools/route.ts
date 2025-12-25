/**
 * Tools API Route Handler
 * Returns MCP tools list for the frontend dashboard
 */

import { NextResponse } from 'next/server';

const TOOLS = [
  { name: 'devskyy_scan_code', description: 'Scan code for issues and vulnerabilities', category: 'code', parameters: [] },
  { name: 'devskyy_fix_code', description: 'Automatically fix identified code issues', category: 'code', parameters: [] },
  { name: 'devskyy_self_healing', description: 'Self-healing code repair system', category: 'code', parameters: [] },
  { name: 'devskyy_generate_wordpress_theme', description: 'Generate WordPress/Elementor themes', category: 'wordpress', parameters: [] },
  { name: 'devskyy_ml_prediction', description: 'ML-based predictions and forecasting', category: 'analytics', parameters: [] },
  { name: 'devskyy_manage_products', description: 'WooCommerce product management', category: 'commerce', parameters: [] },
  { name: 'devskyy_dynamic_pricing', description: 'AI-powered dynamic pricing', category: 'commerce', parameters: [] },
  { name: 'devskyy_marketing_campaign', description: 'Marketing campaign management', category: 'marketing', parameters: [] },
  { name: 'devskyy_multi_agent_workflow', description: 'Multi-agent task orchestration', category: 'orchestration', parameters: [] },
  { name: 'devskyy_system_monitoring', description: 'System health and monitoring', category: 'monitoring', parameters: [] },
  { name: 'devskyy_list_agents', description: 'List all available agents', category: 'system', parameters: [] }
];

export async function GET() {
  return NextResponse.json(TOOLS);
}

