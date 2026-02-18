/**
 * SkyyRose - Nanobanana Pro Brand System
 * Advanced prompt engineering for complete brand visual identity
 *
 * Generates:
 * - Fashion model product photography (16 products)
 * - Hero/scene background images
 * - Marketing/ad materials
 * - Social media content
 * - Email campaign visuals
 *
 * All using Nanobanana MCP server with SkyyRose brand DNA
 */

const path = require('path');
const fs = require('fs').promises;
const { spawn } = require('child_process');

// SkyyRose Brand DNA - Core Visual Identity
const BRAND_DNA = {
  // Color Psychology
  colors: {
    'BLACK ROSE': {
      primary: '#B76E79',
      secondary: '#8B4556',
      accent: '#E8A5B2',
      mood: 'Gothic romance, mysterious elegance, dark florals',
      palette: 'Deep blacks, rose gold accents, burgundy shadows, moonlight silver'
    },
    'LOVE HURTS': {
      primary: '#8B0000',
      secondary: '#5C0000',
      accent: '#C41E3A',
      mood: 'Dramatic passion, edgy sophistication, bold intensity',
      palette: 'Blood red, deep crimson, black leather, gold hardware'
    },
    'SIGNATURE': {
      primary: '#D4AF37',
      secondary: '#B8941E',
      accent: '#FFD700',
      mood: 'High fashion prestige, editorial excellence, luxury power',
      palette: 'Champagne gold, pure white, marble textures, crystal clarity'
    }
  },

  // Photography Style (Vogue/Harper's Bazaar quality)
  photography: {
    quality: 'Ultra-high resolution, 8K quality, professional retouching',
    lighting: 'Professional editorial lighting, dramatic shadows, accent highlights',
    composition: 'Rule of thirds, negative space, fashion editorial standards',
    focus: 'Tack-sharp product details, shallow depth of field on background',
    postProcessing: 'Color grading like Vogue covers, rich blacks, vibrant brand colors'
  },

  // Model Direction
  models: {
    diversity: 'Diverse representation, all ethnicities, body types, gender expressions',
    expression: 'Confident, sophisticated, powerful, editorial intensity',
    pose: 'High fashion poses, dynamic movement, architectural body lines',
    styling: 'Professional hair/makeup matching collection aesthetic',
    age: 'Age range 20-35, mature sophistication'
  },

  // Setting/Environment
  settings: {
    'BLACK ROSE': 'Gothic gardens, cathedral interiors, moonlit terraces, vintage libraries with dark florals',
    'LOVE HURTS': 'Dramatic ballrooms, baroque theaters, candlelit chambers, edgy urban nightscapes',
    'SIGNATURE': 'Minimalist runways, marble penthouses, modern art galleries, luxury hotel lobbies'
  },

  // Brand Essence
  essence: {
    keywords: 'Luxury, sophistication, boldness, individuality, artistry, prestige, rebellion',
    vibes: 'Dark elegance meets high fashion, gothic romance meets editorial power',
    competitors: 'Alexander McQueen, Rick Owens, Balmain, Givenchy (aim to exceed)',
    inspiration: 'Vogue Italia editorials, Alexander McQueen runway shows, Tim Walker photography'
  }
};

// Prompt Engineering Templates
const PROMPT_TEMPLATES = {
  /**
   * Fashion Model Photography (Product Focus)
   */
  fashionModel: (product, collection) => {
    const colorDNA = BRAND_DNA.colors[collection];
    const setting = BRAND_DNA.settings[collection];

    return `
PROFESSIONAL LUXURY FASHION EDITORIAL PHOTOGRAPHY

BRAND: SkyyRose ${collection} Collection
PRODUCT: ${product.name}
STYLE: Vogue/Harper's Bazaar editorial quality

SUBJECT - FASHION MODEL:
- Professional fashion model wearing ${product.description.garment}
- Diverse representation, editorial beauty, age 20-35
- Expression: Confident, powerful, sophisticated intensity
- Pose: ${product.modelPose}
- Hair/Makeup: Professional editorial styling for ${collection} aesthetic
- Body language: Architectural, dynamic, high-fashion editorial

GARMENT DETAILS (CRITICAL - MUST BE EXACT):
- Item: ${product.description.garment}
- Fit: ${product.description.fit}
- Details: ${product.description.details}
- Styling: ${product.description.styling}
- PRODUCT MUST BE CLEARLY VISIBLE AND ACCURATE TO DESCRIPTION

SETTING & ENVIRONMENT:
- Location: ${setting}
- Background: ${product.background}
- Mood: ${colorDNA.mood}
- Atmosphere: Luxury, aspirational, editorial excellence

LIGHTING & PHOTOGRAPHY:
- Professional editorial lighting with ${colorDNA.primary} accent highlights
- Dramatic shadows creating depth and dimension
- Lighting style: ${BRAND_DNA.photography.lighting}
- Focus: Tack-sharp on garment details, shallow DoF on background

COMPOSITION:
- ${BRAND_DNA.photography.composition}
- Frame: Full-length or 3/4 shot showing complete garment
- Negative space: Balanced, breathable, luxury composition
- Perspective: Eye-level to slightly low angle for power

COLOR GRADING & POST-PROCESSING:
- Color palette: ${colorDNA.palette}
- Brand color ${colorDNA.primary} as accent throughout image
- Rich, vibrant colors with ${BRAND_DNA.photography.postProcessing}
- Mood: ${colorDNA.mood}

TECHNICAL SPECIFICATIONS:
- Resolution: 8K ultra-high quality (7680x4320)
- Aspect ratio: 4:5 (optimal for fashion/product)
- Quality: Magazine cover standard - Vogue, Harper's Bazaar, Elle quality
- Sharpness: Crystal clear product details, professional retouching
- File type: Highest quality output

BRAND STANDARDS:
- Exceed Alexander McQueen, Balmain, Givenchy visual quality
- Inspiration: Vogue Italia editorials, Tim Walker photography aesthetic
- Essence: ${BRAND_DNA.essence.vibes}

CRITICAL REQUIREMENTS:
1. Product garment MUST be exactly as described - this is primary focus
2. Model should enhance but not overshadow the product
3. Image must look like it belongs in Vogue or Harper's Bazaar
4. Professional, aspirational, luxury at every detail
5. Color accuracy to brand palette is essential
    `.trim();
  },

  /**
   * Scene/Environment Photography (No Models)
   */
  sceneBackground: (collection, sceneName, description) => {
    const colorDNA = BRAND_DNA.colors[collection];
    const setting = BRAND_DNA.settings[collection];

    return `
LUXURY FASHION SHOWROOM ENVIRONMENT PHOTOGRAPHY

BRAND: SkyyRose ${collection} Collection
SCENE: ${sceneName}
PURPOSE: Immersive 3D virtual showroom background

ENVIRONMENT:
- Setting: ${setting}
- Description: ${description}
- Mood: ${colorDNA.mood}
- Atmosphere: Luxury fashion showroom, editorial quality space

DESIGN ELEMENTS:
- Architecture: ${collection === 'BLACK ROSE' ? 'Gothic arches, ornate details, vintage elegance' :
                 collection === 'LOVE HURTS' ? 'Baroque opulence, dramatic theater design, candlelit ambiance' :
                 'Minimalist modern, clean lines, marble and glass, museum-quality'}
- Lighting: Professional showroom lighting with ${colorDNA.primary} accent
- Color scheme: ${colorDNA.palette}
- Textures: Luxury materials, high-end finishes, editorial quality surfaces

COMPOSITION:
- Wide-angle view suitable for product hotspot placement
- Clear foreground, midground, background depth
- Multiple focal points for product placement
- Spacious, breathable, luxury showroom aesthetic

LIGHTING & ATMOSPHERE:
- Professional interior photography lighting
- ${colorDNA.primary} color wash/accent lighting
- Dramatic shadows creating depth
- Atmospheric, immersive, aspirational mood

TECHNICAL SPECIFICATIONS:
- Resolution: 8K ultra-high quality (7680x4320)
- Aspect ratio: 16:9 (optimal for immersive web experience)
- Quality: Architectural Digest editorial standard
- Sharpness: Crystal clear throughout
- Perspective: Straight architectural lines, professional interior photography

BRAND STANDARDS:
- Exceed luxury hotel photography, Architectural Digest quality
- Showroom should feel like entering a luxury boutique
- Immersive, aspirational, invite exploration
- Color accuracy to ${collection} brand palette essential

CRITICAL REQUIREMENTS:
1. Space must be suitable for placing 6-8 product hotspots
2. No people or mannequins (this is environment only)
3. Lighting must complement product photography
4. Atmosphere must match ${collection} collection identity
5. Professional luxury showroom standard throughout
    `.trim();
  },

  /**
   * Marketing/Ad Campaign Photography
   */
  marketingAd: (collection, adType, copy) => {
    const colorDNA = BRAND_DNA.colors[collection];

    return `
LUXURY FASHION ADVERTISING CAMPAIGN

BRAND: SkyyRose ${collection} Collection
AD TYPE: ${adType}
PURPOSE: High-end fashion advertising campaign

CAMPAIGN CONCEPT:
- Message: ${copy}
- Visual style: ${colorDNA.mood}
- Target audience: Luxury fashion consumers, high-income, fashion-forward
- Platform: ${adType.includes('social') ? 'Instagram/Facebook' : 'Print magazine'}

VISUAL COMPOSITION:
${adType === 'hero-banner' ? `
- Full-width hero banner composition
- Model(s) in ${collection} collection pieces
- Bold, arresting, stops the scroll
- Clear space for headline text overlay
` : adType === 'social-feed' ? `
- Square format (1:1 ratio)
- Mobile-optimized composition
- Instantly eye-catching
- Clear product focus with lifestyle context
` : adType === 'story-ad' ? `
- Vertical format (9:16 ratio)
- Full-screen immersive
- Dynamic, energetic composition
- Swipe-up worthy visual
` : `
- Print magazine layout
- Premium paper quality aesthetic
- Editorial sophistication
- Timeless, collectible image
`}

MODEL & STYLING:
- Professional fashion model embodying ${collection} aesthetic
- Editorial styling, professional hair/makeup
- Confidence, sophistication, aspiration
- Wearing key pieces from ${collection} collection

LIGHTING & MOOD:
- ${BRAND_DNA.photography.lighting}
- ${colorDNA.primary} brand color prominently featured
- Mood: ${colorDNA.mood}
- Atmosphere: Luxury, desire, aspiration

COLOR GRADING:
- Palette: ${colorDNA.palette}
- Post-processing: High-end fashion campaign standard
- Brand color integration throughout composition
- Rich, vibrant, magazine-quality color

TECHNICAL SPECIFICATIONS:
- Resolution: 8K quality for maximum versatility
- Format: ${adType.includes('social') ? 'Optimized for social media' : 'Print-ready quality'}
- Quality: Luxury fashion campaign standard (Dior, Chanel, Gucci level)
- Text space: Clear areas for headline/copy overlay

BRAND STANDARDS:
- Compete with Dior, Chanel, Balmain campaigns
- Immediate visual impact
- Aspirational yet attainable
- ${BRAND_DNA.essence.vibes}

CRITICAL REQUIREMENTS:
1. Must sell the lifestyle and the product
2. Immediate emotional response from viewer
3. Share-worthy, conversation-starting visual
4. Represents SkyyRose brand values: ${BRAND_DNA.essence.keywords}
5. Professional luxury fashion campaign quality
    `.trim();
  },

  /**
   * Social Media Content
   */
  socialContent: (collection, contentType, product = null) => {
    const colorDNA = BRAND_DNA.colors[collection];

    const contentSpecs = {
      'feed-post': { ratio: '1:1', size: '1080x1080', purpose: 'Main feed engagement' },
      'story': { ratio: '9:16', size: '1080x1920', purpose: 'Story content' },
      'reel-cover': { ratio: '9:16', size: '1080x1920', purpose: 'Reels cover image' },
      'carousel': { ratio: '1:1', size: '1080x1080', purpose: 'Carousel slide' }
    };

    const spec = contentSpecs[contentType];

    return `
INSTAGRAM/SOCIAL MEDIA CONTENT - SKYYROSE

BRAND: SkyyRose ${collection} Collection
CONTENT TYPE: ${contentType}
FORMAT: ${spec.ratio} (${spec.size})
PURPOSE: ${spec.purpose}

${product ? `
PRODUCT FOCUS:
- Featured product: ${product.name}
- Garment: ${product.description.garment}
- Styling context: Lifestyle + product
` : `
BRAND/LIFESTYLE CONTENT:
- Collection: ${collection}
- Mood: ${colorDNA.mood}
- Brand storytelling focus
`}

VISUAL STYLE:
- Instagram-optimized composition
- Mobile-first viewing
- Scroll-stopping visual
- Clear, bold, instantly recognizable as SkyyRose

MODEL & STYLING:
- Relatable yet aspirational
- Diverse representation
- Editorial quality but social-media authentic
- ${collection} aesthetic embodied

LIGHTING & MOOD:
- Clean, sharp, professional
- ${colorDNA.primary} brand color featured
- Mood: ${colorDNA.mood}
- Atmosphere: Aspirational lifestyle

COMPOSITION:
- Mobile-optimized framing
- Clear focal point
- Negative space for text overlay potential
- Thumb-stopping visual impact

TECHNICAL SPECIFICATIONS:
- Resolution: ${spec.size} (Instagram optimized)
- Aspect ratio: ${spec.ratio}
- Quality: High-end social media content
- File size: Optimized for fast loading

BRAND STANDARDS:
- Instantly recognizable as SkyyRose
- Cohesive with overall feed aesthetic
- ${BRAND_DNA.essence.vibes}
- Professional yet authentic

ENGAGEMENT OPTIMIZATION:
1. Immediate visual impact (stop the scroll)
2. Clear brand identity
3. Aspirational yet relatable
4. Share-worthy, save-worthy content
5. Drives profile visits and website clicks
    `.trim();
  }
};

// Nanobanana Generation Configuration
const NANOBANANA_CONFIG = {
  model: 'gemini-2.5-flash-image',
  outputDir: 'assets/images/generated',

  // Generation queues
  queues: {
    fashionModels: {
      dir: 'assets/images/products',
      count: 16,
      priority: 1
    },
    scenes: {
      dir: 'assets/images/scenes/generated',
      count: 6,
      priority: 2
    },
    marketing: {
      dir: 'assets/images/marketing',
      count: 12, // 4 ad types × 3 collections
      priority: 3
    },
    social: {
      dir: 'assets/images/social',
      count: 24, // 4 content types × 3 collections × 2 variations
      priority: 4
    }
  },

  // Rate limiting (respect Nanobanana/Gemini limits)
  rateLimit: {
    requestsPerMinute: 10,
    delayBetweenRequests: 6000, // 6 seconds
    retryAttempts: 3,
    retryDelay: 10000 // 10 seconds
  }
};

/**
 * Call Nanobanana MCP server to generate image
 */
async function generateWithNanobanana(prompt, outputPath, options = {}) {
  return new Promise((resolve, reject) => {
    console.log(`\n🎨 Generating with Nanobanana Pro...`);
    console.log(`   Output: ${path.basename(outputPath)}`);

    // Prepare Nanobanana MCP command
    const args = [
      'generate-image',
      '--prompt', prompt,
      '--output', outputPath,
      '--model', options.model || NANOBANANA_CONFIG.model,
      '--no-preview', // Don't auto-open (batch generation)
      ...(options.aspectRatio ? ['--aspect-ratio', options.aspectRatio] : []),
      ...(options.style ? ['--style', options.style] : [])
    ];

    // Spawn Nanobanana MCP process
    const nanobanana = spawn('npx', ['@google/genai-mcp-nanobanana', ...args], {
      cwd: path.resolve(__dirname, '../../gemini/extensions/nanobanana'),
      env: {
        ...process.env,
        NANOBANANA_GEMINI_API_KEY: process.env.GEMINI_API_KEY
      }
    });

    let output = '';
    let errorOutput = '';

    nanobanana.stdout.on('data', (data) => {
      output += data.toString();
      process.stdout.write(data);
    });

    nanobanana.stderr.on('data', (data) => {
      errorOutput += data.toString();
      process.stderr.write(data);
    });

    nanobanana.on('close', (code) => {
      if (code === 0) {
        console.log(`   ✓ Generated successfully`);
        resolve({ success: true, output, path: outputPath });
      } else {
        console.error(`   ✗ Generation failed (exit code ${code})`);
        reject(new Error(`Nanobanana generation failed: ${errorOutput}`));
      }
    });

    nanobanana.on('error', (err) => {
      console.error(`   ✗ Process error: ${err.message}`);
      reject(err);
    });
  });
}

/**
 * Generate all fashion model product photography
 */
async function generateFashionModels() {
  console.log('\n📸 GENERATING FASHION MODEL PHOTOGRAPHY');
  console.log('='.repeat(70));

  const products = require('../assets/js/config.js').PRODUCTS || [];
  const results = [];

  for (const product of products) {
    const prompt = PROMPT_TEMPLATES.fashionModel(product, product.collection);
    const outputPath = path.join(NANOBANANA_CONFIG.queues.fashionModels.dir, `${product.id}.jpg`);

    try {
      // Ensure output directory
      await fs.mkdir(path.dirname(outputPath), { recursive: true });

      // Generate with Nanobanana
      const result = await generateWithNanobanana(prompt, outputPath, {
        aspectRatio: '4:5', // Fashion product ratio
        style: 'editorial-photography'
      });

      results.push({ product: product.id, success: true, path: result.path });

      // Rate limiting
      await sleep(NANOBANANA_CONFIG.rateLimit.delayBetweenRequests);

    } catch (error) {
      console.error(`Failed to generate ${product.id}:`, error.message);
      results.push({ product: product.id, success: false, error: error.message });
    }
  }

  return results;
}

/**
 * Generate scene backgrounds
 */
async function generateScenes() {
  console.log('\n🏛️ GENERATING SCENE BACKGROUNDS');
  console.log('='.repeat(70));

  const scenes = [
    { collection: 'BLACK ROSE', name: 'gothic-garden', description: 'Moonlit gothic garden with rose arbors, stone pathways, and mysterious atmosphere' },
    { collection: 'BLACK ROSE', name: 'cathedral-interior', description: 'Gothic cathedral interior with stained glass, candles, and enchanted rose centerpiece' },
    { collection: 'LOVE HURTS', name: 'baroque-ballroom', description: 'Dramatic baroque ballroom with crystal chandeliers, red velvet, and ornate details' },
    { collection: 'LOVE HURTS', name: 'theater-stage', description: 'Vintage theater stage with dramatic lighting and passionate ambiance' },
    { collection: 'SIGNATURE', name: 'modern-runway', description: 'Minimalist modern runway with clean lines, marble floors, and champagne lighting' },
    { collection: 'SIGNATURE', name: 'penthouse-gallery', description: 'Luxury penthouse art gallery with floor-to-ceiling windows and museum-quality space' }
  ];

  const results = [];

  for (const scene of scenes) {
    const prompt = PROMPT_TEMPLATES.sceneBackground(scene.collection, scene.name, scene.description);
    const outputPath = path.join(NANOBANANA_CONFIG.queues.scenes.dir, `${scene.collection.toLowerCase().replace(' ', '-')}-${scene.name}.jpg`);

    try {
      await fs.mkdir(path.dirname(outputPath), { recursive: true });

      const result = await generateWithNanobanana(prompt, outputPath, {
        aspectRatio: '16:9', // Immersive scene ratio
        style: 'architectural-photography'
      });

      results.push({ scene: scene.name, success: true, path: result.path });

      await sleep(NANOBANANA_CONFIG.rateLimit.delayBetweenRequests);

    } catch (error) {
      console.error(`Failed to generate ${scene.name}:`, error.message);
      results.push({ scene: scene.name, success: false, error: error.message });
    }
  }

  return results;
}

/**
 * Generate marketing/ad materials
 */
async function generateMarketing() {
  console.log('\n📢 GENERATING MARKETING MATERIALS');
  console.log('='.repeat(70));

  const campaigns = [
    { collection: 'BLACK ROSE', type: 'hero-banner', copy: 'Where darkness blooms into elegance' },
    { collection: 'BLACK ROSE', type: 'social-feed', copy: 'Gothic romance meets modern luxury' },
    { collection: 'BLACK ROSE', type: 'story-ad', copy: 'Discover the mystery' },
    { collection: 'BLACK ROSE', type: 'print-magazine', copy: 'THE BLACK ROSE Collection' },

    { collection: 'LOVE HURTS', type: 'hero-banner', copy: 'Passion that commands attention' },
    { collection: 'LOVE HURTS', type: 'social-feed', copy: 'Bold. Dramatic. Unapologetic.' },
    { collection: 'LOVE HURTS', type: 'story-ad', copy: 'Feel the intensity' },
    { collection: 'LOVE HURTS', type: 'print-magazine', copy: 'LOVE HURTS Collection' },

    { collection: 'SIGNATURE', type: 'hero-banner', copy: 'Where prestige meets perfection' },
    { collection: 'SIGNATURE', type: 'social-feed', copy: 'Redefining luxury fashion' },
    { collection: 'SIGNATURE', type: 'story-ad', copy: 'Experience excellence' },
    { collection: 'SIGNATURE', type: 'print-magazine', copy: 'SIGNATURE Collection' }
  ];

  const results = [];

  for (const campaign of campaigns) {
    const prompt = PROMPT_TEMPLATES.marketingAd(campaign.collection, campaign.type, campaign.copy);
    const filename = `${campaign.collection.toLowerCase().replace(' ', '-')}-${campaign.type}.jpg`;
    const outputPath = path.join(NANOBANANA_CONFIG.queues.marketing.dir, filename);

    try {
      await fs.mkdir(path.dirname(outputPath), { recursive: true });

      const aspectRatio = campaign.type === 'story-ad' ? '9:16' :
                          campaign.type.includes('social') ? '1:1' : '16:9';

      const result = await generateWithNanobanana(prompt, outputPath, {
        aspectRatio,
        style: 'fashion-campaign'
      });

      results.push({ campaign: filename, success: true, path: result.path });

      await sleep(NANOBANANA_CONFIG.rateLimit.delayBetweenRequests);

    } catch (error) {
      console.error(`Failed to generate ${filename}:`, error.message);
      results.push({ campaign: filename, success: false, error: error.message });
    }
  }

  return results;
}

/**
 * Utility: Sleep function
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Main execution: Generate all brand visuals
 */
async function generateAllBrandVisuals() {
  console.log('\n🌹 SKYYROSE BRAND VISUAL GENERATION');
  console.log('🤖 Powered by Nanobanana Pro + Gemini 2.5 Flash Image');
  console.log('='.repeat(70));
  console.log(`Model: ${NANOBANANA_CONFIG.model}`);
  console.log(`Rate limit: ${NANOBANANA_CONFIG.rateLimit.requestsPerMinute} requests/min`);
  console.log('='.repeat(70));

  const startTime = Date.now();
  const results = {
    fashionModels: null,
    scenes: null,
    marketing: null
  };

  try {
    // Generate in priority order
    results.fashionModels = await generateFashionModels();
    results.scenes = await generateScenes();
    results.marketing = await generateMarketing();

    const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(1);

    console.log('\n' + '='.repeat(70));
    console.log('✨ BRAND VISUAL GENERATION COMPLETE');
    console.log('='.repeat(70));
    console.log(`\n⏱️  Total time: ${duration} minutes`);
    console.log(`\n📊 Results:`);
    console.log(`  Fashion Models: ${results.fashionModels.filter(r => r.success).length}/${results.fashionModels.length} successful`);
    console.log(`  Scenes: ${results.scenes.filter(r => r.success).length}/${results.scenes.length} successful`);
    console.log(`  Marketing: ${results.marketing.filter(r => r.success).length}/${results.marketing.length} successful`);

    // Save generation report
    await fs.writeFile(
      'assets/images/GENERATION_REPORT.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        duration: `${duration} minutes`,
        results,
        brandDNA: BRAND_DNA
      }, null, 2)
    );

    console.log(`\n📄 Report saved: assets/images/GENERATION_REPORT.json`);

  } catch (error) {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  }
}

// Execute if run directly
if (require.main === module) {
  generateAllBrandVisuals();
}

module.exports = {
  BRAND_DNA,
  PROMPT_TEMPLATES,
  generateWithNanobanana,
  generateFashionModels,
  generateScenes,
  generateMarketing,
  generateAllBrandVisuals
};
