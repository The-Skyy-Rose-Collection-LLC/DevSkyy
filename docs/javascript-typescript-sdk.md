# DevSkyy JavaScript/TypeScript SDK

Complete JavaScript and TypeScript SDK for the DevSkyy Enterprise Platform's 54-agent ecosystem.

## 🚀 Quick Start

### Installation

```bash
npm install devskyy
# or
yarn add devskyy
```

### Basic Usage

```typescript
import { initialize, createTask, getAgents } from 'devskyy';

// Initialize the platform
await initialize();

// Create a task for the WordPress agent
const taskId = await createTask('wordpress_agent', 'create_post', {
  title: 'Hello World',
  content: 'This post was created by DevSkyy!'
});

// Get all available agents
const agents = getAgents();
console.log(`Available agents: ${agents.length}`);
```

## 📦 Features

### Core Platform
- **54-Agent Ecosystem**: Complete integration with all DevSkyy agents
- **TypeScript Support**: Full type safety and IntelliSense
- **Real-time Monitoring**: Live agent status and task tracking
- **Error Handling**: Comprehensive error management and recovery

### AI Integrations
- **OpenAI API**: GPT-4o, GPT-4o-mini, o1-preview models
- **Text Generation**: Completions and chat completions
- **Image Generation**: DALL-E 3 integration
- **Vision Analysis**: Image understanding capabilities
- **Embeddings**: Text vectorization for semantic search

### 3D Visualization
- **Three.js Integration**: Complete 3D graphics support
- **Scene Management**: Easy scene creation and manipulation
- **Animation System**: Built-in animation loops and controls
- **WebGL Optimization**: High-performance rendering

### Development Tools
- **ESLint Configuration**: Comprehensive linting rules
- **Prettier Formatting**: Consistent code formatting
- **Jest Testing**: Complete test suite with utilities
- **TypeScript Compilation**: Optimized build process

## 🏗️ Architecture

### Core Classes

#### `DevSkyy`
Main SDK class for platform management:

```typescript
import { DevSkyy } from 'devskyy';

const platform = new DevSkyy();
await platform.initialize();

// Get platform statistics
const stats = platform.getStats();

// Health check
const health = await platform.healthCheck();

// Graceful shutdown
await platform.shutdown();
```

#### `AgentService`
Manages the 54-agent ecosystem:

```typescript
import { AgentService } from 'devskyy';

const agentService = new AgentService();

// Get agents by type
const wordpressAgents = agentService.getAgentsByType('wordpress_agent');

// Create and monitor tasks
const taskId = await agentService.createTask('seo_agent', 'analyze_keywords', {
  content: 'Your content here',
  targetKeywords: ['keyword1', 'keyword2']
});

// Get task status
const task = agentService.getTask(taskId);
```

#### `OpenAIService`
Complete OpenAI API integration:

```typescript
import { openaiService } from 'devskyy';

// Text completion
const completion = await openaiService.createCompletion({
  prompt: 'Explain quantum computing',
  maxTokens: 200
});

// Chat completion
const chat = await openaiService.createChatCompletion({
  messages: [
    { role: 'user', content: 'Hello!' }
  ]
});

// Image generation
const image = await openaiService.createImage({
  prompt: 'A futuristic cityscape',
  size: '1024x1024'
});
```

#### `ThreeJSService`
3D graphics and visualization:

```typescript
import { threeJSService } from 'devskyy';

// Initialize scene
const container = document.getElementById('canvas-container');
threeJSService.initializeScene(container);

// Create 3D objects
const cube = threeJSService.createCube(1, 0x00ff00);
threeJSService.addToScene(cube);

// Start animation
threeJSService.startAnimation(() => {
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
});
```

## 🤖 Agent Types

The SDK supports all 54 DevSkyy agents:

### Content & Media Agents
- `wordpress_agent` - WordPress management
- `content_agent` - Content generation
- `seo_agent` - SEO optimization
- `social_media_agent` - Social media management

### Technical Agents
- `api_agent` - API integration
- `database_agent` - Database management
- `security_agent` - Security monitoring
- `deployment_agent` - Deployment automation

### AI & Analytics Agents
- `ml_agent` - Machine learning
- `data_agent` - Data processing
- `analytics_agent` - Analytics & reporting
- `monitoring_agent` - System monitoring

## 📋 Configuration

### Environment Variables

```bash
# Core Configuration
NODE_ENV=production
API_VERSION=v1
BASE_URL=https://api.devskyy.com

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=devskyy
DB_USER=devskyy
DB_PASSWORD=your-password

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Security
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# Three.js
THREEJS_ENABLE_WEBGL2=true
THREEJS_ENABLE_SHADOWS=true
THREEJS_ANTIALIAS=true
```

### TypeScript Configuration

The SDK includes optimized TypeScript configuration:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests for CI
npm run test:ci
```

### Test Utilities

The SDK includes comprehensive test utilities:

```typescript
import { createMockAgent, createMockTask, waitFor } from 'devskyy/tests';

describe('Agent Service', () => {
  it('should create tasks', async () => {
    const agent = createMockAgent({ type: 'wordpress_agent' });
    const task = createMockTask({ agentId: agent.id });

    // Test implementation
    expect(task).toHaveValidStructure({
      id: 'string',
      agentId: 'string',
      status: 'string'
    });
  });
});
```

## 🔧 Development Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run build:watch  # Build in watch mode

# Code Quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint issues
npm run format       # Format with Prettier
npm run type-check   # TypeScript type checking

# Maintenance
npm run clean        # Clean build artifacts
npm run deps:update  # Update dependencies
npm run security:audit # Security audit
```

## 📚 Examples

### Complete Agent Workflow

```typescript
import { initialize, createTask, getTask } from 'devskyy';

async function completeWorkflow() {
  // Initialize platform
  await initialize();

  // Create content with content agent
  const contentTaskId = await createTask('content_agent', 'generate_article', {
    topic: 'AI in Enterprise',
    length: 1000,
    tone: 'professional'
  });

  // Wait for completion
  let contentTask = getTask(contentTaskId);
  while (contentTask?.status === 'running') {
    await new Promise(resolve => setTimeout(resolve, 1000));
    contentTask = getTask(contentTaskId);
  }

  if (contentTask?.status === 'completed') {
    // Optimize with SEO agent
    const seoTaskId = await createTask('seo_agent', 'optimize_content', {
      content: contentTask.result?.data.content,
      targetKeywords: ['AI', 'enterprise', 'automation']
    });

    // Publish with WordPress agent
    const publishTaskId = await createTask('wordpress_agent', 'create_post', {
      title: contentTask.result?.data.title,
      content: contentTask.result?.data.content,
      status: 'publish'
    });

    console.log('Content workflow completed!');
  }
}
```

## 🔒 Security

### Best Practices

1. **Environment Variables**: Store sensitive data in environment variables
2. **API Key Rotation**: Regularly rotate API keys
3. **Input Validation**: Validate all inputs before processing
4. **Error Handling**: Implement comprehensive error handling
5. **Rate Limiting**: Respect API rate limits

### Security Features

- JWT token authentication
- AES-256-GCM encryption
- CSRF protection
- Input sanitization
- Secure headers

## 📖 API Reference

### Types

```typescript
interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  capabilities: string[];
  version: string;
  lastActive: Date;
  metadata: Record<string, unknown>;
}

interface AgentTask {
  id: string;
  agentId: string;
  type: string;
  payload: Record<string, unknown>;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  result?: TaskResult;
  error?: TaskError;
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: [docs.devskyy.com](https://docs.devskyy.com)
- **Issues**: [GitHub Issues](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues)
- **Discord**: [DevSkyy Community](https://discord.gg/devskyy)
- **Email**: support@devskyy.com
