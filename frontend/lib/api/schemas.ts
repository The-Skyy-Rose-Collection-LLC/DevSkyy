import { z } from 'zod';

// Provider Schemas
export const ProviderInfoSchema = z.object({
    name: z.string(),
    display_name: z.string(),
    enabled: z.boolean(),
    avg_latency_ms: z.number(),
    win_rate: z.number(),
    total_competitions: z.number(),
});

export const ProviderStatsSchema = z.object({
    provider: z.string(),
    total_competitions: z.number(),
    wins: z.number(),
    win_rate: z.number(),
    avg_score: z.number(),
    avg_latency_ms: z.number(),
    total_cost_usd: z.number(),
});

// Competition Schemas
export const EntryScoreSchema = z.object({
    relevance: z.number().default(0),
    quality: z.number().default(0),
    completeness: z.number().default(0),
    efficiency: z.number().default(0),
    brand_alignment: z.number().default(0),
    total: z.number().default(0),
});

export const CompetitionEntrySchema = z.object({
    provider: z.string(),
    rank: z.number(),
    scores: EntryScoreSchema,
    latency_ms: z.number(),
    cost_usd: z.number(),
    response_preview: z.string().default(''),
});

export const CompetitionResponseSchema = z.object({
    id: z.string(),
    task_id: z.string(),
    prompt_preview: z.string(),
    status: z.string(),
    winner: CompetitionEntrySchema.nullable(),
    entries: z.array(CompetitionEntrySchema),
    ab_test_reasoning: z.string().nullable().optional(),
    ab_test_confidence: z.number().nullable().optional(),
    total_duration_ms: z.number(),
    total_cost_usd: z.number(),
    created_at: z.string(),
});

export const HistoryEntrySchema = z.object({
    id: z.string(),
    prompt_preview: z.string(),
    winner_provider: z.string(),
    winner_score: z.number(),
    total_cost_usd: z.number(),
    created_at: z.string(),
});

// Pipeline & 3D Schemas
export const PipelineStatusSchema = z.object({
    status: z.enum(['healthy', 'degraded', 'down']),
    active_jobs: z.number(),
    queued_jobs: z.number(),
    providers_online: z.number(),
    providers_total: z.number(),
});

export const Provider3DSchema = z.object({
    id: z.string(),
    name: z.string(),
    type: z.enum(['commercial', 'huggingface', 'local']),
    capabilities: z.array(z.string()),
    avg_generation_time_s: z.number(),
    status: z.enum(['online', 'offline', 'busy']),
});

export const Job3DSchema = z.object({
    id: z.string(),
    status: z.enum(['queued', 'processing', 'completed', 'failed']),
    provider: z.string(),
    input_type: z.enum(['text', 'image']),
    input: z.string(),
    output_url: z.string().optional(),
    error: z.string().optional(),
    created_at: z.string(),
    completed_at: z.string().optional(),
});

// Health Schema
export const HealthResponseSchema = z.object({
    status: z.string(),
    version: z.string(),
    uptime: z.number(),
});

// Asset Schemas
export const AssetSchema = z.object({
    id: z.string(),
    filename: z.string(),
    path: z.string(),
    collection: z.enum(['black_rose', 'signature', 'love_hurts', 'showroom', 'runway']),
    type: z.enum(['image', '3d_model', 'video', 'texture']),
    metadata: z.object({
        sku: z.string().optional(),
        product_name: z.string().optional(),
        tags: z.array(z.string()).optional(),
        width: z.number().optional(),
        height: z.number().optional(),
        size_bytes: z.number().optional(),
        format: z.string().optional(),
    }).optional(),
    thumbnail_url: z.string().optional(),
    created_at: z.string(),
    updated_at: z.string().optional(),
});

export const AssetListResponseSchema = z.object({
    assets: z.array(AssetSchema),
    total: z.number(),
    page: z.number(),
    limit: z.number(),
    has_more: z.boolean(),
});

// QA Review Schemas
export const QAReviewSchema = z.object({
    id: z.string(),
    asset_id: z.string(),
    job_id: z.string(),
    reference_image_url: z.string(),
    generated_model_url: z.string(),
    fidelity_score: z.number().min(0).max(100),
    fidelity_breakdown: z.object({
        geometry: z.number(),
        materials: z.number(),
        colors: z.number(),
        proportions: z.number(),
        branding: z.number(),
        texture_detail: z.number(),
    }).optional(),
    status: z.enum(['pending', 'approved', 'rejected', 'regenerating']),
    notes: z.string().optional(),
    reviewed_by: z.string().optional(),
    created_at: z.string(),
    reviewed_at: z.string().optional(),
});

export const QAReviewListResponseSchema = z.object({
    reviews: z.array(QAReviewSchema),
    total: z.number(),
    pending_count: z.number(),
    approved_count: z.number(),
    rejected_count: z.number(),
});

// Batch Job Schema
export const BatchJobSchema = z.object({
    id: z.string(),
    status: z.enum(['pending', 'processing', 'completed', 'failed', 'paused']),
    total_assets: z.number(),
    processed_assets: z.number(),
    failed_assets: z.number(),
    current_asset: z.string().optional(),
    progress_percentage: z.number(),
    started_at: z.string().optional(),
    completed_at: z.string().optional(),
    error_log: z.array(z.string()).optional(),
});


// Settings Schema
export const SettingsSchema = z.object({
    wordpress: z.object({
        url: z.string(),
        consumerKey: z.string(),
        consumerSecret: z.string(),
        autoSync: z.boolean(),
    }),
    vercel: z.object({
        projectId: z.string(),
        apiToken: z.string(),
        orgId: z.string(),
    }),
    autonomous: z.object({
        enabled: z.boolean(),
        circuitBreakerThreshold: z.number(),
        retryAttempts: z.number(),
        retryDelay: z.number(),
    }),
    ui: z.object({
        theme: z.enum(['light', 'dark']),
        typography: z.enum(['playfair', 'inter', 'system']),
        accentColor: z.string(),
    }),
    system: z.object({
        apiTimeout: z.number(),
        maxConcurrentRequests: z.number(),
        logLevel: z.enum(['debug', 'info', 'warn', 'error']),
    }),
});

// Agent Schemas
export const AgentInfoSchema = z.object({
    name: z.string(),
    version: z.string(),
    category: z.string(),
    status: z.string(),
    capabilities: z.array(z.string()),
    endpoints: z.array(z.string()),
    last_execution: z.string().nullable().optional(),
});

export const AgentListResponseSchema = z.object({
    timestamp: z.string(),
    total_agents: z.number(),
    active_agents: z.number(),
    agents_by_category: z.record(z.string(), z.number()),
    agents: z.array(AgentInfoSchema),
});

// Task Schema
export const TaskMetricsSchema = z.object({
    startTime: z.string(),
    endTime: z.string().optional(),
    durationMs: z.number().optional(),
    tokensUsed: z.number().optional(),
    costUsd: z.number().optional(),
    provider: z.string().optional(),
    promptTechnique: z.string().optional(),
});

export const TaskSchema = z.object({
    taskId: z.string(),
    agentType: z.string(),
    prompt: z.string(),
    status: z.enum(['pending', 'running', 'completed', 'failed']),
    result: z.any().optional(),
    error: z.string().optional(),
    createdAt: z.string(),
    metrics: TaskMetricsSchema,
});
