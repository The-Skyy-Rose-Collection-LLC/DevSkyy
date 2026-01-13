'use client';

/**
 * CopilotKit Provider
 * ===================
 * Wraps the application with CopilotKit context for AI-powered features.
 */

import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import { useCopilotAction } from '@copilotkit/react-core';
import '@copilotkit/react-ui/styles.css';

interface CopilotProviderProps {
  children: React.ReactNode;
}

/**
 * Inner component to register actions (must be inside CopilotKit context)
 */
function CopilotActionsProvider({ children }: { children: React.ReactNode }) {
  // Register: List Agents
  useCopilotAction({
    name: 'list_agents',
    description: 'List all available SuperAgents in the DevSkyy platform',
    parameters: [
      {
        name: 'filter',
        type: 'string',
        description: 'Optional filter (commerce, creative, marketing, support, operations, analytics)',
      },
    ],
    handler: async ({ filter }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents`);
      if (!response.ok) return { error: 'Failed to list agents' };
      const agents = await response.json();
      return filter ? agents.filter((a: any) => a.category === filter) : agents;
    },
  });

  // Register: Execute Agent
  useCopilotAction({
    name: 'execute_agent',
    description: 'Execute a task using a specific SuperAgent',
    parameters: [
      {
        name: 'agent',
        type: 'string',
        description: 'Agent name (commerce, creative, marketing, support, operations, analytics)',
        required: true,
      },
      {
        name: 'task',
        type: 'string',
        description: 'Task description or command',
        required: true,
      },
    ],
    handler: async ({ agent, task }) => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents/${agent}/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task }),
        }
      );
      return response.ok ? await response.json() : { error: 'Execution failed' };
    },
  });

  // Register: List Products
  useCopilotAction({
    name: 'list_products',
    description: 'List products from WooCommerce',
    parameters: [
      {
        name: 'limit',
        type: 'number',
        description: 'Maximum number of products (default: 10)',
      },
      {
        name: 'collection',
        type: 'string',
        description: 'Filter by collection (black-rose, love-hurts, signature)',
      },
    ],
    handler: async ({ limit = 10, collection }) => {
      const params = new URLSearchParams({
        per_page: String(limit),
        ...(collection && { category: collection }),
      });
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/woocommerce/products?${params}`
      );
      return response.ok ? await response.json() : { error: 'Failed to fetch products' };
    },
  });

  // Register: Generate 3D Model
  useCopilotAction({
    name: 'generate_3d_model',
    description: 'Generate a 3D model from text description or image',
    parameters: [
      {
        name: 'prompt',
        type: 'string',
        description: 'Text description of the 3D model',
        required: true,
      },
      {
        name: 'mode',
        type: 'string',
        description: 'Generation mode: "text" or "image"',
        required: true,
      },
      {
        name: 'imageUrl',
        type: 'string',
        description: 'URL of reference image (for image mode)',
      },
    ],
    handler: async ({ prompt, mode, imageUrl }) => {
      const endpoint =
        mode === 'text' ? '/api/v1/3d/generate-from-text' : '/api/v1/3d/generate-from-image';
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, image_url: imageUrl }),
      });
      return response.ok ? await response.json() : { error: '3D generation failed' };
    },
  });

  // Register: Train LoRA
  useCopilotAction({
    name: 'train_lora',
    description: 'Train SkyyRose LoRA model from WooCommerce products',
    parameters: [
      {
        name: 'collections',
        type: 'string',
        description: 'Comma-separated collections (BLACK_ROSE,LOVE_HURTS,SIGNATURE)',
        required: true,
      },
      {
        name: 'maxProducts',
        type: 'number',
        description: 'Maximum number of products',
      },
      {
        name: 'epochs',
        type: 'number',
        description: 'Training epochs (default: 100)',
      },
    ],
    handler: async ({ collections, maxProducts, epochs = 100 }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/lora/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collections: collections.split(','),
          max_products: maxProducts,
          epochs,
        }),
      });
      return response.ok ? await response.json() : { error: 'Training failed to start' };
    },
  });

  return <>{children}</>;
}

export function CopilotProvider({ children }: CopilotProviderProps) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <CopilotActionsProvider>
        <CopilotSidebar
          defaultOpen={false}
          clickOutsideToClose={false}
          labels={{
            title: 'DevSkyy AI Assistant',
            initial:
              'Hello! I can help you with:\n• Managing SuperAgents\n• Creating 3D assets\n• WooCommerce products\n• LoRA training\n• Running LLM Round Tables\n\nWhat would you like to do?',
          }}
          instructions="You are an AI assistant for the DevSkyy platform. You help users manage SuperAgents, create 3D assets, run A/B tests, and coordinate multi-agent workflows. You have access to WooCommerce products, LoRA training, and visual generation tools. When users ask to perform tasks, use the available actions to interact with the DevSkyy backend."
        >
          {children}
        </CopilotSidebar>
      </CopilotActionsProvider>
    </CopilotKit>
  );
}
