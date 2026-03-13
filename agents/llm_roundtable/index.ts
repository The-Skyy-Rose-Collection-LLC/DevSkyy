/**
 * LLM Roundtable — Public API
 *
 * @package DevSkyy
 */

export { roundtableServer } from "./engine.js";

export {
  recordLearning,
  updateRoutingWeights,
  getLearnedRoute,
  isModelDisabled,
  recordFailure,
  recordSuccess,
  getFallbackModel,
  withRetry,
  isAnomalousScore,
  isTechniqueUnderperforming,
  checkEloHealth,
  getHealthReport,
  getRecentCorrections,
} from "./adaptive.js";

export type {
  LearningRecord,
  RoutingWeight,
  CircuitBreaker,
  CorrectionRecord,
} from "./adaptive.js";
