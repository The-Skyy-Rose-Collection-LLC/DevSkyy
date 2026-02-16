/**
 * Gemini AI Client for Node.js
 * Complete integration with Google's Gemini API
 * Updated for new @google/genai SDK (v1.41.0+)
 */

const { GoogleGenAI } = require('@google/genai');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

class GeminiClient {
  constructor(options = {}) {
    this.apiKey = options.apiKey || process.env.GEMINI_API_KEY;

    if (!this.apiKey) {
      throw new Error('Gemini API key is required. Set GEMINI_API_KEY in .env file');
    }

    // Initialize new SDK client
    this.ai = new GoogleGenAI({ apiKey: this.apiKey });

    // Load settings
    const settingsPath = path.join(__dirname, '../../config/settings.json');
    this.settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));

    // Load model configurations
    const modelsPath = path.join(__dirname, '../../config/models.json');
    this.modelConfigs = JSON.parse(fs.readFileSync(modelsPath, 'utf8'));

    this.defaultModel = options.model || this.settings.defaultModel;
    this.generationConfig = { ...this.settings.generationConfig, ...options.generationConfig };

    // Safety settings (new SDK format)
    this.safetySettings = this.settings.safetySettings.map(setting => ({
      category: setting.category,
      threshold: setting.threshold
    }));

    // Rate limiting
    this.requestQueue = [];
    this.lastRequestTime = 0;
    this.minRequestInterval = 60000 / this.settings.rateLimit.requestsPerMinute;
  }

  /**
   * Apply rate limiting
   */
  async rateLimit() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;

    if (timeSinceLastRequest < this.minRequestInterval) {
      const delay = this.minRequestInterval - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    this.lastRequestTime = Date.now();
  }

  /**
   * Generate content from text prompt
   */
  async generateContent(options) {
    await this.rateLimit();

    const { prompt, model, ...config } = options;
    const modelName = model || this.defaultModel;

    try {
      const response = await this.ai.models.generateContent({
        model: modelName,
        contents: prompt,
        config: {
          ...this.generationConfig,
          ...config,
          safetySettings: this.safetySettings
        }
      });

      return {
        text: response.text,
        candidates: response.candidates,
        promptFeedback: response.promptFeedback,
        usageMetadata: response.usageMetadata
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Generate content with streaming
   */
  async *generateContentStream(options) {
    await this.rateLimit();

    const { prompt, model, ...config } = options;
    const modelName = model || this.defaultModel;

    try {
      const stream = await this.ai.models.generateContentStream({
        model: modelName,
        contents: prompt,
        config: {
          ...this.generationConfig,
          ...config,
          safetySettings: this.safetySettings
        }
      });

      for await (const chunk of stream) {
        yield {
          text: chunk.text || '',
          done: false
        };
      }

      yield {
        text: '',
        done: true
      };
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Start a chat conversation
   */
  startChat(options = {}) {
    const { model, history = [], ...config } = options;
    const modelName = model || this.defaultModel;

    // Create chat session with new SDK
    return {
      model: modelName,
      history,
      config: {
        ...this.generationConfig,
        ...config,
        safetySettings: this.safetySettings
      },
      ai: this.ai,

      async sendMessage(message) {
        const response = await this.ai.models.generateContent({
          model: this.model,
          contents: [
            ...this.history.map(h => ({ role: h.role, parts: [{ text: h.content }] })),
            { role: 'user', parts: [{ text: message }] }
          ],
          config: this.config
        });

        // Add to history
        this.history.push({ role: 'user', content: message });
        this.history.push({ role: 'model', content: response.text });

        return {
          response: {
            text: () => response.text,
            candidates: response.candidates
          }
        };
      }
    };
  }

  /**
   * Analyze an image
   */
  async analyzeImage(options) {
    await this.rateLimit();

    const { imagePath, imageData, prompt, model = 'gemini-2.5-flash' } = options;
    const modelName = model;

    let imagePart;
    if (imagePath) {
      const imageBuffer = fs.readFileSync(imagePath);
      const mimeType = this.getMimeType(imagePath);
      imagePart = {
        inlineData: {
          data: imageBuffer.toString('base64'),
          mimeType
        }
      };
    } else if (imageData) {
      imagePart = imageData;
    } else {
      throw new Error('Either imagePath or imageData must be provided');
    }

    try {
      const response = await this.ai.models.generateContent({
        model: modelName,
        contents: [
          {
            role: 'user',
            parts: [
              { text: prompt },
              imagePart
            ]
          }
        ],
        config: {
          ...this.generationConfig,
          safetySettings: this.safetySettings
        }
      });

      return {
        text: response.text,
        candidates: response.candidates,
        usageMetadata: response.usageMetadata
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Generate with function calling
   */
  async generateWithTools(options) {
    await this.rateLimit();

    const { prompt, tools, model, ...config } = options;
    const modelName = model || this.defaultModel;

    const functionDeclarations = tools.map(tool => ({
      name: tool.name,
      description: tool.description,
      parameters: tool.parameters
    }));

    try {
      const response = await this.ai.models.generateContent({
        model: modelName,
        contents: prompt,
        tools: [{ functionDeclarations }],
        config: {
          ...this.generationConfig,
          ...config,
          safetySettings: this.safetySettings
        }
      });

      // Extract function calls from response
      const functionCall = response.candidates?.[0]?.content?.parts?.find(
        part => part.functionCall
      )?.functionCall;

      return {
        text: response.text || '',
        functionCall: functionCall ? {
          name: functionCall.name,
          args: functionCall.args
        } : null,
        usageMetadata: response.usageMetadata
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Count tokens in text
   */
  async countTokens(text, model = null) {
    const modelName = model || this.defaultModel;

    try {
      const result = await this.ai.models.countTokens({
        model: modelName,
        contents: text
      });
      return result.totalTokens;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Embed text for semantic search
   */
  async embedContent(text, model = 'text-embedding-004') {
    await this.rateLimit();

    try {
      const result = await this.ai.models.embedContent({
        model: model,
        content: text
      });
      return result.embedding.values;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get MIME type from file path
   */
  getMimeType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.webp': 'image/webp',
      '.heic': 'image/heic',
      '.heif': 'image/heif'
    };
    return mimeTypes[ext] || 'application/octet-stream';
  }

  /**
   * Handle API errors
   */
  handleError(error) {
    const errorResponse = {
      error: true,
      message: error.message,
      type: error.constructor.name
    };

    if (error.message.includes('API key')) {
      errorResponse.type = 'AuthenticationError';
      errorResponse.message = 'Invalid API key. Check your GEMINI_API_KEY';
    } else if (error.message.includes('quota') || error.message.includes('rate limit')) {
      errorResponse.type = 'RateLimitError';
      errorResponse.message = 'Rate limit exceeded. Please wait and retry';
    } else if (error.message.includes('safety')) {
      errorResponse.type = 'SafetyError';
      errorResponse.message = 'Content blocked by safety filters';
    }

    if (this.settings.logging.logRequests) {
      console.error('Gemini API Error:', errorResponse);
    }

    throw errorResponse;
  }

  /**
   * Get available models
   */
  getAvailableModels() {
    return this.modelConfigs.models;
  }

  /**
   * Get recommended model for task
   */
  getRecommendedModel(taskType) {
    return this.modelConfigs.modelSelection[taskType] || this.defaultModel;
  }

  /**
   * List models from API
   */
  async listModels() {
    try {
      const models = await this.ai.models.list();
      return models;
    } catch (error) {
      return this.handleError(error);
    }
  }
}

module.exports = { GeminiClient };
