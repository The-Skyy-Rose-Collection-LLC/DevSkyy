#!/usr/bin/env node
/**
 * SkyyRose 2-Vision Fashion Model Generator
 * ==========================================
 * Maximum Accuracy Pipeline:
 *   1. GPT-4o Vision analyzes source photos → ultra-detailed garment specs
 *   2. Gemini 3 Pro Image generates model photos → 100% replica accuracy
 *
 * Reads products from Prompt Studio overrides (auto-updates with new products)
 */

// Load environment variables first
// Load DevSkyy/.env for OPENAI_API_KEY (parent directory)
require('dotenv').config({ path: require('path').join(__dirname, '../../.env') });
// Load gemini/.env for GEMINI_API_KEY (override any stale keys)
require('dotenv').config({ path: require('path').join(__dirname, '../../gemini/.env'), override: true });

const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');
const { GoogleGenAI } = require('@google/genai');

const ROOT = path.join(__dirname, '..');
const OVERRIDES_DIR = path.join(ROOT, 'assets/data/prompts/overrides');
const SOURCE_DIR = path.join(ROOT, 'assets/images/source-products');
const OUTPUT_DIR = path.join(ROOT, 'assets/images/products');

// Initialize both vision models
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const gemini = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

/**
 * Stage 1: GPT-4o Vision analyzes source photo for ultra-detailed specs
 */
async function analyzeWithGPT4(imagePath, productData) {
  console.log(`\n  🔍 GPT-4o Vision analyzing: ${path.basename(imagePath)}`);

  const imageBuffer = fs.readFileSync(imagePath);
  const base64Image = imageBuffer.toString('base64');

  const prompt = `You are a luxury fashion technical designer analyzing a garment photo for a model photoshoot.

PRODUCT: ${productData.name}
COLLECTION: ${productData.collection}

Analyze this product photo and provide EXACT specifications for an AI model generation:

1. GARMENT TYPE & CUT
   - Exact silhouette (fitted, oversized, athletic, etc.)
   - Length (cropped, standard, extended, etc.)
   - Neckline/collar style
   - Sleeve type and length
   - Any unique construction details

2. FABRIC & TEXTURE
   - Material type (cotton fleece, satin, mesh, etc.)
   - Texture (smooth, ribbed, sherpa, etc.)
   - Weight appearance (lightweight, midweight, heavy)
   - Finish (matte, glossy, heathered, etc.)

3. COLOR PALETTE (be SPECIFIC)
   - Base color(s) with exact shade names
   - Accent colors
   - Color blocking if applicable

4. BRANDING & LOGOS (CRITICAL - describe EXACTLY what you see)
   - Location of each logo/graphic
   - Size (small, medium, large, or measurements if visible)
   - Technique (embroidered, printed, silicone, patch, etc.)
   - Colors used in logo
   - Exact text if readable

5. DETAILS & HARDWARE
   - Ribbing (cuffs, hem, collar)
   - Drawstrings
   - Pockets
   - Zippers, buttons, snaps
   - Any other visible details

6. FIT & DRAPE
   - How it should hang on a model
   - Key fit points to emphasize

Return ONLY the analysis in clear, detailed paragraphs. Be extremely specific about logo placement and branding.`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          {
            type: 'image_url',
            image_url: {
              url: `data:image/jpeg;base64,${base64Image}`,
              detail: 'high'
            }
          }
        ]
      }
    ],
    max_tokens: 1500,
    temperature: 0.3
  });

  const analysis = response.choices[0].message.content;
  console.log(`  ✓ Analysis complete (${analysis.length} chars)`);
  return analysis;
}

/**
 * Stage 2: Gemini 3 Pro Image generates model photo with GPT-4 specs
 */
async function generateWithGemini(imagePath, productData, gpt4Analysis, view = 'front') {
  console.log(`  🎨 Gemini 3 Pro Image generating ${view} view model photo...`);

  const imageBuffer = fs.readFileSync(imagePath);
  const base64Image = imageBuffer.toString('base64');

  const collectionMood = {
    'black-rose': 'Gothic romance, mysterious elegance, dark florals. Rose gold #B76E79 accents.',
    'love-hurts': 'Dramatic passion, bold intensity. Deep crimson #8B0000 with black leather.',
    'signature': 'High fashion prestige, editorial excellence. Champagne gold #D4AF37 luxury.',
    'kids-capsule': 'Joyful luxury, elevated kids editorial. Vibrant, SPECIAL, premium quality.'
  };

  const viewInstructions = view === 'back'
    ? 'Model is facing AWAY from camera, showing the BACK of the garment. Back of head and shoulders visible. Full back view of the product from head to below waist.'
    : 'Model is facing FORWARD toward camera, showing the FRONT of the garment. Face visible, confident expression. Full front view of the product from head to below waist.';

  const prompt = `Create a professional editorial fashion photograph for a luxury streetwear brand.

REFERENCE PRODUCT (match this EXACTLY):
${gpt4Analysis}

CRITICAL ACCURACY REQUIREMENTS:
- The garment must be a 100% IDENTICAL REPLICA of the reference image
- Every logo, graphic, text, and branding element must match EXACTLY in:
  * Placement, size, color, and technique
  * NO additions, NO changes, NO creative interpretation
- Fabric texture, color, and drape must match the reference perfectly
- This is for product sales - accuracy is MANDATORY

MODEL & POSE:
- ${productData.collection === 'kids-capsule' ? 'Child model (8-10 years old appearance)' : 'Adult professional fashion model'}
- ${viewInstructions}
- Editorial pose: ${productData.modelPose || 'Standing confidently, natural elegant stance'}
- Expression: ${productData.collection === 'kids-capsule' ? 'Joyful, warm, playful but premium' : 'Confident, sophisticated, high fashion'}

PHOTOGRAPHY STYLE:
- Editorial quality: Vogue/Harper's Bazaar standard
- Medium format camera aesthetic (Hasselblad)
- Professional lighting: soft key light, subtle rim light in brand color (${collectionMood[productData.collection]?.match(/#[A-F0-9]{6}/)?.[0] || '#B76E79'})
- Setting: ${productData.setting || collectionMood[productData.collection]}
- Shallow depth of field, subject in sharp focus
- Aspect ratio: 3:4 portrait orientation

FINAL CHECK:
✓ Garment is identical to reference (logos, colors, details)
✓ ${view.toUpperCase()} view is clearly shown
✓ Professional editorial quality
✓ Brand aesthetic matches collection mood

Generate the image now.`;

  const response = await gemini.models.generateContent({
    model: 'gemini-3-pro-image-preview',
    contents: [
      prompt,
      {
        inlineData: {
          mimeType: 'image/jpeg',
          data: base64Image
        }
      }
    ],
    config: {
      responseModalities: ['TEXT', 'IMAGE'],
      imageConfig: {
        aspectRatio: '3:4',
        imageSize: '4K'
      }
    }
  });

  // Extract generated image from response
  if (!response.candidates?.[0]?.content?.parts) {
    throw new Error('No response parts generated');
  }

  for (const part of response.candidates[0].content.parts) {
    if (part.inlineData) {
      const generatedImage = part.inlineData.data;
      console.log(`  ✓ ${view} view generated successfully (4K resolution)`);
      return Buffer.from(generatedImage, 'base64');
    }
  }

  throw new Error('No image found in response');
}

/**
 * Process a single product (front + back if available)
 */
async function processProduct(productId) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`📦 ${productId.toUpperCase()}`);
  console.log('='.repeat(60));

  // Load product data from override
  const overridePath = path.join(OVERRIDES_DIR, `${productId}.json`);
  if (!fs.existsSync(overridePath)) {
    console.log(`  ⚠️  No override found, skipping`);
    return { productId, status: 'skipped', reason: 'no override' };
  }

  const productData = JSON.parse(fs.readFileSync(overridePath, 'utf8'));

  if (!productData.referenceImages || productData.referenceImages.length === 0) {
    console.log(`  ⚠️  No reference images, skipping`);
    return { productId, status: 'skipped', reason: 'no reference images' };
  }

  const results = [];
  const outputDir = path.join(OUTPUT_DIR, productId);
  fs.mkdirSync(outputDir, { recursive: true });

  // Process front view (first reference image)
  try {
    const frontRefPath = path.join(SOURCE_DIR, productData.referenceImages[0]);

    // Stage 1: GPT-4o Vision analysis
    const gpt4Analysis = await analyzeWithGPT4(frontRefPath, productData);

    // Save analysis for review
    fs.writeFileSync(
      path.join(outputDir, `${productId}-gpt4-analysis-front.txt`),
      gpt4Analysis
    );

    // Stage 2: Gemini 3 Pro Image generation
    const frontImage = await generateWithGemini(frontRefPath, productData, gpt4Analysis, 'front');

    const frontOutputPath = path.join(outputDir, `${productId}-model-front.jpg`);
    fs.writeFileSync(frontOutputPath, frontImage);

    console.log(`  ✅ Front view saved: ${frontOutputPath}`);
    results.push({ view: 'front', status: 'success', path: frontOutputPath });

  } catch (err) {
    console.log(`  ❌ Front view failed: ${err.message}`);
    results.push({ view: 'front', status: 'failed', error: err.message });
  }

  // Process back view if available (second reference image)
  if (productData.referenceImages.length > 1 && productData.referenceImages[1].includes('back')) {
    try {
      await new Promise(resolve => setTimeout(resolve, 3000)); // Rate limiting

      const backRefPath = path.join(SOURCE_DIR, productData.referenceImages[1]);

      // Stage 1: GPT-4o Vision analysis
      const gpt4Analysis = await analyzeWithGPT4(backRefPath, productData);

      // Save analysis for review
      fs.writeFileSync(
        path.join(outputDir, `${productId}-gpt4-analysis-back.txt`),
        gpt4Analysis
      );

      // Stage 2: Gemini 3 Pro Image generation
      const backImage = await generateWithGemini(backRefPath, productData, gpt4Analysis, 'back');

      const backOutputPath = path.join(outputDir, `${productId}-model-back.jpg`);
      fs.writeFileSync(backOutputPath, backImage);

      console.log(`  ✅ Back view saved: ${backOutputPath}`);
      results.push({ view: 'back', status: 'success', path: backOutputPath });

    } catch (err) {
      console.log(`  ❌ Back view failed: ${err.message}`);
      results.push({ view: 'back', status: 'failed', error: err.message });
    }
  }

  return { productId, results };
}

/**
 * Main execution
 */
async function main() {
  console.log('\n🌹 SkyyRose 2-Vision Fashion Model Generator');
  console.log('🤖 GPT-4o Vision (analysis) + Gemini 3 Pro Image (generation)');
  console.log('📸 Maximum Accuracy Pipeline\n');
  console.log('='.repeat(60));

  // Check API keys
  if (!process.env.OPENAI_API_KEY) {
    console.error('❌ OPENAI_API_KEY not found');
    process.exit(1);
  }
  if (!process.env.GEMINI_API_KEY) {
    console.error('❌ GEMINI_API_KEY not found');
    process.exit(1);
  }
  console.log('✓ API keys loaded');

  // Get products to generate (from args or all)
  const requestedProducts = process.argv.slice(2);
  const allOverrides = fs.readdirSync(OVERRIDES_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => f.replace('.json', ''));

  const productsToGenerate = requestedProducts.length > 0
    ? requestedProducts
    : allOverrides;

  console.log(`\n📦 Generating ${productsToGenerate.length} products:`);
  console.log(`   ${productsToGenerate.join(', ')}\n`);

  const allResults = [];
  const startTime = Date.now();

  for (const productId of productsToGenerate) {
    const result = await processProduct(productId);
    allResults.push(result);

    // Rate limiting between products
    if (productsToGenerate.indexOf(productId) < productsToGenerate.length - 1) {
      console.log('\n  ⏸️  Rate limiting (5s)...');
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }

  // Summary
  const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
  const successful = allResults.filter(r => r.results?.some(v => v.status === 'success')).length;
  const failed = allResults.filter(r => r.results?.every(v => v.status === 'failed')).length;

  console.log('\n' + '='.repeat(60));
  console.log('✨ 2-Vision Generation Complete!');
  console.log('='.repeat(60));
  console.log(`\n📊 Results:`);
  console.log(`   ✅ Successful: ${successful}/${productsToGenerate.length}`);
  console.log(`   ❌ Failed: ${failed}/${productsToGenerate.length}`);
  console.log(`   ⏱️  Duration: ${duration} minutes\n`);

  // Save report
  const report = {
    timestamp: new Date().toISOString(),
    pipeline: '2-vision (GPT-4o Vision + Gemini 3 Pro Image)',
    models: {
      analysis: 'gpt-4o',
      generation: 'gemini-3-pro-image-preview (4K)'
    },
    duration_minutes: parseFloat(duration),
    total: productsToGenerate.length,
    successful,
    failed,
    results: allResults
  };

  fs.writeFileSync(
    path.join(OUTPUT_DIR, '2VISION_GENERATION_REPORT.json'),
    JSON.stringify(report, null, 2)
  );

  console.log(`📄 Report saved: assets/images/products/2VISION_GENERATION_REPORT.json\n`);
}

main().catch(console.error);
