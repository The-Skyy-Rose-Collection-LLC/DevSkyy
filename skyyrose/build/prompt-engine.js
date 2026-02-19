/**
 * SkyyRose Prompt Engine
 *
 * Resolves final generation prompts from layered config:
 *   Base template → Collection DNA → Product override → Flash garment analysis
 *
 * Core principle: brandingTech + logoFingerprint are the accuracy enforcement layer.
 * The ML (Flash vision fingerprint) is the source of truth for decoration technique.
 * Do NOT assume technique from marketing copy — run `fingerprint <sku>` first.
 *
 * Usage:
 *   const engine = new PromptEngine(configDir);
 *   const prompt = engine.resolve('br-001', 'fashion-model', { garmentAnalysis });
 */

'use strict';

const path = require('path');
const fs   = require('fs');

const DEFAULT_CONFIG_DIR = path.join(__dirname, '../assets/data/prompts');

class PromptEngine {
  constructor(configDir = DEFAULT_CONFIG_DIR) {
    this.configDir     = configDir;
    this.templatesDir  = path.join(configDir, 'templates');
    this.overridesDir  = path.join(configDir, 'overrides');
    this.versionsDir   = path.join(configDir, 'versions');
    this._config       = null;
    this._templates    = {};
    this._overrides    = {};
  }

  // ── Loading ────────────────────────────────────────────────────────────────

  _loadConfig() {
    if (this._config) return this._config;
    const configPath = path.join(this.configDir, 'prompt-config.json');
    if (!fs.existsSync(configPath)) {
      throw new Error(`prompt-config.json not found at ${configPath}`);
    }
    this._config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    return this._config;
  }

  _loadTemplate(templateId) {
    if (this._templates[templateId]) return this._templates[templateId];
    const templatePath = path.join(this.templatesDir, `${templateId}.json`);
    if (!fs.existsSync(templatePath)) {
      throw new Error(`Template not found: ${templateId} (${templatePath})`);
    }
    this._templates[templateId] = JSON.parse(fs.readFileSync(templatePath, 'utf8'));
    return this._templates[templateId];
  }

  _loadOverride(productId) {
    if (this._overrides[productId]) return this._overrides[productId];
    const overridePath = path.join(this.overridesDir, `${productId}.json`);
    if (!fs.existsSync(overridePath)) return null;
    this._overrides[productId] = JSON.parse(fs.readFileSync(overridePath, 'utf8'));
    return this._overrides[productId];
  }

  _getCollection(productId) {
    const override = this._loadOverride(productId);
    if (override) return override.collection;
    // Infer from prefix
    if (productId.startsWith('br-')) return 'black-rose';
    if (productId.startsWith('lh-')) return 'love-hurts';
    if (productId.startsWith('sg-')) return 'signature';
    if (productId.startsWith('kids-')) return 'kids-capsule';
    return 'signature';
  }

  // ── Core Resolution ────────────────────────────────────────────────────────

  /**
   * Resolve a final prompt string for a product + template combination.
   * @param {string} productId - e.g. 'br-001'
   * @param {string} templateId - 'fashion-model' | 'skyy-pose' | 'scene' | 'ad-creative'
   * @param {object} options
   *   @param {string} [options.garmentAnalysis] - Flash Stage-1 vision output (anchors generation)
   *   @param {string} [options.pose] - For skyy-pose: 'idle' | 'point' | 'walk'
   *   @param {object} [options.campaignContext] - For ad-creative: { platform, campaign }
   * @returns {string} Final prompt string
   */
  resolve(productId, templateId, options = {}) {
    const config     = this._loadConfig();
    const template   = this._loadTemplate(templateId);
    const override   = this._loadOverride(productId);
    const collection = this._getCollection(productId);
    const collectionDNA = config.collections[collection] || {};

    if (templateId === 'fashion-model') {
      return this._resolveFashionModel(productId, template, override, collectionDNA, options);
    }
    if (templateId === 'skyy-pose') {
      return this._resolveSkyyPose(productId, template, override, collectionDNA, options);
    }
    if (templateId === 'scene') {
      return this._resolveScene(productId, template, override, collectionDNA, options);
    }
    if (templateId === 'ad-creative') {
      return this._resolveAdCreative(productId, template, override, collectionDNA, options);
    }
    throw new Error(`Unknown templateId: ${templateId}`);
  }

  _resolveFashionModel(productId, template, override, collectionDNA, { garmentAnalysis } = {}) {
    const productName    = override?.name || productId;
    const collectionName = collectionDNA.displayName || 'SkyyRose';
    const garmentTypeLock = override?.garmentTypeLock || null;

    // Accuracy blocks — these MUST appear first
    const brandingBlock = this._buildBrandingBlock(override);
    const fingerprintBlock = this._buildFingerprintBlock(override);
    const garmentLockBlock = garmentTypeLock
      ? `\n⚠️  GARMENT TYPE LOCK (READ FIRST):\n${garmentTypeLock}\nDo NOT substitute any other garment type. Generate EXACTLY this.\n`
      : '';
    const analysisBlock = garmentAnalysis
      ? `\n🔬 FLASH VISION ANALYSIS — TECHNICAL SPEC (highest priority reference):\n${garmentAnalysis}\n`
      : '';

    const pose    = override?.modelPose || 'Standing confidently, full body visible';
    const setting = override?.setting || `${collectionDNA.settings?.[0] || 'luxury studio'}`;

    return `
${template.header}

BRAND: SkyyRose ${collectionName} Collection
PRODUCT: ${productName}
STYLE: ${template.styleLine?.replace('{collectionName}', collectionName).replace('{productName}', productName) || 'Vogue, Harper\'s Bazaar, Elle editorial quality'}
${brandingBlock}${fingerprintBlock}${garmentLockBlock}${analysisBlock}
SUBJECT - FASHION MODEL:
- ${template.subject.description.replace('{garment}', override?.description?.garment || productName)}
- Expression: ${template.subject.expression}
- Pose: ${pose}
- ${template.subject.diversity}

GARMENT DETAILS (CRITICAL - MUST MATCH REFERENCE EXACTLY):
${override?.description ? Object.entries(override.description).map(([k, v]) => `- ${k.charAt(0).toUpperCase() + k.slice(1)}: ${v}`).join('\n') : `- Product: ${productName}`}
- ${template.garmentBlock.reproduce}
- ${template.garmentBlock.visibility}

SETTING & ENVIRONMENT:
${setting}
- ${collectionDNA.mood || ''}
- ${collectionDNA.settings?.join(', ') || ''} aesthetic

PHOTOGRAPHY STYLE:
- ${template.photography.style}
- ${template.photography.camera}
- ${template.photography.casting}
- ${template.photography.standard}

LIGHTING:
- ${template.lighting.style}
- ${collectionDNA.accentColor} accent lighting throughout
- ${template.lighting.shadows}
- ${template.lighting.keyLight}

COLOR PALETTE:
- Primary colors: ${collectionDNA.palette || ''}
- Brand accent color: ${collectionDNA.accentColor} prominently featured
- Rich, saturated colors with luxury depth
- Editorial color grading (Vogue/Harper's Bazaar quality)

COMPOSITION:
- ${template.composition.framing}
- ${template.composition.rule}
- ${template.composition.space}
- ${template.composition.positioning}

TECHNICAL SPECIFICATIONS:
- ${template.technical.aspectRatio}
- Quality: ${template.technical.quality}
- ${template.technical.sharpness}

CRITICAL REQUIREMENTS:
${template.criticalRequirements.map((r, i) => `${i + 1}. ${r.replace('{garment}', garmentTypeLock || productName)}`).join('\n')}

${template.closingLine}
    `.trim();
  }

  _resolveSkyyPose(productId, template, override, collectionDNA, { pose = 'idle', garmentAnalysis } = {}) {
    const productName = override?.name || productId;
    const poseSpec    = template.poses[pose] || template.poses.idle;

    const brandingBlock    = this._buildBrandingBlock(override);
    const fingerprintBlock = this._buildFingerprintBlock(override);
    const analysisBlock    = garmentAnalysis
      ? `TECHNICAL GARMENT SPEC (for reference accuracy):\n${garmentAnalysis}\n`
      : '';

    const setting = override?.setting || collectionDNA.settings?.[0] || 'luxury studio backdrop';

    return `
${template.header}

${template.referenceInstruction}

══════════════════════════════════════════════
${template.artStyle.block}
══════════════════════════════════════════════
${template.artStyle.style}
${template.artStyle.tone}
${template.artStyle.instruction}

══════════════════════════════════════════════
REQUIREMENT 1: SKYY MUST BE IDENTICAL TO REFERENCE
══════════════════════════════════════════════
The first image is the reference. The output character MUST be IDENTICAL.
Same face. Same afro. Same skin tone. Same body proportions. Same art style.

CHARACTER SPECS:
- ${template.character.ageAppearance}
- Build: ${template.character.build}
- Hair: ${template.character.hair}
- Skin: ${template.character.skin}
- Face: ${template.character.face}
- Expression: ${template.character.expression}

${template.character.criticalRules.map(r => `⚠️ ${r}`).join('\n')}

══════════════════════════════════════════════
REQUIREMENT 2: CLOTHING MUST MATCH PRODUCT EXACTLY
══════════════════════════════════════════════
${brandingBlock}${fingerprintBlock}${analysisBlock}
PRODUCT: ${productName} (${collectionDNA.displayName || ''} Collection)

CLOTHING RULES:
${template.clothingRules.map(r => `- ${r}`).join('\n')}

══════════════════════════════════════════════
POSE: ${poseSpec.label}
══════════════════════════════════════════════
${poseSpec.description}
Camera: ${poseSpec.cameraAngle}

SETTING:
${setting}
Mood: ${collectionDNA.mood || ''}

BACKGROUND:
${template.background.style}
${template.background.instruction}

CRITICAL FINAL RULES:
${template.criticalRules.map(r => `- ${r}`).join('\n')}
    `.trim();
  }

  _resolveScene(productId, template, override, collectionDNA) {
    const collection = override?.collection || this._getCollection(productId);
    const roomSpec   = template.rooms[collection] || Object.values(template.rooms)[0];

    return `
${template.header}

COLLECTION: ${collectionDNA.displayName || collection}
ROOM: ${roomSpec.name}
CONCEPT: ${roomSpec.concept}

ENVIRONMENT ELEMENTS (all must be present):
${roomSpec.elements.map(e => `- ${e}`).join('\n')}

LIGHTING:
${roomSpec.lighting}

COLOR PALETTE:
${roomSpec.palette}

MOOD:
${roomSpec.mood}
${collectionDNA.mood || ''}

TIME:
${roomSpec.timeOfDay}

TECHNICAL:
- Aspect ratio: ${template.technical.aspectRatio}
- Quality: ${template.technical.quality}
- Depth: ${template.technical.depth}
- ${template.technical.empty}

CRITICAL RULES:
${template.criticalRules.map(r => `- ${r}`).join('\n')}
    `.trim();
  }

  _resolveAdCreative(productId, template, override, collectionDNA, { campaignContext = {} } = {}) {
    const productName  = override?.name || productId;
    const collection   = override?.collection || this._getCollection(productId);
    const platform     = campaignContext.platform || 'instagram';
    const platformSpec = template.platforms[platform] || template.platforms.instagram;
    const voice        = template.collectionVoice[collection] || template.collectionVoice.signature;
    const special      = collectionDNA.specialInstruction || '';

    const brandingBlock    = this._buildBrandingBlock(override);
    const fingerprintBlock = this._buildFingerprintBlock(override);

    return `
${template.header}

COLLECTION: ${collectionDNA.displayName || collection}
PRODUCT: ${productName}
PLATFORM: ${platform.toUpperCase()} (${platformSpec.ratio})

PLATFORM SPECS:
- Format: ${platformSpec.style}
- Text overlay: ${platformSpec.textOverlay}
- Composition: ${platformSpec.composition}

COLLECTION VOICE:
- Tone: ${voice.tone}
- Copy style: ${voice.copyStyle}
- Color emphasis: ${voice.colorEmphasis}
- Visual style: ${voice.visualStyle}
${special ? `\nSPECIAL INSTRUCTION: ${special}` : ''}
${voice.specialInstruction ? `\n⭐ ${voice.specialInstruction}` : ''}

${brandingBlock}${fingerprintBlock}

PRODUCT PLACEMENT:
- ${template.productPlacement.primary}
- ${template.productPlacement.brandingBlock}
${campaignContext.campaign ? `\nCAMPAIGN CONTEXT:\n${campaignContext.campaign}` : ''}

TECHNICAL:
- Quality: ${template.technical.quality}
- Color grading: ${template.technical.colorGrading}
- Sharpness: ${template.technical.sharpness}

CRITICAL RULES:
${template.criticalRules.map(r => `- ${r}`).join('\n')}

TAGLINE OPTIONS (use one or create collection-appropriate variant):
${(voice.taglines || []).map(t => `"${t}"`).join(' | ')}
    `.trim();
  }

  // ── Accuracy Blocks ────────────────────────────────────────────────────────

  _buildBrandingBlock(override) {
    if (!override?.brandingTech) return '';
    const bt = override.brandingTech;
    if (bt.technique === 'TBD') {
      return `\n⚠️  BRANDING TECHNIQUE: TBD — run: node build/prompt-studio.js fingerprint ${override.productId}\n`;
    }
    if (bt.promptBlock) {
      return `\n${bt.promptBlock}\n`;
    }
    return `\n🔒 BRANDING TECHNIQUE: ${bt.technique.toUpperCase()}\n- ${bt.logo}\n- NOT: ${(bt.notTechniques || []).join(', ')}\n`;
  }

  _buildFingerprintBlock(override) {
    if (!override?.logoFingerprint) return '';
    const fp = override.logoFingerprint;
    const lines = [`\n🔍 LOGO FINGERPRINT — AI VISION VERIFIED SPEC (DO NOT DEVIATE):`];
    lines.push(`[Verified by Flash vision ${fp.analyzedAt?.slice(0, 10)} | accuracy: ${fp.accuracyScore || '?'}]`);
    (fp.logos || []).forEach((logo, i) => {
      lines.push(`\nLogo ${i + 1} (${logo.location}):`);
      lines.push(`  Description: ${logo.description}`);
      lines.push(`  → Technique: ${logo.technique.toUpperCase()}`);
      if (logo.color) lines.push(`  → Color: ${logo.color}`);
      if (logo.size) lines.push(`  → Size: ${logo.size}`);
      if (logo.notTechniques?.length) lines.push(`  → NOT: ${logo.notTechniques.join(', ')}`);
    });
    lines.push('');
    return lines.join('\n');
  }

  // ── Version Management ─────────────────────────────────────────────────────

  listVersions(templateId) {
    if (!fs.existsSync(this.versionsDir)) return [];
    return fs.readdirSync(this.versionsDir)
      .filter(f => f.startsWith(`${templateId}-`) && f.endsWith('.json'))
      .map(f => ({ file: f, label: f.replace(`${templateId}-`, '').replace('.json', '') }));
  }

  saveVersion(templateId, label) {
    const templatePath = path.join(this.templatesDir, `${templateId}.json`);
    if (!fs.existsSync(templatePath)) throw new Error(`Template not found: ${templateId}`);
    const versionPath = path.join(this.versionsDir, `${templateId}-${label}.json`);
    fs.copyFileSync(templatePath, versionPath);
    return versionPath;
  }

  rollback(templateId, versionLabel) {
    const versionPath  = path.join(this.versionsDir, `${templateId}-${versionLabel}.json`);
    if (!fs.existsSync(versionPath)) throw new Error(`Version not found: ${templateId}-${versionLabel}`);
    const templatePath = path.join(this.templatesDir, `${templateId}.json`);
    const currentLabel = `pre-rollback-${Date.now()}`;
    this.saveVersion(templateId, currentLabel);
    fs.copyFileSync(versionPath, templatePath);
    delete this._templates[templateId]; // invalidate cache
    return { rolledBack: versionLabel, savedCurrentAs: currentLabel };
  }

  diff(templateId, labelA, labelB) {
    const readContent = (label) => {
      if (label === 'current') {
        return fs.readFileSync(path.join(this.templatesDir, `${templateId}.json`), 'utf8');
      }
      return fs.readFileSync(path.join(this.versionsDir, `${templateId}-${label}.json`), 'utf8');
    };
    const a = readContent(labelA);
    const b = readContent(labelB);
    if (a === b) return { same: true, changes: [] };

    const linesA = a.split('\n');
    const linesB = b.split('\n');
    const changes = [];
    const maxLen = Math.max(linesA.length, linesB.length);
    for (let i = 0; i < maxLen; i++) {
      if (linesA[i] !== linesB[i]) {
        changes.push({ line: i + 1, from: linesA[i] ?? '(none)', to: linesB[i] ?? '(none)' });
      }
    }
    return { same: false, changes };
  }

  // ── Accuracy Validation ────────────────────────────────────────────────────

  /**
   * Validate accuracy fields for a product override.
   * @returns {{ valid: boolean, missingFields: string[], warnings: string[] }}
   */
  validateAccuracy(productId) {
    const override = this._loadOverride(productId);
    const missingFields = [];
    const warnings = [];

    if (!override) {
      return { valid: false, missingFields: ['override file missing'], warnings: [] };
    }

    if (!override.brandingTech) {
      missingFields.push('brandingTech');
    } else {
      if (!override.brandingTech.technique) missingFields.push('brandingTech.technique');
      if (override.brandingTech.technique === 'TBD') warnings.push('brandingTech.technique is TBD — run: node build/prompt-studio.js fingerprint ' + productId);
      if (!override.brandingTech.notTechniques?.length) warnings.push('brandingTech.notTechniques is empty — what should this NOT look like?');
    }

    if (!override.garmentTypeLock && !override.description) {
      warnings.push('No garmentTypeLock or description — AI may misidentify garment type');
    }

    if (!override.logoFingerprint) {
      warnings.push('logoFingerprint not populated — run: node build/prompt-studio.js fingerprint ' + productId);
    }

    const valid = missingFields.length === 0 && !warnings.some(w => w.includes('TBD'));
    return { valid, missingFields, warnings };
  }

  /**
   * Audit all product overrides for missing/incomplete brandingTech.
   * @returns {Array<{productId, status, issues}>}
   */
  auditBranding() {
    if (!fs.existsSync(this.overridesDir)) return [];
    const files = fs.readdirSync(this.overridesDir).filter(f => f.endsWith('.json'));
    return files.map(f => {
      const productId = f.replace('.json', '');
      const { valid, missingFields, warnings } = this.validateAccuracy(productId);
      const override = this._loadOverride(productId);
      return {
        productId,
        name: override?.name || productId,
        collection: override?.collection || '?',
        technique: override?.brandingTech?.technique || 'MISSING',
        fingerprinted: !!override?.logoFingerprint,
        status: valid ? 'ok' : (missingFields.length ? 'missing' : 'warn'),
        issues: [...missingFields.map(f => `missing: ${f}`), ...warnings]
      };
    }).sort((a, b) => a.productId.localeCompare(b.productId));
  }

  /**
   * Write logoFingerprint data to a product override file.
   * Called by prompt-studio.js after running Flash vision analysis.
   */
  writeFingerprint(productId, fingerprintData) {
    const overridePath = path.join(this.overridesDir, `${productId}.json`);
    if (!fs.existsSync(overridePath)) {
      throw new Error(`Override not found: ${productId}`);
    }
    const override = JSON.parse(fs.readFileSync(overridePath, 'utf8'));
    override.logoFingerprint = fingerprintData;
    // Also update brandingTech.technique if fingerprint confirms it
    if (fingerprintData.logos?.length && override.brandingTech?.technique === 'TBD') {
      const primaryTechnique = fingerprintData.logos[0]?.technique;
      if (primaryTechnique) {
        override.brandingTech.technique = primaryTechnique;
        override.brandingTech.logo = fingerprintData.logos.map(l => `${l.location}: ${l.description}`).join('; ');
      }
    }
    fs.writeFileSync(overridePath, JSON.stringify(override, null, 2));
    delete this._overrides[productId]; // invalidate cache
  }
}

module.exports = { PromptEngine, DEFAULT_CONFIG_DIR };
