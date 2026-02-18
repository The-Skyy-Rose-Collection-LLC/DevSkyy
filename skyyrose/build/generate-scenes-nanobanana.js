/**
 * SkyyRose - Scene Generation with Nanobanana Pro
 * Generates immersive scene backgrounds for 3D experience
 *
 * Focus: 6 luxury showroom environments across 3 collections
 */

const path = require('path');
const fs = require('fs').promises;
const { execSync } = require('child_process');

// SkyyRose Brand DNA for Scenes
const SCENE_SPECS = {
  'BLACK ROSE': {
    color: '#B76E79',
    mood: 'Gothic romance, mysterious elegance, dark florals',
    palette: 'Deep blacks, rose gold accents, burgundy shadows, moonlight silver',
    settings: 'Gothic gardens, cathedral interiors, moonlit terraces, vintage libraries with dark florals'
  },
  'LOVE HURTS': {
    color: '#8B0000',
    mood: 'Dramatic passion, edgy sophistication, bold intensity',
    palette: 'Blood red, deep crimson, black leather, gold hardware',
    settings: 'Dramatic ballrooms, baroque theaters, candlelit chambers, edgy urban nightscapes'
  },
  'SIGNATURE': {
    color: '#D4AF37',
    mood: 'High fashion prestige, editorial excellence, luxury power',
    palette: 'Champagne gold, pure white, marble textures, crystal clarity',
    settings: 'Minimalist runways, marble penthouses, modern art galleries, luxury hotel lobbies'
  }
};

// Scene Definitions
const SCENES = [
  // BLACK ROSE Scenes
  {
    id: 'black-rose-garden',
    collection: 'BLACK ROSE',
    name: 'The Gothic Garden',
    description: 'Moonlit gothic garden with wrought-iron rose arbors, cobblestone pathways winding through dark florals, vintage lamp posts casting rose-gold light, mysterious foggy atmosphere, black roses blooming everywhere, gothic architecture in background',
    aspectRatio: '16:9',
    priority: 1 // Primary scene
  },
  {
    id: 'black-rose-interior',
    collection: 'BLACK ROSE',
    name: 'The Cathedral Sanctuary',
    description: 'Gothic cathedral interior with soaring vaulted ceilings, stained glass windows casting colored light, enchanted rose under glass dome centerpiece, scattered rose petals on marble floor, candlelight creating dramatic shadows, ornate furniture with deep purple velvet',
    aspectRatio: '16:9',
    priority: 2
  },

  // LOVE HURTS Scenes
  {
    id: 'love-hurts-ballroom',
    collection: 'LOVE HURTS',
    name: 'The Grand Ballroom',
    description: 'Opulent baroque ballroom with crystal chandeliers, ornate gold-framed mirrors, red velvet curtains, polished marble floors reflecting candlelight, grand staircase, rose under glass dome centerpiece surrounded by candles and rose petals, dramatic passionate atmosphere',
    aspectRatio: '16:9',
    priority: 1 // Primary scene
  },
  {
    id: 'love-hurts-theater',
    collection: 'LOVE HURTS',
    name: 'The Theater Stage',
    description: 'Vintage theater stage with dramatic red curtains, ornate proscenium arch with gold details, stage lights creating dramatic shadows, plush red velvet seating, mysterious backstage glimpse, passionate and edgy atmosphere',
    aspectRatio: '16:9',
    priority: 2
  },

  // SIGNATURE Scenes
  {
    id: 'signature-runway',
    collection: 'SIGNATURE',
    name: 'The Luxury Runway',
    description: 'Minimalist high-fashion runway with sleek black catwalk, professional stage lighting, floor-to-ceiling windows with city skyline, clean white walls, marble accents, modern sculptural seating, champagne and gold accent lighting, museum-quality prestige atmosphere',
    aspectRatio: '16:9',
    priority: 1 // Primary scene
  },
  {
    id: 'signature-penthouse',
    collection: 'SIGNATURE',
    name: 'The Penthouse Gallery',
    description: 'Ultra-luxury penthouse art gallery with floor-to-ceiling windows overlooking city, white marble floors, modern art pieces, gold accent lighting, minimalist luxury furniture, crystal clear atmosphere, editorial prestige',
    aspectRatio: '16:9',
    priority: 2
  }
];

/**
 * Create advanced prompt for scene generation
 */
function createScenePrompt(scene) {
  const brandDNA = SCENE_SPECS[scene.collection];

  return `
ULTRA-LUXURY FASHION SHOWROOM ENVIRONMENT

PROJECT: SkyyRose ${scene.collection} Collection - ${scene.name}
PURPOSE: Immersive 3D virtual showroom background for high-end e-commerce
QUALITY STANDARD: Architectural Digest editorial + luxury hotel photography

ENVIRONMENT DESCRIPTION:
${scene.description}

ARCHITECTURAL STYLE & DESIGN:
${scene.collection === 'BLACK ROSE' ?
`- Gothic Revival architecture with ornate details
- Wrought-iron elements with rose motifs
- Vintage elegant finishes
- Stone, dark wood, and aged metals
- Mysterious, romantic atmosphere` :
scene.collection === 'LOVE HURTS' ?
`- Baroque opulence with dramatic flair
- Ornate gold details and crystal elements
- Rich red velvet and deep burgundy
- Theatrical, passionate design
- Bold, commanding presence` :
`- Contemporary minimalist architecture
- Clean lines and geometric precision
- Marble, glass, and polished metals
- Museum-quality luxury finishes
- Sophisticated, editorial elegance`}

LIGHTING DESIGN:
- Professional interior photography lighting
- ${brandDNA.color} color wash as accent lighting throughout space
- Dramatic shadows creating depth and dimension
- Ambient, atmospheric, luxury showroom quality
- Strategic highlights on architectural features
- Soft glow creating warmth and invitation

COLOR PALETTE:
- Primary colors: ${brandDNA.palette}
- Brand accent color: ${brandDNA.color} prominently featured
- Rich, saturated colors with luxury depth
- Color grading: Architectural Digest magazine quality
- Mood: ${brandDNA.mood}

COMPOSITION & FRAMING:
- Wide-angle interior photography perspective
- Straight architectural lines (no lens distortion)
- Clear foreground, midground, background depth layers
- Multiple focal points suitable for product hotspot placement
- Spacious, breathable, luxury boutique aesthetic
- Rule of thirds composition for visual interest

SPATIAL REQUIREMENTS:
- Open space suitable for 6-8 product hotspot placements
- Clear walkways and viewing areas
- Depth and dimension for immersive feel
- NO people, NO mannequins, NO products (environment only)
- Ready for virtual product overlay

ATMOSPHERE & MOOD:
- Inviting yet exclusive luxury showroom
- Aspirational, desire-inducing environment
- Editorial photography quality
- Makes viewers want to step inside
- Reflects ${scene.collection} brand identity perfectly

TECHNICAL SPECIFICATIONS:
- Resolution: 8K ultra-high quality (7680x4320 pixels)
- Aspect ratio: 16:9 (optimal for immersive web experience)
- Format: Landscape orientation
- Quality: Magazine editorial standard (Architectural Digest, Elle Decor)
- Sharpness: Crystal clear throughout entire frame
- Perspective: Professional architectural photography

REFERENCE QUALITY:
- Luxury hotel lobby photography (Four Seasons, Ritz-Carlton level)
- Architectural Digest editorial spreads
- High-end retail boutique photography (Chanel, Dior showrooms)
- Museum-quality interior design photography

CRITICAL REQUIREMENTS:
1. Space must feel like walking into an exclusive luxury boutique
2. Lighting must complement future product photography overlays
3. Atmosphere must perfectly match ${scene.collection} brand identity
4. NO people or mannequins - pure environment photography
5. Professional luxury showroom standard throughout
6. Color accuracy to ${scene.collection} palette is essential
7. Image must be suitable for 6-8 interactive product hotspots

BRAND ESSENCE:
The environment should embody: ${brandDNA.mood}
Settings inspiration: ${brandDNA.settings}
This is the ${scene.name} - make it unforgettable.

Generate an 8K ultra-luxury showroom environment that exceeds Architectural Digest quality.
  `.trim();
}

/**
 * Generate scene with Nanobanana using MCP
 */
async function generateScene(scene) {
  console.log(`\n🎬 Generating: ${scene.name}`);
  console.log(`   Collection: ${scene.collection}`);
  console.log(`   ID: ${scene.id}`);
  console.log('─'.repeat(70));

  const prompt = createScenePrompt(scene);
  const outputDir = path.join(__dirname, '../assets/images/scenes/ai-generated');
  const outputPath = path.join(outputDir, `${scene.id}.png`);

  // Ensure output directory exists
  await fs.mkdir(outputDir, { recursive: true });

  try {
    // Save prompt for reference
    const promptPath = path.join(outputDir, `${scene.id}-prompt.txt`);
    await fs.writeFile(promptPath, prompt);
    console.log(`   💾 Prompt saved: ${path.basename(promptPath)}`);

    // Check if Nanobanana is available
    const nanobananaPath = path.join(__dirname, '../../gemini/extensions/nanobanana');

    console.log(`\n   🤖 Calling Nanobanana MCP Server...`);
    console.log(`   📝 Prompt length: ${prompt.length} characters`);

    // Call Nanobanana via npx (MCP server)
    const command = `cd "${nanobananaPath}" && npx ts-node mcp-server/src/index.ts generate-image --prompt "${prompt.replace(/"/g, '\\"')}" --output "${outputPath}" --aspect-ratio ${scene.aspectRatio} --no-preview`;

    console.log(`   ⚙️  Executing Nanobanana...`);

    const output = execSync(command, {
      encoding: 'utf-8',
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer
      env: {
        ...process.env,
        NANOBANANA_GEMINI_API_KEY: process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY,
        NANOBANANA_MODEL: 'gemini-2.5-flash-image'
      }
    });

    console.log(output);

    // Check if file was created
    const stats = await fs.stat(outputPath);

    console.log(`\n   ✅ SUCCESS!`);
    console.log(`   📁 Output: ${path.basename(outputPath)}`);
    console.log(`   💾 Size: ${(stats.size / 1024 / 1024).toFixed(2)}MB`);

    return {
      success: true,
      scene: scene.id,
      path: outputPath,
      size: stats.size
    };

  } catch (error) {
    console.error(`\n   ❌ FAILED: ${error.message}`);

    // Check for common issues
    if (error.message.includes('GEMINI_API_KEY') || error.message.includes('GOOGLE_API_KEY')) {
      console.error(`\n   ⚠️  API Key not found!`);
      console.error(`   💡 Set GEMINI_API_KEY environment variable`);
      console.error(`   💡 Or set GOOGLE_API_KEY environment variable`);
    }

    return {
      success: false,
      scene: scene.id,
      error: error.message
    };
  }
}

/**
 * Generate all scenes
 */
async function generateAllScenes() {
  console.log('\n🌹 SkyyRose Scene Generation with Nanobanana Pro');
  console.log('🤖 Powered by Gemini 2.5 Flash Image');
  console.log('='.repeat(70));

  const startTime = Date.now();
  const results = [];

  // Sort by priority
  const sortedScenes = SCENES.sort((a, b) => a.priority - b.priority);

  console.log(`\n📋 Generation Queue:`);
  sortedScenes.forEach((scene, i) => {
    console.log(`   ${i + 1}. ${scene.name} (${scene.collection})`);
  });

  console.log('\n' + '='.repeat(70));

  // Generate scenes sequentially (to respect rate limits)
  for (const scene of sortedScenes) {
    const result = await generateScene(scene);
    results.push(result);

    // Rate limiting: 6 second delay between requests
    if (scene !== sortedScenes[sortedScenes.length - 1]) {
      console.log(`\n   ⏸️  Rate limiting: Waiting 6 seconds...`);
      await new Promise(resolve => setTimeout(resolve, 6000));
    }
  }

  const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(1);

  console.log('\n' + '='.repeat(70));
  console.log('✨ Scene Generation Complete!');
  console.log('='.repeat(70));

  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);

  console.log(`\n📊 Results:`);
  console.log(`   ✅ Successful: ${successful.length}/${results.length}`);
  console.log(`   ❌ Failed: ${failed.length}/${results.length}`);
  console.log(`   ⏱️  Duration: ${duration} minutes`);

  if (successful.length > 0) {
    const totalSize = successful.reduce((sum, r) => sum + r.size, 0);
    console.log(`   💾 Total size: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);
    console.log(`\n📁 Generated scenes:`);
    successful.forEach(r => {
      console.log(`   ✓ ${r.scene}`);
    });
  }

  if (failed.length > 0) {
    console.log(`\n❌ Failed scenes:`);
    failed.forEach(r => {
      console.log(`   ✗ ${r.scene}: ${r.error}`);
    });
  }

  // Save generation report
  const reportPath = path.join(__dirname, '../assets/images/scenes/ai-generated/GENERATION_REPORT.json');
  await fs.writeFile(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    duration: `${duration} minutes`,
    results: results,
    scenes: SCENES
  }, null, 2));

  console.log(`\n📄 Report saved: ${path.relative(process.cwd(), reportPath)}`);

  console.log('\n🎯 Next steps:');
  console.log('   1. Review generated scenes in: assets/images/scenes/ai-generated/');
  console.log('   2. Run: npm run build:scenes (to optimize for web)');
  console.log('   3. Update 3D immersive pages with new scene paths');
  console.log('');
}

// Execute
if (require.main === module) {
  generateAllScenes().catch(error => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = {
  SCENES,
  SCENE_SPECS,
  createScenePrompt,
  generateScene,
  generateAllScenes
};
