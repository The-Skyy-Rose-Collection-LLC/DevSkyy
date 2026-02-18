/**
 * SkyyRose - Fashion Model Generation with Gemini 2.5 Flash Image
 * Uses REAL product photos as reference images for accurate AI generation
 *
 * Generates professional fashion model photography for all 8 current products
 */

const path = require('path');
const fs = require('fs').promises;
const { GoogleGenAI } = require('@google/genai');

const SOURCE_DIR = path.join(__dirname, '../assets/images/source-products');

// SkyyRose Brand DNA
const BRAND_DNA = {
  'BLACK ROSE': {
    color: '#B76E79',
    mood: 'Gothic romance, mysterious elegance, dark florals',
    palette: 'Deep blacks, rose gold accents, burgundy shadows, moonlight silver',
    settings: 'Gothic gardens, cathedral interiors, moonlit terraces'
  },
  'LOVE HURTS': {
    color: '#8B0000',
    mood: 'Dramatic passion, edgy sophistication, bold intensity',
    palette: 'Blood red, deep crimson, black leather, gold hardware',
    settings: 'Dramatic ballrooms, baroque theaters, candlelit chambers'
  },
  'SIGNATURE': {
    color: '#D4AF37',
    mood: 'High fashion prestige, editorial excellence, luxury power',
    palette: 'Champagne gold, pure white, marble textures, crystal clarity',
    settings: 'Minimalist runways, marble penthouses, modern art galleries'
  }
};

// Product catalog with reference image paths
// NOTE: Check/update referenceImage paths if needed before running
const PRODUCTS = [

  // ── BLACK ROSE Collection ──────────────────────────────────────────────────
  {
    id: 'br-001',
    collection: 'BLACK ROSE',
    available: true,
    name: 'Black Rose Crewneck',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/PhotoRoom_001_20230616_170635.PNG'),
    description: {
      garment: 'Black crewneck sweatshirt, white ribbed collar and cuffs',
      fit: 'Relaxed, slightly oversized streetwear fit',
      details: 'Large center-chest graphic: two BLACK roses erupting from storm clouds like a mushroom cloud — grey/silver graphic on black fabric, tattoo-art style'
    },
    modelPose: 'Standing confidently, one hand in pocket, showing the full front graphic',
    setting: 'Moonlit gothic garden, wrought-iron gates, fog rolling through dark roses'
  },
  {
    id: 'br-002',
    collection: 'BLACK ROSE',
    available: true,
    name: 'Black Rose Joggers',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/PhotoRoom_007_20230616_170635.PNG'),
    description: {
      garment: 'Black jogger pants, white ribbed waistband and ankle cuffs, black drawstring',
      fit: 'Tapered jogger fit, relaxed through the thigh, tapered at ankle',
      details: 'Small BLACK rose mushroom cloud graphic on upper left leg — grey/silver on black, matching the crewneck graphic style'
    },
    modelPose: 'Casual stance, hands in pockets, showing full length of pants and left-leg graphic',
    setting: 'Gothic corridor with dark stone arches and moonlight'
  },
  {
    id: 'br-003',
    collection: 'BLACK ROSE',
    available: true,
    name: '"Black Is Beautiful" Baseball Jersey',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/The BLACK Jersey (BLACK Rose Collection).jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'black-rose/BLACK is Beautiful Giants Front.jpg'),
    description: {
      garment: 'Forest green baseball jersey with gold/yellow and white stripe trim',
      fit: 'Classic button-down baseball jersey, relaxed fit',
      details: 'Arched "BLACK IS BEAUTIFUL" text in gold/yellow varsity lettering across the chest — the O in BLACK replaced by a black rose graphic. "Black Rose Collection" authentic patch on lower right front. SkyyRose tag at collar.'
    },
    modelPose: 'Open jersey over fitted base layer, one hand gesturing outward, proud confident stance',
    setting: 'Dramatic urban skyline at golden hour, golden light casting warmth'
  },
  {
    id: 'br-004',
    collection: 'BLACK ROSE',
    available: true,
    name: 'Black Rose Beanie',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/IMG_7852.JPG'),
    description: {
      garment: 'Black ribbed knit beanie with fold-up cuff',
      fit: 'Classic fitted beanie with wide cuff fold',
      details: 'Square PVC/rubber patch on cuff: black rose mushroom cloud graphic in grey/silver on light background, stitched border'
    },
    modelPose: 'Head and shoulders portrait, slight head tilt showing the patch clearly, intense gaze',
    setting: 'Dark gothic background with soft rose-gold rim lighting'
  },

  // ── LOVE HURTS Collection ─────────────────────────────────────────────────
  {
    id: 'lh-001',
    collection: 'LOVE HURTS',
    available: false,
    preorder: true,
    name: 'Love Hurts Track Pants — Black',
    referenceImage: path.join(SOURCE_DIR, 'love-hurts/joggers.png'),
    description: {
      garment: 'Black track pants with white side stripe, ankle zip hem',
      fit: 'Athletic track fit, tapered leg with zip ankles',
      details: 'Left-leg embroidery: red rose bouquet with a heart and arrow/banner through it — classic tattoo flash style in red, green leaves. White drawstring, white stripe down each leg.'
    },
    modelPose: 'Dynamic athletic stance, one leg slightly forward showing the embroidery, hands relaxed at sides',
    setting: 'Dramatic baroque theater stage, red velvet curtains, moody dramatic lighting'
  },
  {
    id: 'lh-002',
    collection: 'LOVE HURTS',
    available: false,
    preorder: true,
    name: 'Love Hurts Track Pants — White',
    referenceImage: path.join(SOURCE_DIR, 'love-hurts/IMG_2105.png'),
    description: {
      garment: 'White track pants with black side stripe, ankle zip hem',
      fit: 'Athletic track fit, tapered leg with zip ankles',
      details: 'Left-leg embroidery: same red rose bouquet with a heart and arrow/banner — identical tattoo flash style to the black version. Black drawstring, black stripe down each leg.'
    },
    modelPose: 'Confident walking pose, full leg visible, left-leg embroidery facing camera',
    setting: 'Candlelit baroque ballroom, crystal chandeliers, dramatic shadows'
  },

  // ── SIGNATURE Collection ──────────────────────────────────────────────────
  {
    id: 'sg-001',
    collection: 'SIGNATURE',
    available: false,
    preorder: true,
    name: 'Golden Gate Mesh Shorts',
    referenceImage: path.join(SOURCE_DIR, 'signature/The Bridge Series Set \u201cGolden Gate Bridge\u201d.jpeg'),
    description: {
      garment: 'All-over print mesh athletic shorts, white drawstring',
      fit: 'Relaxed mid-thigh length, athletic mesh fabric',
      details: 'Full sublimation print: Golden Gate Bridge at night — deep purple/violet sky, bridge in orange, city reflections in water with streaked neon lights. Small purple/violet rose mushroom cloud logo on lower right front. Black mesh side pockets.'
    },
    modelPose: 'Laid-back confident stance, hands in pockets or one hand lifted, showing the full print',
    setting: 'San Francisco waterfront at night, Golden Gate Bridge lit up in background'
  },
  {
    id: 'sg-002',
    collection: 'SIGNATURE',
    available: false,
    preorder: true,
    name: 'SF Rose White Tee',
    referenceImage: path.join(SOURCE_DIR, 'signature/Signature T \u201cWhite\u201d.jpeg'),
    description: {
      garment: 'White crew-neck t-shirt, SR monogram logo at collar',
      fit: 'Clean, slightly relaxed fit',
      details: 'Center chest graphic: multi-colored rose mushroom cloud — roses contain the Golden Gate Bridge night scene inside them (purple sky, orange bridge, city lights), emerging from dark black clouds. Silver/grey rose outline and stem. Small SR monogram at collar.'
    },
    modelPose: 'Standing tall, arms relaxed, chest forward showing the full graphic clearly',
    setting: 'Clean minimal white studio with subtle SF city skyline silhouette in the distance'
  }
];

/**
 * Load reference image as base64
 */
async function loadReferenceImage(imagePath) {
  try {
    await fs.access(imagePath);
    const data = await fs.readFile(imagePath);
    const ext = path.extname(imagePath).toLowerCase();
    const mimeMap = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };
    const mimeType = mimeMap[ext] || 'image/jpeg';
    return { data: data.toString('base64'), mimeType };
  } catch {
    return null;
  }
}

/**
 * Create professional fashion editorial prompt
 */
function createFashionPrompt(product) {
  const brandDNA = BRAND_DNA[product.collection];

  return `
PROFESSIONAL LUXURY FASHION EDITORIAL PHOTOGRAPHY

BRAND: SkyyRose ${product.collection} Collection
PRODUCT: ${product.name}
STYLE: Vogue, Harper's Bazaar, Elle editorial quality

${product.referenceImage ? `REFERENCE IMAGE PROVIDED ABOVE:
The image above shows the ACTUAL product. Use it as your exact reference — replicate the garment's colors, graphics, text, logos, and design details precisely on the model.

` : ''}SUBJECT - FASHION MODEL:
- Professional fashion model wearing ${product.description.garment}
- Expression: Confident, powerful, sophisticated intensity
- Pose: ${product.modelPose}
- Ethnically diverse representation (vary across generations)

GARMENT DETAILS (CRITICAL - MUST MATCH REFERENCE EXACTLY):
- Item: ${product.description.garment}
- Fit: ${product.description.fit}
- Details: ${product.description.details}
- REPRODUCE EVERY GRAPHIC, TEXT, AND DESIGN ELEMENT FROM THE REFERENCE IMAGE
- PRODUCT MUST BE CLEARLY VISIBLE AND RECOGNIZABLE

SETTING & ENVIRONMENT:
${product.setting}
- ${brandDNA.mood}
- ${brandDNA.settings} aesthetic

PHOTOGRAPHY STYLE:
- Professional editorial fashion photography
- Shot with medium format camera (Hasselblad quality)
- Professional model casting
- High-end fashion magazine standard

LIGHTING:
- Professional editorial lighting setup
- ${brandDNA.color} accent lighting throughout
- Dramatic shadows creating depth and dimension
- Soft key light, dramatic rim lighting

COLOR PALETTE:
- Primary colors: ${brandDNA.palette}
- Brand accent color: ${brandDNA.color} prominently featured
- Rich, saturated colors with luxury depth
- Editorial color grading (Vogue/Harper's Bazaar quality)

COMPOSITION:
- Full-body or 3/4 body shot showing entire garment
- Rule of thirds composition
- Negative space for product focus
- Model positioned to showcase garment details

TECHNICAL SPECIFICATIONS:
- Aspect ratio: Portrait 2:3 (fashion editorial standard)
- Quality: Magazine editorial standard
- Sharpness: Crystal clear, professionally retouched

CRITICAL REQUIREMENTS:
1. Model must be wearing the EXACT product shown in the reference image
2. All graphics, text, logos must be faithfully reproduced from the reference
3. Professional editorial quality throughout
4. Expression and pose match collection identity
5. Lighting complements product and brand colors

Generate a ultra-luxury fashion editorial photograph that exceeds Vogue quality standards.
  `.trim();
}

/**
 * Generate fashion model image with Gemini 2.5 Flash Image
 */
async function generateFashionModel(product, ai) {
  console.log(`\n👗 Generating: ${product.name}`);
  console.log(`   Collection: ${product.collection}`);
  console.log(`   Model: gemini-2.5-flash-image`);
  console.log('─'.repeat(70));

  const outputDir = path.join(__dirname, '../assets/images/products', product.id);
  const outputPath = path.join(outputDir, `${product.id}-model.jpg`);

  try {
    await fs.mkdir(outputDir, { recursive: true });

    const prompt = createFashionPrompt(product);
    const promptPath = path.join(outputDir, `${product.id}-prompt.txt`);
    await fs.writeFile(promptPath, prompt);
    console.log(`   💾 Prompt saved`);

    // Build content parts — include reference image(s) if available
    const parts = [];

    const ref1 = await loadReferenceImage(product.referenceImage);
    if (ref1) {
      parts.push({ inlineData: ref1 });
      console.log(`   🖼️  Reference image loaded: ${path.basename(product.referenceImage)}`);
    }

    // Second reference image (e.g. jersey has front + style shot)
    if (product.referenceImage2) {
      const ref2 = await loadReferenceImage(product.referenceImage2);
      if (ref2) {
        parts.push({ inlineData: ref2 });
        console.log(`   🖼️  Reference image 2 loaded: ${path.basename(product.referenceImage2)}`);
      }
    }

    parts.push({ text: prompt });

    console.log(`   🤖 Calling Gemini 2.5 Flash Image...`);

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: [{ role: 'user', parts }]
    });

    // Extract image data
    let imageBase64 = null;
    if (response.candidates && response.candidates[0]?.content?.parts) {
      for (const part of response.candidates[0].content.parts) {
        if (part.inlineData?.data) {
          imageBase64 = part.inlineData.data;
          console.log(`   📦 Image data found (${imageBase64.length} chars)`);
          break;
        }
      }
    }

    if (!imageBase64) {
      throw new Error('No image data returned from Gemini');
    }

    const imageBuffer = Buffer.from(imageBase64, 'base64');
    await fs.writeFile(outputPath, imageBuffer);
    const stats = await fs.stat(outputPath);

    console.log(`\n   ✅ SUCCESS!`);
    console.log(`   📁 Output: ${path.basename(outputPath)}`);
    console.log(`   💾 Size: ${(stats.size / 1024 / 1024).toFixed(2)}MB`);

    return { success: true, product: product.id, path: outputPath, size: stats.size };

  } catch (error) {
    console.error(`\n   ❌ FAILED: ${error.message}`);
    return { success: false, product: product.id, error: error.message };
  }
}

/**
 * Generate all fashion models
 */
async function generateAllFashionModels(productIds = null) {
  console.log('\n🌹 SkyyRose Fashion Model Generation (with Reference Images)');
  console.log('🤖 Powered by Gemini 2.5 Flash Image');
  console.log('📸 Editorial Quality: Vogue/Harper\'s Bazaar Standard');
  console.log('='.repeat(70));

  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    console.error('✗ GEMINI_API_KEY not found in environment');
    process.exit(1);
  }

  const ai = new GoogleGenAI({ apiKey });
  console.log('✓ Gemini initialized\n');

  // Filter products if specific IDs requested
  const productsToGenerate = productIds
    ? PRODUCTS.filter(p => productIds.includes(p.id))
    : PRODUCTS;

  const startTime = Date.now();
  const results = [];

  for (const product of productsToGenerate) {
    const result = await generateFashionModel(product, ai);
    results.push(result);

    if (product !== productsToGenerate[productsToGenerate.length - 1]) {
      console.log(`\n   ⏸️  Rate limiting: Waiting 6 seconds...`);
      await new Promise(resolve => setTimeout(resolve, 6000));
    }
  }

  const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);

  console.log('\n' + '='.repeat(70));
  console.log('✨ Fashion Model Generation Complete!');
  console.log('='.repeat(70));
  console.log(`\n📊 Results:`);
  console.log(`   ✅ Successful: ${successful.length}/${results.length}`);
  console.log(`   ❌ Failed: ${failed.length}/${results.length}`);
  console.log(`   ⏱️  Duration: ${duration} minutes`);

  if (successful.length > 0) {
    const totalSize = successful.reduce((sum, r) => sum + r.size, 0);
    console.log(`   💾 Total size: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);
  }

  if (failed.length > 0) {
    console.log(`\n❌ Failed products:`);
    failed.forEach(r => console.log(`   ✗ ${r.product}: ${r.error}`));
  }

  const reportPath = path.join(__dirname, '../assets/images/products/GENERATION_REPORT.json');
  await fs.writeFile(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    duration: `${duration} minutes`,
    model: 'gemini-2.5-flash-image',
    quality: 'Editorial (Vogue/Harper\'s Bazaar)',
    referenceImages: true,
    results
  }, null, 2));

  console.log(`\n📄 Report saved: ${path.relative(process.cwd(), reportPath)}\n`);
}

// CLI: node generate-fashion-models.js [product-id ...]
if (require.main === module) {
  const args = process.argv.slice(2);
  const productIds = args.length > 0 ? args : null;

  if (productIds) {
    console.log(`🎯 Generating specific products: ${productIds.join(', ')}`);
  }

  generateAllFashionModels(productIds).catch(error => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { PRODUCTS, BRAND_DNA, createFashionPrompt, generateFashionModel, generateAllFashionModels };
