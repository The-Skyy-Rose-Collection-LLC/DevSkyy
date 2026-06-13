# services/competitive/ — Competitor Asset Analysis

**Brand intelligence over competitor product imagery.** Extracts style + composition + pricing attributes for the admin dashboard.

## Public Surface (`services/competitive/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Service | `CompetitorAnalysisService` | `competitor_analysis.py` |
| Competitor entities | `Competitor`, `CompetitorCreate`, `CompetitorCategory`, `CompetitorListResponse` | `schemas.py` |
| Asset entities | `CompetitorAsset`, `CompetitorAssetCreate`, `CompetitorAssetUpdate`, `CompetitorAssetFilter`, `CompetitorAssetListResponse` | `schemas.py` |
| Extracted attributes | `ExtractedAttributes`, `StyleAttributes` (via re-export), `CompositionType`, `CompositionDistribution`, `StyleCategory`, `StyleDistribution`, `StyleAnalyticsResponse` | `schemas.py` |
| Pricing | `PriceAnalytics`, `PricePositioning` | `schemas.py` |

## Hard Rules

- This module is **read-only for competitor data** from DevSkyy's perspective — never write back to a competitor's site, never scrape behind auth walls
- Attribute extraction uses vision models (`services/ml/visual_feature_extractor.py`) — paid API call. Gate behind admin auth + rate limiter
- `CompetitorAsset` URLs must be public — never store auth tokens for competitor sites
- All Pydantic schemas in `schemas.py` are validation contracts at the API boundary — do not mutate after construction
- Pricing analysis is descriptive, not predictive — `PricePositioning` is bucket-based (`luxury` / `premium` / `mass`), do not use for dynamic pricing

## Consumers

- `api/v1/analytics/competitive/*` — admin dashboard surface
- `services/ml/visual_feature_extractor.py` — vision extraction backend
- `agents/core/marketing/*` — strategic insights from competitor distribution data


