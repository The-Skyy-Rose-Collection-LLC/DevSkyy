import { z } from 'zod';
import * as schemas from './schemas';

// Inferred Types
export type ProviderInfo = z.infer<typeof schemas.ProviderInfoSchema>;
export type ProviderStats = z.infer<typeof schemas.ProviderStatsSchema>;
export type EntryScore = z.infer<typeof schemas.EntryScoreSchema>;
export type CompetitionEntry = z.infer<typeof schemas.CompetitionEntrySchema>;
export type CompetitionResponse = z.infer<typeof schemas.CompetitionResponseSchema>;
export type HistoryEntry = z.infer<typeof schemas.HistoryEntrySchema>;
export type PipelineStatus = z.infer<typeof schemas.PipelineStatusSchema>;
export type Provider3D = z.infer<typeof schemas.Provider3DSchema>;
export type Job3D = z.infer<typeof schemas.Job3DSchema>;
export type HealthResponse = z.infer<typeof schemas.HealthResponseSchema>;
export type Asset = z.infer<typeof schemas.AssetSchema>;
export type AssetListResponse = z.infer<typeof schemas.AssetListResponseSchema>;
export type QAReview = z.infer<typeof schemas.QAReviewSchema>;
export type QAReviewListResponse = z.infer<typeof schemas.QAReviewListResponseSchema>;
export type BatchJob = z.infer<typeof schemas.BatchJobSchema>;
export type Settings = z.infer<typeof schemas.SettingsSchema>;
export type Task = z.infer<typeof schemas.TaskSchema>;
export type TaskMetrics = z.infer<typeof schemas.TaskMetricsSchema>;
export type AgentInfo = z.infer<typeof schemas.AgentInfoSchema>;
export type AgentListResponse = z.infer<typeof schemas.AgentListResponseSchema>;
export type ServiceHealthStatus = z.infer<typeof schemas.ServiceHealthStatusSchema>;
export type SystemStats = z.infer<typeof schemas.SystemStatsSchema>;
export type HealthEvent = z.infer<typeof schemas.HealthEventSchema>;
export type MonitoringHealthResponse = z.infer<typeof schemas.MonitoringHealthResponseSchema>;
export type MetricDataPoint = z.infer<typeof schemas.MetricDataPointSchema>;
export type MetricSeries = z.infer<typeof schemas.MetricSeriesSchema>;
export type MonitoringMetricsResponse = z.infer<typeof schemas.MonitoringMetricsResponseSchema>;



// Request Interfaces
export interface CompetitionRequest {
    prompt: string;
    providers?: string[];
    evaluation_criteria?: string[];
}

export interface TextTo3DRequest {
    prompt: string;
    provider?: string;
    quality?: 'draft' | 'standard' | 'high';
}

export interface ImageTo3DRequest {
    image_url: string;
    provider?: string;
    quality?: 'draft' | 'standard' | 'high';
}

export interface AssetFilters {
    collection?: 'black_rose' | 'signature' | 'love_hurts' | 'showroom' | 'runway';
    type?: 'image' | '3d_model' | 'video' | 'texture';
    search?: string;
    page?: number;
    limit?: number;
}

export interface AssetUpdateRequest {
    metadata?: {
        sku?: string;
        product_name?: string;
        tags?: string[];
    };
}

export interface BatchGenerationRequest {
    asset_ids: string[];
    provider?: string;
    quality?: 'draft' | 'standard' | 'high';
}

export interface QAReviewRequest {
    status: 'approved' | 'rejected';
    notes?: string;
}

export interface RegenerateRequest {
    provider?: string;
    quality?: 'draft' | 'standard' | 'high';
    adjustments?: {
        geometry?: number;
        materials?: number;
        lighting?: number;
    };
}

export type AutonomousOperation = z.infer<typeof schemas.AutonomousOperationSchema>;
export type AutonomousHistoryEntry = z.infer<typeof schemas.AutonomousHistoryEntrySchema>;
export type AutonomousOperationsResponse = z.infer<typeof schemas.AutonomousOperationsResponseSchema>;

export type SkuImageCounts = z.infer<typeof schemas.SkuImageCountsSchema>;
export type HfDatasetInfo = z.infer<typeof schemas.HfDatasetInfoSchema>;
export type HfDatasetsResponse = z.infer<typeof schemas.HfDatasetsResponseSchema>;
export type TrainingProgress = z.infer<typeof schemas.TrainingProgressSchema>;
export type TrainingJobInfo = z.infer<typeof schemas.TrainingJobInfoSchema>;
export type TrainingJobsList = z.infer<typeof schemas.TrainingJobsListSchema>;

// Catalog types
export type CatalogMatchResponse = z.infer<typeof schemas.CatalogMatchResponseSchema>;
export type CatalogSearchResponse = z.infer<typeof schemas.CatalogSearchResponseSchema>;
export type CatalogSimilarResponse = z.infer<typeof schemas.CatalogSimilarResponseSchema>;

export interface CatalogSearchRequest {
    q: string;
    top_k?: number;
    collection?: string;
}

// Brand Assets types
export type BrandAssetCategory = z.infer<typeof schemas.BrandAssetCategorySchema>;
export type AssetApprovalStatus = z.infer<typeof schemas.AssetApprovalStatusSchema>;
export type IngestionJobStatus = z.infer<typeof schemas.IngestionJobStatusSchema>;
export type TrainingReadinessStatus = z.infer<typeof schemas.TrainingReadinessStatusSchema>;
export type BrandAsset = z.infer<typeof schemas.BrandAssetSchema>;
export type BrandAssetsListResponse = z.infer<typeof schemas.BrandAssetsListResponseSchema>;
export type CategoryStats = z.infer<typeof schemas.CategoryStatsSchema>;
export type TrainingReadinessResponse = z.infer<typeof schemas.TrainingReadinessResponseSchema>;
export type BulkIngestionJob = z.infer<typeof schemas.BulkIngestionJobSchema>;

export interface BrandAssetUploadInput {
    url: string;
    category: BrandAssetCategory;
    metadata?: {
        campaign?: string;
        season?: string;
        photographer?: string;
        location?: string;
        tags?: string[];
        notes?: string;
    };
}

export interface BulkIngestionRequest {
    assets: BrandAssetUploadInput[];
    campaign_name?: string;
    auto_approve?: boolean;
    extract_features?: boolean;
}

export interface BrandAssetListFilters {
    category?: BrandAssetCategory;
    approvalStatus?: AssetApprovalStatus;
    campaign?: string;
    page?: number;
    pageSize?: number;
}

// Asset Ingestion + Job Tracking types (distinct from the Asset gallery CRUD types above)
export type AssetIngestResponse = z.infer<typeof schemas.AssetIngestResponseSchema>;
export type AssetProcessingStage = z.infer<typeof schemas.AssetProcessingStageSchema>;
export type AssetJobResponse = z.infer<typeof schemas.AssetJobResponseSchema>;

export interface AssetIngestOptions {
    source?: 'api' | 'woocommerce' | 'dashboard';
    productId?: string;
    processingProfile?: 'full' | 'quick' | 'background_only' | 'reformat';
    callbackUrl?: string;
}

// Competitor Analysis types
export type CompetitorCategory = z.infer<typeof schemas.CompetitorCategorySchema>;
export type PricePositioning = z.infer<typeof schemas.PricePositioningSchema>;
export type CompositionType = z.infer<typeof schemas.CompositionTypeSchema>;
export type StyleCategory = z.infer<typeof schemas.StyleCategorySchema>;
export type Competitor = z.infer<typeof schemas.CompetitorSchema>;
export type CompetitorListResponse = z.infer<typeof schemas.CompetitorListResponseSchema>;
export type CompetitorAsset = z.infer<typeof schemas.CompetitorAssetSchema>;
export type CompetitorAssetListResponse = z.infer<typeof schemas.CompetitorAssetListResponseSchema>;
export type StyleAnalyticsResponse = z.infer<typeof schemas.StyleAnalyticsResponseSchema>;
export type CompetitorAnalyticsSummary = z.infer<typeof schemas.CompetitorAnalyticsSummarySchema>;

export interface CompetitorCreateRequest {
    name: string;
    category?: CompetitorCategory;
    price_positioning?: PricePositioning;
    website?: string;
    notes?: string;
}

export interface CompetitorAssetListFilters {
    competitorId?: string;
    competitorCategory?: CompetitorCategory;
    pricePositioning?: PricePositioning;
    page?: number;
    pageSize?: number;
}

// Dynamic Pricing types
export type PriceOptimization = z.infer<typeof schemas.PriceOptimizationSchema>;
export type DynamicPricingResponse = z.infer<typeof schemas.DynamicPricingResponseSchema>;

export interface DynamicPricingRequest {
    product_ids: string[];
    strategy?: 'competitive' | 'demand_based' | 'ml_optimized' | 'time_based';
    constraints?: Record<string, unknown>;
}
