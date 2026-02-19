/**
 * xAI Grok Client for Node.js — DevSkyy
 * Grok uses OpenAI-compatible API at https://api.x.ai/v1
 * Unique features: Live web search, real-time data, X/Twitter access
 */

const OpenAI = require('openai');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });

class GrokClient {
  constructor(options = {}) {
    this.apiKey = options.apiKey || process.env.XAI_API_KEY || process.env.GROK_API_KEY;

    if (!this.apiKey) {
      throw new Error('xAI API key required. Set XAI_API_KEY in .env');
    }

    const settingsPath = path.join(__dirname, '../../config/settings.json');
    this.settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));

    const modelsPath = path.join(__dirname, '../../config/models.json');
    this.modelConfigs = JSON.parse(fs.readFileSync(modelsPath, 'utf8'));

    // Grok uses OpenAI SDK with xAI base URL
    this.client = new OpenAI({
      apiKey: this.apiKey,
      baseURL: options.baseURL || this.settings.baseURL
    });

    this.defaultModel = options.model || this.settings.defaultModel;
    this.generationConfig = { ...this.settings.generationConfig, ...options.generationConfig };

    this.lastRequestTime = 0;
    this.minRequestInterval = 60000 / this.settings.rateLimit.requestsPerMinute;
  }

  async rateLimit() {
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;
    if (elapsed < this.minRequestInterval) {
      await new Promise(r => setTimeout(r, this.minRequestInterval - elapsed));
    }
    this.lastRequestTime = Date.now();
  }

  /** Generate content */
  async generateContent(options) {
    await this.rateLimit();
    const { prompt, model, systemPrompt, ...config } = options;

    const messages = [];
    if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
    messages.push({ role: 'user', content: prompt });

    try {
      const response = await this.client.chat.completions.create({
        model: model || this.defaultModel,
        messages,
        ...this.generationConfig,
        ...config
      });

      return {
        text: response.choices[0].message.content,
        finishReason: response.choices[0].finish_reason,
        usage: response.usage
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Streaming */
  async *generateContentStream(options) {
    await this.rateLimit();
    const { prompt, model, systemPrompt, ...config } = options;

    const messages = [];
    if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
    messages.push({ role: 'user', content: prompt });

    try {
      const stream = await this.client.chat.completions.create({
        model: model || this.defaultModel,
        messages,
        stream: true,
        ...this.generationConfig,
        ...config
      });

      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta?.content || '';
        if (delta) yield { text: delta, done: false };
      }
      yield { text: '', done: true };
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /** Multi-turn chat */
  startChat(options = {}) {
    const { model, systemPrompt = '', history = [] } = options;
    const client = this.client;
    const defaultModel = model || this.defaultModel;
    const genConfig = this.generationConfig;

    return {
      model: defaultModel,
      history: systemPrompt
        ? [{ role: 'system', content: systemPrompt }, ...history]
        : [...history],

      async sendMessage(message) {
        this.history.push({ role: 'user', content: message });
        const response = await client.chat.completions.create({
          model: this.model, messages: this.history, ...genConfig
        });
        const reply = response.choices[0].message.content;
        this.history.push({ role: 'assistant', content: reply });
        return { response: { text: () => reply }, usage: response.usage };
      }
    };
  }

  /**
   * Live search — Grok's signature feature
   * Accesses real-time web + X/Twitter data
   */
  async liveSearch(options) {
    await this.rateLimit();
    const {
      query,
      model = 'grok-3',
      sources = [{ type: 'web' }, { type: 'x' }],
      systemPrompt = 'You are a helpful assistant with access to real-time web and X (Twitter) data.'
    } = options;

    try {
      const response = await this.client.chat.completions.create({
        model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: query }
        ],
        // xAI search grounding extension
        search_parameters: { mode: 'on', sources },
        max_tokens: this.generationConfig.max_tokens
      });

      const msg = response.choices[0].message;
      return {
        text: msg.content,
        citations: msg.citations || [],
        usage: response.usage
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Vision — image analysis with Grok 2 Vision */
  async analyzeImage(options) {
    await this.rateLimit();
    const { imagePath, imageUrl, prompt, model = 'grok-2-vision-1212', detail = 'auto' } = options;

    let imageContent;
    if (imagePath) {
      const data = fs.readFileSync(imagePath);
      const ext = path.extname(imagePath).slice(1).replace('jpg', 'jpeg');
      imageContent = {
        type: 'image_url',
        image_url: { url: `data:image/${ext};base64,${data.toString('base64')}`, detail }
      };
    } else if (imageUrl) {
      imageContent = { type: 'image_url', image_url: { url: imageUrl, detail } };
    } else {
      throw new Error('Either imagePath or imageUrl required');
    }

    try {
      const response = await this.client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: [{ type: 'text', text: prompt }, imageContent] }],
        max_tokens: this.generationConfig.max_tokens
      });

      return { text: response.choices[0].message.content, usage: response.usage };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Tool / function calling */
  async generateWithTools(options) {
    await this.rateLimit();
    const { prompt, tools, model, systemPrompt } = options;

    const messages = [];
    if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
    messages.push({ role: 'user', content: prompt });

    const openaiTools = tools.map(t => ({
      type: 'function',
      function: { name: t.name, description: t.description, parameters: t.parameters }
    }));

    try {
      const response = await this.client.chat.completions.create({
        model: model || this.defaultModel,
        messages,
        tools: openaiTools,
        tool_choice: 'auto'
      });

      const msg = response.choices[0].message;
      const toolCall = msg.tool_calls?.[0];

      return {
        text: msg.content || '',
        toolCall: toolCall ? {
          name: toolCall.function.name,
          args: JSON.parse(toolCall.function.arguments)
        } : null,
        usage: response.usage
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Image generation with Aurora */
  async generateImage(options) {
    await this.rateLimit();
    const { prompt, model = 'aurora', n = 1, responseFormat = 'url' } = options;

    try {
      const response = await this.client.images.generate({
        model, prompt, n, response_format: responseFormat
      });
      return response.data.map(img => ({ url: img.url, b64: img.b64_json }));
    } catch (error) {
      return this.handleError(error);
    }
  }

  handleError(error) {
    const response = { error: true, message: error.message, type: error.constructor.name };

    if (error.status === 401) {
      response.type = 'AuthenticationError';
      response.message = 'Invalid API key. Check XAI_API_KEY';
    } else if (error.status === 429) {
      response.type = 'RateLimitError';
      response.message = 'Rate limit exceeded. Please wait and retry';
    }

    if (this.settings.logging.logRequests) console.error('Grok API Error:', response);
    throw response;
  }

  getAvailableModels() { return this.modelConfigs.models; }
  getRecommendedModel(t) { return this.modelConfigs.modelSelection[t] || this.defaultModel; }

  async listModels() {
    try {
      const response = await this.client.models.list();
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
}

module.exports = { GrokClient };
