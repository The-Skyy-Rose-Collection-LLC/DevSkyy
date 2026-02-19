/**
 * SkyyRose - Fashion Model Generation with Gemini 2.5 Flash Image
 * Uses REAL product photos as reference images for accurate AI generation
 *
 * Generates professional fashion model photography for all 20 products.
 * All reference images renamed to descriptive format (Feb 2026).
 * Usage: node build/generate-fashion-models.js [product-id ...]
 *
 * ⚠️  DISCLAIMER
 * AI-generated model images are artistic interpretations for visualization purposes.
 * Graphics, text, colorways, and design details may not be 100% accurate replicas
 * of actual SkyyRose products. Always reference the original source photos in
 * source-products/ as the definitive record of each garment's true appearance.
 * Do NOT use generated images as final product listings without manual review.
 */

const path = require('path');
const fs = require('fs').promises;
const { GoogleGenAI } = require('@google/genai');
const { PromptEngine } = require('./prompt-engine');

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

// All 20 products — each entry uses the renamed reference images from source-products/
const PRODUCTS = [

  // ── BLACK ROSE Collection (8 products) ────────────────────────────────────
  {
    id: 'br-001',
    collection: 'BLACK ROSE',
    name: 'Black Rose Crewneck',
    referenceImage:  path.join(SOURCE_DIR, 'black-rose/br-001-crewneck-front.png'),
    referenceImage2: path.join(SOURCE_DIR, 'black-rose/br-001-crewneck-back.png'),
    garmentTypeLock: 'CREWNECK SWEATSHIRT — upper body only. NOT a jersey, NOT a hoodie, NOT a jacket. Round neckline, no buttons, no hood. FRONT VIEW. The logo is an EMBOSSED IMPRESSION — tonal, tone-on-tone, raised/recessed into the fabric — NOT a printed graphic, NOT a patch, NOT embroidered thread.',
    description: {
      garment: 'Black crewneck sweatshirt, white ribbed collar and cuffs',
      fit: 'Relaxed, slightly oversized streetwear fit',
      details: 'Center-chest BLACK Rose logo as an EMBOSSED IMPRESSION — tonal raised/debossed design pressed into the fabric itself, same black-on-black color, subtle 3D texture. No printed ink, no thread, no patch — the logo exists as a physical impression in the material.'
    },
    modelPose: 'Standing confidently facing FORWARD, one hand in pocket, chest area clearly lit to show embossed logo texture — FRONT VIEW',
    setting: 'Moonlit gothic garden, wrought-iron gates, fog rolling through dark roses'
  },
  {
    id: 'br-002',
    collection: 'BLACK ROSE',
    name: 'Black Rose Joggers',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/br-002-joggers.jpeg'),
    garmentTypeLock: 'JOGGER PANTS — lower body only. NOT a hoodie, NOT a sweatshirt, NOT a jacket. Show FULL LENGTH of pants from waist to ankle. Both legs must be visible. Tapered at ankle with ribbed cuffs. The logo is a SILICONE CUT-OUT APPLIQUÉ — three-dimensional raised silicone piece adhered to the fabric, NOT a print, NOT embroidery, NOT a patch.',
    description: {
      garment: 'Black jogger pants, white ribbed waistband and ankle cuffs, black drawstring',
      fit: 'Tapered jogger fit, relaxed through thigh, tapered at ankle',
      details: 'BLACK Rose logo on upper left leg as a SILICONE CUT-OUT APPLIQUÉ — a three-dimensional raised silicone piece, slightly glossy, adhered directly onto the matte fabric. The logo has physical depth and a subtle sheen contrast against the flat black fabric. NOT a printed graphic, NOT embroidery.'
    },
    modelPose: 'Full-length stance showing BOTH LEGS completely from waist to ankle — left-leg silicone logo clearly visible and catching light',
    setting: 'Gothic corridor with dark stone arches and moonlight'
  },
  {
    id: 'br-003',
    collection: 'BLACK ROSE',
    name: '"Black Is Beautiful" Baseball Jersey',
    referenceImage:  path.join(SOURCE_DIR, 'black-rose/br-003-jersey-black-front.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'black-rose/br-003-jersey-giants-front.jpg'),
    description: {
      garment: 'Forest green baseball jersey with gold/yellow and white stripe trim',
      fit: 'Classic button-down baseball jersey, relaxed fit',
      details: '"BLACK IS BEAUTIFUL" varsity lettering across chest in gold/yellow — O in BLACK replaced by black rose graphic. Authentic patch lower right front. Two colorways: Last Oakland and Giants.'
    },
    modelPose: 'Open jersey over fitted base layer, one hand gesturing outward, proud confident stance',
    setting: 'Dramatic urban skyline at golden hour, golden light casting warmth'
  },
  {
    id: 'br-004',
    collection: 'BLACK ROSE',
    name: 'Black Rose Hoodie',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/br-004-hoodie-front.png'),
    description: {
      garment: 'Black pullover hoodie with drawstring hood, kangaroo pocket',
      fit: 'Relaxed, slightly oversized streetwear fit',
      details: 'BLACK rose mushroom cloud graphic on chest — grey/silver on black, matching crewneck graphic family. Ribbed cuffs and hem.'
    },
    modelPose: 'Hood down, hands in kangaroo pocket, confident relaxed stance showing full chest graphic',
    setting: 'Moonlit gothic garden, rose bushes in background, atmospheric fog'
  },
  {
    id: 'br-005',
    collection: 'BLACK ROSE',
    name: 'Black Rose Hoodie — Signature Edition',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/br-005-hoodie-signature-front.png'),
    description: {
      garment: 'Black pullover hoodie, elevated Signature Edition fabrication',
      fit: 'Premium relaxed fit with refined tailoring details',
      details: 'Signature Edition of the BLACK Rose Hoodie — upgraded materials, refined branding, collector collab piece'
    },
    modelPose: 'Editorial stance showing full garment, one hand raised slightly, intense gaze',
    setting: 'Cathedral interior, gothic stone columns, dramatic candlelight and shadow'
  },
  {
    id: 'br-006',
    collection: 'BLACK ROSE',
    name: 'Black Rose Sherpa Jacket',
    referenceImage:  path.join(SOURCE_DIR, 'black-rose/br-006-sherpa-front.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'black-rose/br-006-sherpa-back.jpg'),
    description: {
      garment: 'Black sherpa / bomber jacket with plush lining',
      fit: 'Structured outerwear fit, slightly relaxed through body',
      details: 'BLACK Rose collection branding, rich sherpa texture, quality hardware. Front and back both feature strong design elements.'
    },
    modelPose: 'Jacket fully buttoned, collar turned up, commanding editorial presence showing both front and silhouette',
    setting: 'Moonlit rooftop at night, city lights below, gothic rose gold bokeh'
  },
  {
    id: 'br-007',
    collection: 'BLACK ROSE',
    name: 'BLACK Rose × Love Hurts Basketball Shorts',
    referenceImage:  path.join(SOURCE_DIR, 'black-rose/br-007-shorts-front.png'),
    referenceImage2: path.join(SOURCE_DIR, 'black-rose/br-007-shorts-side.png'),
    description: {
      garment: 'Basketball shorts — BLACK Rose × Love Hurts collab piece',
      fit: 'Athletic mid-thigh length, relaxed athletic fit',
      details: 'Dual-collection branding collab — BLACK Rose mushroom cloud meets Love Hurts rose heart motif. Premium mesh fabric with quality waistband.'
    },
    modelPose: 'Athletic stance, one leg forward showing side graphic, confident sports editorial energy',
    setting: 'Dark gothic gymnasium meets baroque theater — dramatic mixed-world setting'
  },
  {
    id: 'br-008',
    collection: 'BLACK ROSE',
    name: "Women's BLACK Rose Hooded Dress",
    referenceImage: path.join(SOURCE_DIR, 'black-rose/br-008-hooded-dress-front.jpeg'),
    garmentTypeLock: "EXTENDED-LENGTH HOODIE — this is a HOODIE (with kangaroo pocket, drawstring hood, ribbed cuffs) that has been cut extra long, falling past the hips like a dress silhouette. It is NOT a traditional dress, NOT a skirt-based garment. FEMALE MODEL only. The garment looks like a hoodie from the top half but extends into a long hemline. Logo is EMBROIDERED — thread-stitched into the fabric.",
    description: {
      garment: "Black extended-length hoodie, women's cut — hoodie silhouette elongated to dress length. Drawstring hood, kangaroo pocket, ribbed cuffs and extra-long hem.",
      fit: "Oversized hoodie proportions extended long — relaxed through body, hemline falls mid-thigh to knee, distinctly hoodie construction (not dress construction)",
      details: "BLACK Rose logo EMBROIDERED on the chest — thread-stitched embroidery with slight texture raise. NOT a printed graphic, NOT silicone, NOT an impression. The extended hem length gives it a dress-like silhouette while remaining a hoodie in structure."
    },
    modelPose: "FEMALE model, hood up or down, full-length shot clearly showing: (1) the hoodie construction at top, (2) the extra-long extended hem — embroidered logo on chest visible",
    setting: "Gothic cathedral garden, moonlight filtering through stone arches, dark florals"
  },

  // ── LOVE HURTS Collection (3 products) ───────────────────────────────────
  {
    id: 'lh-001',
    collection: 'LOVE HURTS',
    name: 'The Fannie',
    referenceImage:  path.join(SOURCE_DIR, 'love-hurts/lh-001-fannie-front-1.jpeg'),
    referenceImage2: path.join(SOURCE_DIR, 'love-hurts/lh-001-fannie-front-2.jpg'),
    garmentTypeLock: 'FANNY PACK / WAIST BAG — a small accessory bag worn on the body. NOT a dress, NOT a gown, NOT clothing. The model wears their own outfit underneath and the fanny pack is the ACCESSORY being featured, worn cross-body across the chest or around the waist. The bag must be the clear focal point.',
    description: {
      garment: 'Love Hurts fanny pack / waist bag with adjustable strap — compact bag accessory',
      fit: 'Worn cross-body across chest or around the waist as an accessory over clothing',
      details: 'Love Hurts tattoo flash rose heart branding, quality zipper hardware, compact premium fabrication'
    },
    modelPose: 'Model wearing a simple fitted outfit, fanny pack worn cross-body as the hero accessory — bag clearly visible and in focus',
    setting: 'Dramatic baroque theater stage, deep red velvet curtains, moody dramatic lighting'
  },
  {
    id: 'lh-002',
    collection: 'LOVE HURTS',
    name: 'Love Hurts Joggers',
    referenceImage:  path.join(SOURCE_DIR, 'love-hurts/lh-002-joggers-black.png'),
    referenceImage2: path.join(SOURCE_DIR, 'love-hurts/lh-002-joggers-white-1.png'),
    description: {
      garment: 'Jogger pants in two colorways: Black and White',
      fit: 'Athletic-to-streetwear tapered jogger fit, elastic waistband with drawstring',
      details: 'Love Hurts rose heart motif on leg, contrasting stripe, matching colorway hardware. Available in Black and White versions.'
    },
    modelPose: 'Dynamic stance showing full leg length, both colorways visible in composite or alternating',
    setting: 'Candlelit baroque ballroom, crystal chandeliers, dramatic blood-red shadows'
  },
  {
    id: 'lh-003',
    collection: 'LOVE HURTS',
    name: 'Love Hurts Basketball Shorts',
    referenceImage:  path.join(SOURCE_DIR, 'love-hurts/lh-003-shorts-front.jpeg'),
    referenceImage2: path.join(SOURCE_DIR, 'love-hurts/lh-003-shorts-side.png'),
    description: {
      garment: 'Love Hurts basketball shorts, athletic cut',
      fit: 'Relaxed athletic mid-thigh length',
      details: 'Love Hurts collection branding, rose heart tattoo flash graphic, quality mesh fabric, premium waistband'
    },
    modelPose: 'Athletic editorial stance, showing front and side graphic, powerful energy',
    setting: 'Baroque theater stage lit with dramatic crimson spots, dark grandeur'
  },

  // ── SIGNATURE Collection (9 products) ────────────────────────────────────
  {
    id: 'sg-001',
    collection: 'SIGNATURE',
    name: 'The Bay Set',
    referenceImage:  path.join(SOURCE_DIR, 'signature/sg-001-bay-set-1.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'signature/sg-001-bay-set-2.jpg'),
    garmentTypeLock: 'MATCHING COORDINATED SET — both top AND bottom pieces shown together as a complete outfit. Reproduce EXACTLY the top and bottom pieces shown in the reference images — same colors, same graphics, same fabric. NOT separate individual pieces.',
    description: {
      garment: 'Full coordinated matching set — top and bottom worn together, Bay Area Signature Collection',
      fit: 'Matching set shown as complete outfit, relaxed luxe street editorial fit',
      details: 'Bay Bridge night-scene graphics, SR monogram branding, premium fabrication — BOTH top and bottom must be shown as one complete set'
    },
    modelPose: 'Full-length shot showing BOTH top and bottom of the matching set — complete coordinated outfit',
    setting: 'San Francisco waterfront at night, Bay Bridge illuminated in background, champagne gold light'
  },
  {
    id: 'sg-002',
    collection: 'SIGNATURE',
    name: 'Stay Golden Set',
    referenceImage: path.join(SOURCE_DIR, 'signature/sg-002-stay-golden-set.jpg'),
    garmentTypeLock: 'MATCHING COORDINATED SET — both top AND bottom pieces shown together as a complete outfit. Reproduce the EXACT garments in the reference image — same colors, same cut, same graphics. NOT a single tee or single pant — the full set together.',
    description: {
      garment: 'Full coordinated matching set — Stay Golden Signature Collection, top and bottom together',
      fit: 'Matching set shown as complete outfit, elevated street luxury fit',
      details: '"Stay Golden" theme, gold colorway, SR monogram branding — BOTH pieces shown as a complete set'
    },
    modelPose: 'Full-length shot showing BOTH pieces of the complete matching set clearly',
    setting: 'Minimalist marble penthouse, floor-to-ceiling windows, golden afternoon light'
  },
  {
    id: 'sg-003',
    collection: 'SIGNATURE',
    name: 'The Signature Tee — Orchid',
    referenceImage:  path.join(SOURCE_DIR, 'signature/sg-003-tee-orchid-front.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'signature/sg-003-tee-orchid.jpeg'),
    garmentTypeLock: 'T-SHIRT — short sleeve crew-neck tee. NOT a plain tee — it has a GRAPHIC on the front. Reproduce the exact graphic from the reference image. The orchid/purple colorway shirt with its specific print design.',
    description: {
      garment: 'Short sleeve crew-neck tee, orchid/purple colorway with front graphic print',
      fit: 'Clean slightly relaxed fit',
      details: 'Orchid / purple colorway tee — reproduce the EXACT front graphic from the reference image, SR branding'
    },
    modelPose: 'Standing facing forward, arms relaxed, chest forward — front graphic fully visible and sharp',
    setting: 'Minimalist modern art gallery, clean white walls, gallery track lighting'
  },
  {
    id: 'sg-004',
    collection: 'SIGNATURE',
    name: 'The Signature Tee — White',
    referenceImage:  path.join(SOURCE_DIR, 'signature/sg-004-tee-white-front.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'signature/sg-004-tee-white.jpeg'),
    description: {
      garment: 'White crew-neck tee, Signature Collection',
      fit: 'Clean, slightly relaxed fit',
      details: 'Clean white, SR monogram at collar, center chest graphic — multi-colored rose with Golden Gate Bridge scene inside, emerging from dark clouds'
    },
    modelPose: 'Standing tall, arms relaxed, chest forward, graphic clearly visible',
    setting: 'Clean minimal white studio, SF city skyline silhouette in distance through windows'
  },
  {
    id: 'sg-005',
    collection: 'SIGNATURE',
    name: 'Stay Golden Tee',
    referenceImage: path.join(SOURCE_DIR, 'signature/sg-005-stay-golden-tee.jpg'),
    description: {
      garment: 'Stay Golden tee — Signature Collection',
      fit: 'Clean relaxed fit',
      details: '"Stay Golden" theme tee, gold accents, SR monogram branding, premium fabric'
    },
    modelPose: 'Confident relaxed pose, tee fully visible, golden hour editorial energy',
    setting: 'Marble penthouse terrace at golden hour, warm champagne sunlight'
  },
  {
    id: 'sg-006',
    collection: 'SIGNATURE',
    name: 'Mint & Lavender Hoodie',
    referenceImage:  path.join(SOURCE_DIR, 'signature/sg-006-mint-lavender-hoodie-front.jpeg'),
    referenceImage2: path.join(SOURCE_DIR, 'signature/sg-006-mint-lavender-set-1.jpeg'),
    description: {
      garment: 'Signature Collection hoodie in Mint and Lavender colorway, sold separately from set',
      fit: 'Premium relaxed hoodie fit',
      details: 'Mint green and lavender / purple colorway combination, Signature Collection SR branding, part of a coordinated set (sold separately)'
    },
    modelPose: 'Hood down, hands in pocket or one arm raised, editorial stance showing full colorway',
    setting: 'Modern art gallery with pastel wall and gallery lighting, airy luxury feel'
  },
  {
    id: 'sg-007',
    collection: 'SIGNATURE',
    name: 'The Signature Beanie — Red',
    referenceImage: path.join(SOURCE_DIR, 'signature/sg-007-beanie-red.jpg'),
    garmentTypeLock: 'RED KNIT BEANIE — headwear accessory only. The defining characteristic is BRIGHT RED color — NOT dark, NOT olive, NOT black, NOT green. A classic ribbed knit beanie worn on the head. The model wears their own outfit; the beanie is the featured accessory on their head.',
    description: {
      garment: 'Signature Collection knit beanie in BRIGHT RED colorway',
      fit: 'Classic fitted beanie, fold-up cuff, worn on head',
      details: 'Vibrant bright red ribbed knit, Signature Collection patch or embroidery on cuff, premium quality — RED is the essential color'
    },
    modelPose: 'Head and shoulders portrait, slight head tilt showing beanie detail, intense editorial gaze — RED beanie clearly visible on head',
    setting: 'Dark luxury background with gold and champagne rim lighting'
  },
  {
    id: 'sg-008',
    collection: 'SIGNATURE',
    name: 'The Signature Beanie',
    referenceImage: path.join(SOURCE_DIR, 'signature/sg-008-beanie.png'),
    description: {
      garment: 'Signature Collection knit beanie, original colorway',
      fit: 'Classic fitted beanie with wide cuff fold',
      details: 'Signature Collection branding on cuff patch/embroidery, premium knit construction'
    },
    modelPose: 'Head and shoulders editorial portrait, beanie cuff detail clearly visible, confident gaze',
    setting: 'Minimalist dark luxury studio, subtle gold accent lighting'
  },
  {
    id: 'sg-009',
    collection: 'SIGNATURE',
    name: 'The Sherpa Jacket',
    referenceImage:  path.join(SOURCE_DIR, 'signature/sg-009-sherpa-front.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'signature/sg-009-sherpa-back.jpg'),
    description: {
      garment: 'Signature Collection sherpa jacket, premium outerwear',
      fit: 'Structured outerwear fit, relaxed through body',
      details: 'Sherpa texture, Signature Collection SR branding, quality hardware — front and back both feature collection design elements. Moved from Love Hurts to Signature collection.'
    },
    modelPose: 'Jacket fully buttoned, one hand in pocket, showing both front and hinting at back — powerful editorial presence',
    setting: 'Marble penthouse lobby, floor-to-ceiling windows, champagne gold winter light'
  },
];

/**
 * Stage 1: Flash vision — analyze garment from product photos.
 * Returns hyper-detailed technical spec to anchor generation and prevent hallucination.
 * Caches to {outputDir}/{sku}-garment-analysis.txt so re-runs skip the API call.
 */
async function analyzeGarmentWithFlash(product, ai) {
  const outputDir = path.join(__dirname, '../assets/images/products', product.id);
  await fs.mkdir(outputDir, { recursive: true });
  const cacheFile = path.join(outputDir, `${product.id}-garment-analysis.txt`);

  // Return cached analysis if available
  try {
    const cached = await fs.readFile(cacheFile, 'utf8');
    console.log(`   📋 [Flash] Loaded cached analysis (${cached.length} chars)`);
    return cached;
  } catch { /* not cached yet */ }

  console.log(`   🔍 [Flash] Analyzing garment from reference photos...`);

  const parts = [];
  const refs = [product.referenceImage, product.referenceImage2].filter(Boolean);
  for (const refPath of refs) {
    const img = await loadReferenceImage(refPath);
    if (img) {
      parts.push({ inlineData: img });
      console.log(`      📷 ${path.basename(refPath)}`);
    }
  }

  if (parts.length === 0) {
    console.warn(`   ⚠️  No reference images — skipping Flash analysis`);
    return null;
  }

  parts.push({ text: `
You are a luxury fashion technical director at Vogue with 20 years of experience.

Analyze the garment(s) in the image(s) above. Provide an ULTRA-PRECISE technical spec.
This spec will be used to generate a 100% accurate fashion model image — zero hallucination tolerance.

Extract every detail:
1. GARMENT TYPE — exact category. Be very specific: crewneck sweatshirt / hoodie / jogger pants / basketball shorts / baseball jersey / sherpa jacket / hooded dress / fanny pack / beanie / matching set / tee shirt etc.
2. WHAT IT IS NOT — list 3 garment types it could be confused with that it is NOT
3. BASE COLOR — exact color name and any hex approximation
4. SECONDARY COLORS — all accent/contrast colors
5. FIT & SILHOUETTE — cut, length, proportions
6. ALL GRAPHICS — exact position, size, colors, art style
7. ALL TEXT — exact words, placement, font style, color
8. LOGOS & BRANDING — every mark, placement, color
9. HARDWARE — zippers, drawstrings, buttons, patches
10. FABRIC TEXTURE — visible texture, finish, sheen
11. MODEL DIRECTION — describe exactly how a model should wear this and what pose shows it best

Be exhaustive. No assumptions. Only describe what you can see.
  `.trim() });

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [{ role: 'user', parts }],
  });

  const analysis = response.candidates?.[0]?.content?.parts?.[0]?.text || '';
  if (analysis) {
    await fs.writeFile(cacheFile, analysis);
    console.log(`   ✅ [Flash] Analysis complete (${analysis.length} chars)`);
  }
  return analysis;
}

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

// Lazy-initialized PromptEngine instance — shared across all calls
let _promptEngine = null;
function getPromptEngine() {
  if (!_promptEngine) _promptEngine = new PromptEngine();
  return _promptEngine;
}

/**
 * Create professional fashion editorial prompt via PromptEngine.
 * Falls back to the hardcoded prompt if the engine override is missing.
 * @param {object} product - Product config with description, setting, etc.
 * @param {string|null} garmentAnalysis - Flash Stage-1 technical spec (may be null)
 */
function createFashionPrompt(product, garmentAnalysis = null) {
  const engine = getPromptEngine();
  try {
    return engine.resolve(product.id, 'fashion-model', { garmentAnalysis });
  } catch {
    // Fallback: engine couldn't resolve (e.g. override missing) — build inline
    const brandDNA = BRAND_DNA[product.collection];
    const garmentLockBlock = product.garmentTypeLock
      ? `\n⚠️  GARMENT TYPE LOCK (READ FIRST):\n${product.garmentTypeLock}\nDo NOT substitute any other garment type. Generate EXACTLY this.\n`
      : '';
    const analysisBlock = garmentAnalysis
      ? `\n🔬 FLASH VISION ANALYSIS — TECHNICAL SPEC (highest priority reference):\n${garmentAnalysis}\n`
      : '';
    return `
PROFESSIONAL LUXURY FASHION EDITORIAL PHOTOGRAPHY

BRAND: SkyyRose ${product.collection} Collection
PRODUCT: ${product.name}
STYLE: Vogue, Harper's Bazaar, Elle editorial quality
${garmentLockBlock}${analysisBlock}SUBJECT - FASHION MODEL:
- Professional fashion model wearing ${product.description.garment}
- Expression: Confident, powerful, sophisticated intensity
- Pose: ${product.modelPose}
- Ethnically diverse representation (vary across generations)

GARMENT DETAILS (CRITICAL - MUST MATCH REFERENCE EXACTLY):
- Item: ${product.description.garment}
- Fit: ${product.description.fit}
- Details: ${product.description.details}
- REPRODUCE EVERY GRAPHIC, TEXT, AND DESIGN ELEMENT FROM THE REFERENCE IMAGE

SETTING & ENVIRONMENT:
${product.setting}
- ${brandDNA.mood}
- ${brandDNA.settings} aesthetic

PHOTOGRAPHY STYLE:
- Professional editorial fashion photography
- Shot with medium format camera (Hasselblad quality)

LIGHTING:
- Professional editorial lighting setup
- ${brandDNA.color} accent lighting throughout
- Dramatic shadows creating depth and dimension

COLOR PALETTE:
- Primary colors: ${brandDNA.palette}
- Brand accent color: ${brandDNA.color} prominently featured

COMPOSITION:
- Full-body or 3/4 body shot showing entire garment
- Rule of thirds composition

TECHNICAL:
- Portrait 2:3 aspect ratio
- Magazine editorial standard quality

Generate an ultra-luxury fashion editorial photograph that exceeds Vogue quality standards.
    `.trim();
  }
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

    // Stage 1: Flash vision — extract hyper-detailed garment spec to anchor generation
    console.log(`   🔍 [Stage 1] Flash garment analysis...`);
    const garmentAnalysis = await analyzeGarmentWithFlash(product, ai);

    const prompt = createFashionPrompt(product, garmentAnalysis);
    const promptPath = path.join(outputDir, `${product.id}-prompt.txt`);
    await fs.writeFile(promptPath, prompt);
    console.log(`   💾 [Stage 2] Prompt saved`);

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
    disclaimer: 'AI-generated images are artistic interpretations. Graphics, colorways, and design details may not be 100% accurate replicas of actual SkyyRose products. Always verify against source-products/ originals before using in product listings.',
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
