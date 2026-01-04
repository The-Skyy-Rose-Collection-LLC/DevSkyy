/**
 * CopilotKit Custom Actions
 * ==========================
 * Define actions that the AI assistant can perform via the DevSkyy backend.
 */

/**
 * Action Definitions for useCopilotAction hook
 * These are used in the CopilotActionsProvider component
 */

export const devSkyyActions = [
  {
    name: 'list_agents',
    description: 'List all available SuperAgents in the DevSkyy platform',
    parameters: [
      {
        name: 'filter',
        type: 'string' as const,
        description: 'Optional filter (commerce, creative, marketing, support, operations, analytics)',
        required: false,
      },
    ],
    handler: async ({ filter }: { filter?: string }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        return { error: 'Failed to list agents' };
      }

      const agents = await response.json();

      if (filter) {
        return agents.filter((a: any) => a.category === filter);
      }

      return agents;
    },
  },
  {
    name: 'execute_agent',
    description: 'Execute a task using a specific SuperAgent',
    parameters: [
      {
        name: 'agent',
        type: 'string' as const,
        description: 'Agent name (commerce, creative, marketing, support, operations, analytics)',
        required: true,
      },
      {
        name: 'task',
        type: 'string' as const,
        description: 'Task description or command',
        required: true,
      },
      {
        name: 'parameters',
        type: 'object' as const,
        description: 'Optional task parameters',
        required: false,
      },
    ],
    handler: async ({
      agent,
      task,
      parameters,
    }: {
      agent: string;
      task: string;
      parameters?: Record<string, any>;
    }) => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents/${agent}/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task, parameters }),
        }
      );

      if (!response.ok) {
        return { error: `Agent execution failed: ${response.statusText}` };
      }

      return await response.json();
    },
  },
  {
    name: 'list_products',
    description: 'List products from WooCommerce',
    parameters: [
      {
        name: 'limit',
        type: 'number' as const,
        description: 'Maximum number of products to return (default: 10)',
        required: false,
      },
      {
        name: 'collection',
        type: 'string' as const,
        description: 'Filter by collection (black-rose, love-hurts, signature)',
        required: false,
      },
    ],
    handler: async ({ limit = 10, collection }: { limit?: number; collection?: string }) => {
      const params = new URLSearchParams({
        per_page: String(limit),
        ...(collection && { category: collection }),
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/woocommerce/products?${params}`,
        { method: 'GET', headers: { 'Content-Type': 'application/json' } }
      );

      if (!response.ok) {
        return { error: 'Failed to fetch products' };
      }

      return await response.json();
    },
  },
  {
    name: 'generate_3d_model',
    description: 'Generate a 3D model from text description or image',
    parameters: [
      {
        name: 'prompt',
        type: 'string' as const,
        description: 'Text description of the 3D model',
        required: true,
      },
      {
        name: 'mode',
        type: 'string' as const,
        description: 'Generation mode: "text" or "image"',
        required: true,
      },
      {
        name: 'imageUrl',
        type: 'string' as const,
        description: 'URL of reference image (required if mode is "image")',
        required: false,
      },
    ],
    handler: async ({
      prompt,
      mode,
      imageUrl,
    }: {
      prompt: string;
      mode: 'text' | 'image';
      imageUrl?: string;
    }) => {
      const endpoint =
        mode === 'text' ? '/api/v1/3d/generate-from-text' : '/api/v1/3d/generate-from-image';

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, image_url: imageUrl }),
      });

      if (!response.ok) {
        return { error: '3D generation failed' };
      }

      return await response.json();
    },
  },
  {
    name: 'run_round_table',
    description: 'Run LLM Round Table competition with all 6 providers',
    parameters: [
      {
        name: 'query',
        type: 'string' as const,
        description: 'The query or task for the round table',
        required: true,
      },
      {
        name: 'taskCategory',
        type: 'string' as const,
        description: 'Task category (reasoning, creative, classification, etc.)',
        required: false,
      },
    ],
    handler: async ({ query, taskCategory }: { query: string; taskCategory?: string }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/round-table`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          task_category: taskCategory,
          run_ab_test: true,
        }),
      });

      if (!response.ok) {
        return { error: 'Round table execution failed' };
      }

      return await response.json();
    },
  },
  {
    name: 'train_lora',
    description: 'Train SkyyRose LoRA model from WooCommerce products',
    parameters: [
      {
        name: 'collections',
        type: 'object' as const,
        description: 'Collections to include (BLACK_ROSE, LOVE_HURTS, SIGNATURE)',
        required: true,
      },
      {
        name: 'maxProducts',
        type: 'number' as const,
        description: 'Maximum number of products (default: unlimited)',
        required: false,
      },
      {
        name: 'epochs',
        type: 'number' as const,
        description: 'Training epochs (default: 100)',
        required: false,
      },
    ],
    handler: async ({
      collections,
      maxProducts,
      epochs = 100,
    }: {
      collections: string[];
      maxProducts?: number;
      epochs?: number;
    }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/lora/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collections,
          max_products: maxProducts,
          epochs,
        }),
      });

      if (!response.ok) {
        return { error: 'LoRA training failed to start' };
      }

      return await response.json();
    },
  },
];
