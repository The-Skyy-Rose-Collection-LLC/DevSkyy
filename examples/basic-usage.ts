/**
 * DevSkyy Basic Usage Examples
 * Demonstrates core functionality of the TypeScript/JavaScript SDK
 */

import {
  DevSkyy,
  initialize,
  createTask,
  getAgents,
  openaiService,
  threeJSService
} from '../src/index.js';

// Example 1: Basic Platform Initialization
async function basicInitialization(): Promise<void> {
  console.log('🚀 Initializing DevSkyy Platform...');

  try {
    await initialize();
    console.log('✅ Platform initialized successfully');

    // Get platform statistics
    const devSkyy = new DevSkyy();
    const stats = devSkyy.getStats();
    console.log('📊 Platform Stats:', stats);

  } catch (error) {
    console.error('❌ Initialization failed:', error);
  }
}

// Example 2: Agent Management
async function agentManagement(): Promise<void> {
  console.log('🤖 Managing Agents...');

  // Get all agents
  const agents = getAgents();
  console.log(`Found ${agents.length} agents`);

  // List agents by type
  agents.forEach(agent => {
    console.log(`- ${agent.name} (${agent.type}): ${agent.status}`);
  });

  // Create tasks for different agents
  try {
    const wordpressTaskId = await createTask(
      'wordpress_agent',
      'create_post',
      {
        title: 'Welcome to DevSkyy',
        content: 'This post was created by the WordPress agent!',
        status: 'publish'
      },
      'high'
    );
    console.log(`✅ WordPress task created: ${wordpressTaskId}`);

    const seoTaskId = await createTask(
      'seo_agent',
      'analyze_keywords',
      {
        content: 'DevSkyy enterprise platform with 54 agents',
        targetKeywords: ['enterprise', 'platform', 'agents', 'automation']
      }
    );
    console.log(`✅ SEO task created: ${seoTaskId}`);

  } catch (error) {
    console.error('❌ Task creation failed:', error);
  }
}

// Example 3: OpenAI Integration
async function openaiIntegration(): Promise<void> {
  console.log('🧠 OpenAI Integration...');

  try {
    // Text completion
    const completion = await openaiService.createCompletion({
      prompt: 'Explain the benefits of using DevSkyy enterprise platform:',
      maxTokens: 200,
      temperature: 0.7
    });

    if (completion.success) {
      console.log('✅ Completion generated:', completion.data.choices[0]?.text);
    }

    // Chat completion
    const chatResponse = await openaiService.createChatCompletion({
      messages: [
        { role: 'system', content: 'You are a helpful assistant for DevSkyy platform.' },
        { role: 'user', content: 'How do I create a new agent?' }
      ],
      maxTokens: 150
    });

    if (chatResponse.success) {
      console.log('✅ Chat response:', chatResponse.data.choices[0]?.text);
    }

    // Image generation
    const imageResponse = await openaiService.createImage({
      prompt: 'A futuristic enterprise platform dashboard with 54 AI agents',
      size: '1024x1024',
      quality: 'hd'
    });

    if (imageResponse.success) {
      console.log('✅ Image generated:', imageResponse.data.data[0]?.url);
    }

  } catch (error) {
    console.error('❌ OpenAI integration failed:', error);
  }
}

// Example 4: Three.js 3D Visualization
async function threejsVisualization(): Promise<void> {
  console.log('🎨 Three.js 3D Visualization...');

  // This would typically run in a browser environment
  if (typeof window === 'undefined') {
    console.log('⚠️ Three.js examples require browser environment');
    return;
  }

  try {
    // Create container element
    const container = document.createElement('div');
    container.style.width = '800px';
    container.style.height = '600px';
    document.body.appendChild(container);

    // Initialize Three.js scene
    threeJSService.initializeScene(container, {
      enableShadows: true,
      backgroundColor: 0x222222,
      fog: { color: 0x222222, near: 1, far: 100 }
    });

    // Create 3D objects representing agents
    const agentCubes: THREE.Mesh[] = [];
    const agents = getAgents();

    agents.slice(0, 10).forEach((agent, index) => {
      const cube = threeJSService.createCube(
        1,
        Math.random() * 0xffffff,
        [
          (index % 5) * 2 - 4,
          Math.floor(index / 5) * 2 - 1,
          0
        ]
      );

      threeJSService.addToScene(cube);
      agentCubes.push(cube);
    });

    // Add ground plane
    const ground = threeJSService.createPlane(20, 20, 0x404040);
    threeJSService.addToScene(ground);

    // Start animation
    threeJSService.startAnimation(() => {
      // Rotate agent cubes
      agentCubes.forEach((cube, index) => {
        cube.rotation.x += 0.01;
        cube.rotation.y += 0.01 * (index + 1);
      });
    });

    console.log('✅ 3D visualization started');

    // Get scene statistics
    const stats = threeJSService.getSceneStats();
    console.log('📊 Scene Stats:', stats);

  } catch (error) {
    console.error('❌ Three.js visualization failed:', error);
  }
}

// Example 5: Real-time Agent Monitoring
async function agentMonitoring(): Promise<void> {
  console.log('📊 Agent Monitoring...');

  const devSkyy = new DevSkyy();

  // Monitor agent tasks
  setInterval(async () => {
    const stats = devSkyy.getStats();
    console.log('📈 Current Stats:', {
      timestamp: new Date().toISOString(),
      ...stats
    });

    // Health check
    const health = await devSkyy.healthCheck();
    console.log('🏥 Health Status:', health.status);

  }, 5000); // Every 5 seconds
}

// Example 6: Error Handling and Cleanup
async function errorHandlingExample(): Promise<void> {
  console.log('🛡️ Error Handling Example...');

  const devSkyy = new DevSkyy();

  try {
    // Attempt to use service before initialization
    devSkyy.getStats();
  } catch (error) {
    console.log('✅ Caught expected error:', (error as Error).message);
  }

  // Proper initialization and cleanup
  try {
    await devSkyy.initialize();

    // Use the platform
    const stats = devSkyy.getStats();
    console.log('Platform working correctly:', stats);

    // Graceful shutdown
    await devSkyy.shutdown();
    console.log('✅ Platform shutdown completed');

  } catch (error) {
    console.error('❌ Error during operation:', error);
  }
}

// Main execution function
async function runExamples(): Promise<void> {
  console.log('🎯 DevSkyy SDK Examples\n');

  await basicInitialization();
  console.log('\n' + '='.repeat(50) + '\n');

  await agentManagement();
  console.log('\n' + '='.repeat(50) + '\n');

  await openaiIntegration();
  console.log('\n' + '='.repeat(50) + '\n');

  await threejsVisualization();
  console.log('\n' + '='.repeat(50) + '\n');

  await agentMonitoring();
  console.log('\n' + '='.repeat(50) + '\n');

  await errorHandlingExample();

  console.log('\n🎉 All examples completed!');
}

// Run examples if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runExamples().catch(console.error);
}

export {
  basicInitialization,
  agentManagement,
  openaiIntegration,
  threejsVisualization,
  agentMonitoring,
  errorHandlingExample,
  runExamples
};
