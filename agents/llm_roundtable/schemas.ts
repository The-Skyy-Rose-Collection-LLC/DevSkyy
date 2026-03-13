/**
 * LLM Roundtable — Input Validation Schemas
 *
 * Zod schemas for battle inputs. Validates task length, categories,
 * techniques, and model IDs before dispatching to the engine.
 *
 * @package DevSkyy
 */

import { z } from "zod";

export const VALID_CATEGORIES = [
  "Content", "SEO", "Social Media", "Email", "Analytics",
  "Support", "Code", "Creative", "Pricing", "Reasoning",
  "Classification", "Extraction", "Research", "Planning",
  "Vision", "General",
] as const;

export const VALID_TECHNIQUES = [
  "chain_of_thought", "tree_of_thoughts", "react", "rag",
  "few_shot", "structured_output", "constitutional",
  "role_based", "self_consistency", "ensemble",
] as const;

export const VALID_MODELS = [
  "claude-opus", "claude-sonnet", "claude-haiku",
  "gpt-4o", "gemini-2",
] as const;

/** Validates input for a standard multi-model battle. */
export const BattleInputSchema = z.object({
  task: z
    .string()
    .min(5, "Task must be at least 5 characters")
    .max(2000, "Task must be under 2000 characters"),
  category: z.enum(VALID_CATEGORIES).optional().default("General"),
  models: z.array(z.enum(VALID_MODELS)).optional(),
  technique: z.enum(VALID_TECHNIQUES).optional(),
});

/** Validates input for a technique A/B test battle. */
export const TechniqueBattleInputSchema = z.object({
  task: z
    .string()
    .min(5, "Task must be at least 5 characters")
    .max(2000, "Task must be under 2000 characters"),
  category: z.enum(VALID_CATEGORIES).optional().default("General"),
  modelId: z.enum(VALID_MODELS).optional().default("claude-sonnet"),
  techniques: z.array(z.enum(VALID_TECHNIQUES)).min(2).optional(),
});

export type BattleInput = z.infer<typeof BattleInputSchema>;
export type TechniqueBattleInput = z.infer<typeof TechniqueBattleInputSchema>;
