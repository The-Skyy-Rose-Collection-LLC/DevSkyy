/**
 * Type definitions for the Coding Architect Agent
 */

import type { SDKMessage } from "@anthropic-ai/claude-agent-sdk";

/**
 * Agent configuration options
 */
export interface AgentConfig {
  /** Model to use (defaults to claude-sonnet-4-5) */
  model?: string;
  /** Working directory for the agent */
  workingDirectory?: string;
  /** Maximum budget in USD */
  maxBudgetUsd?: number;
  /** Enable verbose logging */
  verbose?: boolean;
}

/**
 * Result from an agent query
 */
export interface AgentResult {
  /** Session ID for the conversation */
  sessionId: string;
  /** All messages from the conversation */
  messages: SDKMessage[];
  /** Final result text */
  result: string;
  /** Total cost in USD */
  totalCostUsd: number;
  /** Execution duration in milliseconds */
  durationMs: number;
}

/**
 * Prompt technique types
 */
export type PromptTechnique =
  | "role_based"
  | "chain_of_thought"
  | "few_shot"
  | "self_consistency"
  | "tree_of_thoughts"
  | "react"
  | "rag"
  | "prompt_chaining"
  | "generated_knowledge"
  | "negative_prompting"
  | "constitutional"
  | "costard"
  | "meta_prompting"
  | "recursive"
  | "structured_output"
  | "temperature_scheduling"
  | "ensemble";

/**
 * Task type for automatic technique selection
 */
export type TaskType =
  | "reasoning"
  | "classification"
  | "creative"
  | "search"
  | "qa"
  | "extraction"
  | "moderation"
  | "generation"
  | "code_review"
  | "architecture"
  | "debugging"
  | "refactoring";

/**
 * Code analysis result
 */
export interface CodeAnalysisResult {
  /** File path analyzed */
  filePath: string;
  /** Language detected */
  language: "typescript" | "python" | "javascript" | "other";
  /** Issues found */
  issues: CodeIssue[];
  /** Metrics computed */
  metrics: CodeMetrics;
  /** Suggestions for improvement */
  suggestions: string[];
}

/**
 * Code issue found during analysis
 */
export interface CodeIssue {
  /** Issue severity */
  severity: "error" | "warning" | "info" | "hint";
  /** Line number */
  line: number;
  /** Column number */
  column?: number;
  /** Issue message */
  message: string;
  /** Rule or check that flagged this */
  rule?: string;
  /** Suggested fix */
  fix?: string;
}

/**
 * Code metrics from analysis
 */
export interface CodeMetrics {
  /** Lines of code */
  linesOfCode: number;
  /** Cyclomatic complexity */
  cyclomaticComplexity: number;
  /** Cognitive complexity */
  cognitiveComplexity?: number;
  /** Maintainability index (0-100) */
  maintainabilityIndex?: number;
  /** Number of functions */
  functionCount: number;
  /** Number of classes */
  classCount: number;
}

/**
 * Architecture recommendation
 */
export interface ArchitectureRecommendation {
  /** Approach name */
  approach: string;
  /** Description of the approach */
  description: string;
  /** Pros of this approach */
  pros: string[];
  /** Cons of this approach */
  cons: string[];
  /** Evaluation score (1-10) */
  score: number;
  /** Whether this is the recommended approach */
  recommended: boolean;
}

/**
 * Tool execution result
 */
export interface ToolResult<T = unknown> {
  /** Whether the tool succeeded */
  success: boolean;
  /** Result data */
  data?: T;
  /** Error message if failed */
  error?: string;
}

/**
 * Message types from the agent
 */
export type MessageType =
  | "assistant"
  | "user"
  | "system"
  | "tool_call"
  | "tool_result"
  | "error";

/**
 * Handler for agent messages
 */
export type MessageHandler = (message: SDKMessage) => void | Promise<void>;

/**
 * Few-shot example for prompting
 */
export interface FewShotExample {
  /** Input prompt */
  input: string;
  /** Expected output */
  output: string;
  /** Optional explanation */
  explanation?: string;
}

/**
 * Prompt template configuration
 */
export interface PromptTemplate {
  /** Template name */
  name: string;
  /** Template description */
  description: string;
  /** The template string with {variables} */
  template: string;
  /** Technique this template uses */
  technique: PromptTechnique;
  /** Required variables */
  variables: string[];
  /** Example outputs */
  examples?: FewShotExample[];
}
