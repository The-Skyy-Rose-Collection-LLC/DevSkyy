/**
 * DevSkyy Dashboard Types
 * =======================
 * Type definitions for the frontend dashboard.
 */

// Agent Types
export type SuperAgentType =
  | 'commerce'
  | 'creative'
  | 'marketing'
  | 'support'
  | 'operations'
  | 'analytics';

export type AgentStatus = 'idle' | 'running' | 'error' | 'learning';

export interface AgentInfo {
  id: string;
  type: SuperAgentType;
  name: string;
  description: string;
  status: AgentStatus;
  capabilities: string[];
  tools: ToolInfo[];
  mlModels: string[];
  stats: AgentStats;
}

export interface AgentStats {
  tasksCompleted: number;
  successRate: number;
  avgLatencyMs: number;
  totalCostUsd: number;
  learningCycles: number;
}

// Tool Types
export interface ToolInfo {
  name: string;
  description: string;
  category: string;
  parameters: ToolParameter[];
}

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: unknown;
}

// LLM Provider Types
export type LLMProvider =
  | 'anthropic'
  | 'openai'
  | 'google'
  | 'mistral'
  | 'cohere'
  | 'groq';

export interface LLMProviderInfo {
  provider: LLMProvider;
  model: string;
  displayName: string;
  status: 'available' | 'unavailable' | 'rate_limited';
  costPer1kTokens: number;
}

// Round Table Types
export type CompetitionStatus =
  | 'pending'
  | 'collecting'
  | 'scoring'
  | 'ab_testing'
  | 'completed'
  | 'failed';

export interface RoundTableEntry {
  id: string;
  taskId: string;
  prompt: string;
  status: CompetitionStatus;
  participants: RoundTableParticipant[];
  winner?: RoundTableParticipant;
  abTestResult?: ABTestResult;
  createdAt: string;
  completedAt?: string;
  totalDurationMs?: number;
  totalCostUsd?: number;
}

export interface RoundTableParticipant {
  provider: LLMProvider;
  model: string;
  response: string;
  scores: ResponseScores;
  latencyMs: number;
  costUsd: number;
  rank: number;
}

export interface ResponseScores {
  relevance: number;
  coherence: number;
  completeness: number;
  creativity: number;
  overall: number;
}

// A/B Testing Types
export type ABTestStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'insufficient_data';

export interface ABTestResult {
  testId: string;
  variantA: ABTestVariant;
  variantB: ABTestVariant;
  winner: 'A' | 'B' | 'tie';
  confidence: number;
  pValue: number;
  sampleSize: number;
  status: ABTestStatus;
  reasoning?: string;
}

export interface ABTestVariant {
  provider: LLMProvider;
  model: string;
  conversions: number;
  impressions: number;
  conversionRate: number;
}

export interface ABTestHistoryEntry {
  id: string;
  taskType: string;
  variantA: string;
  variantB: string;
  winner: string;
  confidence: number;
  createdAt: string;
}

// Task Types
export type TaskCategory =
  | 'reasoning'
  | 'classification'
  | 'creative'
  | 'search'
  | 'qa'
  | 'extraction'
  | 'moderation'
  | 'generation'
  | 'analysis';

export interface TaskRequest {
  agentType: SuperAgentType;
  prompt: string;
  category?: TaskCategory;
  useRoundTable?: boolean;
  parameters?: Record<string, unknown>;
}

export interface TaskResponse {
  taskId: string;
  agentType?: SuperAgentType;
  prompt?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: unknown;
  error?: string;
  metrics?: TaskMetrics;
  createdAt?: string;
}

// Brand Kit Types
export interface BrandColor {
  name: string;
  hex: string;
  rgb: string;
}

export interface BrandTone {
  primary: string;
  descriptors: string[];
  avoid: string[];
}

export interface BrandTypography {
  heading: string;
  body: string;
  accent: string;
}

export interface BrandTargetAudience {
  age_range: string;
  description: string;
  interests: string[];
  values: string[];
}

export interface CollectionConfig {
  name: string;
  tagline: string;
  mood: string;
  colors: string;
  style: string;
  description: string;
}

export interface BrandConfig {
  name: string;
  tagline: string;
  philosophy: string;
  location: string;
  tone: BrandTone;
  colors: Record<string, BrandColor>;
  typography: BrandTypography;
  target_audience: BrandTargetAudience;
  product_types: string[];
  quality_descriptors: string[];
}

export interface BrandData {
  brand: BrandConfig;
  collections: Record<string, CollectionConfig>;
}

export interface TaskMetrics {
  startTime: string;
  endTime?: string;
  durationMs?: number;
  tokensUsed?: number;
  costUsd?: number;
  provider?: LLMProvider;
  promptTechnique?: string;
}

// Visual Generation Types
export type VisualProvider =
  | 'google_imagen'
  | 'google_veo'
  | 'huggingface_flux'
  | 'tripo3d'
  | 'fashn';

export type GenerationType =
  | 'image_from_text'
  | 'video_from_text'
  | '3d_from_text'
  | '3d_from_image'
  | 'virtual_tryon';

export interface VisualGenerationRequest {
  type: GenerationType;
  prompt: string;
  provider?: VisualProvider;
  options?: Record<string, unknown>;
}

export interface VisualGenerationResult {
  id: string;
  type: GenerationType;
  provider: VisualProvider;
  url: string;
  thumbnailUrl?: string;
  metadata?: Record<string, unknown>;
}

// Dashboard Metrics
export interface DashboardMetrics {
  totalTasks: number;
  tasksToday: number;
  successRate: number;
  avgLatencyMs: number;
  totalCostUsd: number;
  costToday: number;
  activeAgents: number;
  roundTableWins: Record<LLMProvider, number>;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
}

export interface MetricsTimeSeries {
  tasks: TimeSeriesDataPoint[];
  latency: TimeSeriesDataPoint[];
  cost: TimeSeriesDataPoint[];
  successRate: TimeSeriesDataPoint[];
}

// Prompt Engineering Types
export type PromptTechnique =
  | 'chain_of_thought'
  | 'few_shot'
  | 'tree_of_thoughts'
  | 'react'
  | 'rag'
  | 'constitutional'
  | 'self_consistency'
  | 'structured_output'
  | 'role_based'
  | 'meta_prompting'
  | 'prompt_chaining'
  | 'analogical_reasoning'
  | 'socratic_method'
  | 'contrastive_learning'
  | 'recursive_refinement'
  | 'multi_persona'
  | 'constraint_based';

export interface PromptTechniqueInfo {
  technique: PromptTechnique;
  name: string;
  description: string;
  bestFor: TaskCategory[];
  example?: string;
}

// Learning Module Types
export interface LearningRecord {
  id: string;
  agentType: SuperAgentType;
  taskType: TaskCategory;
  success: boolean;
  metrics: TaskMetrics;
  improvements?: string[];
  timestamp: string;
}

export interface LearningStats {
  totalRecords: number;
  improvementRate: number;
  topPerformingTasks: TaskCategory[];
  recentImprovements: string[];
}

// Chat Types
export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  agentType?: SuperAgentType;
  toolCalls?: ToolCall[];
  metadata?: Record<string, unknown>;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
  startTime?: number;
  endTime?: number;
}

export interface StreamChunk {
  type: 'content' | 'tool_call' | 'tool_result' | 'status' | 'error';
  content?: string;
  toolCall?: ToolCall;
  status?: string;
  error?: string;
}

export interface ChatSession {
  id: string;
  agentType: SuperAgentType;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}
