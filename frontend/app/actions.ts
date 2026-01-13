/**
 * Server Actions
 * ==============
 * Next.js 15 server actions for forms and mutations.
 */

'use server';

import { revalidatePath } from 'next/cache';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type ActionState = {
  message: string;
  success?: boolean;
  data?: any;
};

/**
 * Execute Task Action
 * Runs a task using a SuperAgent
 */
export async function executeTask(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const agent = formData.get('agent') as string;
  const task = formData.get('task') as string;

  if (!agent || !task) {
    return {
      message: 'Please provide both agent and task description',
      success: false,
    };
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/agents/${agent}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task }),
    });

    if (!res.ok) {
      const error = await res.json();
      return {
        message: `Failed to execute task: ${error.detail || res.statusText}`,
        success: false,
      };
    }

    const data = await res.json();

    // Revalidate dashboard to show updated metrics
    revalidatePath('/');

    return {
      message: `✓ Task completed successfully!`,
      success: true,
      data,
    };
  } catch (error) {
    return {
      message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      success: false,
    };
  }
}

/**
 * Generate 3D Model Action
 * Creates a 3D model from text or image
 */
export async function generate3DModel(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const prompt = formData.get('prompt') as string;
  const mode = formData.get('mode') as string;
  const imageUrl = formData.get('imageUrl') as string;

  if (!prompt) {
    return {
      message: 'Please provide a prompt',
      success: false,
    };
  }

  try {
    const endpoint =
      mode === 'text'
        ? '/api/v1/3d/generate-from-text'
        : '/api/v1/3d/generate-from-image';

    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        ...(imageUrl && { image_url: imageUrl }),
      }),
    });

    if (!res.ok) {
      const error = await res.json();
      return {
        message: `Failed to generate 3D model: ${error.detail || res.statusText}`,
        success: false,
      };
    }

    const data = await res.json();

    return {
      message: '✓ 3D model generated successfully!',
      success: true,
      data,
    };
  } catch (error) {
    return {
      message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      success: false,
    };
  }
}

/**
 * Train LoRA Action
 * Starts LoRA training from WooCommerce products
 */
export async function trainLoRA(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const collections = formData.get('collections') as string;
  const maxProducts = formData.get('maxProducts') as string;
  const epochs = formData.get('epochs') as string;

  if (!collections) {
    return {
      message: 'Please select at least one collection',
      success: false,
    };
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/lora/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collections: collections.split(','),
        max_products: maxProducts ? parseInt(maxProducts) : undefined,
        epochs: epochs ? parseInt(epochs) : 100,
      }),
    });

    if (!res.ok) {
      const error = await res.json();
      return {
        message: `Failed to start training: ${error.detail || res.statusText}`,
        success: false,
      };
    }

    const data = await res.json();

    return {
      message: '✓ LoRA training started successfully!',
      success: true,
      data,
    };
  } catch (error) {
    return {
      message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      success: false,
    };
  }
}
