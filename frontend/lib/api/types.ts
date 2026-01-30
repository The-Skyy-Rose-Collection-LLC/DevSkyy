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
