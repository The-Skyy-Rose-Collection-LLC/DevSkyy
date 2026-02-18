/**
 * tool-calling.js
 * SkyyRose Programmatic Tool Calling Demonstration Engine
 *
 * Demonstrates tool/function calling with four AI providers:
 *   1. OpenAI SDK (direct, manual tool loop)
 *   2. Vercel AI SDK (generateText with tool() helper)
 *   3. Google Gemini (@google/genai, dynamic import)
 *   4. Anthropic Claude (@anthropic-ai/sdk, manual tool loop)
 *
 * Run: node build/tool-calling.js
 *
 * Requires environment variables (at least one provider key):
 *   OPENAI_API_KEY     - for OpenAI and Vercel AI SDK engines
 *   GEMINI_API_KEY     - for Gemini engine
 *   ANTHROPIC_API_KEY  - for Claude engine
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Package imports
// ---------------------------------------------------------------------------

// OpenAI SDK
const { OpenAI } = require('openai');

// Anthropic SDK
const Anthropic = require('@anthropic-ai/sdk');

// Vercel AI SDK  (ai@6.x ships generateText, generateObject, tool as named exports)
const { generateText, generateObject, tool } = require('ai');

// @ai-sdk/gateway provides a Vercel-hosted OpenAI-compatible language model
// that works with generateText without requiring @ai-sdk/openai
const { createGateway } = require('@ai-sdk/gateway');

// zod is used by the Vercel AI SDK tool() helper for parameter schemas
const { z } = require('zod');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PRODUCT_DATA_PATH = path.resolve(__dirname, '../assets/data/product-content.json');

const VALID_COLLECTIONS = ['black-rose', 'love-hurts', 'signature'];

const SYSTEM_PROMPT = `You are a helpful shopping assistant for SkyyRose, a luxury gothic-inspired fashion brand.
You help customers find products, check availability, and manage their cart.
Be concise, knowledgeable about the brand, and guide customers to the right products.`;

// ---------------------------------------------------------------------------
// Shared tool implementations
// These are the actual functions executed when a tool is called.
// Both the OpenAI and Vercel AI SDK engines route here.
// ---------------------------------------------------------------------------

/**
 * Load product catalog from disk (cached on first call via productDataCache).
 * @param {object|null} productDataCache - reference to cache object
 * @returns {object} keyed product map
 */
function loadProductDataSync() {
  try {
    const raw = fs.readFileSync(PRODUCT_DATA_PATH, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.warn('[ToolEngine] Warning: could not load product-content.json:', err.message);
    return {};
  }
}

/**
 * Tool: search_products
 * Search SkyyRose products by name, collection, or general query.
 *
 * @param {object} params
 * @param {string} params.query        - search term matched against name/description
 * @param {string} [params.collection] - filter by collection slug
 * @param {number} [params.maxResults] - cap on returned results (default 5)
 * @param {object} productData         - full product catalog
 * @returns {object}
 */
function impl_search_products({ query, collection, maxResults = 5 }, productData) {
  const q = (query || '').toLowerCase();
  const results = [];

  for (const [id, product] of Object.entries(productData)) {
    // Collection filter
    if (collection && product.collection !== collection) continue;

    // Text match: name, short_description, collection name
    const haystack = [
      product.name,
      product.short_description,
      product.collection,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();

    if (q && !haystack.includes(q)) continue;

    results.push({
      id,
      name:             product.name,
      collection:       product.collection,
      short_description: product.short_description,
    });

    if (results.length >= maxResults) break;
  }

  return {
    found:   results.length,
    query,
    collection: collection || 'all',
    products: results,
  };
}

/**
 * Tool: get_product_details
 * Return full product record for a given ID or fuzzy name match.
 *
 * @param {object} params
 * @param {string} params.productId - product ID (e.g. 'br-001') or name fragment
 * @param {object} productData
 * @returns {object}
 */
function impl_get_product_details({ productId }, productData) {
  // Direct ID lookup
  if (productData[productId]) {
    return { id: productId, ...productData[productId] };
  }

  // Fuzzy name match
  const needle = productId.toLowerCase();
  for (const [id, product] of Object.entries(productData)) {
    if (
      product.name &&
      product.name.toLowerCase().includes(needle)
    ) {
      return { id, ...product };
    }
  }

  return { error: `Product not found: ${productId}` };
}

/**
 * Tool: get_cart_contents
 * Return current shopping cart (mock — no persistent state in this demo).
 *
 * @returns {object}
 */
function impl_get_cart_contents() {
  return {
    items: [],
    total: 0,
    currency: 'USD',
    message: 'Cart is currently empty (demo mode — no persistent cart state)',
  };
}

/**
 * Tool: add_to_cart
 * Add a product to the cart (mock action — logs and returns success).
 *
 * @param {object} params
 * @param {string} params.productId
 * @param {number} params.quantity
 * @param {string} [params.size]
 * @param {string} [params.color]
 * @returns {object}
 */
function impl_add_to_cart({ productId, quantity, size, color }) {
  const details = [`productId=${productId}`, `qty=${quantity}`];
  if (size)  details.push(`size=${size}`);
  if (color) details.push(`color=${color}`);

  console.log(`  [Cart] add_to_cart called: ${details.join(', ')}`);

  return {
    success:   true,
    cartCount: quantity,
    message:   `Added ${quantity}x ${productId}${size ? ` (${size})` : ''} to cart`,
  };
}

/**
 * Tool: check_availability
 * Check whether a product / size / color combination is in stock (mock).
 *
 * @param {object} params
 * @param {string} params.productId
 * @param {string} [params.size]
 * @param {string} [params.color]
 * @returns {object}
 */
function impl_check_availability({ productId, size, color }) {
  return {
    productId,
    size:     size  || 'any',
    color:    color || 'any',
    inStock:  true,
    quantity: 10,
    message:  'Available for immediate shipping',
  };
}

// ---------------------------------------------------------------------------
// Tool router
// Used by both OpenAI and Gemini engines to dispatch tool calls.
// ---------------------------------------------------------------------------

/**
 * Execute a named tool and return its result.
 *
 * @param {string} toolName
 * @param {object} params
 * @param {object} productData - product catalog (already loaded)
 * @returns {object}
 */
function executeTool(toolName, params, productData) {
  console.log(`  [Tool] executing: ${toolName}`, params);

  switch (toolName) {
    case 'search_products':
      return impl_search_products(params, productData);

    case 'get_product_details':
      return impl_get_product_details(params, productData);

    case 'get_cart_contents':
      return impl_get_cart_contents();

    case 'add_to_cart':
      return impl_add_to_cart(params);

    case 'check_availability':
      return impl_check_availability(params);

    default:
      return { error: `Unknown tool: ${toolName}` };
  }
}

// ---------------------------------------------------------------------------
// PRODUCT_TOOLS — tool definitions in both SDK formats
// ---------------------------------------------------------------------------

/**
 * OpenAI format tool definitions.
 * Passed directly to the `tools` parameter of chat.completions.create().
 */
const OPENAI_TOOLS = [
  {
    type: 'function',
    function: {
      name:        'search_products',
      description: 'Search SkyyRose products by name, collection, or category',
      parameters: {
        type:     'object',
        required: ['query'],
        properties: {
          query: {
            type:        'string',
            description: 'Search term — matched against product name and description',
          },
          collection: {
            type:        'string',
            enum:        VALID_COLLECTIONS,
            description: 'Optional collection filter',
          },
          maxResults: {
            type:        'integer',
            description: 'Maximum number of results to return (default 5)',
            default:     5,
          },
        },
      },
    },
  },
  {
    type: 'function',
    function: {
      name:        'get_product_details',
      description: 'Get full details for a specific SkyyRose product by ID or name',
      parameters: {
        type:     'object',
        required: ['productId'],
        properties: {
          productId: {
            type:        'string',
            description: 'Product ID (e.g. "br-001") or product name / name fragment',
          },
        },
      },
    },
  },
  {
    type: 'function',
    function: {
      name:        'get_cart_contents',
      description: 'Get current shopping cart contents and total',
      parameters: {
        type:       'object',
        properties: {},
      },
    },
  },
  {
    type: 'function',
    function: {
      name:        'add_to_cart',
      description: 'Add a SkyyRose product to the shopping cart',
      parameters: {
        type:     'object',
        required: ['productId', 'quantity'],
        properties: {
          productId: {
            type:        'string',
            description: 'Product ID to add',
          },
          quantity: {
            type:        'integer',
            description: 'Number of units to add',
            minimum:     1,
          },
          size: {
            type:        'string',
            description: 'Size variant (e.g. "S", "M", "L", "XL")',
          },
          color: {
            type:        'string',
            description: 'Color variant if applicable',
          },
        },
      },
    },
  },
  {
    type: 'function',
    function: {
      name:        'check_availability',
      description: 'Check if a specific SkyyRose product / size / color is in stock',
      parameters: {
        type:     'object',
        required: ['productId'],
        properties: {
          productId: {
            type:        'string',
            description: 'Product ID to check',
          },
          size: {
            type:        'string',
            description: 'Size to check availability for',
          },
          color: {
            type:        'string',
            description: 'Color to check availability for',
          },
        },
      },
    },
  },
];

/**
 * Vercel AI SDK format tool definitions.
 * Uses the tool() helper from 'ai' with Zod schemas for parameters.
 * The execute function is wired to the shared tool implementations.
 *
 * @param {object} productData - product catalog injected at runtime
 * @returns {object} tools map for generateText({ tools })
 */
function buildVercelTools(productData) {
  return {
    search_products: tool({
      description: 'Search SkyyRose products by name, collection, or category',
      parameters: z.object({
        query:      z.string().describe('Search term matched against product name and description'),
        collection: z.enum(VALID_COLLECTIONS).optional().describe('Optional collection filter'),
        maxResults: z.number().int().optional().default(5).describe('Max results to return'),
      }),
      execute: async (params) => impl_search_products(params, productData),
    }),

    get_product_details: tool({
      description: 'Get full details for a specific SkyyRose product by ID or name',
      parameters: z.object({
        productId: z.string().describe('Product ID (e.g. "br-001") or name fragment'),
      }),
      execute: async (params) => impl_get_product_details(params, productData),
    }),

    get_cart_contents: tool({
      description: 'Get current shopping cart contents and total',
      parameters: z.object({}),
      execute: async () => impl_get_cart_contents(),
    }),

    add_to_cart: tool({
      description: 'Add a SkyyRose product to the shopping cart',
      parameters: z.object({
        productId: z.string().describe('Product ID to add'),
        quantity:  z.number().int().min(1).describe('Number of units to add'),
        size:      z.string().optional().describe('Size variant'),
        color:     z.string().optional().describe('Color variant'),
      }),
      execute: async (params) => impl_add_to_cart(params),
    }),

    check_availability: tool({
      description: 'Check if a specific SkyyRose product / size / color is in stock',
      parameters: z.object({
        productId: z.string().describe('Product ID to check'),
        size:      z.string().optional().describe('Size to check'),
        color:     z.string().optional().describe('Color to check'),
      }),
      execute: async (params) => impl_check_availability(params),
    }),
  };
}

/**
 * Gemini format function declarations.
 * Used with @google/genai's functionDeclarations API.
 */
const GEMINI_FUNCTION_DECLARATIONS = [
  {
    name:        'search_products',
    description: 'Search SkyyRose products by name, collection, or category',
    parameters: {
      type: 'OBJECT',
      properties: {
        query:      { type: 'STRING', description: 'Search term' },
        collection: { type: 'STRING', description: 'Collection filter: black-rose, love-hurts, or signature' },
        maxResults: { type: 'NUMBER', description: 'Max number of results (default 5)' },
      },
      required: ['query'],
    },
  },
  {
    name:        'get_product_details',
    description: 'Get full details for a specific SkyyRose product by ID or name',
    parameters: {
      type: 'OBJECT',
      properties: {
        productId: { type: 'STRING', description: 'Product ID or name fragment' },
      },
      required: ['productId'],
    },
  },
  {
    name:        'get_cart_contents',
    description: 'Get current shopping cart contents and total',
    parameters: {
      type:       'OBJECT',
      properties: {},
    },
  },
  {
    name:        'add_to_cart',
    description: 'Add a SkyyRose product to the shopping cart',
    parameters: {
      type: 'OBJECT',
      properties: {
        productId: { type: 'STRING', description: 'Product ID to add' },
        quantity:  { type: 'NUMBER', description: 'Number of units to add' },
        size:      { type: 'STRING', description: 'Size variant' },
        color:     { type: 'STRING', description: 'Color variant' },
      },
      required: ['productId', 'quantity'],
    },
  },
  {
    name:        'check_availability',
    description: 'Check if a specific product/size/color is in stock',
    parameters: {
      type: 'OBJECT',
      properties: {
        productId: { type: 'STRING', description: 'Product ID to check' },
        size:      { type: 'STRING', description: 'Size to check' },
        color:     { type: 'STRING', description: 'Color to check' },
      },
      required: ['productId'],
    },
  },
];

// ---------------------------------------------------------------------------
// ToolCallingEngine class
// ---------------------------------------------------------------------------

class ToolCallingEngine {
  constructor() {
    /** @type {OpenAI|null} */
    this.openaiClient = null;

    /** @type {object} product catalog loaded from JSON */
    this.productData = {};

    // Init OpenAI client (silently skip if key not set)
    if (process.env.OPENAI_API_KEY) {
      this.openaiClient = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
      console.log('[ToolEngine] OpenAI client initialized.');
    } else {
      console.warn('[ToolEngine] OPENAI_API_KEY not set — OpenAI and Vercel AI SDK engines will be skipped.');
    }

    // Load product catalog synchronously at construction time
    this.productData = loadProductDataSync();
    const count = Object.keys(this.productData).length;
    console.log(`[ToolEngine] Loaded ${count} products from catalog.`);
  }

  // -------------------------------------------------------------------------
  // Engine 1: OpenAI SDK (direct, manual agentic tool loop)
  // -------------------------------------------------------------------------

  /**
   * Run a user message through the OpenAI SDK with full tool calling loop.
   *
   * The loop:
   *   1. Send message + tool definitions to GPT-4o-mini.
   *   2. If the response contains tool_calls, execute each one.
   *   3. Append tool results as role:'tool' messages.
   *   4. Send the updated conversation back to the model.
   *   5. Repeat until no more tool_calls or max iterations reached.
   *
   * @param {string} userMessage
   * @returns {Promise<string>} final text response
   */
  async runWithOpenAI(userMessage) {
    if (!this.openaiClient) {
      return '[Skipped] OpenAI engine requires OPENAI_API_KEY.';
    }

    console.log('\n--- OpenAI SDK Engine ---');

    const messages = [
      { role: 'system',  content: SYSTEM_PROMPT },
      { role: 'user',    content: userMessage  },
    ];

    const MAX_ITERATIONS = 5;
    let iteration = 0;

    while (iteration < MAX_ITERATIONS) {
      iteration++;
      console.log(`  [OpenAI] Iteration ${iteration}...`);

      const response = await this.openaiClient.chat.completions.create({
        model:       'gpt-4o-mini',
        messages,
        tools:       OPENAI_TOOLS,
        tool_choice: 'auto',
      });

      const message = response.choices[0].message;

      // Append the assistant's response to the conversation history
      messages.push(message);

      // If no tool calls, the model has finished — return its text
      if (!message.tool_calls || message.tool_calls.length === 0) {
        console.log(`  [OpenAI] Done after ${iteration} iteration(s).`);
        return message.content || '';
      }

      // Execute each tool call and append results
      for (const toolCall of message.tool_calls) {
        const toolName = toolCall.function.name;
        let params;

        try {
          params = JSON.parse(toolCall.function.arguments);
        } catch {
          params = {};
        }

        const result = executeTool(toolName, params, this.productData);

        messages.push({
          role:         'tool',
          tool_call_id: toolCall.id,
          content:      JSON.stringify(result),
        });
      }
    }

    // Fallback if we hit the iteration cap without a final text response
    const last = messages[messages.length - 1];
    return (last && last.content) ? last.content : '[OpenAI] Max iterations reached.';
  }

  // -------------------------------------------------------------------------
  // Engine 2: Vercel AI SDK (generateText with tool() helper)
  // -------------------------------------------------------------------------

  /**
   * Run a user message through the Vercel AI SDK's generateText().
   *
   * Uses @ai-sdk/gateway to create a language model compatible with the
   * Vercel AI SDK's unified provider interface. Tools are defined with the
   * tool() helper and Zod schemas — the SDK handles the agentic loop
   * automatically (maxSteps controls max tool-call rounds).
   *
   * @param {string} userMessage
   * @returns {Promise<string>} final text response
   */
  async runWithVercelAI(userMessage) {
    if (!process.env.OPENAI_API_KEY) {
      return '[Skipped] Vercel AI SDK engine requires OPENAI_API_KEY (used via gateway).';
    }

    console.log('\n--- Vercel AI SDK Engine ---');

    // Build gateway-backed language model
    // createGateway wraps the Anthropic gateway; for OpenAI models we pass
    // the API key via OPENAI_API_KEY environment variable which the gateway
    // picks up automatically when the model ID is prefixed with 'openai/'.
    const gateway = createGateway({ apiKey: process.env.OPENAI_API_KEY });
    const model   = gateway.languageModel('openai/gpt-4o-mini');

    const vercelTools = buildVercelTools(this.productData);

    const result = await generateText({
      model,
      system:   SYSTEM_PROMPT,
      prompt:   userMessage,
      tools:    vercelTools,
      maxSteps: 5,   // SDK will automatically loop tool calls up to this many steps
    });

    console.log(`  [Vercel AI] Steps used: ${result.steps ? result.steps.length : 'N/A'}`);

    return result.text || '[Vercel AI] No text response.';
  }

  // -------------------------------------------------------------------------
  // Engine 3: Google Gemini (@google/genai, dynamic import)
  // -------------------------------------------------------------------------

  /**
   * Run a user message through Google Gemini with function calling.
   *
   * @google/genai is imported dynamically so the file still loads if the
   * package is absent (though it IS in package.json for this project).
   *
   * The loop mirrors the OpenAI engine:
   *   1. Send message + function declarations to Gemini.
   *   2. If the response has functionCall parts, execute each function.
   *   3. Append function results as a 'function' role turn.
   *   4. Repeat until a text response is received or max iterations hit.
   *
   * @param {string} userMessage
   * @returns {Promise<string>} final text response
   */
  async runWithGemini(userMessage) {
    if (!process.env.GEMINI_API_KEY) {
      return '[Skipped] Gemini engine requires GEMINI_API_KEY.';
    }

    console.log('\n--- Gemini Engine ---');

    let GoogleGenAI;
    try {
      ({ GoogleGenAI } = await import('@google/genai'));
    } catch (err) {
      return `[Skipped] Could not import @google/genai: ${err.message}`;
    }

    const client = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

    // Conversation history in Gemini's content format
    const contents = [
      { role: 'user', parts: [{ text: userMessage }] },
    ];

    const MAX_ITERATIONS = 5;
    let iteration = 0;

    while (iteration < MAX_ITERATIONS) {
      iteration++;
      console.log(`  [Gemini] Iteration ${iteration}...`);

      const response = await client.models.generateContent({
        model:    'gemini-2.0-flash',
        contents,
        config: {
          systemInstruction: SYSTEM_PROMPT,
          tools: [{ functionDeclarations: GEMINI_FUNCTION_DECLARATIONS }],
        },
      });

      const candidate = response.candidates && response.candidates[0];
      if (!candidate || !candidate.content) {
        return '[Gemini] No candidate content returned.';
      }

      const parts = candidate.content.parts || [];

      // Collect any function calls from this response
      const functionCallParts = parts.filter(p => p.functionCall);
      const textParts         = parts.filter(p => p.text);

      // If there are no function calls, the model is done
      if (functionCallParts.length === 0) {
        console.log(`  [Gemini] Done after ${iteration} iteration(s).`);
        return textParts.map(p => p.text).join('') || '[Gemini] No text response.';
      }

      // Append the model's response turn to history
      contents.push({ role: 'model', parts });

      // Execute each function call and collect results
      const functionResponseParts = [];

      for (const part of functionCallParts) {
        const { name, args } = part.functionCall;
        const result = executeTool(name, args || {}, this.productData);

        functionResponseParts.push({
          functionResponse: {
            name,
            response: { output: result },
          },
        });
      }

      // Append all function results as a single 'function' turn
      contents.push({ role: 'function', parts: functionResponseParts });
    }

    return '[Gemini] Max iterations reached without a final text response.';
  }

  // -------------------------------------------------------------------------
  // Engine 4: Anthropic Claude (@anthropic-ai/sdk, manual tool loop)
  // -------------------------------------------------------------------------

  /**
   * Run a user message through Anthropic Claude with tool use.
   *
   * Claude uses a manual loop identical in structure to OpenAI:
   *   1. Send messages + tools to claude.messages.create()
   *   2. If stop_reason === 'tool_use', execute each tool_use content block
   *   3. Append assistant turn then a user turn with tool_result blocks
   *   4. Repeat until stop_reason === 'end_turn' or max iterations
   *
   * @param {string} userMessage
   * @returns {Promise<string>} final text response
   */
  async runWithClaude(userMessage) {
    if (!process.env.ANTHROPIC_API_KEY) {
      return '[Skipped] Claude engine requires ANTHROPIC_API_KEY.';
    }

    console.log('\n--- Claude Engine (claude-opus-4-6) ---');

    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

    // Build Claude tool definitions from shared OPENAI_TOOLS structure
    // Claude uses the same JSON Schema format for parameters
    const claudeTools = OPENAI_TOOLS.map((t) => ({
      name:        t.function.name,
      description: t.function.description,
      input_schema: t.function.parameters,  // Claude calls it input_schema
    }));

    const messages = [{ role: 'user', content: userMessage }];

    const MAX_ITERATIONS = 5;
    let iteration = 0;

    while (iteration < MAX_ITERATIONS) {
      iteration++;
      console.log(`  [Claude] Iteration ${iteration}...`);

      const response = await client.messages.create({
        model:      'claude-opus-4-6',
        max_tokens: 1024,
        system:     SYSTEM_PROMPT,
        tools:      claudeTools,
        messages,
      });

      // Append assistant turn
      messages.push({ role: 'assistant', content: response.content });

      // Check finish reason
      if (response.stop_reason === 'end_turn') {
        console.log(`  [Claude] Done after ${iteration} iteration(s).`);
        // Extract final text from content blocks
        const text = response.content
          .filter((b) => b.type === 'text')
          .map((b) => b.text)
          .join('');
        return text || '[Claude] No text response.';
      }

      if (response.stop_reason !== 'tool_use') {
        return `[Claude] Unexpected stop_reason: ${response.stop_reason}`;
      }

      // Execute each tool_use block and collect tool_result blocks
      const toolResultBlocks = [];

      for (const block of response.content) {
        if (block.type !== 'tool_use') continue;

        const result = executeTool(block.name, block.input || {}, this.productData);
        console.log(`  [Claude] Tool called: ${block.name}`);

        toolResultBlocks.push({
          type:       'tool_result',
          tool_use_id: block.id,
          content:    JSON.stringify(result),
        });
      }

      // Append all tool results as a single user turn
      messages.push({ role: 'user', content: toolResultBlocks });
    }

    return '[Claude] Max iterations reached without a final response.';
  }

  // -------------------------------------------------------------------------
  // Demo runner
  // -------------------------------------------------------------------------

  /**
   * Run a demonstration query through all four engines and log results.
   * Engines with missing API keys are gracefully skipped.
   */
  async demo() {
    const DEMO_QUERY = "What jackets do you have? Find me all jackets. Then add the first one you find to my cart.";

    console.log('\n==========================================================');
    console.log('  SkyyRose Tool Calling Engine — Demo');
    console.log('==========================================================');
    console.log(`  Query: "${DEMO_QUERY}"`);
    console.log('==========================================================\n');

    // --- Engine 1: OpenAI ---
    try {
      const openaiResult = await this.runWithOpenAI(DEMO_QUERY);
      console.log('\n[OpenAI Result]');
      console.log(openaiResult);
    } catch (err) {
      console.error('[OpenAI Error]', err.message);
    }

    // --- Engine 2: Vercel AI SDK ---
    try {
      const vercelResult = await this.runWithVercelAI(DEMO_QUERY);
      console.log('\n[Vercel AI SDK Result]');
      console.log(vercelResult);
    } catch (err) {
      console.error('[Vercel AI SDK Error]', err.message);
    }

    // --- Engine 3: Gemini ---
    try {
      const geminiResult = await this.runWithGemini(DEMO_QUERY);
      console.log('\n[Gemini Result]');
      console.log(geminiResult);
    } catch (err) {
      console.error('[Gemini Error]', err.message);
    }

    // --- Engine 4: Claude ---
    try {
      const claudeResult = await this.runWithClaude(DEMO_QUERY);
      console.log('\n[Claude Result]');
      console.log(claudeResult);
    } catch (err) {
      console.error('[Claude Error]', err.message);
    }

    console.log('\n==========================================================');
    console.log('  Demo complete.');
    console.log('==========================================================\n');
  }
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  ToolCallingEngine,
  OPENAI_TOOLS,
  GEMINI_FUNCTION_DECLARATIONS,
  buildVercelTools,
  executeTool,
  VALID_COLLECTIONS,
};

// ---------------------------------------------------------------------------
// Entry point — run demo when executed directly
// ---------------------------------------------------------------------------

if (require.main === module) {
  const engine = new ToolCallingEngine();
  engine.demo().catch((err) => {
    console.error('[ToolCallingEngine] Fatal error:', err);
    process.exit(1);
  });
}
