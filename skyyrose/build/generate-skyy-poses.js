/**
 * SkyyRose — Skyy Pose Generation
 *
 * Two-stage pipeline for 100% accurate character + product rendering:
 *
 *   STAGE 1: Gemini 2.5 Flash (vision) analyzes each product reference photo
 *            and extracts hyper-detailed garment description — every color,
 *            graphic, text, stitching, hardware, and logo detail.
 *
 *   STAGE 2: Gemini Flash Image (character reference) generates Skyy wearing
 *            the product. Skyy's PNG + product image both passed as reference.
 *            Imagen 4 generates clean high-res standalone alternates.
 *
 * Output structure:
 *   assets/images/avatar/poses/
 *     skyy-idle-{sku}.png      ← presenting pose (default room state)
 *     skyy-point-{sku}.png     ← pointing at product
 *     skyy-walk-{sku}.png      ← walking/stride pose
 *
 * Usage:
 *   node build/generate-skyy-poses.js                    # all 20 products
 *   node build/generate-skyy-poses.js br-001             # single product
 *   node build/generate-skyy-poses.js br-001 --pose idle # specific pose
 *   node build/generate-skyy-poses.js --collection black-rose
 */

'use strict';

const path   = require('path');
const fs     = require('fs').promises;
const fssync = require('fs');
const { GoogleGenAI } = require('@google/genai');
const { PromptEngine } = require('./prompt-engine');

// Lazy-initialized shared PromptEngine
let _promptEngine = null;
function getPromptEngine() {
  if (!_promptEngine) _promptEngine = new PromptEngine();
  return _promptEngine;
}

// Load env manually — real keys from gemini/.env win over placeholders
// (same pattern as skyyrose_content_agent.py)
function loadEnvFile(filePath) {
  try {
    const text = fssync.readFileSync(filePath, 'utf8');
    for (const line of text.split('\n')) {
      const [k, ...vs] = line.trim().split('=');
      if (!k || k.startsWith('#')) continue;
      const v = vs.join('=').replace(/^["']|["']$/g, '');
      process.env[k] = v;   // override=true semantics
    }
  } catch { /* file doesn't exist — skip */ }
}

const localEnv  = path.join(__dirname, '../.env');
const geminiEnv = path.join(__dirname, '../../gemini/.env');
loadEnvFile(localEnv);
loadEnvFile(geminiEnv);   // real keys loaded last → always win

// ──────────────────────────────────────────────────────────────────────────────
// Config
// ──────────────────────────────────────────────────────────────────────────────

const SOURCE_DIR     = path.join(__dirname, '../assets/images/source-products');
const SKYY_PNG       = path.join(__dirname, '../assets/images/avatar/skyy.png');
const POSES_DIR      = path.join(__dirname, '../assets/images/avatar/poses');
// Enhanced asset catalog — reusable by all future AI model pipelines
const GARMENT_CATALOG = path.join(__dirname, '../assets/data/garment-analysis.json');

const MODEL_VISION   = 'gemini-2.5-flash';          // Stage 1: product analysis
const MODEL_FLASH_IMG = 'gemini-2.5-flash-image';    // Stage 2a: character reference generation
const MODEL_IMAGEN4  = 'imagen-4.0-generate-001';    // Stage 2b: high-res standalone

// Skyy character description — derived from skyy.png reference image
// CRITICAL: She is a 3D CGI animated Pixar-style character — NOT a real human, NOT photorealistic
const SKYY_CHARACTER = `
ART STYLE — MANDATORY:
3D CGI animated character. Pixar / Disney quality rendering.
Warm, stylized, NOT photorealistic. Smooth surfaces, expressive proportions.
Consistent with the provided reference character image (first image).

CHARACTER IDENTITY — MATCH THE REFERENCE IMAGE EXACTLY:
- Overall: Young girl character, approximately 8-10 years old appearance
- Build: Petite, compact, childlike proportions — shorter stature, round cute body shape
- NOT an adult — NOT tall fashion-model proportions

HAIR — CRITICAL:
- Large, voluminous, fluffy natural afro
- Pure dark brown/black color ONLY — no red tint, no colored glow, no ambient light bleeding into the hair
- The afro stays its natural dark color regardless of the scene lighting
- Big, round, cloud-like — takes up significant space above and around the head
- Soft curly texture — individual curls visible within the puff
- Hair color must remain true dark brown/black — not affected by background colors

SKIN:
- Warm medium-brown complexion
- Smooth, even 3D CGI skin tone (not photorealistic texture)

FACE:
- Large, wide-set expressive eyes with long lashes — signature cute look
- Small round nose
- Warm friendly smile — showing white teeth
- Round chubby cheeks
- Childlike, sweet, approachable expression

EXPRESSION: Friendly, warm, confident — the little ambassador of the brand

CRITICAL RULES:
1. Art style MUST be 3D CGI animated — Pixar/Disney quality
2. Large natural afro is non-negotiable — this is her defining feature
3. Young girl proportions — petite and cute, NOT adult model
4. Match the reference character image attached as the first image
`.trim();

const POSE_SPECS = {
  idle: {
    label: 'Presenting — arms slightly open, welcoming pose',
    description: 'Standing tall facing forward, arms slightly extended at sides in a welcoming open gesture — like she\'s presenting the collection. Weight slightly on one hip. Confident, warm, editorial. Full body visible from head to toe.',
    cameraAngle: 'Full body shot, slight low angle (3/4 height), head at upper third',
  },
  point: {
    label: 'Pointing — hand extended toward product/collection',
    description: 'One arm extended forward pointing toward camera-left, fingers elegant and deliberate. Other hand resting on hip. Engaging gaze. Body turned 3/4 toward camera. Full body visible.',
    cameraAngle: 'Full body 3/4 angle, head and pointing hand in upper quadrant',
  },
  walk: {
    label: 'Walking — confident runway stride',
    description: 'Mid-stride walking pose — one leg forward, slight arm swing, head high, shoulder back. Runway walk energy. The garment moves naturally with the stride. Full body from head to foot.',
    cameraAngle: 'Full body slight diagonal, mid-stride captured at peak motion',
  },
};

// ──────────────────────────────────────────────────────────────────────────────
// Product catalog with reference images
// ──────────────────────────────────────────────────────────────────────────────

const PRODUCTS = [
  // ── BLACK ROSE (8 products) ────────────────────────────────────────────────
  { id: 'br-001', collection: 'BLACK ROSE', name: 'Black Rose Crewneck',
    refs: ['black-rose/br-001-crewneck-front.png', 'black-rose/br-001-crewneck-back.png'],
    setting: 'Moonlit gothic garden, wrought-iron gates, rose vines, atmospheric fog' },
  { id: 'br-002', collection: 'BLACK ROSE', name: 'Black Rose Joggers',
    refs: ['black-rose/br-002-joggers.jpeg'],
    setting: 'Gothic corridor, dark stone arches, moonlight shafts through narrow windows' },
  // br-003 split by colorway — each gets its own Bay Area setting
  { id: 'br-003-oakland', collection: 'BLACK ROSE', name: '"Black Is Beautiful" Jersey — Last Oakland',
    refs: ['black-rose/br-003-jersey-last-oakland-front.jpg', 'black-rose/br-003-jersey-last-oakland-back.jpg'],
    setting: 'Oakland at golden hour — Bay Bridge stretching across the water behind her, Oakland skyline glowing amber, Oakland Athletics green-and-gold color palette in the environment, gritty urban energy mixed with luxury, East Bay pride' },
  { id: 'br-003-giants', collection: 'BLACK ROSE', name: '"Black Is Beautiful" Jersey — SF Giants',
    refs: ['black-rose/br-003-jersey-giants-front.jpg', 'black-rose/br-003-jersey-giants-back.png'],
    setting: 'San Francisco — Golden Gate Bridge dramatic backdrop, Oracle Park and the Bay visible, San Francisco Giants orange-and-black color palette echoing in the environment, Bay fog rolling in at sunset, iconic SF skyline' },
  { id: 'br-004', collection: 'BLACK ROSE', name: 'Black Rose Hoodie',
    refs: ['black-rose/br-004-hoodie-front.png'],
    setting: 'Moonlit gothic garden, rose bushes, atmospheric fog' },
  { id: 'br-005', collection: 'BLACK ROSE', name: 'Black Rose Hoodie — Signature Edition',
    refs: ['black-rose/br-005-hoodie-signature-front.png'],
    setting: 'Cathedral interior, gothic stone columns, dramatic candlelight' },
  { id: 'br-006', collection: 'BLACK ROSE', name: 'Black Rose Sherpa Jacket',
    refs: ['black-rose/br-006-sherpa-front.jpg', 'black-rose/br-006-sherpa-back.jpg'],
    setting: 'Moonlit rooftop at night, city lights below, rose gold bokeh' },
  { id: 'br-007', collection: 'BLACK ROSE', name: 'BLACK Rose × Love Hurts Basketball Shorts',
    refs: ['black-rose/br-007-shorts-front.png', 'black-rose/br-007-shorts-side.png', 'black-rose/br-007-shorts-alt.jpeg'],
    setting: 'Dark gothic gymnasium meets baroque theater' },
  { id: 'br-008', collection: 'BLACK ROSE', name: "Women's BLACK Rose Hooded Dress",
    refs: ['black-rose/br-008-hooded-dress-front.jpeg'],
    setting: 'Gothic cathedral garden, moonlight through stone arches, dark florals' },

  // ── LOVE HURTS (4 products) ────────────────────────────────────────────────
  { id: 'lh-001', collection: 'LOVE HURTS', name: 'The Fannie',
    refs: ['love-hurts/lh-001-fannie-front-1.jpeg', 'love-hurts/lh-001-fannie-front-2.jpg'],
    setting: 'Baroque theater stage, deep red velvet curtains, moody dramatic lighting' },
  { id: 'lh-002', collection: 'LOVE HURTS', name: 'Love Hurts Joggers',
    refs: ['love-hurts/lh-002-joggers-black.png', 'love-hurts/lh-002-joggers-white-1.png', 'love-hurts/lh-002-joggers-white-2.png'],
    setting: 'Candlelit baroque ballroom, crystal chandeliers, blood-red shadows' },
  { id: 'lh-003', collection: 'LOVE HURTS', name: 'Love Hurts Basketball Shorts',
    refs: ['love-hurts/lh-003-shorts-front.jpeg', 'love-hurts/lh-003-shorts-side.png', 'love-hurts/lh-003-shorts-side-2.png'],
    setting: 'Baroque theater stage, crimson spotlights, dark grandeur' },
  { id: 'lh-004', collection: 'LOVE HURTS', name: 'Love Hurts Varsity Jacket',
    refs: ['love-hurts/Love-Hurts-Varsity-Jacket.jpg'],
    setting: 'Grand baroque staircase, crimson carpet, dramatic shadows and candlelight' },

  // ── SIGNATURE (8 products) ────────────────────────────────────────────────
  { id: 'sg-001', collection: 'SIGNATURE', name: 'The Bay Set',
    refs: ['signature/sg-001-bay-set-1.jpg', 'signature/sg-001-bay-set-2.jpg'],
    setting: 'San Francisco Bay views, golden bridge backdrop, minimalist luxury terrace' },
  { id: 'sg-002', collection: 'SIGNATURE', name: 'Stay Golden Set',
    refs: ['signature/sg-002-stay-golden-set.jpg'],
    setting: 'Minimalist white studio, champagne gold accent lighting, luxury negative space' },
  { id: 'sg-003', collection: 'SIGNATURE', name: 'The Signature Tee',
    refs: ['signature/sg-003-tee-orchid-front.jpg', 'signature/sg-003-tee-orchid.jpeg'],
    setting: 'Modern art gallery, pastel orchid accent walls, editorial gallery lighting' },
  { id: 'sg-005', collection: 'SIGNATURE', name: 'Stay Golden Tee',
    refs: ['signature/sg-005-stay-golden-tee.jpg'],
    setting: 'Rooftop at golden hour, city skyline, champagne light flooding the scene' },
  { id: 'sg-006', collection: 'SIGNATURE', name: 'Mint & Lavender Hoodie',
    refs: ['signature/sg-006-mint-lavender-hoodie-front.jpeg', 'signature/sg-006-mint-lavender-set-1.jpeg', 'signature/sg-006-mint-lavender-set-2.jpeg'],
    setting: 'Modern art gallery with pastel wall and gallery lighting, airy luxury feel' },
  { id: 'sg-007', collection: 'SIGNATURE', name: 'The Signature Beanie',
    refs: ['signature/sg-007-beanie-red.jpg'],
    setting: 'Dark luxury background, gold and champagne rim lighting, editorial portrait' },
  { id: 'sg-009', collection: 'SIGNATURE', name: 'The Sherpa Jacket',
    refs: ['signature/sg-009-sherpa-front.jpg', 'signature/sg-009-sherpa-back.jpg'],
    setting: 'Marble penthouse lobby, floor-to-ceiling windows, champagne winter light' },
  { id: 'sg-010', collection: 'SIGNATURE', name: 'The Bridge Series Shorts',
    refs: ['signature/Photoroom_012_20240926_104051.jpg'],
    setting: 'San Francisco bridge view at golden hour, elevated urban luxury backdrop' },
];

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────

async function loadImageBase64(imagePath) {
  const ext = path.extname(imagePath).toLowerCase();
  const mimeMap = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };
  const mimeType = mimeMap[ext] || 'image/jpeg';
  try {
    await fs.access(imagePath);
    const data = await fs.readFile(imagePath);
    return { data: data.toString('base64'), mimeType };
  } catch {
    return null;
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function collectionAccent(collection) {
  const accents = {
    'BLACK ROSE': { color: '#B76E79', mood: 'Gothic romance, mysterious elegance' },
    'LOVE HURTS': { color: '#8B0000', mood: 'Raw passion, dramatic intensity, street heat' },
    'SIGNATURE':  { color: '#D4AF37', mood: 'High fashion prestige, elevated editorial luxury' },
  };
  return accents[collection] || accents['SIGNATURE'];
}

// ──────────────────────────────────────────────────────────────────────────────
// Stage 1: Gemini Flash vision analysis
// Extracts hyper-detailed garment description from product reference images
// ──────────────────────────────────────────────────────────────────────────────

async function analyzeGarment(product, ai) {
  console.log(`   🔍 [Stage 1] Flash analyzing garment: ${product.name}`);

  const parts = [];

  // Load all reference images for this product
  for (const refPath of product.refs) {
    const fullPath = path.join(SOURCE_DIR, refPath);
    const img = await loadImageBase64(fullPath);
    if (img) {
      parts.push({ inlineData: img });
      console.log(`      📷 Loaded: ${path.basename(refPath)}`);
    }
  }

  if (parts.length === 0) {
    console.warn(`      ⚠️  No reference images found for ${product.id}`);
    return `${product.collection} collection garment — ${product.name}`;
  }

  parts.push({ text: `
You are a luxury fashion technical analyst with 20 years experience at Vogue and Parsons.

Analyze the garment(s) shown in the image(s) above and provide an ULTRA-PRECISE technical description.
This description will be used to generate a 100% accurate replica on a model.

Extract and describe:
1. GARMENT TYPE — exact category (hoodie, jogger, jersey, dress, etc.)
2. BASE COLOR — exact hex or descriptive color (jet black, cream white, forest green, etc.)
3. SECONDARY COLORS — all accent colors in order of prominence
4. FIT — silhouette (oversized, relaxed, fitted, tapered, etc.), length, proportions
5. GRAPHICS — every graphic element: location on garment, exact size relative to garment, content, colors, style (tattoo-flash, bold print, embroidery, etc.)
6. TEXT — every word, letter, number visible — exact font style, color, placement
7. LOGOS & BRANDING — all logos, patches, wordmarks — location, color, size
8. HARDWARE — zippers, buttons, drawstrings, eyelets — color and material finish
9. FABRIC TEXTURE — visible texture, sheen, thickness, ribbing, mesh, sherpa, etc.
10. SPECIAL DETAILS — collar type, cuffs, waistband, hems, panels, seams

Be EXHAUSTIVE. Every detail that would be needed to recreate this garment from scratch.
Format as a clear technical spec, not prose.
  `.trim() });

  const response = await ai.models.generateContent({
    model: MODEL_VISION,
    contents: [{ role: 'user', parts }],
  });

  const text = response.candidates?.[0]?.content?.parts?.[0]?.text || '';
  console.log(`      ✅ Analysis complete (${text.length} chars)`);
  return text;
}

// ──────────────────────────────────────────────────────────────────────────────
// Stage 2a: Flash Image — Skyy character pose with full references
// ──────────────────────────────────────────────────────────────────────────────

async function generateSkyyPose_FlashImage(product, poseKey, garmentAnalysis, skyyImage, ai) {
  const pose    = POSE_SPECS[poseKey];
  const accent  = collectionAccent(product.collection);
  const outFile = path.join(POSES_DIR, `skyy-${poseKey}-${product.id}.png`);

  console.log(`   🎨 [Stage 2a] Flash Image → ${poseKey} pose`);

  const parts = [];

  // Character reference: Skyy PNG
  if (skyyImage) {
    parts.push({ inlineData: skyyImage });
  }

  // Product reference images
  for (const refPath of product.refs) {
    const fullPath = path.join(SOURCE_DIR, refPath);
    const img = await loadImageBase64(fullPath);
    if (img) parts.push({ inlineData: img });
  }

  // Resolve prompt via PromptEngine — falls back to inline if override missing
  let prompt;
  try {
    prompt = getPromptEngine().resolve(product.id, 'skyy-pose', { pose: poseKey, garmentAnalysis });
  } catch {
    // Inline fallback (engine override missing for this product)
    prompt = `
3D CGI ANIMATED CHARACTER IMAGE — PIXAR QUALITY

FIRST IMAGE = CHARACTER REFERENCE (Skyy). REMAINING IMAGES = PRODUCT REFERENCE (garment to replicate).

ART STYLE — NON-NEGOTIABLE: 3D CGI animated. Pixar / Disney movie quality. Stylized, warm, NOT photorealistic.
MATCH THE ART STYLE OF THE FIRST REFERENCE IMAGE EXACTLY.

REQUIREMENT 1 — SKYY MUST BE IDENTICAL TO REFERENCE:
${SKYY_CHARACTER}

REQUIREMENT 2 — CLOTHING MUST MATCH PRODUCT EXACTLY:
PRODUCT: ${product.name} (${product.collection} Collection)
TECHNICAL GARMENT SPEC:
${garmentAnalysis}
- IDENTICAL reproduction of every graphic, text, logo, color, hardware detail
- Scale to fit Skyy's petite proportions naturally

POSE: ${pose.label}
${pose.description}
CAMERA: ${pose.cameraAngle}

SETTING: ${product.setting}
Brand mood: ${accent.mood}

CHECKLIST:
✓ Skyy = reference image (same face, afro, skin, art style)
✓ Clothing = product photos (every graphic/text/logo/color matches)
✓ 3D CGI Pixar art style
✓ Full body visible
✓ Clean white or transparent background

OUTPUT IMAGE ONLY.
    `.trim();
  }

  parts.push({ text: prompt });

  const response = await ai.models.generateContent({
    model: MODEL_FLASH_IMG,
    contents: [{ role: 'user', parts }],
  });

  let imageBase64 = null;
  for (const part of (response.candidates?.[0]?.content?.parts || [])) {
    if (part.inlineData?.data) {
      imageBase64 = part.inlineData.data;
      break;
    }
  }

  if (!imageBase64) {
    const textFallback = response.candidates?.[0]?.content?.parts?.[0]?.text || '';
    throw new Error(`No image returned from Flash Image. Text: ${textFallback.slice(0, 200)}`);
  }

  await fs.writeFile(outFile, Buffer.from(imageBase64, 'base64'));
  const stats = await fs.stat(outFile);
  console.log(`      ✅ Saved: ${path.basename(outFile)} (${(stats.size / 1024).toFixed(0)}KB)`);
  return outFile;
}

// ──────────────────────────────────────────────────────────────────────────────
// Stage 2b: Imagen 4 — high-res alternate using detailed text description
// ──────────────────────────────────────────────────────────────────────────────

async function generateSkyyPose_Imagen4(product, poseKey, garmentAnalysis, ai) {
  const pose    = POSE_SPECS[poseKey];
  const accent  = collectionAccent(product.collection);
  const outFile = path.join(POSES_DIR, `skyy-${poseKey}-${product.id}-hd.png`);

  console.log(`   🖼️  [Stage 2b] Imagen 4 → ${poseKey} pose (HD)`);

  const prompt = `
3D CGI ANIMATED CHARACTER — PIXAR / DISNEY QUALITY

ART STYLE: 3D CGI animated, warm and stylized. Pixar movie quality. NOT photorealistic.

CHARACTER — SKYY (SkyyRose brand mascot):
${SKYY_CHARACTER}

GARMENT — ${product.name} (${product.collection} Collection):
${garmentAnalysis}

POSE: ${pose.description}
CAMERA: ${pose.cameraAngle}

SETTING: ${product.setting}
MOOD: ${accent.mood}

IDENTICAL REQUIREMENTS:
- CHARACTER: Skyy must be IDENTICAL to her reference — 3D CGI Pixar style, large natural afro, young girl proportions, warm brown skin, big expressive eyes
- CLOTHING: Garment must be IDENTICAL to product photos — every graphic, text, logo, and color reproduced exactly. Zero tolerance for inaccuracy.
- Full body visible, portrait 3:4 orientation
- Clean white or transparent background
- Warm Pixar-quality lighting
  `.trim();

  const response = await ai.models.generateImages({
    model: MODEL_IMAGEN4,
    prompt,
    config: {
      numberOfImages: 1,
      aspectRatio:    '3:4',   // Imagen 4 supports: 1:1, 9:16, 16:9, 4:3, 3:4
      personGeneration: 'ALLOW_ADULT',
    },
  });

  const imageBytes = response?.generatedImages?.[0]?.image?.imageBytes;
  if (!imageBytes) {
    throw new Error('No image bytes from Imagen 4');
  }

  const buf = Buffer.isBuffer(imageBytes) ? imageBytes : Buffer.from(imageBytes, 'base64');
  await fs.writeFile(outFile, buf);
  const stats = await fs.stat(outFile);
  console.log(`      ✅ Saved: ${path.basename(outFile)} (${(stats.size / 1024).toFixed(0)}KB)`);
  return outFile;
}

// ──────────────────────────────────────────────────────────────────────────────
// Enhanced asset catalog — garment-analysis.json
// Accumulated across all runs. Used by future AI model pipelines:
//   - Ad creative generation
//   - Virtual try-on
//   - New character pose series
//   - Social content automation
//   - Product chatbot enrichment
// ──────────────────────────────────────────────────────────────────────────────

async function updateGarmentCatalog(product, garmentAnalysis) {
  // Load existing catalog or start fresh
  let catalog = {};
  try {
    const existing = await fs.readFile(GARMENT_CATALOG, 'utf8');
    catalog = JSON.parse(existing);
  } catch {
    // First run — initialize
    catalog = {
      _meta: {
        description: 'SkyyRose enhanced garment analysis catalog. Generated by Gemini 2.5 Flash vision. ' +
                     'Each entry contains hyper-detailed garment specs for AI model generation pipelines.',
        models_used: { analysis: MODEL_VISION, generation: MODEL_FLASH_IMG, hd: MODEL_IMAGEN4 },
        character: 'Skyy — see assets/images/avatar/skyy.png',
        poses_available: Object.keys(POSE_SPECS),
        last_updated: null,
        total_products: 0,
      },
      products: {},
    };
  }

  // Upsert this product's entry
  catalog.products[product.id] = {
    id:             product.id,
    name:           product.name,
    collection:     product.collection,
    refs:           product.refs,
    setting:        product.setting,
    garmentAnalysis,                   // Full Flash vision extraction
    posesGenerated: Object.keys(POSE_SPECS).map(p => `skyy-${p}-${product.id}.png`),
    hdPoses:        Object.keys(POSE_SPECS).map(p => `skyy-${p}-${product.id}-hd.png`),
    analyzedAt:     new Date().toISOString(),
    // Prompt-ready summary for future AI pipelines
    aiPromptBlock: `PRODUCT: ${product.name} (${product.collection} Collection)\n${garmentAnalysis}`,
  };

  catalog._meta.last_updated  = new Date().toISOString();
  catalog._meta.total_products = Object.keys(catalog.products).length;

  // Atomic write
  const tmpPath = GARMENT_CATALOG + '.tmp';
  await fs.writeFile(tmpPath, JSON.stringify(catalog, null, 2));
  await fs.rename(tmpPath, GARMENT_CATALOG);

  console.log(`      📚 Catalog updated: ${Object.keys(catalog.products).length} products indexed`);
}

// ──────────────────────────────────────────────────────────────────────────────
// Main: process one product × all poses
// ──────────────────────────────────────────────────────────────────────────────

async function processProduct(product, ai, skyyImage, options = {}) {
  const poses = options.pose ? [options.pose] : Object.keys(POSE_SPECS);
  const results = [];

  console.log(`\n${'═'.repeat(70)}`);
  console.log(`👗 ${product.name}`);
  console.log(`   Collection: ${product.collection} | SKU: ${product.id}`);
  console.log(`${'─'.repeat(70)}`);

  // Stage 1: analyze garment — load from cache if already done
  let garmentAnalysis;
  const cacheFile = path.join(POSES_DIR, `${product.id}-garment-analysis.txt`);
  try {
    garmentAnalysis = await fs.readFile(cacheFile, 'utf8');
    console.log(`   📋 [Stage 1] Loaded cached garment analysis (${garmentAnalysis.length} chars)`);
  } catch {
    // No cache — run Flash analysis
  }

  if (!garmentAnalysis) {
  try {
    garmentAnalysis = await analyzeGarment(product, ai);

    // Save individual analysis (debug/audit)
    await fs.writeFile(cacheFile, garmentAnalysis);

    // Persist to enhanced garment catalog for future AI pipelines
    await updateGarmentCatalog(product, garmentAnalysis);

  } catch (err) {
    console.error(`   ❌ Stage 1 failed: ${err.message}`);
    return [{ product: product.id, success: false, error: `Analysis: ${err.message}` }];
  }
  } // end if (!garmentAnalysis)

  await sleep(3000); // brief pause between stage 1 and 2

  // Stage 2: generate each pose
  for (const poseKey of poses) {
    // Skip if already generated (resume support)
    const skipCheck = path.join(POSES_DIR, `skyy-${poseKey}-${product.id}.png`);
    try {
      await fs.access(skipCheck);
      console.log(`   ⏭️  Skipping ${poseKey} — already exists`);
      results.push({ product: product.id, pose: poseKey, success: true, path: skipCheck, model: 'skipped' });
      continue;
    } catch { /* doesn't exist — proceed */ }

    try {
      // Try Flash Image first (has character reference = better consistency)
      const filePath = await generateSkyyPose_FlashImage(product, poseKey, garmentAnalysis, skyyImage, ai);
      results.push({ product: product.id, pose: poseKey, success: true, path: filePath, model: MODEL_FLASH_IMG });
    } catch (flashErr) {
      console.warn(`      ⚠️  Flash Image failed (${flashErr.message.slice(0, 80)}), falling back to Imagen 4...`);
      await sleep(2000);
      try {
        const filePath = await generateSkyyPose_Imagen4(product, poseKey, garmentAnalysis, ai);
        results.push({ product: product.id, pose: poseKey, success: true, path: filePath, model: MODEL_IMAGEN4 });
      } catch (imgErr) {
        console.error(`      ❌ Both models failed for ${poseKey}: ${imgErr.message}`);
        results.push({ product: product.id, pose: poseKey, success: false, error: imgErr.message });
      }
    }

    // Rate limit buffer between poses
    if (poses.indexOf(poseKey) < poses.length - 1) {
      console.log(`      ⏸️  Rate limit buffer: 5s...`);
      await sleep(5000);
    }
  }

  return results;
}

// ──────────────────────────────────────────────────────────────────────────────
// Entry point
// ──────────────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  // Parse flags
  const poseFlag       = args.find(a => a.startsWith('--pose='))?.split('=')[1]
                      || (args.indexOf('--pose') >= 0 ? args[args.indexOf('--pose') + 1] : null);
  const collectionFlag = args.find(a => a.startsWith('--collection='))?.split('=')[1]
                      || (args.indexOf('--collection') >= 0 ? args[args.indexOf('--collection') + 1] : null);
  const productIds     = args.filter(a => !a.startsWith('--'));
  const imagen4Only    = args.includes('--imagen4-only');
  const flashOnly      = args.includes('--flash-only');

  console.log('\n🌹 SkyyRose — Skyy Pose Generation');
  console.log('📸 Stage 1: Gemini 2.5 Flash vision → garment analysis');
  console.log(`🎨 Stage 2: ${imagen4Only ? 'Imagen 4 only' : flashOnly ? 'Flash Image only' : 'Flash Image + Imagen 4 fallback'}`);
  console.log('='.repeat(70));

  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    console.error('✗ GEMINI_API_KEY not found');
    process.exit(1);
  }

  const ai = new GoogleGenAI({ apiKey });
  console.log('✓ Gemini AI initialized');

  // Load Skyy character reference image once
  const skyyImage = await loadImageBase64(SKYY_PNG);
  if (skyyImage) {
    console.log(`✓ Skyy character reference loaded (${(skyyImage.data.length * 0.75 / 1024).toFixed(0)}KB)`);
  } else {
    console.warn('⚠️  Skyy reference image not found at assets/images/avatar/skyy.png');
  }

  // Ensure output directory exists
  await fs.mkdir(POSES_DIR, { recursive: true });
  console.log(`✓ Output directory: ${path.relative(process.cwd(), POSES_DIR)}\n`);

  // Filter products
  let products = PRODUCTS;
  if (productIds.length > 0) {
    products = PRODUCTS.filter(p => productIds.includes(p.id));
    if (products.length === 0) {
      console.error(`✗ No products found for IDs: ${productIds.join(', ')}`);
      process.exit(1);
    }
  } else if (collectionFlag) {
    const colNorm = collectionFlag.toLowerCase().replace(/-/g, ' ');
    products = PRODUCTS.filter(p => p.collection.toLowerCase() === colNorm);
    if (products.length === 0) {
      console.error(`✗ No products found for collection: ${collectionFlag}`);
      process.exit(1);
    }
  }

  console.log(`📦 Products to process: ${products.length}`);
  if (poseFlag) console.log(`📐 Pose filter: ${poseFlag}`);
  console.log('');

  // Validate pose
  if (poseFlag && !POSE_SPECS[poseFlag]) {
    console.error(`✗ Unknown pose: ${poseFlag}. Valid: ${Object.keys(POSE_SPECS).join(', ')}`);
    process.exit(1);
  }

  const allResults = [];
  const startTime  = Date.now();

  for (let i = 0; i < products.length; i++) {
    const product = products[i];
    const results = await processProduct(product, ai, skyyImage, { pose: poseFlag });
    allResults.push(...results);

    // Rate limit buffer between products (skip after last)
    if (i < products.length - 1) {
      console.log(`\n   ⏸️  Rate limit buffer: 10s before next product...`);
      await sleep(10000);
    }
  }

  // ── Summary ──────────────────────────────────────────────────────────────
  const duration    = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
  const successful  = allResults.filter(r => r.success);
  const failed      = allResults.filter(r => !r.success);

  console.log(`\n${'='.repeat(70)}`);
  console.log('✨ Skyy Pose Generation Complete!');
  console.log('='.repeat(70));
  console.log(`\n📊 Results:`);
  console.log(`   ✅ Generated: ${successful.length} images`);
  console.log(`   ❌ Failed:    ${failed.length}`);
  console.log(`   ⏱️  Duration:  ${duration} minutes`);

  if (failed.length > 0) {
    console.log('\n❌ Failed:');
    failed.forEach(r => console.log(`   ✗ ${r.product} ${r.pose || ''}: ${r.error}`));
  }

  if (successful.length > 0) {
    console.log('\n📁 Generated files:');
    successful.forEach(r => console.log(`   ✓ ${path.basename(r.path)} [${r.model}]`));
  }

  // Save run report
  const reportPath = path.join(POSES_DIR, 'GENERATION_REPORT.json');
  await fs.writeFile(reportPath, JSON.stringify({
    timestamp:  new Date().toISOString(),
    duration:   `${duration} minutes`,
    models:     { analysis: MODEL_VISION, generation: MODEL_FLASH_IMG, fallback: MODEL_IMAGEN4 },
    summary:    { total: allResults.length, successful: successful.length, failed: failed.length },
    results:    allResults,
  }, null, 2));

  console.log(`\n📋 Run report:      ${path.relative(process.cwd(), reportPath)}`);
  console.log(`📚 Enhanced catalog: ${path.relative(process.cwd(), GARMENT_CATALOG)}`);
  console.log(`\n   The enhanced catalog (garment-analysis.json) contains hyper-detailed`);
  console.log(`   garment specs for every analyzed product. Future AI pipelines can load`);
  console.log(`   this file instead of re-analyzing product photos from scratch.`);
  process.exit(failed.length > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('\n💥 Fatal:', err.message);
  process.exit(1);
});
