---
name: clickhouse-io
description: ClickHouse database patterns for high-performance analytics.
---

# ClickHouse Analytics Patterns

## Table Engines
- **MergeTree**: Standard OLAP, partitioned by time
- **ReplacingMergeTree**: Deduplication
- **AggregatingMergeTree**: Pre-aggregated metrics

## Query Optimization
```sql
-- Filter on indexed columns first
WHERE date >= '2025-01-01' AND market_id = 'x'

-- Use ClickHouse-specific functions
uniq(), quantile(), toStartOfHour()
```

## Data Insertion
- **Batch inserts** (recommended): 1000+ rows per insert
- **Never** single-row inserts in loops
- Use **materialized views** for real-time aggregations

## Performance Monitoring
```sql
SELECT query, query_duration_ms FROM system.query_log
WHERE query_duration_ms > 1000
ORDER BY query_duration_ms DESC LIMIT 10;
```

## Related Tools
- **MCP**: `analytics_query` for ClickHouse queries
- **Skill**: `backend-patterns` for ETL pipelines
- **Agent**: `architect` for schema design
