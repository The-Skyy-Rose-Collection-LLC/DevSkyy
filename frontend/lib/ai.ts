/**
 * Vercel AI SDK Utilities
 * =======================
 * Streaming utilities and helpers for AI-powered chat interfaces.
 */

import { streamText, generateText, type ModelMessage } from 'ai';
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { google } from '@ai-sdk/google';

// ============================================================================
// Types
// ============================================================================

export type AIProvider = 'openai' | 'anthropic' | 'google';

export interface StreamOptions {
  provider?: AIProvider;
  model?: string;
  temperature?: number;
  maxOutputTokens?: number;
  systemPrompt?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// ============================================================================
// Default Models
// ============================================================================

const DEFAULT_MODELS: Record<AIProvider, string> = {
  openai: 'gpt-4-turbo',
  anthropic: 'claude-3-5-sonnet-20241022',
  google: 'gemini-1.5-pro',
};

// ============================================================================
// Model Resolution
// ============================================================================

/**
 * Get the model instance for a given provider and model ID.
 */
function getModel(provider: AIProvider, modelId: string) {
  switch (provider) {
    case 'openai':
      return openai(modelId);
    case 'anthropic':
      return anthropic(modelId);
    case 'google':
      return google(modelId);
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

// ============================================================================
// Streaming Functions
// ============================================================================

/**
 * Stream text completion from an AI model.
 * Returns a result that can be consumed via textStream, text, etc.
 */
export async function streamChatCompletion(
  messages: ChatMessage[],
  options: StreamOptions = {}
) {
  const {
    provider = 'anthropic',
    model,
    temperature = 0.7,
    maxOutputTokens = 4096,
    systemPrompt,
  } = options;

  const modelId = model || DEFAULT_MODELS[provider];
  const modelInstance = getModel(provider, modelId);

  // Convert to ModelMessage format
  const coreMessages: ModelMessage[] = messages.map((msg) => ({
    role: msg.role,
    content: msg.content,
  }));

  // Add system prompt if provided
  if (systemPrompt) {
    coreMessages.unshift({
      role: 'system',
      content: systemPrompt,
    });
  }

  const result = streamText({
    model: modelInstance,
    messages: coreMessages,
    temperature,
    maxOutputTokens,
  });

  return result;
}

/**
 * Generate a complete text response (non-streaming).
 * Useful for shorter responses or when you need the full text immediately.
 */
export async function generateChatCompletion(
  messages: ChatMessage[],
  options: StreamOptions = {}
) {
  const {
    provider = 'anthropic',
    model,
    temperature = 0.7,
    maxOutputTokens = 4096,
    systemPrompt,
  } = options;

  const modelId = model || DEFAULT_MODELS[provider];
  const modelInstance = getModel(provider, modelId);

  // Convert to ModelMessage format
  const coreMessages: ModelMessage[] = messages.map((msg) => ({
    role: msg.role,
    content: msg.content,
  }));

  // Add system prompt if provided
  if (systemPrompt) {
    coreMessages.unshift({
      role: 'system',
      content: systemPrompt,
    });
  }

  const result = await generateText({
    model: modelInstance,
    messages: coreMessages,
    temperature,
    maxOutputTokens,
  });

  return result;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a ReadableStream from an AI stream result.
 * Useful for sending streaming responses from API routes.
 */
export function createReadableStream(
  textStream: AsyncIterable<string>
): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();

  return new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of textStream) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });
}

/**
 * Collect a text stream into a complete string.
 */
export async function collectStream(
  textStream: AsyncIterable<string>
): Promise<string> {
  let result = '';
  for await (const chunk of textStream) {
    result += chunk;
  }
  return result;
}

// ============================================================================
// React Hook Helpers
// ============================================================================

/**
 * Default system prompts for different agent types.
 * These can be used with the useChat hook from 'ai/react'.
 */
export const AGENT_SYSTEM_PROMPTS: Record<string, string> = {
  commerce: `You are a Commerce SuperAgent for SkyyRose, a luxury fashion brand.
You help with product recommendations, inventory queries, order management, and sales analytics.
Be professional, knowledgeable about fashion, and always maintain the brand's luxurious tone.`,

  creative: `You are a Creative SuperAgent for SkyyRose.
You assist with content creation, visual design guidance, marketing copy, and brand storytelling.
Be innovative, artistic, and aligned with SkyyRose's elegant aesthetic.`,

  marketing: `You are a Marketing SuperAgent for SkyyRose.
You help with campaign planning, audience analysis, performance metrics, and marketing strategy.
Be data-driven while maintaining the brand's sophisticated voice.`,

  support: `You are a Support SuperAgent for SkyyRose.
You provide customer service, handle inquiries, resolve issues, and ensure customer satisfaction.
Be empathetic, helpful, and represent the brand's commitment to exceptional service.`,

  operations: `You are an Operations SuperAgent for SkyyRose.
You manage logistics, supply chain, inventory, and operational efficiency.
Be precise, systematic, and focused on optimizing business processes.`,

  analytics: `You are an Analytics SuperAgent for SkyyRose.
You analyze data, generate insights, create reports, and support data-driven decisions.
Be thorough, accurate, and translate complex data into actionable insights.`,
};

/**
 * Get the system prompt for a specific agent type.
 */
export function getAgentSystemPrompt(agentType: string): string {
  return AGENT_SYSTEM_PROMPTS[agentType] || AGENT_SYSTEM_PROMPTS.support;
}
