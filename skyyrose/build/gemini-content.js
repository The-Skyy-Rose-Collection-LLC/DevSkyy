/**
 * SkyyRose — Gemini AI Content Generator
 * =======================================
 * Uses Gemini Vision to analyze product images and generate:
 *   - WooCommerce product descriptions (long + short)
 *   - WCAG alt text for every product image
 *   - Instagram captions (per collection tone)
 *   - TikTok captions
 *   - SEO meta description
 *
 * Output: assets/data/product-content.json
 *         assets/data/alt-text.json
 *
 * Usage:
 *   node build/gemini-content.js              # all products
 *   node build/gemini-content.js br-001       # single product
 *   node build/gemini-content.js --alts-only  # alt text only
 *   node build/gemini-content.js --desc-only  # descriptions only
 */

const path = require('path');
const fs   = require('fs').promises;
const { GoogleGenAI } = require('@google/genai');

const API_KEY = 'AIzaSyCYSqK5iqa0vg-BysCkU3GH7Fo-skop7qc';
const ai = new GoogleGenAI({ apiKey: API_KEY });

const ROOT       = path.join(__dirname, '..');
const ECOM_DIR   = path.join(ROOT, 'assets/images/products-ecom');
const DATA_DIR   = path.join(ROOT, 'assets/data');
const CONTENT_OUT = path.join(DATA_DIR, 'product-content.json');
const ALTS_OUT    = path.join(DATA_DIR, 'alt-text.json');

const DELAY_MS = 3000;

const args       = process.argv.slice(2);
const targetId   = args.find(a => !a.startsWith('--'));
const altsOnly   = args.includes('--alts-only');
const descOnly   = args.includes('--desc-only');
const doAlts     = !descOnly;
const doDesc     = !altsOnly;

// ── Collection tone prompts ────────────────────────────────────────────────
const COLLECTION_TONES = {
  'black-rose': {
    tone: 'gothic luxury, dark romance, bold and mysterious',
    voice: 'dark, evocative, confident. References roses, darkness, beauty in pain.',
    instagram_style: 'moody, poetic, uses rose emoji 🌹 and black heart 🖤',
  },
  'love-hurts': {
    tone: 'passionate, raw, edgy streetwear energy',
    voice: 'intense, real, street meets luxury. References passion, love, pain as beauty.',
    instagram_style: 'bold, raw, uses fire 🔥 and heart 💔 emojis',
  },
  'signature': {
    tone: 'elevated California luxury, Bay Area proud, prestige streetwear',
    voice: 'confident, aspirational, West Coast premium. References gold, Bay, legacy.',
    instagram_style: 'clean, aspirational, uses star ⭐ and gold 💛 emojis',
  },
};

// ── Product catalog ────────────────────────────────────────────────────────
const PRODUCTS = [
  { id:'br-001', name:'BLACK Rose Crewneck', col:'black-rose', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-002', name:'BLACK Rose Joggers',  col:'black-rose', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-003', name:'BLACK is Beautiful Jersey', col:'black-rose', status:'Pre-Order',
    colorways:'White, Black, Giants, Last Oakland', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-004', name:'BLACK Rose Hoodie', col:'black-rose', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-005', name:'BLACK Rose Hoodie — Signature Edition', col:'black-rose', status:'Available', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-006', name:'BLACK Rose Sherpa Jacket', col:'black-rose', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-007', name:'BLACK Rose × Love Hurts Basketball Shorts', col:'black-rose', status:'Available', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'br-008', name:"Women's BLACK Rose Hooded Dress", col:'black-rose', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'lh-001', name:'The Fannie', col:'love-hurts', status:'Pre-Order', sizes:'One Size' },
  { id:'lh-002', name:'Love Hurts Joggers', col:'love-hurts', status:'Available', colorways:'Black, White', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'lh-003', name:'Love Hurts Basketball Shorts', col:'love-hurts', status:'Available', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'lh-004', name:'Love Hurts Varsity Jacket', col:'love-hurts', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-001', name:'The Bay Set', col:'signature', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-002', name:'Stay Golden Set', col:'signature', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-003', name:'The Signature Tee', col:'signature', status:'Available', colorways:'Orchid, White', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-005', name:'Stay Golden Tee', col:'signature', status:'Available', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-006', name:'Mint & Lavender Hoodie', col:'signature', status:'Available', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-007', name:'The Signature Beanie', col:'signature', status:'Available', colorways:'Red, Purple, Black', sizes:'One Size' },
  { id:'sg-009', name:'The Sherpa Jacket', col:'signature', status:'Pre-Order', sizes:'S/M/L/XL/2XL/3XL' },
  { id:'sg-010', name:'The Bridge Series Shorts', col:'signature', status:'Pre-Order', colorways:'Bay Bridge, Golden Gate', sizes:'S/M/L/XL/2XL/3XL' },
];

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function imageToBase64(imgPath) {
  const buf = await fs.readFile(imgPath);
  const ext = path.extname(imgPath).toLowerCase();
  const mime = ext === '.png' ? 'image/png' : 'image/jpeg';
  return { data: buf.toString('base64'), mimeType: mime };
}

async function getHeroImage(productId) {
  const dir = path.join(ECOM_DIR, productId);
  try {
    const files = await fs.readdir(dir);
    // Prefer web.jpg (white bg, cleanest), then master.png
    const webJpg = files.find(f => f.endsWith('-product-web.jpg'));
    const master = files.find(f => f.endsWith('-product-master.png'));
    const hero   = webJpg || master;
    if (hero) return path.join(dir, hero);
  } catch {}
  return null;
}

async function generateDescription(product, imagePath) {
  const tone = COLLECTION_TONES[product.col];
  const colorwayLine = product.colorways ? `Available colorways: ${product.colorways}.` : '';
  const statusLine = product.status === 'Pre-Order' ? 'This is a PRE-ORDER item.' : '';

  const imgData = await imageToBase64(imagePath);

  const prompt = `You are writing product copy for SkyyRose, a luxury streetwear brand from the Bay Area, California.

BRAND VOICE: ${tone.tone}. ${tone.voice}

Product: ${product.name}
Collection: ${product.col.replace('-', ' ').toUpperCase()}
Sizes: ${product.sizes}
${colorwayLine}
${statusLine}

Looking at this product image, write:

1. DESCRIPTION (150-200 words): Rich, evocative product description for WooCommerce. Lead with the feeling, then details. No bullet points. Paragraph form. End with a brand statement.

2. SHORT_DESCRIPTION (1-2 sentences, max 50 words): Used as the product subtitle/excerpt on shop pages. Punchy and memorable.

3. SEO_META (max 160 chars): Google meta description. Include product name and key feature.

4. INSTAGRAM (1 caption, 3-5 sentences + hashtags): Match tone: ${tone.instagram_style}. End with 8-12 relevant hashtags.

5. TIKTOK (1 caption, 2-3 sentences): Short, punchy, trending energy. Max 150 chars.

Format your response as valid JSON:
{
  "description": "...",
  "short_description": "...",
  "seo_meta": "...",
  "instagram": "...",
  "tiktok": "..."
}`;

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [{
      parts: [
        { inlineData: imgData },
        { text: prompt }
      ]
    }]
  });

  const text = response.text || response.candidates?.[0]?.content?.parts?.[0]?.text || '';

  // Extract JSON from response
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('No JSON in response');
  return JSON.parse(jsonMatch[0]);
}

async function generateAltText(productId, imagePath) {
  const product = PRODUCTS.find(p => p.id === productId);
  const imgData = await imageToBase64(imagePath);
  const filename = path.basename(imagePath, path.extname(imagePath));

  const prompt = `Write a concise, descriptive alt text for this product image for a luxury streetwear brand called SkyyRose.

Product: ${product?.name || productId}
Collection: ${product?.col?.replace('-', ' ').toUpperCase() || 'SkyyRose'}
Image filename: ${filename}

Alt text requirements (WCAG 2.1 AA):
- 1-2 sentences max, under 125 characters ideally
- Describe what is shown (garment type, color, key design elements)
- Include the product name
- Do NOT start with "Image of" or "Photo of"
- No markdown, just plain text

Respond with ONLY the alt text, nothing else.`;

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [{
      parts: [
        { inlineData: imgData },
        { text: prompt }
      ]
    }]
  });

  return (response.text || '').trim().replace(/^["']|["']$/g, '');
}

async function processProduct(product, contentData, altData) {
  const dir = path.join(ECOM_DIR, product.id);
  let files = [];
  try { files = await fs.readdir(dir); } catch { return; }

  const webImages = files.filter(f => f.endsWith('-web.jpg'));
  if (webImages.length === 0) {
    console.log(`  ⚠️  No web images found for ${product.id}`);
    return;
  }

  console.log(`\n  [${product.col.replace('-',' ').toUpperCase()}] ${product.id} — ${product.name}`);

  // ── Descriptions ──────────────────────────────────────────────────────────
  if (doDesc && !contentData[product.id]) {
    const heroPath = await getHeroImage(product.id);
    if (heroPath) {
      try {
        console.log(`    Generating descriptions…`);
        const content = await generateDescription(product, heroPath);
        contentData[product.id] = {
          name: product.name,
          collection: product.col,
          ...content
        };
        console.log(`    ✅ Descriptions generated`);
      } catch (err) {
        console.log(`    ❌ Description failed: ${err.message?.slice(0, 100)}`);
      }
      await sleep(DELAY_MS);
    }
  } else if (contentData[product.id]) {
    console.log(`    ⏭  Description already exists`);
  }

  // ── Alt Text ──────────────────────────────────────────────────────────────
  if (doAlts) {
    if (!altData[product.id]) altData[product.id] = {};

    for (const imgFile of webImages) {
      const stem = imgFile.replace('-web.jpg', '');
      if (altData[product.id][stem]) {
        console.log(`    ⏭  Alt text exists: ${stem}`);
        continue;
      }
      try {
        console.log(`    Generating alt text: ${stem}…`);
        const alt = await generateAltText(product.id, path.join(dir, imgFile));
        altData[product.id][stem] = alt;
        console.log(`    ✅ "${alt.slice(0, 80)}${alt.length > 80 ? '…' : ''}"`);
      } catch (err) {
        console.log(`    ❌ Alt text failed: ${err.message?.slice(0, 80)}`);
      }
      await sleep(DELAY_MS);
    }
  }
}

async function main() {
  await fs.mkdir(DATA_DIR, { recursive: true });

  // Load existing data
  let contentData = {};
  let altData = {};
  try { contentData = JSON.parse(await fs.readFile(CONTENT_OUT, 'utf8')); } catch {}
  try { altData     = JSON.parse(await fs.readFile(ALTS_OUT, 'utf8')); }     catch {}

  const mode = [doDesc && 'descriptions+captions', doAlts && 'alt text'].filter(Boolean).join(' + ');
  console.log('\n SkyyRose — Gemini AI Content Generator');
  console.log('='.repeat(56));
  console.log(`  Mode: ${mode}`);
  console.log(`  Model: gemini-2.5-flash`);
  console.log(`  Products: ${targetId || 'all'}\n`);

  const toProcess = targetId
    ? PRODUCTS.filter(p => p.id === targetId)
    : PRODUCTS;

  for (const product of toProcess) {
    await processProduct(product, contentData, altData);
    // Save after each product (so progress is preserved on interrupt)
    if (doDesc) await fs.writeFile(CONTENT_OUT, JSON.stringify(contentData, null, 2));
    if (doAlts) await fs.writeFile(ALTS_OUT,    JSON.stringify(altData, null, 2));
  }

  console.log('\n' + '='.repeat(56));
  console.log(`  Done`);
  if (doDesc) console.log(`  Descriptions: ${CONTENT_OUT}`);
  if (doAlts) console.log(`  Alt text:     ${ALTS_OUT}\n`);
}

main().catch(e => { console.error('\nFatal:', e); process.exit(1); });
