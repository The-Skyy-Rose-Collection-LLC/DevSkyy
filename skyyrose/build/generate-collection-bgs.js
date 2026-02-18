/**
 * SkyyRose — Collection Background Generation
 * Generates atmospheric backgrounds per collection using Gemini image generation
 * Each collection gets 3 background variants for product compositing
 */

const path = require('path');
const fs   = require('fs').promises;
const { GoogleGenAI } = require('@google/genai');

const API_KEY = 'AIzaSyCYSqK5iqa0vg-BysCkU3GH7Fo-skop7qc';
const ai = new GoogleGenAI({ apiKey: API_KEY });

const OUT_DIR = path.join(__dirname, '../assets/images/collection-bgs');

const BACKGROUNDS = [

  // ── BLACK ROSE ────────────────────────────────────────────────────────────
  {
    id: 'black-rose-void',
    collection: 'black-rose',
    label: 'The Void',
    prompt: `Ultra-luxury fashion product background. Deep void black environment, absolute darkness with wisps of dark smoke curling from below. Scattered black roses with deep crimson centers floating in the darkness. Subtle rose-gold light (#B76E79) emanating from below catching smoke edges. Rich black marble floor reflecting faint light. Moody, gothic, mysterious. Photography studio quality. Pure flat background for product placement, center area completely clear. No people, no text, no mannequins. 4K editorial fashion background.`
  },
  {
    id: 'black-rose-garden',
    collection: 'black-rose',
    label: 'Midnight Garden',
    prompt: `Ultra-luxury fashion product background. Moonlit gothic garden at midnight. Wrought iron rose archway framing the scene. Black roses blooming in dramatic moonlight with silver-blue highlights. Cobblestone path disappearing into darkness. Deep fog rolling at ground level. Dramatic chiaroscuro lighting — near black darkness with silver moonlight accents and barely-there rose-gold glow (#B76E79). Cinematic gothic romance atmosphere. Clear open center for product placement. No people. Fashion editorial quality, 4K.`
  },
  {
    id: 'black-rose-studio',
    collection: 'black-rose',
    label: 'Dark Studio',
    prompt: `Ultra-luxury fashion product background. Dark studio with black textured wall — deep charcoal concrete with subtle rose petal texture. Low dramatic side lighting casting long shadows. A few single black roses with petals falling against the dark ground. Polished black floor reflecting ambient rose-gold light from edge. Minimalist, premium, dark editorial luxury. Clean center space for product. Photography studio standard. No people, no text. 4K quality.`
  },

  // ── LOVE HURTS ────────────────────────────────────────────────────────────
  {
    id: 'love-hurts-crimson',
    collection: 'love-hurts',
    label: 'Crimson Depths',
    prompt: `Ultra-luxury fashion product background. Deep crimson and black gradient environment. Thorny rose branches creeping from the edges with blood-red roses and sharp thorns. Dramatic chiaroscuro lighting with deep red (#8B0000) spotlight from above. Cracked dry earth texture at ground level with scattered rose petals. Intense, passionate, edgy, dangerous beauty. Clear center area for product placement. Fashion editorial quality. No people, no text. 4K.`
  },
  {
    id: 'love-hurts-passion',
    collection: 'love-hurts',
    label: 'Passionate Fury',
    prompt: `Ultra-luxury fashion product background. Dark dramatic environment with deep burgundy velvet draping from the sides. Shattered glass fragments on a black floor reflecting deep crimson light. Red rose petals scattered across a dark marble surface. Smoke wisps illuminated in deep red. Moody cinematic lighting — hot white backlight with deep crimson side fills. Raw, intense, passionate atmosphere. Open center for product. Fashion photography quality. No people. 4K editorial.`
  },
  {
    id: 'love-hurts-raw',
    collection: 'love-hurts',
    label: 'Raw Edge',
    prompt: `Ultra-luxury fashion product background. Urban raw concrete wall with deep red lighting. Thorny rose vines climbing the concrete sides with blood-red (#8B0000) blooms. Cracked concrete floor with dramatic shadows. Rain-slicked black ground surface. Gritty luxury aesthetic — street meets high fashion. Intense red and black palette with raw texture. Clear center for product placement. No people, no text. Fashion editorial 4K.`
  },

  // ── SIGNATURE ─────────────────────────────────────────────────────────────
  {
    id: 'signature-golden',
    collection: 'signature',
    label: 'Golden Hour',
    prompt: `Ultra-luxury fashion product background. Golden hour Bay Area atmosphere. Warm champagne and gold tones throughout. Soft bokeh of city lights and the Bay Bridge silhouette in the distance, bathed in golden light (#D4AF37). Smooth warm gradient from rich gold to cream at the base. Golden dust particles floating in warm light. Elevated, prestigious, California luxury aesthetic. Wide open clean center for product. No people, no text. Fashion editorial 4K.`
  },
  {
    id: 'signature-marble',
    collection: 'signature',
    label: 'Marble Luxury',
    prompt: `Ultra-luxury fashion product background. Premium white and gold Calacatta marble surface. Warm gold veining flowing through pristine white marble. Soft champagne studio lighting creating gentle shadows. Gold leaf accents scattered subtly on the marble. Minimal vase with white roses with gold-tipped petals at corner. Ultra-clean, editorial, high-fashion luxury. Clear center for product. No people, no text. Fashion photography 4K studio quality.`
  },
  {
    id: 'signature-editorial',
    collection: 'signature',
    label: 'Editorial Gold',
    prompt: `Ultra-luxury fashion product background. Minimalist luxury studio — warm champagne and cream gradient background. Soft golden light wrapping from the right side. Abstract gold foil texture elements floating subtly in the upper corners. Rich warm whites transitioning to champagne gold at the base. Clean, editorial, prestige aesthetic — think Vogue cover background. Completely open center for product. No people, no text. High-fashion 4K.`
  },
];

const DELAY_MS = 4000; // rate limit buffer

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function generateBackground(bg) {
  const colDir = path.join(OUT_DIR, bg.collection);
  await fs.mkdir(colDir, { recursive: true });
  const outPath = path.join(colDir, `${bg.id}.png`);

  // Skip if already exists
  try { await fs.access(outPath); console.log(`  ⏭  Already exists: ${bg.id}`); return; }
  catch {}

  console.log(`  Generating: ${bg.id} — ${bg.label}…`);

  try {
    const response = await ai.models.generateImages({
      model: 'imagen-4.0-generate-001',
      prompt: bg.prompt,
      config: {
        numberOfImages: 1,
        aspectRatio: '1:1',
        outputMimeType: 'image/png',
      }
    });

    const img = response.generatedImages?.[0];
    if (img?.image?.imageBytes) {
      const buf = Buffer.from(img.image.imageBytes, 'base64');
      await fs.writeFile(outPath, buf);
      const kb = Math.round(buf.length / 1024);
      console.log(`  ✅ ${bg.id} saved (${kb}KB)`);
    } else {
      console.log(`  ⚠️  No image in response for ${bg.id}`);
      console.log(`     Response:`, JSON.stringify(response).slice(0, 200));
    }
  } catch (err) {
    console.log(`  ❌ ${bg.id}: ${err.message?.slice(0, 200) || err}`);
  }
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  console.log('\n SkyyRose — Collection Background Generation');
  console.log('=' .repeat(56));
  console.log(`  Generating ${BACKGROUNDS.length} backgrounds across 3 collections\n`);

  const cols = ['black-rose', 'love-hurts', 'signature'];
  const colLabels = { 'black-rose': 'BLACK ROSE', 'love-hurts': 'LOVE HURTS', 'signature': 'SIGNATURE' };

  for (const col of cols) {
    console.log(`\n[ ${colLabels[col]} ]`);
    const items = BACKGROUNDS.filter(b => b.collection === col);
    for (let i = 0; i < items.length; i++) {
      await generateBackground(items[i]);
      if (i < items.length - 1) await sleep(DELAY_MS);
    }
  }

  console.log('\n' + '='.repeat(56));
  console.log(` Done — backgrounds in: assets/images/collection-bgs/\n`);
}

main().catch(e => { console.error('\nFatal:', e); process.exit(1); });
