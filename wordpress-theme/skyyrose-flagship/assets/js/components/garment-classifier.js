/**
 * Garment Classifier — CLIP zero-shot inference in the browser.
 *
 * Gates uploads before they reach paid pipelines (FASHN, Compositor, Gemini).
 * FASHN is ~$1.20 per try-on run; rejecting one bad upload pays for many
 * classifier sessions. The classifier runs entirely client-side with no
 * network round-trip after model download.
 *
 * Pipeline: file -> RawImage -> CLIP zero-shot -> bucket aggregation -> verdict.
 *
 * @package SkyyRose
 * @since   1.1.0
 */

const TRANSFORMERS_CDN =
  'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';

const MODEL_ID = 'Xenova/clip-vit-base-patch32';
const TASK = 'zero-shot-image-classification';

/**
 * Candidate label set. Each natural-language prompt maps to a "bucket" —
 * either a FASHN GarmentCategory enum value or REJECT.
 *
 * The aggregation step sums scores per bucket. A garment label set with
 * multiple synonyms reinforces the correct bucket, which is critical for
 * CLIP because it tends to spread probability across visually similar
 * descriptions (hoodie vs sweatshirt vs pullover).
 */
const CANDIDATES = Object.freeze([
  // tops
  { prompt: 'a photo of a hoodie or sweatshirt', bucket: 'tops' },
  { prompt: 'a photo of a t-shirt', bucket: 'tops' },
  { prompt: 'a photo of a jersey or sports shirt', bucket: 'tops' },
  { prompt: 'a photo of a long-sleeve shirt', bucket: 'tops' },
  // outerwear
  { prompt: 'a photo of a jacket or bomber', bucket: 'outerwear' },
  { prompt: 'a photo of a coat or trench', bucket: 'outerwear' },
  // bottoms
  { prompt: 'a photo of pants or jeans', bucket: 'bottoms' },
  { prompt: 'a photo of shorts', bucket: 'bottoms' },
  // dresses
  { prompt: 'a photo of a dress', bucket: 'dresses' },
  // rejects (these absorb probability mass when the image is not a garment)
  { prompt: 'a selfie or portrait of a person', bucket: 'reject_person' },
  { prompt: 'a screenshot of a webpage or app', bucket: 'reject_screenshot' },
  { prompt: 'a blank or solid color background', bucket: 'reject_blank' },
  { prompt: 'a watermarked stock photo', bucket: 'reject_watermark' },
  { prompt: 'an unrelated object that is not clothing', bucket: 'reject_other' },
]);

const VALID_GARMENT_BUCKETS = new Set(['tops', 'bottoms', 'dresses', 'outerwear']);

let pipelinePromise = null;
let transformersModule = null;

/**
 * Lazy-load Transformers.js from CDN. Resolves once, caches forever.
 *
 * Importing dynamically (rather than as a top-level static import) lets the
 * module live alongside non-ES-module legacy theme JS without forcing the
 * whole page into module mode.
 */
async function loadTransformers() {
  if (transformersModule) return transformersModule;
  transformersModule = await import(/* @vite-ignore */ TRANSFORMERS_CDN);
  return transformersModule;
}

/**
 * Get (or create) the singleton CLIP pipeline.
 *
 * @param {(info: object) => void} [onProgress] - download progress callback
 * @returns {Promise<Function>}
 */
export async function getClassifier(onProgress) {
  if (pipelinePromise) return pipelinePromise;

  pipelinePromise = (async () => {
    const { pipeline, env } = await loadTransformers();

    // Cache models in the browser; defaults are sane but make explicit.
    env.allowLocalModels = false;
    env.useBrowserCache = true;

    return pipeline(TASK, MODEL_ID, {
      dtype: 'q8',
      device: 'wasm',
      progress_callback: onProgress,
    });
  })();

  // If load fails, allow retry on next call.
  pipelinePromise.catch(() => {
    pipelinePromise = null;
  });

  return pipelinePromise;
}

/**
 * Run zero-shot classification on a File or Blob.
 *
 * @param {File|Blob|string} input
 * @param {Function} pipe - the loaded pipeline
 * @returns {Promise<Array<{label: string, score: number}>>}
 */
async function runInference(input, pipe) {
  const labels = CANDIDATES.map((c) => c.prompt);
  const url = typeof input === 'string' ? input : URL.createObjectURL(input);
  try {
    return await pipe(url, labels);
  } finally {
    if (typeof input !== 'string') URL.revokeObjectURL(url);
  }
}

/**
 * Sum scores per bucket. Returns a plain object keyed by bucket name.
 */
function aggregate(rawScores) {
  const buckets = Object.create(null);
  for (const { label, score } of rawScores) {
    const match = CANDIDATES.find((c) => c.prompt === label);
    if (!match) continue;
    buckets[match.bucket] = (buckets[match.bucket] || 0) + score;
  }
  return buckets;
}

/**
 * Read image dimensions and basic metadata without loading into Three.js.
 *
 * @param {File|Blob} file
 * @returns {Promise<{width: number, height: number, size: number, type: string}>}
 */
function readImageMeta(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const meta = {
        width: img.naturalWidth,
        height: img.naturalHeight,
        size: file.size,
        type: file.type || 'application/octet-stream',
      };
      URL.revokeObjectURL(url);
      resolve(meta);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Image could not be decoded'));
    };
    img.src = url;
  });
}

/**
 * Decide whether the upload is safe to send downstream.
 *
 * USER CONTRIBUTION POINT — see {@link evaluatePolicy} below. The technical
 * pipeline (load -> infer -> aggregate) is fixed; the policy is where SkyyRose
 * domain knowledge lives.
 */
function buildVerdict(buckets, meta) {
  const ranked = Object.entries(buckets)
    .sort(([, a], [, b]) => b - a)
    .map(([bucket, score]) => ({ bucket, score }));

  const top = ranked[0] || { bucket: 'reject_other', score: 0 };
  const runnerUp = ranked[1] || { bucket: 'reject_other', score: 0 };

  return evaluatePolicy({
    topBucket: top.bucket,
    topScore: top.score,
    runnerUpScore: runnerUp.score,
    isGarment: VALID_GARMENT_BUCKETS.has(top.bucket),
    ranked,
    meta,
  });
}

/**
 * Gate thresholds. These are the dials that tune false-accept vs false-reject.
 * If FASHN waste rises, raise MIN_TOP_SCORE and MIN_GAP. If users complain
 * about clear garment shots being rejected, lower them.
 */
const POLICY = Object.freeze({
  MIN_WIDTH: 512,
  MIN_HEIGHT: 512,
  MIN_TOP_SCORE: 0.5,
  MIN_GAP: 0.15,
});

/**
 * Brand-voiced reject messages keyed by classifier verdict. Kept in one place
 * so copywriting changes don't touch the gate logic.
 */
const REJECT_MESSAGES = Object.freeze({
  reject_person:
    'That looks like a person, not the garment. Upload the clothing item by itself — flat-lay or on a hanger.',
  reject_screenshot:
    'Screenshots can\'t be used as references. Upload an original photo of the garment.',
  reject_blank:
    'This image looks blank or low-detail. Try better lighting and a closer crop.',
  reject_watermark:
    'Watermarked stock photos can\'t be used. Upload an original shot of the garment.',
  reject_other:
    'We can\'t identify a garment in this image. Try a clear photo of the clothing item only.',
  ambiguous:
    'The image is ambiguous. Try a sharper, well-lit shot of the garment alone — no busy backgrounds.',
  too_small:
    'Image is too small. Use at least 512x512 pixels for usable results.',
});

function makeVerdict(accepted, reason, category, confidence, ranked, meta) {
  return { accepted, reason, category, confidence, diagnostics: { ranked, meta } };
}

/**
 * ───────────────────────────────────────────────────────────────────────────
 *  POLICY — production gate.
 * ───────────────────────────────────────────────────────────────────────────
 *
 * Order of checks is deliberate — cheaper rejections first:
 *   1. Image dimensions (already known, no extra work)
 *   2. Non-garment buckets (any reject_* hit blocks the upload)
 *   3. Confidence floor + gap to runner-up (catches ambiguous classifications)
 *   4. Accept with category mapped to FASHN GarmentCategory
 */
function evaluatePolicy({ topBucket, topScore, runnerUpScore, isGarment, ranked, meta }) {
  if (meta.width < POLICY.MIN_WIDTH || meta.height < POLICY.MIN_HEIGHT) {
    return makeVerdict(false, REJECT_MESSAGES.too_small, null, topScore, ranked, meta);
  }

  if (!isGarment) {
    const reason = REJECT_MESSAGES[topBucket] || REJECT_MESSAGES.reject_other;
    return makeVerdict(false, reason, null, topScore, ranked, meta);
  }

  const gap = topScore - runnerUpScore;
  if (topScore < POLICY.MIN_TOP_SCORE || gap < POLICY.MIN_GAP) {
    return makeVerdict(false, REJECT_MESSAGES.ambiguous, null, topScore, ranked, meta);
  }

  return makeVerdict(true, 'Garment confirmed.', topBucket, topScore, ranked, meta);
}

/**
 * Public API — single call: file in, verdict out.
 *
 * @param {File|Blob} file
 * @param {(info: object) => void} [onProgress] - model load progress
 * @returns {Promise<object>} verdict object (see evaluatePolicy contract)
 */
export async function classifyGarment(file, onProgress) {
  if (!(file instanceof Blob)) {
    throw new TypeError('classifyGarment expects a File or Blob');
  }

  const [meta, pipe] = await Promise.all([
    readImageMeta(file),
    getClassifier(onProgress),
  ]);

  const raw = await runInference(file, pipe);
  const buckets = aggregate(raw);
  return buildVerdict(buckets, meta);
}

/**
 * Free the model from memory. Call on page unload or when the upload form
 * unmounts, especially on long-running SPAs.
 */
export async function disposeClassifier() {
  if (!pipelinePromise) return;
  try {
    const pipe = await pipelinePromise;
    if (pipe && typeof pipe.dispose === 'function') {
      await pipe.dispose();
    }
  } finally {
    pipelinePromise = null;
  }
}

export const __testing = { CANDIDATES, POLICY, REJECT_MESSAGES, aggregate, evaluatePolicy };
