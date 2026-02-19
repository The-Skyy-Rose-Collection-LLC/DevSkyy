#!/usr/bin/env node
/**
 * SkyyRose Prompt Studio — CLI
 *
 * Commands:
 *   list                                 List all products with brandingTech status
 *   inspect <sku> <template>             Show final resolved prompt
 *   audit-branding                       Products missing/incomplete brandingTech
 *
 *   override <sku> <field> <value>       Set a field on a product override
 *
 *   fingerprint <sku>                    Flash vision → writes logoFingerprint to override
 *   fingerprint-all                      Fingerprint all products
 *   verify-output <sku> <image-path>     Post-generation accuracy check vs fingerprint
 *   accuracy-report                      Aggregate accuracy status across all products
 *
 *   save-version <template> <label>      Snapshot current template
 *   versions <template>                  List saved versions
 *   diff <template> <vA> <vB>            Diff two versions
 *   rollback <template> <label>          Restore a version
 *
 *   test <sku> <template> [pose]         Generate 1 test image (preview)
 *   generate-ad <sku|collection> <platform>  Generate ad creative
 *
 * Usage:
 *   node build/prompt-studio.js <command> [args]
 */

'use strict';

const path   = require('path');
const fs     = require('fs').promises;
const fssync = require('fs');
const { PromptEngine } = require('./prompt-engine');

// ── Env loading (same pattern as skyy poses) ────────────────────────────────

function loadEnvFile(filePath) {
  try {
    const text = fssync.readFileSync(filePath, 'utf8');
    for (const line of text.split('\n')) {
      const [k, ...vs] = line.trim().split('=');
      if (!k || k.startsWith('#')) continue;
      process.env[k] = vs.join('=').replace(/^["']|["']$/g, '');
    }
  } catch { /* skip */ }
}

loadEnvFile(path.join(__dirname, '../.env'));
loadEnvFile(path.join(__dirname, '../../gemini/.env')); // real keys win

// ── Constants ────────────────────────────────────────────────────────────────

const SOURCE_DIR = path.join(__dirname, '../assets/images/source-products');
const OUTPUT_DIR = path.join(__dirname, '../assets/images/products');

const COLLECTION_PRODUCTS = {
  'black-rose':   ['br-001','br-002','br-003','br-004','br-005','br-006','br-007','br-008'],
  'love-hurts':   ['lh-001','lh-002','lh-003','lh-004','lh-005'],
  'signature':    ['sg-001','sg-002','sg-003','sg-004','sg-005','sg-006','sg-007','sg-008','sg-009','sg-011','sg-012','sg-013','sg-014'],
  'kids-capsule': ['kids-001','kids-002'],
};

const STATUS_ICONS = { ok: '✅', warn: '⚠️ ', missing: '❌' };
const TECHNIQUE_EMOJIS = {
  embossed: '🔲', silicone: '🔵', embroidered: '🧵', sublimation: '🎨',
  'woven-label-patch': '🏷️', 'laser-engraved': '🔆', 'laser-engraved leather patch': '🔆',
  mixed: '🔀', TBD: '❓', MISSING: '🚫'
};

// ── Gemini client ────────────────────────────────────────────────────────────

function getAI() {
  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY not found — check skyyrose/.env or gemini/.env');
  const { GoogleGenAI } = require('@google/genai');
  return new GoogleGenAI({ apiKey });
}

async function loadImageBase64(imagePath) {
  try {
    await fs.access(imagePath);
    const data = await fs.readFile(imagePath);
    const ext  = path.extname(imagePath).toLowerCase();
    const mime = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' }[ext] || 'image/jpeg';
    return { data: data.toString('base64'), mimeType: mime };
  } catch {
    return null;
  }
}

// ── Commands ─────────────────────────────────────────────────────────────────

async function cmdList() {
  const engine = new PromptEngine();
  const report = engine.auditBranding();
  const config = JSON.parse(fssync.readFileSync(
    path.join(engine.configDir, 'prompt-config.json'), 'utf8'
  ));

  console.log('\n🌹 SkyyRose Prompt Studio — Product List');
  console.log('='.repeat(70));

  const byCollection = {};
  for (const item of report) {
    const col = item.collection || 'unknown';
    (byCollection[col] = byCollection[col] || []).push(item);
  }

  for (const [col, products] of Object.entries(byCollection)) {
    const colDNA = config.collections[col];
    console.log(`\n── ${colDNA?.displayName || col.toUpperCase()} ──────────────────────────────`);
    for (const p of products) {
      const icon    = STATUS_ICONS[p.status] || '?';
      const tech    = TECHNIQUE_EMOJIS[p.technique] || '?';
      const fp      = p.fingerprinted ? '🔍' : '○';
      console.log(`  ${icon} ${tech} ${fp}  ${p.productId.padEnd(12)} ${p.name}`);
    }
  }

  const ok      = report.filter(r => r.status === 'ok').length;
  const warn    = report.filter(r => r.status === 'warn').length;
  const missing = report.filter(r => r.status === 'missing').length;
  const fpd     = report.filter(r => r.fingerprinted).length;

  console.log('\n' + '─'.repeat(70));
  console.log(`Legend: ✅ ok  ⚠️  warn  ❌ missing | 🔍 fingerprinted  ○ not fingerprinted`);
  console.log(`Technique: 🔲 embossed  🔵 silicone  🧵 embroidered  🎨 sublimation  🏷️ woven  🔆 laser  🔀 mixed  ❓ TBD  🚫 missing`);
  console.log(`\nSummary: ${ok} ok | ${warn} warn | ${missing} missing | ${fpd}/${report.length} fingerprinted`);
}

async function cmdInspect(productId, templateId) {
  if (!productId || !templateId) {
    console.error('Usage: node build/prompt-studio.js inspect <sku> <template>');
    process.exit(1);
  }
  const engine = new PromptEngine();
  console.log(`\n🔍 Resolved prompt: ${productId} × ${templateId}`);
  console.log('='.repeat(70));

  const garmentAnalysis = await loadCachedAnalysis(productId);
  const prompt = engine.resolve(productId, templateId, { garmentAnalysis });
  console.log(prompt);

  const { valid, missingFields, warnings } = engine.validateAccuracy(productId);
  console.log('\n' + '─'.repeat(70));
  console.log(`Accuracy: ${valid ? '✅ valid' : '⚠️  issues found'}`);
  if (missingFields.length) console.log(`  Missing: ${missingFields.join(', ')}`);
  if (warnings.length) warnings.forEach(w => console.log(`  ⚠️  ${w}`));
}

async function cmdAuditBranding() {
  const engine = new PromptEngine();
  const report = engine.auditBranding();

  const needsWork = report.filter(r => r.status !== 'ok');
  const ok        = report.filter(r => r.status === 'ok');

  console.log('\n🔒 Branding Technique Audit');
  console.log('='.repeat(70));

  if (needsWork.length === 0) {
    console.log('✅ All products have confirmed brandingTech!\n');
  } else {
    console.log(`\n❌ Needs work (${needsWork.length}):`);
    for (const item of needsWork) {
      const tech = TECHNIQUE_EMOJIS[item.technique] || '?';
      console.log(`\n  ${item.productId} — ${item.name} ${tech} [${item.technique}]`);
      item.issues.forEach(issue => console.log(`    → ${issue}`));
    }
  }

  if (ok.length) {
    console.log(`\n✅ Confirmed (${ok.length}):`);
    for (const item of ok) {
      const tech = TECHNIQUE_EMOJIS[item.technique] || '?';
      const fp   = item.fingerprinted ? ' 🔍' : '';
      console.log(`  ${item.productId} — ${item.technique} ${tech}${fp}`);
    }
  }

  console.log(`\nTotal: ${ok.length}/${report.length} confirmed`);
  console.log(`Fingerprinted: ${report.filter(r => r.fingerprinted).length}/${report.length}`);
  console.log('\nNext step: node build/prompt-studio.js fingerprint-all');
}

async function cmdOverride(productId, fieldPath, value) {
  if (!productId || !fieldPath || value === undefined) {
    console.error('Usage: node build/prompt-studio.js override <sku> <field> <value>');
    console.error('  e.g. node build/prompt-studio.js override br-001 brandingTech.technique embossed');
    process.exit(1);
  }

  const engine       = new PromptEngine();
  const overridePath = path.join(engine.overridesDir, `${productId}.json`);

  let override;
  try {
    override = JSON.parse(fssync.readFileSync(overridePath, 'utf8'));
  } catch {
    console.error(`Override not found: ${productId}`);
    process.exit(1);
  }

  // Set nested field via dot notation
  const parts = fieldPath.split('.');
  let obj = override;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!obj[parts[i]]) obj[parts[i]] = {};
    obj = obj[parts[i]];
  }
  obj[parts[parts.length - 1]] = value;

  await fs.writeFile(overridePath, JSON.stringify(override, null, 2));
  console.log(`✅ Updated ${productId}.${fieldPath} = ${JSON.stringify(value)}`);
}

async function cmdFingerprint(productId) {
  const engine  = new PromptEngine();
  const override = engine._loadOverride(productId);
  if (!override) {
    console.error(`No override found for ${productId} — create it first`);
    process.exit(1);
  }

  const ai = getAI();
  console.log(`\n🔍 Fingerprinting: ${productId} — ${override.name}`);
  console.log('─'.repeat(60));

  // Load reference images
  const refs  = override.referenceImages || [];
  const parts = [];

  for (const ref of refs) {
    const fullPath = path.join(SOURCE_DIR, ref);
    const img      = await loadImageBase64(fullPath);
    if (img) {
      parts.push({ inlineData: img });
      console.log(`  📷 Loaded: ${path.basename(ref)}`);
    }
  }

  if (parts.length === 0) {
    console.error(`  ❌ No reference images found for ${productId}`);
    process.exit(1);
  }

  parts.push({ text: `
You are a luxury fashion technical director specializing in garment decoration and branding techniques.

Analyze the garment(s) in the images above.
Your job: identify EVERY logo, graphic, and branding element — and determine the EXACT decoration technique used for each.

For EACH branding element found, provide:
1. LOCATION — where on the garment (e.g. "center chest", "left thigh", "back upper")
2. DESCRIPTION — what it is (rose logo, text, graphic, patch, etc.)
3. TECHNIQUE — the EXACT decoration method:
   - embossed: physically pressed/debossed impression INTO fabric (tonal, same color as fabric)
   - silicone: 3D raised silicone cut-out appliqué adhered to fabric (slight gloss)
   - embroidered: thread-stitched (raised texture from thread buildup, can see individual threads)
   - sublimation: dye-printed INTO fabric fibers (no surface texture, color is IN the fabric)
   - woven-label-patch: jacquard-woven label sewn on (small rectangular/square patch with woven pattern)
   - laser-engraved: burned/debossed into leather or material surface
   - printed: screen print or direct-to-garment print (flat, sits ON fabric surface)
   - heat-transfer: vinyl or transfer sheet applied with heat (slight edge visible, different texture than fabric)
   - embroidered-patch: pre-made embroidered badge sewn onto garment
4. COLOR — exact color(s) of the element
5. SIZE — approximate size relative to garment
6. NOT_TECHNIQUES — list 3 techniques it is DEFINITELY NOT

Respond in this exact JSON format:
{
  "logos": [
    {
      "location": "center chest",
      "description": "exact description",
      "technique": "embossed",
      "color": "black-on-black tonal",
      "size": "approx 3 inches",
      "notTechniques": ["printed", "embroidered", "silicone"]
    }
  ],
  "accuracyScore": 0.95,
  "notes": "any important observations"
}

Be precise. This data becomes a legally-meaningful product specification used in customer-facing imagery.
  `.trim() });

  const { GoogleGenAI } = require('@google/genai');
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [{ role: 'user', parts }],
  });

  const text = response.candidates?.[0]?.content?.parts?.[0]?.text || '';

  // Extract JSON from response
  let fingerprintData;
  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error('No JSON found in response');
    fingerprintData = JSON.parse(jsonMatch[0]);
  } catch (err) {
    console.error(`  ❌ Failed to parse Flash response: ${err.message}`);
    console.error('  Raw response:', text.slice(0, 500));
    process.exit(1);
  }

  fingerprintData.analyzedAt  = new Date().toISOString();
  fingerprintData.model       = 'gemini-2.5-flash';
  fingerprintData.productId   = productId;
  fingerprintData.verifiedBy  = 'Flash vision fingerprint';

  engine.writeFingerprint(productId, fingerprintData);

  console.log(`\n  ✅ Fingerprint saved for ${productId}:`);
  (fingerprintData.logos || []).forEach(logo => {
    const emoji = TECHNIQUE_EMOJIS[logo.technique] || '?';
    console.log(`     ${emoji} ${logo.location}: ${logo.technique} — ${logo.description}`);
  });
  console.log(`  Score: ${fingerprintData.accuracyScore || 'n/a'}`);
  if (fingerprintData.notes) console.log(`  Notes: ${fingerprintData.notes}`);
}

async function cmdFingerprintAll(force = false) {
  const engine = new PromptEngine();
  const report = engine.auditBranding();
  const todo   = force ? report : report.filter(r => !r.fingerprinted);

  console.log(`\n🔍 Fingerprinting ${force ? 'ALL' : 'unfingerprinted'} products (${todo.length}/${report.length})`);

  for (const item of todo) {
    try {
      await cmdFingerprint(item.productId);
      console.log(`  ⏸️  Rate limiting (3s)...`);
      await new Promise(r => setTimeout(r, 3000));
    } catch (err) {
      console.error(`  ❌ Failed ${item.productId}: ${err.message}`);
    }
  }
  console.log('\n✅ Fingerprint-all complete');
}

async function cmdVerifyOutput(productId, imagePath) {
  if (!productId || !imagePath) {
    console.error('Usage: node build/prompt-studio.js verify-output <sku> <image-path>');
    process.exit(1);
  }

  const engine   = new PromptEngine();
  const override = engine._loadOverride(productId);
  if (!override?.logoFingerprint) {
    console.error(`No fingerprint for ${productId} — run: node build/prompt-studio.js fingerprint ${productId}`);
    process.exit(1);
  }

  const ai        = getAI();
  const fp        = override.logoFingerprint;
  const absPath   = path.isAbsolute(imagePath) ? imagePath : path.join(process.cwd(), imagePath);
  const img       = await loadImageBase64(absPath);

  if (!img) {
    console.error(`Image not found: ${absPath}`);
    process.exit(1);
  }

  console.log(`\n🔬 Verifying output accuracy: ${productId}`);
  console.log(`  Image: ${path.basename(absPath)}`);

  const specLines = (fp.logos || []).map((logo, i) =>
    `Logo ${i + 1} (${logo.location}): should be ${logo.technique} — ${logo.description}. NOT: ${logo.notTechniques?.join(', ')}`
  ).join('\n');

  const parts = [
    { inlineData: img },
    { text: `
Analyze this AI-generated fashion image and check if the branding/logo techniques match the specification below.

SPECIFICATION:
${specLines}

For each logo in the spec, determine:
1. Is the logo/branding visible in the generated image?
2. Does the decoration technique appear to match the spec?
3. Does it look like any of the prohibited techniques?

Rate each as:
- PASS: technique appears correct
- WARN: logo present but technique is unclear or ambiguous
- FAIL: wrong technique detected

Respond in JSON:
{
  "results": [
    {
      "location": "center chest",
      "specTechnique": "embossed",
      "visible": true,
      "status": "PASS|WARN|FAIL",
      "reason": "brief explanation"
    }
  ],
  "overallStatus": "PASS|WARN|FAIL",
  "overallScore": 0.95
}
    `.trim() }
  ];

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [{ role: 'user', parts }]
  });

  const text = response.candidates?.[0]?.content?.parts?.[0]?.text || '';
  let verifyResult;
  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    verifyResult = JSON.parse(jsonMatch[0]);
  } catch {
    verifyResult = { overallStatus: 'WARN', overallScore: 0, rawText: text };
  }

  verifyResult.verifiedAt = new Date().toISOString();
  verifyResult.productId  = productId;
  verifyResult.image      = path.basename(absPath);

  const icon = { PASS: '✅', WARN: '⚠️ ', FAIL: '❌' }[verifyResult.overallStatus] || '?';
  console.log(`\n  ${icon} Overall: ${verifyResult.overallStatus} (score: ${verifyResult.overallScore || 'n/a'})`);
  (verifyResult.results || []).forEach(r => {
    const ri = { PASS: '✅', WARN: '⚠️ ', FAIL: '❌' }[r.status] || '?';
    console.log(`  ${ri} ${r.location}: ${r.status} — ${r.reason}`);
  });

  // Append to GENERATION_REPORT.json
  const reportPath = path.join(OUTPUT_DIR, 'GENERATION_REPORT.json');
  let report = {};
  try { report = JSON.parse(fssync.readFileSync(reportPath, 'utf8')); } catch {}
  if (!report.accuracyChecks) report.accuracyChecks = [];
  report.accuracyChecks.push(verifyResult);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(`  📄 Saved to GENERATION_REPORT.json`);

  return verifyResult;
}

async function cmdAccuracyReport() {
  const engine = new PromptEngine();
  const report = engine.auditBranding();

  // Load GENERATION_REPORT for verify-output results
  const reportPath = path.join(OUTPUT_DIR, 'GENERATION_REPORT.json');
  let genReport = {};
  try { genReport = JSON.parse(fssync.readFileSync(reportPath, 'utf8')); } catch {}
  const checks = genReport.accuracyChecks || [];

  console.log('\n📊 SkyyRose Accuracy Report');
  console.log('='.repeat(70));

  let pass = 0, warn = 0, fail = 0, notChecked = 0;
  for (const item of report) {
    const check = checks.filter(c => c.productId === item.productId).pop();
    const { valid, warnings } = engine.validateAccuracy(item.productId);
    let statusLine = '';
    if (check) {
      const icon = { PASS: '✅', WARN: '⚠️ ', FAIL: '❌' }[check.overallStatus] || '?';
      statusLine = `${icon} verified (score: ${check.overallScore})`;
      if (check.overallStatus === 'PASS') pass++;
      else if (check.overallStatus === 'WARN') warn++;
      else fail++;
    } else {
      statusLine = item.fingerprinted ? '🔍 fingerprinted, not verified' : '○ not fingerprinted';
      notChecked++;
    }
    const tech = TECHNIQUE_EMOJIS[item.technique] || '?';
    console.log(`  ${tech} ${item.productId.padEnd(12)} ${item.name.padEnd(35)} ${statusLine}`);
  }

  console.log('\n' + '─'.repeat(70));
  console.log(`Verified: ✅ ${pass} pass  ⚠️  ${warn} warn  ❌ ${fail} fail`);
  console.log(`Not verified: ${notChecked} (run fingerprint + verify-output first)`);
  console.log('\nNext: node build/prompt-studio.js verify-output <sku> <output-image>');
}

async function cmdSaveVersion(templateId, label) {
  if (!templateId || !label) {
    console.error('Usage: node build/prompt-studio.js save-version <template> <label>');
    process.exit(1);
  }
  const engine     = new PromptEngine();
  const savedPath  = engine.saveVersion(templateId, label);
  console.log(`✅ Saved: ${path.basename(savedPath)}`);
}

async function cmdVersions(templateId) {
  if (!templateId) {
    console.error('Usage: node build/prompt-studio.js versions <template>');
    process.exit(1);
  }
  const engine   = new PromptEngine();
  const versions = engine.listVersions(templateId);
  console.log(`\nVersions for ${templateId}:`);
  if (!versions.length) {
    console.log('  (none saved yet — run: node build/prompt-studio.js save-version ' + templateId + ' baseline-v1)');
  } else {
    versions.forEach(v => console.log(`  - ${v.label}  (${v.file})`));
  }
}

async function cmdDiff(templateId, vA, vB) {
  if (!templateId || !vA || !vB) {
    console.error('Usage: node build/prompt-studio.js diff <template> <vA> <vB>');
    process.exit(1);
  }
  const engine = new PromptEngine();
  const result = engine.diff(templateId, vA, vB);
  console.log(`\nDiff: ${templateId} / ${vA} → ${vB}`);
  if (result.same) {
    console.log('  No differences.');
    return;
  }
  console.log(`  ${result.changes.length} line(s) changed:\n`);
  result.changes.forEach(c => {
    console.log(`  Line ${c.line}:`);
    console.log(`    - ${c.from}`);
    console.log(`    + ${c.to}`);
  });
}

async function cmdRollback(templateId, label) {
  if (!templateId || !label) {
    console.error('Usage: node build/prompt-studio.js rollback <template> <label>');
    process.exit(1);
  }
  const engine = new PromptEngine();
  const result = engine.rollback(templateId, label);
  console.log(`✅ Rolled back ${templateId} to ${result.rolledBack}`);
  console.log(`   Current was saved as: ${result.savedCurrentAs}`);
}

async function cmdTest(productId, templateId, pose) {
  if (!productId || !templateId) {
    console.error('Usage: node build/prompt-studio.js test <sku> <template> [pose]');
    process.exit(1);
  }

  const engine        = new PromptEngine();
  const override      = engine._loadOverride(productId);
  const ai            = getAI();
  const garmentAnalysis = await loadCachedAnalysis(productId);
  const options = pose ? { pose, garmentAnalysis } : { garmentAnalysis };

  const prompt = engine.resolve(productId, templateId, options);
  console.log(`\n🧪 Test generation: ${productId} × ${templateId}${pose ? ` [${pose}]` : ''}`);
  console.log('─'.repeat(60));

  // Load reference images
  const refs  = override?.referenceImages || [];
  const parts = [];
  for (const ref of refs) {
    const img = await loadImageBase64(path.join(SOURCE_DIR, ref));
    if (img) {
      parts.push({ inlineData: img });
      console.log(`  📷 ${path.basename(ref)}`);
    }
  }
  parts.push({ text: prompt });

  console.log(`  🤖 Calling gemini-2.5-flash-image...`);

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: [{ role: 'user', parts }]
  });

  let imageBase64 = null;
  for (const part of (response.candidates?.[0]?.content?.parts || [])) {
    if (part.inlineData?.data) { imageBase64 = part.inlineData.data; break; }
  }

  if (!imageBase64) {
    console.error('  ❌ No image returned');
    const text = response.candidates?.[0]?.content?.parts?.[0]?.text;
    if (text) console.log('  Model response:', text.slice(0, 200));
    process.exit(1);
  }

  const outDir  = path.join(OUTPUT_DIR, productId);
  await fs.mkdir(outDir, { recursive: true });
  const suffix  = pose ? `-${pose}` : '';
  const outPath = path.join(outDir, `${productId}-${templateId}${suffix}-test.jpg`);
  await fs.writeFile(outPath, Buffer.from(imageBase64, 'base64'));
  const stat = await fs.stat(outPath);

  console.log(`  ✅ Saved: ${path.relative(process.cwd(), outPath)}`);
  console.log(`  💾 Size: ${(stat.size / 1024).toFixed(0)}KB`);
}

async function cmdGenerateAd(target, platform) {
  if (!target || !platform) {
    console.error('Usage: node build/prompt-studio.js generate-ad <sku|collection> <platform>');
    console.error('  Platforms: instagram | stories | tiktok-cover | launch-banner');
    process.exit(1);
  }

  // Determine if target is a collection or a product SKU
  const isCollection = Object.keys(COLLECTION_PRODUCTS).includes(target);
  const productIds   = isCollection ? COLLECTION_PRODUCTS[target] : [target];

  const engine = new PromptEngine();
  const ai     = getAI();

  console.log(`\n🎯 Generating ad creative: ${target} × ${platform} (${productIds.length} product(s))`);

  for (const productId of productIds) {
    const override = engine._loadOverride(productId);
    if (!override) { console.warn(`  ⚠️  Skipping ${productId} — no override`); continue; }

    const garmentAnalysis = await loadCachedAnalysis(productId);
    const prompt = engine.resolve(productId, 'ad-creative', {
      garmentAnalysis,
      campaignContext: { platform, campaign: isCollection ? `${target} collection campaign` : '' }
    });

    console.log(`\n  📱 ${productId} — ${override.name}`);

    const refs  = override.referenceImages || [];
    const parts = [];
    for (const ref of refs.slice(0, 2)) { // Max 2 reference images for ads
      const img = await loadImageBase64(path.join(SOURCE_DIR, ref));
      if (img) parts.push({ inlineData: img });
    }
    parts.push({ text: prompt });

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: [{ role: 'user', parts }]
    });

    let imageBase64 = null;
    for (const part of (response.candidates?.[0]?.content?.parts || [])) {
      if (part.inlineData?.data) { imageBase64 = part.inlineData.data; break; }
    }

    if (!imageBase64) {
      console.error(`    ❌ No image for ${productId}`);
      continue;
    }

    const adDir  = path.join(OUTPUT_DIR, productId, 'ads');
    await fs.mkdir(adDir, { recursive: true });
    const outPath = path.join(adDir, `${productId}-ad-${platform}.jpg`);
    await fs.writeFile(outPath, Buffer.from(imageBase64, 'base64'));
    console.log(`    ✅ ${path.relative(process.cwd(), outPath)}`);

    if (productIds.length > 1 && productId !== productIds[productIds.length - 1]) {
      console.log('    ⏸️  Rate limiting (4s)...');
      await new Promise(r => setTimeout(r, 4000));
    }
  }

  console.log('\n✅ Ad creative generation complete');
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function loadCachedAnalysis(productId) {
  const analysisPath = path.join(OUTPUT_DIR, productId, `${productId}-garment-analysis.txt`);
  try {
    return await fs.readFile(analysisPath, 'utf8');
  } catch {
    return null;
  }
}

// ── Entry point ───────────────────────────────────────────────────────────────

async function main() {
  const [,, cmd, ...args] = process.argv;

  const commands = {
    list:              () => cmdList(),
    inspect:           () => cmdInspect(args[0], args[1]),
    'audit-branding':  () => cmdAuditBranding(),
    override:          () => cmdOverride(args[0], args[1], args[2]),
    fingerprint:       () => cmdFingerprint(args[0]),
    'fingerprint-all': () => cmdFingerprintAll(args.includes('--force')),
    'verify-output':   () => cmdVerifyOutput(args[0], args[1]),
    'accuracy-report': () => cmdAccuracyReport(),
    'save-version':    () => cmdSaveVersion(args[0], args[1]),
    versions:          () => cmdVersions(args[0]),
    diff:              () => cmdDiff(args[0], args[1], args[2]),
    rollback:          () => cmdRollback(args[0], args[1]),
    test:              () => cmdTest(args[0], args[1], args[2]),
    'generate-ad':     () => cmdGenerateAd(args[0], args[1]),
  };

  if (!cmd || !commands[cmd]) {
    console.log('\n🌹 SkyyRose Prompt Studio\n');
    console.log('Commands:');
    console.log('  list                              List all products with brandingTech status');
    console.log('  inspect <sku> <template>          Show final resolved prompt');
    console.log('  audit-branding                    Products missing/incomplete brandingTech');
    console.log('  override <sku> <field> <value>    Set a field on a product override');
    console.log('  fingerprint <sku>                 Flash vision → writes logoFingerprint');
    console.log('  fingerprint-all [--force]         Fingerprint all (or use --force to re-fingerprint)');
    console.log('  verify-output <sku> <image>       Post-generation accuracy check');
    console.log('  accuracy-report                   Aggregate accuracy status');
    console.log('  save-version <template> <label>   Snapshot current template');
    console.log('  versions <template>               List saved versions');
    console.log('  diff <template> <vA> <vB>         Diff two versions');
    console.log('  rollback <template> <label>       Restore a version');
    console.log('  test <sku> <template> [pose]      Generate 1 test image');
    console.log('  generate-ad <sku|collection> <platform>  Generate ad creative');
    console.log('\nTemplates: fashion-model | skyy-pose | scene | ad-creative');
    console.log('Platforms: instagram | stories | tiktok-cover | launch-banner');
    process.exit(cmd ? 1 : 0);
  }

  try {
    await commands[cmd]();
  } catch (err) {
    console.error(`\n❌ Error: ${err.message}`);
    if (process.env.DEBUG) console.error(err.stack);
    process.exit(1);
  }
}

main();
