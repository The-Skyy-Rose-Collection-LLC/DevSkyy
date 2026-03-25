/**
 * OpenAI Client for Node.js — DevSkyy
 * Covers: Chat, Streaming, Vision, Embeddings, Images, Assistants, Realtime
 * SDK: openai v4 + @openai/agents
 */

const OpenAI = require('openai');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });

class OpenAIClient {
  constructor(options = {}) {
    this.apiKey = options.apiKey || process.env.OPENAI_API_KEY;

    if (!this.apiKey) {
      throw new Error('OpenAI API key required. Set OPENAI_API_KEY in .env');
    }

    this.client = new OpenAI({ apiKey: this.apiKey });

    const settingsPath = path.join(__dirname, '../../config/settings.json');
    this.settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));

    const modelsPath = path.join(__dirname, '../../config/models.json');
    this.modelConfigs = JSON.parse(fs.readFileSync(modelsPath, 'utf8'));

    this.defaultModel = options.model || this.settings.defaultModel;
    this.generationConfig = { ...this.settings.generationConfig, ...options.generationConfig };

    // Rate limiting
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

  /** Generate content from text prompt */
  async generateContent(options) {
    await this.rateLimit();
    const { prompt, model, systemPrompt, ...config } = options;

    try {
      const messages = [];
      if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
      messages.push({ role: 'user', content: prompt });

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

  /** Streaming response */
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
          model: this.model,
          messages: this.history,
          ...genConfig
        });

        const reply = response.choices[0].message.content;
        this.history.push({ role: 'assistant', content: reply });

        return { response: { text: () => reply }, usage: response.usage };
      }
    };
  }

  /** Analyze image (vision) */
  async analyzeImage(options) {
    await this.rateLimit();
    const { imagePath, imageUrl, prompt, model = 'gpt-4o', detail = 'auto' } = options;

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

  /** Function / tool calling */
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

  /** Structured output with JSON schema */
  async generateStructured(options) {
    await this.rateLimit();
    const { prompt, schema, schemaName = 'response', model, systemPrompt } = options;

    const messages = [];
    if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
    messages.push({ role: 'user', content: prompt });

    try {
      const response = await this.client.chat.completions.create({
        model: model || this.defaultModel,
        messages,
        response_format: {
          type: 'json_schema',
          json_schema: { name: schemaName, schema, strict: true }
        }
      });

      return {
        data: JSON.parse(response.choices[0].message.content),
        usage: response.usage
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Generate embeddings */
  async embedContent(text, model = 'text-embedding-3-small') {
    await this.rateLimit();

    const input = Array.isArray(text) ? text : [text];
    try {
      const response = await this.client.embeddings.create({ model, input });
      return Array.isArray(text)
        ? response.data.map(d => d.embedding)
        : response.data[0].embedding;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Generate images */
  async generateImage(options) {
    await this.rateLimit();
    const {
      prompt, model = 'gpt-image-1',
      size = '1024x1024', quality = 'standard', n = 1
    } = options;

    try {
      const response = await this.client.images.generate({
        model, prompt, size, quality, n
      });
      return response.data.map(img => ({ url: img.url, b64: img.b64_json }));
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Transcribe audio with Whisper */
  async transcribeAudio(options) {
    const { filePath, language, model = 'whisper-1' } = options;
    try {
      const response = await this.client.audio.transcriptions.create({
        file: fs.createReadStream(filePath),
        model,
        ...(language ? { language } : {})
      });
      return { text: response.text };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Text-to-speech */
  async textToSpeech(options) {
    const { text, voice = 'alloy', model = 'tts-1-hd', outputPath } = options;
    try {
      const mp3 = await this.client.audio.speech.create({
        model, voice, input: text
      });
      const buffer = Buffer.from(await mp3.arrayBuffer());
      if (outputPath) fs.writeFileSync(outputPath, buffer);
      return buffer;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Create an Assistant */
  async createAssistant(options) {
    const { name, instructions, model, tools = [] } = options;
    try {
      return await this.client.beta.assistants.create({
        name, instructions,
        model: model || this.defaultModel,
        tools
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /** Run an Assistant on a thread */
  async runAssistant(options) {
    const { assistantId, message } = options;
    try {
      const thread = await this.client.beta.threads.create();
      await this.client.beta.threads.messages.create(thread.id, {
        role: 'user', content: message
      });

      const run = await this.client.beta.threads.runs.createAndPoll(
        thread.id, { assistant_id: assistantId }
      );

      if (run.status !== 'completed') {
        throw new Error(`Run ended with status: ${run.status}`);
      }

      const messages = await this.client.beta.threads.messages.list(thread.id);
      const reply = messages.data[0].content[0];
      return { text: reply.type === 'text' ? reply.text.value : '', threadId: thread.id };
    } catch (error) {
      return this.handleError(error);
    }
  }

  handleError(error) {
    const response = { error: true, message: error.message, type: error.constructor.name };

    if (error.status === 401) {
      response.type = 'AuthenticationError';
      response.message = 'Invalid API key. Check OPENAI_API_KEY';
    } else if (error.status === 429) {
      response.type = 'RateLimitError';
      response.message = 'Rate limit exceeded. Please wait and retry';
    } else if (error.status === 400) {
      response.type = 'BadRequestError';
    }

    if (this.settings.logging.logRequests) {
      console.error('OpenAI API Error:', response);
    }

    throw response;
  }

  getAvailableModels() { return this.modelConfigs.models; }
  getRecommendedModel(taskType) {
    return this.modelConfigs.modelSelection[taskType] || this.defaultModel;
  }

  async listModels() {
    try {
      const response = await this.client.models.list();
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
}

module.exports = { OpenAIClient };
