/**
 * SkyyRose - Scene Generation with Gemini 2.5 Flash Image
 * Direct integration using @google/genai SDK (same as Nanobanana)
 *
 * Generates 6 immersive scene backgrounds for 3D experience
 */

const path = require('path');
const fs = require('fs').promises;

// Import Gemini Client (reuse existing integration)
const { GeminiClient } = require('../../gemini/clients/node/gemini-client');

// Scene specifications (same as before)
const SCENES = [
  {
    id: 'black-rose-garden',
    collection: 'BLACK ROSE',
    name: 'The Gothic Garden',
    prompt: `
Ultra-luxury fashion showroom: Moonlit gothic garden with wrought-iron rose arbors, cobblestone pathways through dark florals, vintage lamp posts with rose-gold light (#B76E79), mysterious fog, black roses everywhere, gothic architecture background.
Style: Architectural Digest editorial quality.
Lighting: Professional interior photography with rose-gold (#B76E79) accent wash, dramatic shadows.
Colors: Deep blacks, rose gold, burgundy, moonlight silver.
Composition: Wide-angle, 16:9, clear space for 6-8 product placements.
NO people, NO mannequins.
Atmosphere: Inviting luxury boutique, gothic romance, mysterious elegance.
Quality: 8K ultra-high resolution, magazine editorial standard.
    `.trim(),
    aspectRatio: '16:9',
    priority: 1
  },
  {
    id: 'black-rose-interior',
    collection: 'BLACK ROSE',
    name: 'The Cathedral Sanctuary',
    prompt: `
Ultra-luxury fashion showroom: Gothic cathedral interior, soaring vaulted ceilings, stained glass windows with colored light, enchanted rose under glass dome centerpiece, scattered rose petals on marble floor, candlelight with dramatic shadows, ornate furniture with deep purple velvet.
Style: Architectural Digest + luxury hotel photography.
Lighting: Professional with rose-gold (#B76E79) accent highlights.
Colors: Deep blacks, rose gold, purple velvet, stained glass colors.
Composition: Wide-angle 16:9, space for 6-8 product placements.
NO people, NO mannequins.
Atmosphere: Gothic sanctuary, romantic mystery, luxury boutique.
Quality: 8K ultra-high resolution, editorial standard.
    `.trim(),
    aspectRatio: '16:9',
    priority: 2
  },
  {
    id: 'love-hurts-ballroom',
    collection: 'LOVE HURTS',
    name: 'The Grand Ballroom',
    prompt: `
Ultra-luxury fashion showroom: Opulent baroque ballroom, crystal chandeliers, ornate gold mirrors, red velvet curtains, polished marble reflecting candlelight, grand staircase, rose under glass dome with candles and petals, dramatic passionate atmosphere.
Style: Luxury hotel + Architectural Digest quality.
Lighting: Professional with blood-red (#8B0000) accent lighting, dramatic shadows.
Colors: Blood red, deep crimson, gold accents, black marble.
Composition: Wide-angle 16:9, space for 6-8 product placements.
NO people, NO mannequins.
Atmosphere: Dramatic passion, baroque luxury, edgy sophistication.
Quality: 8K ultra-high resolution, editorial standard.
    `.trim(),
    aspectRatio: '16:9',
    priority: 1
  },
  {
    id: 'love-hurts-theater',
    collection: 'LOVE HURTS',
    name: 'The Theater Stage',
    prompt: `
Ultra-luxury fashion showroom: Vintage theater stage, dramatic red curtains, ornate gold proscenium arch, stage lights creating shadows, plush red velvet seating, mysterious backstage glimpse, passionate edgy atmosphere.
Style: Editorial photography quality.
Lighting: Theatrical lighting with red (#8B0000) accent, dramatic shadows.
Colors: Deep red, gold details, black stage, burgundy velvet.
Composition: Wide-angle 16:9, space for 6-8 product placements.
NO people, NO mannequins.
Atmosphere: Theatrical drama, passionate intensity, luxury performance space.
Quality: 8K ultra-high resolution, magazine standard.
    `.trim(),
    aspectRatio: '16:9',
    priority: 2
  },
  {
    id: 'signature-runway',
    collection: 'SIGNATURE',
    name: 'The Luxury Runway',
    prompt: `
Ultra-luxury fashion showroom: Minimalist high-fashion runway, sleek black catwalk, professional stage lighting, floor-to-ceiling windows with city skyline, clean white walls, marble accents, modern sculptural seating, champagne and gold (#D4AF37) accent lighting, museum-quality prestige.
Style: High-fashion runway + Architectural Digest.
Lighting: Professional with champagne-gold (#D4AF37) accent wash.
Colors: Pure white, champagne gold, black runway, marble textures.
Composition: Wide-angle 16:9, space for 6-8 product placements.
NO people, NO mannequins.
Atmosphere: Editorial prestige, minimalist luxury, high-fashion power.
Quality: 8K ultra-high resolution, runway photography standard.
    `.trim(),
    aspectRatio: '16:9',
    priority: 1
  },
  {
    id: 'signature-penthouse',
    collection: 'SIGNATURE',
    name: 'The Penthouse Gallery',
    prompt: `
Ultra-luxury fashion showroom: Penthouse art gallery, floor-to-ceiling windows overlooking city, white marble floors, modern art pieces, gold (#D4AF37) accent lighting, minimalist luxury furniture, crystal clear atmosphere, editorial prestige.
Style: Luxury real estate + museum photography.
Lighting: Natural daylight + gold accent highlights.
Colors: Pure white, champagne gold, marble, glass clarity.
Composition: Wide-angle 16:9, space for 6-8 product placements.
NO people, NO mannequins.
Atmosphere: Museum-quality luxury, editorial excellence, prestige power.
Quality: 8K ultra-high resolution, architectural photography standard.
    `.trim(),
    aspectRatio: '16:9',
    priority: 2
  }
];

/**
 * Generate scene with Gemini 2.5 Flash Image
 */
async function generateScene(scene, geminiClient) {
  console.log(`\n🎬 Generating: ${scene.name}`);
  console.log(`   Collection: ${scene.collection}`);
  console.log(`   Model: gemini-2.5-flash-image`);
  console.log('─'.repeat(70));

  const outputDir = path.join(__dirname, '../assets/images/scenes/ai-generated');
  const outputPath = path.join(outputDir, `${scene.id}.png`);

  try {
    // Ensure output directory
    await fs.mkdir(outputDir, { recursive: true });

    // Save prompt for reference
    const promptPath = path.join(outputDir, `${scene.id}-prompt.txt`);
    await fs.writeFile(promptPath, scene.prompt);
    console.log(`   💾 Prompt saved`);

    console.log(`   🤖 Calling Gemini 2.5 Flash Image...`);

    // Generate with Gemini (using Nanobanana's model)
    const result = await geminiClient.generateImage({
      model: 'gemini-2.5-flash-image',
      prompt: scene.prompt,
      aspectRatio: scene.aspectRatio || '16:9'
    });

    if (!result || !result.image) {
      throw new Error('No image returned from Gemini');
    }

    // Save image
    let imageData;
    if (Buffer.isBuffer(result.image)) {
      imageData = result.image;
    } else if (typeof result.image === 'string') {
      // Base64
      const base64Data = result.image.replace(/^data:image\/\w+;base64,/, '');
      imageData = Buffer.from(base64Data, 'base64');
    } else {
      throw new Error('Unknown image format returned');
    }

    await fs.writeFile(outputPath, imageData);

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
  console.log('\n🌹 SkyyRose Scene Generation');
  console.log('🤖 Powered by Gemini 2.5 Flash Image (via Nanobanana architecture)');
  console.log('='.repeat(70));

  // Initialize Gemini client
  let geminiClient;
  try {
    geminiClient = new GeminiClient();
    console.log('✓ Gemini client initialized\n');
  } catch (error) {
    console.error('✗ Failed to initialize Gemini client:', error.message);
    console.error('ℹ️  Make sure GEMINI_API_KEY is set in environment');
    process.exit(1);
  }

  const startTime = Date.now();
  const results = [];

  // Sort by priority
  const sortedScenes = SCENES.sort((a, b) => a.priority - b.priority);

  console.log(`📋 Generation Queue:`);
  sortedScenes.forEach((scene, i) => {
    console.log(`   ${i + 1}. ${scene.name} (${scene.collection})`);
  });

  console.log('\n' + '='.repeat(70));

  // Generate scenes with rate limiting
  for (const scene of sortedScenes) {
    const result = await generateScene(scene, geminiClient);
    results.push(result);

    // Rate limiting: 6 second delay
    if (scene !== sortedScenes[sortedScenes.length - 1]) {
      console.log(`\n   ⏸️  Rate limiting: Waiting 6 seconds...\n`);
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
    successful.forEach(r => console.log(`   ✓ ${r.scene}`));
  }

  if (failed.length > 0) {
    console.log(`\n❌ Failed scenes:`);
    failed.forEach(r => console.log(`   ✗ ${r.scene}: ${r.error}`));
  }

  // Save report
  const reportPath = path.join(__dirname, '../assets/images/scenes/ai-generated/GENERATION_REPORT.json');
  await fs.writeFile(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    duration: `${duration} minutes`,
    model: 'gemini-2.5-flash-image',
    results
  }, null, 2));

  console.log(`\n📄 Report saved: ${path.relative(process.cwd(), reportPath)}`);
  console.log('\n🎯 Next steps:');
  console.log('   1. Review: assets/images/scenes/ai-generated/');
  console.log('   2. Optimize: npm run build:scenes');
  console.log('   3. Update 3D pages with new scenes\n');
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
  generateScene,
  generateAllScenes
};
