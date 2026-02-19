/**
 * Anthropic Claude Client for Node.js — DevSkyy
 * Claude 4.5/4.6: Sonnet, Opus, Haiku
 * Capabilities: Chat, streaming, vision, tool use, long context (200K)
 */

const Anthropic = require('@anthropic-ai/sdk');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });

class AnthropicClient {
  constructor(options = {}) {
    this.apiKey = options.apiKey || process.env.ANTHROPIC_API_KEY;

    if (!this.apiKey) {
      throw new Error('Anthropic API key required. Set ANTHROPIC_API_KEY in .env');
    }

    const settingsPath = path.join(__dirname, '../../config/settings.json');
    this.settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));

    const modelsPath = path.join(__dirname, '../../config/models.json');
    this.modelConfigs = JSON.parse(fs.readFileSync(modelsPath, 'utf8'));

    this.client = new Anthropic({
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

    const messages = [{ role: 'user', content: prompt }];

    try {
      const response = await this.client.messages.create({
        model: model || this.defaultModel,
        messages,
        system: systemPrompt,
        ...this.generationConfig,
        ...config
      });

      return {
        text: response.content[0].text,
        stopReason: response.stop_reason,
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

    const messages = [{ role: 'user', content: prompt }];

    try {
      const stream = await this.client.messages.stream({
        model: model || this.defaultModel,
        messages,
        system: systemPrompt,
        ...this.generationConfig,
        ...config
      });

      for await (const event of stream) {
        if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
          yield { text: event.delta.text, done: false };
        }
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
      systemPrompt,
      history: [...history],

      async sendMessage(message) {
        this.history.push({ role: 'user', content: message });

        const response = await client.messages.create({
          model: this.model,
          messages: this.history,
          system: this.systemPrompt,
          ...genConfig
        });

        const reply = response.content[0].text;
        this.history.push({ role: 'assistant', content: reply });

        return { response: { text: () => reply }, usage: response.usage };
      }
    };
  }

  /** Vision — image analysis */
  async analyzeImage(options) {
    await this.rateLimit();
    const { imagePath, imageUrl, prompt, model, detail = 'auto' } = options;

    let imageContent;
    if (imagePath) {
      const data = fs.readFileSync(imagePath);
      const ext = path.extname(imagePath).slice(1);
      const mediaType = `image/${ext === 'jpg' ? 'jpeg' : ext}`;

      imageContent = {
        type: 'image',
        source: {
          type: 'base64',
          media_type: mediaType,
          data: data.toString('base64')
        }
      };
    } else if (imageUrl) {
      imageContent = {
        type: 'image',
        source: { type: 'url', url: imageUrl }
      };
    } else {
      throw new Error('Either imagePath or imageUrl required');
    }

    try {
      const response = await this.client.messages.create({
        model: model || this.defaultModel,
        messages: [{
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            imageContent
          ]
        }],
        max_tokens: this.generationConfig.max_tokens
      });

      return { text: response.content[0].text, usage: response.usage };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Tool / function calling */
  async generateWithTools(options) {
    await this.rateLimit();
    const { prompt, tools, model, systemPrompt } = options;

    const messages = [{ role: 'user', content: prompt }];

    const claudeTools = tools.map(t => ({
      name: t.name,
      description: t.description,
      input_schema: t.parameters
    }));

    try {
      const response = await this.client.messages.create({
        model: model || this.defaultModel,
        messages,
        system: systemPrompt,
        tools: claudeTools,
        ...this.generationConfig
      });

      const textContent = response.content.find(c => c.type === 'text');
      const toolUse = response.content.find(c => c.type === 'tool_use');

      return {
        text: textContent?.text || '',
        toolCall: toolUse ? {
          name: toolUse.name,
          args: toolUse.input
        } : null,
        usage: response.usage
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  handleError(error) {
    const response = { error: true, message: error.message, type: error.constructor.name };

    if (error.status === 401) {
      response.type = 'AuthenticationError';
      response.message = 'Invalid API key. Check ANTHROPIC_API_KEY';
    } else if (error.status === 429) {
      response.type = 'RateLimitError';
      response.message = 'Rate limit exceeded. Please wait and retry';
    }

    if (this.settings.logging.logRequests) console.error('Anthropic API Error:', response);
    throw response;
  }

  getAvailableModels() { return this.modelConfigs.models; }
  getRecommendedModel(t) { return this.modelConfigs.modelSelection[t] || this.defaultModel; }

  async listModels() {
    // Anthropic doesn't have a models.list() endpoint, return configured models
    return this.getAvailableModels();
  }
}

module.exports = { AnthropicClient };
