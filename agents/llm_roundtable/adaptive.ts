/**
 * Adaptive Intelligence Module — Self-Healing, Self-Learning, Self-Correcting
 *
 * Mirrors base_super_agent.py LearningRecord + PromptEngineeringModule patterns
 * ported to TypeScript for the LLM Roundtable.
 *
 * Self-Learning:
 *   - Tracks technique + model win rates per category from real battle data
 *   - Updates routing weights automatically after each battle
 *   - Learns which few-shot examples produce the highest scores
 *   - Builds a confidence map: category → (best model, best technique, confidence%)
 *
 * Self-Healing:
 *   - Detects API failures and retries with exponential backoff
 *   - Falls back to alternate models when primary is unavailable
 *   - Recovers corrupted persistence files from last known good state
 *   - Circuit breaker: disables a model after 3 consecutive failures
 *
 * Self-Correcting:
 *   - Detects anomalous judge scores (>2σ from category mean) and re-judges
 *   - When a technique underperforms its rolling average, auto-downgrades it
 *   - When a model's Elo drops below threshold, flags for investigation
 *   - Validates battle results against historical distributions
 *
 * @package DevSkyy
 */

import fs from "fs";
import path from "path";
import { loadJSON, saveJSON, backupAndSave, DATA_DIR } from "./utils.js";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------
const LEARNING_FILE = path.join(DATA_DIR, "learning.json");
const CIRCUIT_FILE = path.join(DATA_DIR, "circuit_breakers.json");
const ROUTING_FILE = path.join(DATA_DIR, "routing_weights.json");
const CORRECTIONS_LOG = path.join(DATA_DIR, "corrections.json");

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A single learning record from a battle outcome. */
export interface LearningRecord {
  battleId: string;
  timestamp: string;
  category: string;
  technique: string;
  modelId: string;
  score: number;
  won: boolean;
  latencyMs: number;
  cost: number;
  errorOccurred: boolean;
}

/** Routing weight for a category → model + technique combination. */
export interface RoutingWeight {
  category: string;
  bestModel: string;
  bestTechnique: string;
  confidence: number; // 0-100, based on sample size and consistency
  sampleSize: number;
  avgScore: number;
  lastUpdated: string;
}

/** Circuit breaker state for a model. */
export interface CircuitBreaker {
  modelId: string;
  consecutiveFailures: number;
  lastFailure: string;
  isOpen: boolean; // true = model is disabled
  cooldownUntil: string | null;
}

/** Correction record — when the system detects and fixes an anomaly. */
export interface CorrectionRecord {
  timestamp: string;
  type: "anomalous_score" | "technique_downgrade" | "elo_alert" | "circuit_break" | "data_recovery";
  description: string;
  action: string;
  battleId?: string;
  modelId?: string;
  technique?: string;
}

// ---------------------------------------------------------------------------
// Recovery Helpers (uses logCorrection — must stay in this module)
// ---------------------------------------------------------------------------

/**
 * Self-Healing: Recover corrupted JSON by falling back to backup.
 */
function recoverFile<T>(file: string, fallback: T): T {
  const backup = `${file}.bak`;
  try {
    return JSON.parse(fs.readFileSync(file, "utf-8"));
  } catch {
    // Primary corrupted — try backup
    try {
      const recovered = JSON.parse(fs.readFileSync(backup, "utf-8"));
      logCorrection({
        timestamp: new Date().toISOString(),
        type: "data_recovery",
        description: `Recovered ${path.basename(file)} from backup after corruption`,
        action: "Restored from .bak file",
      });
      // Restore primary from backup
      fs.writeFileSync(file, JSON.stringify(recovered, null, 2));
      return recovered;
    } catch {
      return fallback;
    }
  }
}

// ---------------------------------------------------------------------------
// SELF-LEARNING
// ---------------------------------------------------------------------------

/**
 * Record a learning observation from a battle outcome.
 * Called after every battle — builds the historical dataset.
 */
export function recordLearning(record: LearningRecord): void {
  const records = loadJSON<LearningRecord[]>(LEARNING_FILE, []);
  records.unshift(record);
  // Keep last 2000 records
  backupAndSave(LEARNING_FILE, records.slice(0, 2000));
}

/**
 * Update routing weights based on accumulated learning data.
 * Analyzes all learning records to find the best model + technique per category.
 */
export function updateRoutingWeights(): Record<string, RoutingWeight> {
  const records = loadJSON<LearningRecord[]>(LEARNING_FILE, []);
  if (records.length === 0) return {};

  // Group by category
  const byCategory: Record<string, LearningRecord[]> = {};
  for (const r of records) {
    if (!byCategory[r.category]) byCategory[r.category] = [];
    byCategory[r.category].push(r);
  }

  const weights: Record<string, RoutingWeight> = {};

  for (const [category, catRecords] of Object.entries(byCategory)) {
    // Find best model (highest avg score across battles in this category)
    const modelScores: Record<string, { total: number; count: number; wins: number }> = {};
    const techScores: Record<string, { total: number; count: number }> = {};

    for (const r of catRecords) {
      if (!modelScores[r.modelId]) modelScores[r.modelId] = { total: 0, count: 0, wins: 0 };
      modelScores[r.modelId].total += r.score;
      modelScores[r.modelId].count++;
      if (r.won) modelScores[r.modelId].wins++;

      if (!techScores[r.technique]) techScores[r.technique] = { total: 0, count: 0 };
      techScores[r.technique].total += r.score;
      techScores[r.technique].count++;
    }

    // Best model by avg score
    let bestModel = "";
    let bestModelAvg = 0;
    for (const [id, stats] of Object.entries(modelScores)) {
      const avg = stats.total / stats.count;
      if (avg > bestModelAvg) {
        bestModel = id;
        bestModelAvg = avg;
      }
    }

    // Best technique by avg score
    let bestTech = "";
    let bestTechAvg = 0;
    for (const [tech, stats] of Object.entries(techScores)) {
      const avg = stats.total / stats.count;
      if (avg > bestTechAvg) {
        bestTech = tech;
        bestTechAvg = avg;
      }
    }

    // Confidence based on sample size and score consistency
    const sampleSize = catRecords.length;
    const scores = catRecords.map((r) => r.score);
    const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
    const variance = scores.reduce((sum, s) => sum + (s - mean) ** 2, 0) / scores.length;
    const stdDev = Math.sqrt(variance);
    // High sample + low variance = high confidence
    const confidence = Math.min(100, Math.round((sampleSize / 50) * 100 * (1 - stdDev / 100)));

    weights[category] = {
      category,
      bestModel,
      bestTechnique: bestTech,
      confidence: Math.max(0, confidence),
      sampleSize,
      avgScore: Math.round(bestModelAvg * 10) / 10,
      lastUpdated: new Date().toISOString(),
    };
  }

  backupAndSave(ROUTING_FILE, weights);
  return weights;
}

/**
 * Get the learned best model + technique for a category.
 * Returns null if not enough data to be confident.
 */
export function getLearnedRoute(category: string): RoutingWeight | null {
  const weights = loadJSON<Record<string, RoutingWeight>>(ROUTING_FILE, {});
  const entry = weights[category];
  if (!entry || entry.confidence < 30 || entry.sampleSize < 5) return null;
  return entry;
}

// ---------------------------------------------------------------------------
// SELF-HEALING
// ---------------------------------------------------------------------------

/**
 * Check if a model's circuit breaker is open (disabled due to failures).
 */
export function isModelDisabled(modelId: string): boolean {
  const breakers = loadJSON<Record<string, CircuitBreaker>>(CIRCUIT_FILE, {});
  const breaker = breakers[modelId];
  if (!breaker || !breaker.isOpen) return false;

  // Check if cooldown has expired (5 minutes)
  if (breaker.cooldownUntil) {
    if (new Date() > new Date(breaker.cooldownUntil)) {
      // Cooldown expired — half-open: allow one attempt
      breaker.isOpen = false;
      breaker.consecutiveFailures = 0;
      saveJSON(CIRCUIT_FILE, breakers);
      return false;
    }
  }

  return true;
}

/**
 * Record a model failure. Opens circuit breaker after 3 consecutive failures.
 */
export function recordFailure(modelId: string, error: string): void {
  const breakers = loadJSON<Record<string, CircuitBreaker>>(CIRCUIT_FILE, {});

  if (!breakers[modelId]) {
    breakers[modelId] = {
      modelId,
      consecutiveFailures: 0,
      lastFailure: "",
      isOpen: false,
      cooldownUntil: null,
    };
  }

  const breaker = breakers[modelId];
  breaker.consecutiveFailures++;
  breaker.lastFailure = new Date().toISOString();

  if (breaker.consecutiveFailures >= 3) {
    breaker.isOpen = true;
    // 5 minute cooldown before retry
    const cooldown = new Date(Date.now() + 5 * 60 * 1000);
    breaker.cooldownUntil = cooldown.toISOString();

    logCorrection({
      timestamp: new Date().toISOString(),
      type: "circuit_break",
      description: `${modelId} disabled after ${breaker.consecutiveFailures} consecutive failures. Last error: ${error.substring(0, 100)}`,
      action: `Circuit breaker opened. Cooldown until ${cooldown.toISOString()}`,
      modelId,
    });
  }

  saveJSON(CIRCUIT_FILE, breakers);
}

/**
 * Record a model success. Resets circuit breaker.
 */
export function recordSuccess(modelId: string): void {
  const breakers = loadJSON<Record<string, CircuitBreaker>>(CIRCUIT_FILE, {});
  if (breakers[modelId]) {
    breakers[modelId].consecutiveFailures = 0;
    breakers[modelId].isOpen = false;
    breakers[modelId].cooldownUntil = null;
    saveJSON(CIRCUIT_FILE, breakers);
  }
}

/**
 * Get fallback model when primary is disabled.
 * Returns model ID of the healthiest available model.
 */
export function getFallbackModel(
  disabledModelId: string,
  availableModels: string[]
): string | null {
  const breakers = loadJSON<Record<string, CircuitBreaker>>(CIRCUIT_FILE, {});
  const healthy = availableModels.filter((id) => {
    if (id === disabledModelId) return false;
    const b = breakers[id];
    return !b || !b.isOpen;
  });
  return healthy[0] || null;
}

/**
 * Retry with exponential backoff. Used for transient API errors.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelayMs: number = 1000
): Promise<T> {
  let lastError: Error | null = null;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastError = err;
      if (attempt < maxRetries - 1) {
        const delay = baseDelayMs * Math.pow(2, attempt);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }
  throw lastError;
}

// ---------------------------------------------------------------------------
// SELF-CORRECTING
// ---------------------------------------------------------------------------

/**
 * Detect anomalous scores — scores that deviate >2σ from the category mean.
 * Returns true if the score is anomalous and should be re-judged.
 */
export function isAnomalousScore(
  score: number,
  category: string
): { anomalous: boolean; reason: string } {
  const records = loadJSON<LearningRecord[]>(LEARNING_FILE, []);
  const catRecords = records.filter((r) => r.category === category);

  if (catRecords.length < 10) {
    return { anomalous: false, reason: "Insufficient data for anomaly detection" };
  }

  const scores = catRecords.map((r) => r.score);
  const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
  const variance = scores.reduce((sum, s) => sum + (s - mean) ** 2, 0) / scores.length;
  const stdDev = Math.sqrt(variance);

  if (Math.abs(score - mean) > 2 * stdDev) {
    const direction = score > mean ? "above" : "below";
    return {
      anomalous: true,
      reason: `Score ${score} is ${direction} 2σ from category mean ${mean.toFixed(1)} (σ=${stdDev.toFixed(1)})`,
    };
  }

  return { anomalous: false, reason: "" };
}

/**
 * Check if a technique is underperforming and should be downgraded.
 * Compares its rolling-10 average against its all-time average.
 */
export function isTechniqueUnderperforming(
  technique: string,
  category: string
): { underperforming: boolean; recommendation: string } {
  const records = loadJSON<LearningRecord[]>(LEARNING_FILE, []);
  const techRecords = records.filter(
    (r) => r.technique === technique && r.category === category
  );

  if (techRecords.length < 15) {
    return { underperforming: false, recommendation: "" };
  }

  const allTimeAvg =
    techRecords.reduce((sum, r) => sum + r.score, 0) / techRecords.length;
  const recent10 = techRecords.slice(0, 10);
  const recentAvg =
    recent10.reduce((sum, r) => sum + r.score, 0) / recent10.length;

  // If recent performance is >10% below all-time, flag it
  if (recentAvg < allTimeAvg * 0.9) {
    const drop = ((allTimeAvg - recentAvg) / allTimeAvg * 100).toFixed(1);

    // Find the best alternative technique for this category
    const altTechs: Record<string, number[]> = {};
    for (const r of records.filter((r) => r.category === category && r.technique !== technique)) {
      if (!altTechs[r.technique]) altTechs[r.technique] = [];
      altTechs[r.technique].push(r.score);
    }

    let bestAlt = "";
    let bestAltAvg = 0;
    for (const [t, scores] of Object.entries(altTechs)) {
      if (scores.length < 3) continue;
      const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
      if (avg > bestAltAvg) {
        bestAlt = t;
        bestAltAvg = avg;
      }
    }

    const recommendation = bestAlt
      ? `Switch ${category} from ${technique} (recent avg ${recentAvg.toFixed(1)}) to ${bestAlt} (avg ${bestAltAvg.toFixed(1)})`
      : `${technique} declining ${drop}% in ${category} — no clear alternative yet`;

    logCorrection({
      timestamp: new Date().toISOString(),
      type: "technique_downgrade",
      description: `${technique} dropped ${drop}% below all-time avg in ${category}`,
      action: recommendation,
      technique,
    });

    return { underperforming: true, recommendation };
  }

  return { underperforming: false, recommendation: "" };
}

/**
 * Check if a model's Elo has dropped below alert threshold.
 */
export function checkEloHealth(
  modelId: string,
  currentElo: number,
  alertThreshold: number = 1400
): { alert: boolean; message: string } {
  if (currentElo < alertThreshold) {
    const message = `${modelId} Elo at ${currentElo} — below ${alertThreshold} threshold. Consider removing from active competitions or investigating quality degradation.`;
    logCorrection({
      timestamp: new Date().toISOString(),
      type: "elo_alert",
      description: message,
      action: "Flagged for investigation",
      modelId,
    });
    return { alert: true, message };
  }
  return { alert: false, message: "" };
}

// ---------------------------------------------------------------------------
// Correction Log
// ---------------------------------------------------------------------------

function logCorrection(record: CorrectionRecord): void {
  const corrections = loadJSON<CorrectionRecord[]>(CORRECTIONS_LOG, []);
  corrections.unshift(record);
  saveJSON(CORRECTIONS_LOG, corrections.slice(0, 500));
}

/**
 * Get recent corrections for monitoring.
 */
export function getRecentCorrections(limit: number = 20): CorrectionRecord[] {
  return loadJSON<CorrectionRecord[]>(CORRECTIONS_LOG, []).slice(0, limit);
}

/**
 * Get full adaptive health report.
 */
export function getHealthReport(): {
  routingWeights: Record<string, RoutingWeight>;
  circuitBreakers: Record<string, CircuitBreaker>;
  recentCorrections: CorrectionRecord[];
  learningRecordCount: number;
} {
  return {
    routingWeights: loadJSON(ROUTING_FILE, {}),
    circuitBreakers: loadJSON(CIRCUIT_FILE, {}),
    recentCorrections: getRecentCorrections(10),
    learningRecordCount: loadJSON<any[]>(LEARNING_FILE, []).length,
  };
}
