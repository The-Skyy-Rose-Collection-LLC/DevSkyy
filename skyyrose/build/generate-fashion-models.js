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
    description: {
      garment: 'Black crewneck sweatshirt, white ribbed collar and cuffs',
      fit: 'Relaxed, slightly oversized streetwear fit',
      details: 'Large center-chest graphic: two BLACK roses erupting from storm clouds like a mushroom cloud — grey/silver on black, tattoo-art style'
    },
    modelPose: 'Standing confidently, one hand in pocket, showing the full front graphic',
    setting: 'Moonlit gothic garden, wrought-iron gates, fog rolling through dark roses'
  },
  {
    id: 'br-002',
    collection: 'BLACK ROSE',
    name: 'Black Rose Joggers',
    referenceImage: path.join(SOURCE_DIR, 'black-rose/br-002-joggers.jpeg'),
    description: {
      garment: 'Black jogger pants, white ribbed waistband and ankle cuffs, black drawstring',
      fit: 'Tapered jogger fit, relaxed through thigh, tapered at ankle',
      details: 'Small BLACK rose mushroom cloud graphic on upper left leg — grey/silver on black, matching crewneck graphic family'
    },
    modelPose: 'Casual stance, hands in pockets, showing full length of pants and left-leg graphic',
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
    description: {
      garment: "Black hooded dress, women's fit, attached hood",
      fit: "Fitted through body with flared or flowing skirt, feminine silhouette",
      details: "BLACK Rose collection branding on dress — rose graphics, premium fabrication, dramatic hooded silhouette"
    },
    modelPose: "Hood up for dramatic silhouette, hand on hip, full-length showing the dress silhouette",
    setting: "Gothic cathedral garden, moonlight filtering through stone arches, dark florals"
  },

  // ── LOVE HURTS Collection (3 products) ───────────────────────────────────
  {
    id: 'lh-001',
    collection: 'LOVE HURTS',
    name: 'The Fannie',
    referenceImage:  path.join(SOURCE_DIR, 'love-hurts/lh-001-fannie-front-1.jpeg'),
    referenceImage2: path.join(SOURCE_DIR, 'love-hurts/lh-001-fannie-front-2.jpg'),
    description: {
      garment: 'Love Hurts fanny pack / waist bag with adjustable strap',
      fit: 'Worn cross-body or around the waist',
      details: 'Love Hurts tattoo flash rose heart branding, quality zipper hardware, compact premium fabrication'
    },
    modelPose: 'Worn cross-body across chest, one hand resting on it, bold fashion-forward editorial pose',
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
    description: {
      garment: 'Full coordinated set — Bay Area / Bay Bridge Signature Collection',
      fit: 'Matching set, relaxed luxe street editorial fit',
      details: 'Bay Bridge night-scene graphics, SR monogram branding, premium fabrication — top and bottom shown together as full set'
    },
    modelPose: 'Full outfit visible, confident editorial stance showing complete coordinated set',
    setting: 'San Francisco waterfront at night, Bay Bridge illuminated in background, champagne gold light'
  },
  {
    id: 'sg-002',
    collection: 'SIGNATURE',
    name: 'Stay Golden Set',
    referenceImage: path.join(SOURCE_DIR, 'signature/sg-002-stay-golden-set.jpg'),
    description: {
      garment: 'Full coordinated set — Stay Golden Signature Collection',
      fit: 'Matching set, elevated street luxury editorial fit',
      details: '"Stay Golden" theme, gold colorway throughout, SR monogram branding, premium quality fabrication'
    },
    modelPose: 'Standing tall showing full set, editorial confidence, bathed in champagne gold light',
    setting: 'Minimalist marble penthouse, floor-to-ceiling windows, golden afternoon light'
  },
  {
    id: 'sg-003',
    collection: 'SIGNATURE',
    name: 'The Signature Tee — Orchid',
    referenceImage:  path.join(SOURCE_DIR, 'signature/sg-003-tee-orchid-front.jpg'),
    referenceImage2: path.join(SOURCE_DIR, 'signature/sg-003-tee-orchid.jpeg'),
    description: {
      garment: 'Crew-neck tee in Orchid colorway, Signature Collection',
      fit: 'Clean slightly relaxed fit',
      details: 'Orchid / purple colorway, SR monogram at collar, Signature Collection branding. Soft premium fabric.'
    },
    modelPose: 'Standing tall, arms relaxed, chest forward showing tee and its graphic or colorway clearly',
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
    description: {
      garment: 'Signature Collection knit beanie in Red colorway',
      fit: 'Classic fitted beanie, fold-up cuff',
      details: 'Red ribbed knit, Signature Collection patch or embroidery on cuff, premium quality'
    },
    modelPose: 'Head and shoulders portrait, slight head tilt showing beanie detail, intense editorial gaze',
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
