"""
Comprehensive tests for infrastructure/elasticsearch_manager.py

WHY: Ensure Elasticsearch search and analytics work correctly with ≥70% coverage
HOW: Test all search operations, index management, ILM policies, and fashion-specific features
IMPACT: Validates enterprise search infrastructure reliability

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥70%
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from elasticsearch.exceptions import ApiError, NotFoundError, RequestError

# Alias for compatibility
ElasticsearchException = ApiError

from infrastructure.elasticsearch_manager import ElasticsearchManager, SearchMetrics


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client for testing."""
    client = MagicMock()

    # Mock async methods
    client.info = AsyncMock(return_value={"version": {"number": "8.0.0"}})
    client.close = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.indices = MagicMock()
    client.indices.exists = AsyncMock(return_value=False)
    client.indices.create = AsyncMock(return_value={"acknowledged": True})
    client.indices.stats = AsyncMock(return_value={})
    client.ilm = MagicMock()
    client.ilm.get_lifecycle = AsyncMock(side_effect=NotFoundError())
    client.ilm.put_lifecycle = AsyncMock(return_value={"acknowledged": True})
    client.cluster = MagicMock()
    client.cluster.health = AsyncMock(
        return_value={
            "status": "green",
            "number_of_nodes": 3,
            "active_shards": 10,
        }
    )
    client.index = AsyncMock(return_value={"_id": "doc123", "result": "created"})
    client.search = AsyncMock(
        return_value={
            "hits": {
                "hits": [{"_id": "1", "_source": {"name": "test"}}],
                "total": {"value": 1},
                "max_score": 1.0,
            },
            "took": 10,
        }
    )

    return client


@pytest.fixture
async def es_manager(mock_es_client):
    """Create ElasticsearchManager instance with mocked client."""
    with patch("infrastructure.elasticsearch_manager.AsyncElasticsearch", return_value=mock_es_client):
        manager = ElasticsearchManager(
            hosts=["localhost:9200"],
            username="elastic",
            password="password",
            use_ssl=True,
            verify_certs=True,
        )
        await manager.connect()
        yield manager
        await manager.disconnect()


# ============================================================================
# TEST SearchMetrics
# ============================================================================


class TestSearchMetrics:
    """Test SearchMetrics dataclass."""

    def test_search_metrics_initialization(self):
        """Test SearchMetrics initialization with default values."""
        metrics = SearchMetrics()

        assert metrics.total_queries == 0
        assert metrics.successful_queries == 0
        assert metrics.failed_queries == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.total_response_time == 0.0
        assert metrics.last_updated is None

    def test_success_rate_zero_queries(self):
        """Test success_rate returns 0.0 when no queries."""
        metrics = SearchMetrics()
        assert metrics.success_rate == 0.0

    def test_success_rate_calculation(self):
        """Test success_rate calculates correctly."""
        metrics = SearchMetrics(total_queries=100, successful_queries=80, failed_queries=20)
        assert metrics.success_rate == 0.8

    def test_success_rate_all_successful(self):
        """Test success_rate when all queries succeed."""
        metrics = SearchMetrics(total_queries=50, successful_queries=50)
        assert metrics.success_rate == 1.0

    def test_to_dict(self):
        """Test SearchMetrics.to_dict() converts to dictionary."""
        timestamp = datetime(2025, 11, 23, 12, 0, 0)
        metrics = SearchMetrics(
            total_queries=100,
            successful_queries=90,
            failed_queries=10,
            avg_response_time=250.5,
            total_response_time=25050.0,
            last_updated=timestamp,
        )

        result = metrics.to_dict()

        assert result["total_queries"] == 100
        assert result["successful_queries"] == 90
        assert result["failed_queries"] == 10
        assert result["success_rate"] == 0.9
        assert result["avg_response_time"] == 250.5
        assert result["last_updated"] == "2025-11-23T12:00:00"

    def test_to_dict_no_timestamp(self):
        """Test to_dict() with None timestamp."""
        metrics = SearchMetrics()
        result = metrics.to_dict()

        assert result["last_updated"] is None


# ============================================================================
# TEST ElasticsearchManager Initialization
# ============================================================================


class TestElasticsearchManagerInitialization:
    """Test ElasticsearchManager initialization."""

    def test_initialization_default_params(self):
        """Test manager initializes with default parameters."""
        manager = ElasticsearchManager()

        assert manager.hosts == ["localhost:9200"]
        assert manager.username is None
        assert manager.password is None
        assert manager.is_connected is False
        assert isinstance(manager.metrics, SearchMetrics)

    def test_initialization_custom_params(self):
        """Test manager initializes with custom parameters."""
        manager = ElasticsearchManager(
            hosts=["es1:9200", "es2:9200"],
            username="admin",
            password="secret",
            use_ssl=True,
            verify_certs=False,
            timeout=60,
            max_retries=5,
        )

        assert manager.hosts == ["es1:9200", "es2:9200"]
        assert manager.username == "admin"
        assert manager.password == "secret"

    def test_indices_defined(self):
        """Test all required indices are defined."""
        manager = ElasticsearchManager()

        assert "logs" in manager.indices
        assert "metrics" in manager.indices
        assert "user_data" in manager.indices
        assert "fashion_trends" in manager.indices
        assert "products" in manager.indices
        assert "analytics" in manager.indices
        assert "recommendations" in manager.indices
        assert "inventory" in manager.indices
        assert "user_behavior" in manager.indices

    def test_index_mappings_defined(self):
        """Test index mappings are defined."""
        manager = ElasticsearchManager()

        mappings = manager._get_index_mappings()

        assert "logs" in mappings
        assert "fashion_trends" in mappings
        assert "products" in mappings
        assert "user_behavior" in mappings
        assert "analytics" in mappings

    def test_ilm_policies_defined(self):
        """Test ILM policies are defined."""
        manager = ElasticsearchManager()

        policies = manager._get_ilm_policies()

        assert "logs_policy" in policies
        assert "analytics_policy" in policies
        assert "fashion_trends_policy" in policies


# ============================================================================
# TEST Connection Management
# ============================================================================


class TestConnectionManagement:
    """Test Elasticsearch connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, es_manager):
        """Test successful Elasticsearch connection."""
        assert es_manager.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_es_client):
        """Test connection failure handling."""
        mock_es_client.info = AsyncMock(side_effect=ElasticsearchException("Connection failed"))

        with patch("infrastructure.elasticsearch_manager.AsyncElasticsearch", return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = await manager.connect()

            assert result is False
            assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, es_manager):
        """Test disconnection."""
        await es_manager.disconnect()

        assert es_manager.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_with_error(self, es_manager):
        """Test disconnect handles errors gracefully."""
        es_manager.client.close = AsyncMock(side_effect=Exception("Close error"))

        # Should not raise exception
        await es_manager.disconnect()


# ============================================================================
# TEST Index Management
# ============================================================================


class TestIndexManagement:
    """Test index initialization and management."""

    @pytest.mark.asyncio
    async def test_initialize_indices_creates_new(self, es_manager, mock_es_client):
        """Test initializing non-existent indices."""
        mock_es_client.indices.exists = AsyncMock(return_value=False)

        await es_manager._initialize_indices()

        # Should have called create for each index
        assert mock_es_client.indices.create.called

    @pytest.mark.asyncio
    async def test_initialize_indices_skips_existing(self, es_manager, mock_es_client):
        """Test initialization skips existing indices."""
        mock_es_client.indices.exists = AsyncMock(return_value=True)
        mock_es_client.indices.create = AsyncMock()

        await es_manager._initialize_indices()

        # Should not create already existing indices
        assert not mock_es_client.indices.create.called

    @pytest.mark.asyncio
    async def test_initialize_indices_handles_errors(self, es_manager, mock_es_client):
        """Test index initialization handles errors gracefully."""
        mock_es_client.indices.exists = AsyncMock(return_value=False)
        mock_es_client.indices.create = AsyncMock(side_effect=RequestError("Create failed"))

        # Should not raise exception
        await es_manager._initialize_indices()


# ============================================================================
# TEST ILM Policy Management
# ============================================================================


class TestILMPolicyManagement:
    """Test Index Lifecycle Management policy setup."""

    @pytest.mark.asyncio
    async def test_setup_ilm_policies_creates_new(self, es_manager, mock_es_client):
        """Test creating new ILM policies."""
        mock_es_client.ilm.get_lifecycle = AsyncMock(side_effect=NotFoundError())

        await es_manager._setup_ilm_policies()

        # Should have called put_lifecycle for each policy
        assert mock_es_client.ilm.put_lifecycle.called

    @pytest.mark.asyncio
    async def test_setup_ilm_policies_skips_existing(self, es_manager, mock_es_client):
        """Test setup skips existing ILM policies."""
        mock_es_client.ilm.get_lifecycle = AsyncMock(return_value={"policy": {}})
        mock_es_client.ilm.put_lifecycle = AsyncMock()

        await es_manager._setup_ilm_policies()

        # Should not create already existing policies
        assert not mock_es_client.ilm.put_lifecycle.called

    @pytest.mark.asyncio
    async def test_setup_ilm_policies_handles_errors(self, es_manager, mock_es_client):
        """Test ILM policy setup handles errors gracefully."""
        mock_es_client.ilm.get_lifecycle = AsyncMock(side_effect=NotFoundError())
        mock_es_client.ilm.put_lifecycle = AsyncMock(side_effect=RequestError("Policy creation failed"))

        # Should not raise exception
        await es_manager._setup_ilm_policies()


# ============================================================================
# TEST Metrics Recording
# ============================================================================


class TestMetricsRecording:
    """Test search metrics recording."""

    @pytest.mark.asyncio
    async def test_record_metrics_successful(self, es_manager):
        """Test recording successful query metrics."""
        initial_successful = es_manager.metrics.successful_queries

        await es_manager._record_metrics(150.5, success=True)

        assert es_manager.metrics.successful_queries == initial_successful + 1
        assert es_manager.metrics.total_queries > 0
        assert es_manager.metrics.avg_response_time > 0

    @pytest.mark.asyncio
    async def test_record_metrics_failed(self, es_manager):
        """Test recording failed query metrics."""
        initial_failed = es_manager.metrics.failed_queries

        await es_manager._record_metrics(200.0, success=False)

        assert es_manager.metrics.failed_queries == initial_failed + 1

    @pytest.mark.asyncio
    async def test_record_metrics_average_calculation(self, es_manager):
        """Test average response time calculation."""
        await es_manager._record_metrics(100.0, success=True)
        await es_manager._record_metrics(200.0, success=True)

        assert es_manager.metrics.avg_response_time == 150.0


# ============================================================================
# TEST Document Indexing
# ============================================================================


class TestDocumentIndexing:
    """Test document indexing operations."""

    @pytest.mark.asyncio
    async def test_index_document_success(self, es_manager, mock_es_client):
        """Test successful document indexing."""
        document = {
            "message": "Test log message",
            "level": "INFO",
        }

        result = await es_manager.index_document("logs", document)

        assert result is True
        assert mock_es_client.index.called

    @pytest.mark.asyncio
    async def test_index_document_with_id(self, es_manager, mock_es_client):
        """Test indexing document with specific ID."""
        document = {"trend_id": "trend123", "name": "Summer Styles"}

        result = await es_manager.index_document("fashion_trends", document, doc_id="trend123")

        assert result is True
        mock_es_client.index.assert_called_once()
        call_kwargs = mock_es_client.index.call_args[1]
        assert call_kwargs["id"] == "trend123"

    @pytest.mark.asyncio
    async def test_index_document_adds_timestamp(self, es_manager, mock_es_client):
        """Test indexing adds timestamp if not present."""
        document = {"message": "Test"}

        await es_manager.index_document("logs", document)

        # Check that timestamp was added
        call_kwargs = mock_es_client.index.call_args[1]
        indexed_doc = call_kwargs["body"]
        assert "timestamp" in indexed_doc

    @pytest.mark.asyncio
    async def test_index_document_preserves_timestamp(self, es_manager, mock_es_client):
        """Test indexing preserves existing timestamp."""
        timestamp = "2025-11-23T10:00:00"
        document = {"message": "Test", "timestamp": timestamp}

        await es_manager.index_document("logs", document)

        call_kwargs = mock_es_client.index.call_args[1]
        indexed_doc = call_kwargs["body"]
        assert indexed_doc["timestamp"] == timestamp

    @pytest.mark.asyncio
    async def test_index_document_invalid_index(self, es_manager):
        """Test indexing with invalid index type."""
        with pytest.raises(ValueError, match="Unknown index type"):
            await es_manager.index_document("nonexistent", {"data": "test"})

    @pytest.mark.asyncio
    async def test_index_document_error_handling(self, es_manager, mock_es_client):
        """Test document indexing handles errors gracefully."""
        mock_es_client.index = AsyncMock(side_effect=ElasticsearchException("Index error"))

        result = await es_manager.index_document("logs", {"message": "test"})

        assert result is False


# ============================================================================
# TEST Search Operations
# ============================================================================


class TestSearchOperations:
    """Test search query operations."""

    @pytest.mark.asyncio
    async def test_search_success(self, es_manager, mock_es_client):
        """Test successful search query."""
        query = {"match": {"message": "error"}}

        result = await es_manager.search("logs", query)

        assert "hits" in result
        assert "total" in result
        assert "max_score" in result
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, es_manager, mock_es_client):
        """Test search with pagination."""
        query = {"match_all": {}}

        await es_manager.search("logs", query, size=20, from_=10)

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        assert search_body["size"] == 20
        assert search_body["from"] == 10

    @pytest.mark.asyncio
    async def test_search_with_sorting(self, es_manager, mock_es_client):
        """Test search with sorting."""
        query = {"match_all": {}}
        sort = [{"timestamp": {"order": "desc"}}]

        await es_manager.search("logs", query, sort=sort)

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        assert "sort" in search_body
        assert search_body["sort"] == sort

    @pytest.mark.asyncio
    async def test_search_invalid_index(self, es_manager):
        """Test search with invalid index type."""
        with pytest.raises(ValueError, match="Unknown index type"):
            await es_manager.search("nonexistent", {"match_all": {}})

    @pytest.mark.asyncio
    async def test_search_error_handling(self, es_manager, mock_es_client):
        """Test search handles errors gracefully."""
        mock_es_client.search = AsyncMock(side_effect=ElasticsearchException("Search error"))

        result = await es_manager.search("logs", {"match_all": {}})

        assert "error" in result
        assert result["total"] == 0
        assert len(result["hits"]) == 0

    @pytest.mark.asyncio
    async def test_search_slow_query_warning(self, es_manager, mock_es_client, caplog):
        """Test warning logged for slow queries."""
        # Mock slow response
        with patch("time.time", side_effect=[0, 2.5]):  # 2.5 seconds elapsed
            await es_manager.search("logs", {"match_all": {}})

        # Check if warning was logged
        assert any("exceeded target response time" in record.message for record in caplog.records)


# ============================================================================
# TEST Full-Text Search
# ============================================================================


class TestFullTextSearch:
    """Test full-text search with relevance scoring."""

    @pytest.mark.asyncio
    async def test_full_text_search_default_fields(self, es_manager, mock_es_client):
        """Test full-text search with default fields."""
        result = await es_manager.full_text_search("fashion_trends", "summer dresses")

        assert "hits" in result
        mock_es_client.search.assert_called_once()

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        assert "query" in search_body
        assert "bool" in search_body["query"]

    @pytest.mark.asyncio
    async def test_full_text_search_custom_fields(self, es_manager, mock_es_client):
        """Test full-text search with custom fields."""
        fields = ["title^3", "description^2"]

        await es_manager.full_text_search("products", "vintage style", fields=fields)

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        multi_match = search_body["query"]["bool"]["should"][0]["multi_match"]
        assert multi_match["fields"] == fields

    @pytest.mark.asyncio
    async def test_full_text_search_with_min_score(self, es_manager, mock_es_client):
        """Test full-text search with minimum score filter."""
        await es_manager.full_text_search("products", "designer bags", min_score=0.5)

        # Query should include min_score filter
        mock_es_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_text_search_products_fields(self, es_manager, mock_es_client):
        """Test full-text search uses correct default fields for products."""
        await es_manager.full_text_search("products", "leather jacket")

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        multi_match = search_body["query"]["bool"]["should"][0]["multi_match"]

        # Should include product-specific fields
        assert "name^3" in multi_match["fields"]
        assert "description^2" in multi_match["fields"]
        assert "brand^2" in multi_match["fields"]


# ============================================================================
# TEST Fashion-Specific Search
# ============================================================================


class TestFashionTrendSearch:
    """Test fashion industry specific trend search."""

    @pytest.mark.asyncio
    async def test_fashion_trend_search_basic(self, es_manager, mock_es_client):
        """Test basic fashion trend search."""
        result = await es_manager.fashion_trend_search("sustainable fashion")

        assert "hits" in result
        mock_es_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_fashion_trend_search_with_season(self, es_manager, mock_es_client):
        """Test fashion trend search filtered by season."""
        await es_manager.fashion_trend_search("dresses", season="summer")

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        filters = search_body["query"]["bool"]["filter"]

        # Should include season filter
        assert any(f.get("term", {}).get("season") == "summer" for f in filters)

    @pytest.mark.asyncio
    async def test_fashion_trend_search_with_category(self, es_manager, mock_es_client):
        """Test fashion trend search filtered by category."""
        await es_manager.fashion_trend_search("casual", category="apparel")

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        filters = search_body["query"]["bool"]["filter"]

        # Should include category filter
        assert any(f.get("term", {}).get("category") == "apparel" for f in filters)

    @pytest.mark.asyncio
    async def test_fashion_trend_search_with_year(self, es_manager, mock_es_client):
        """Test fashion trend search filtered by year."""
        await es_manager.fashion_trend_search("trends", year=2025)

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        filters = search_body["query"]["bool"]["filter"]

        # Should include year filter
        assert any(f.get("term", {}).get("year") == 2025 for f in filters)

    @pytest.mark.asyncio
    async def test_fashion_trend_search_with_min_popularity(self, es_manager, mock_es_client):
        """Test fashion trend search filtered by minimum popularity."""
        await es_manager.fashion_trend_search("trending", min_popularity=0.8)

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        filters = search_body["query"]["bool"]["filter"]

        # Should include popularity filter
        assert any("range" in f and "popularity_score" in f.get("range", {}) for f in filters)

    @pytest.mark.asyncio
    async def test_fashion_trend_search_sorting(self, es_manager, mock_es_client):
        """Test fashion trend search is sorted by popularity and score."""
        await es_manager.fashion_trend_search("fashion")

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        sort = search_body.get("sort", [])

        # Should sort by popularity first, then score
        assert len(sort) == 2


# ============================================================================
# TEST Analytics Data
# ============================================================================


class TestAnalyticsData:
    """Test analytics data retrieval with aggregations."""

    @pytest.mark.asyncio
    async def test_get_analytics_data_basic(self, es_manager, mock_es_client):
        """Test basic analytics data retrieval."""
        mock_es_client.search = AsyncMock(
            return_value={
                "aggregations": {
                    "time_series": {
                        "buckets": [
                            {"key_as_string": "2025-11-23T10:00:00", "metric_value": {"value": 100.5}},
                            {"key_as_string": "2025-11-23T11:00:00", "metric_value": {"value": 105.2}},
                        ]
                    }
                }
            }
        )

        start_date = datetime(2025, 11, 23, 0, 0, 0)
        end_date = datetime(2025, 11, 23, 23, 59, 59)

        result = await es_manager.get_analytics_data("page_views", start_date, end_date)

        assert result["metric_name"] == "page_views"
        assert result["aggregation"] == "avg"
        assert result["interval"] == "1h"
        assert len(result["data_points"]) == 2

    @pytest.mark.asyncio
    async def test_get_analytics_data_custom_aggregation(self, es_manager, mock_es_client):
        """Test analytics with custom aggregation."""
        mock_es_client.search = AsyncMock(
            return_value={"aggregations": {"time_series": {"buckets": []}}}
        )

        start_date = datetime(2025, 11, 23, 0, 0, 0)
        end_date = datetime(2025, 11, 23, 23, 59, 59)

        await es_manager.get_analytics_data("sales", start_date, end_date, aggregation="sum")

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        aggs = search_body["aggs"]["time_series"]["aggs"]

        assert "sum" in list(aggs["metric_value"].keys())[0]

    @pytest.mark.asyncio
    async def test_get_analytics_data_custom_interval(self, es_manager, mock_es_client):
        """Test analytics with custom time interval."""
        mock_es_client.search = AsyncMock(
            return_value={"aggregations": {"time_series": {"buckets": []}}}
        )

        start_date = datetime(2025, 11, 23, 0, 0, 0)
        end_date = datetime(2025, 11, 23, 23, 59, 59)

        await es_manager.get_analytics_data("traffic", start_date, end_date, interval="5m")

        call_kwargs = mock_es_client.search.call_args[1]
        search_body = call_kwargs["body"]
        histogram = search_body["aggs"]["time_series"]

        assert histogram["date_histogram"]["fixed_interval"] == "5m"

    @pytest.mark.asyncio
    async def test_get_analytics_data_error_handling(self, es_manager, mock_es_client):
        """Test analytics data handles errors gracefully."""
        mock_es_client.search = AsyncMock(side_effect=ElasticsearchException("Query error"))

        start_date = datetime(2025, 11, 23, 0, 0, 0)
        end_date = datetime(2025, 11, 23, 23, 59, 59)

        result = await es_manager.get_analytics_data("metric", start_date, end_date)

        assert "error" in result


# ============================================================================
# TEST Metrics and Health Check
# ============================================================================


class TestMetricsAndHealthCheck:
    """Test metrics and health check operations."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, es_manager, mock_es_client):
        """Test getting search and cluster metrics."""
        metrics = await es_manager.get_metrics()

        assert "search_metrics" in metrics
        assert "cluster_health" in metrics
        assert "indices_stats" in metrics
        assert "is_connected" in metrics
        assert "configured_indices" in metrics

    @pytest.mark.asyncio
    async def test_get_metrics_error_handling(self, es_manager, mock_es_client):
        """Test metrics handles errors gracefully."""
        mock_es_client.cluster.health = AsyncMock(side_effect=ElasticsearchException("Health error"))

        metrics = await es_manager.get_metrics()

        assert "search_metrics" in metrics
        assert metrics["cluster_health"] is None

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, es_manager, mock_es_client):
        """Test health check returns healthy status."""
        result = await es_manager.health_check()

        assert result["status"] == "healthy"
        assert result["cluster_status"] == "green"
        assert "number_of_nodes" in result
        assert "active_shards" in result
        assert "response_time_ms" in result
        assert "meets_target" in result

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, es_manager, mock_es_client):
        """Test health check returns unhealthy status on error."""
        mock_es_client.cluster.health = AsyncMock(side_effect=ElasticsearchException("Cluster down"))

        result = await es_manager.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_health_check_meets_target(self, es_manager, mock_es_client):
        """Test health check evaluates if response time meets target."""
        result = await es_manager.health_check()

        assert "meets_target" in result
        assert isinstance(result["meets_target"], bool)
        # Target is <2000ms
        assert result["meets_target"] == (result["response_time_ms"] < 2000)


# ============================================================================
# TEST Global Instance
# ============================================================================


def test_global_elasticsearch_manager():
    """Test global elasticsearch_manager instance exists."""
    from infrastructure.elasticsearch_manager import elasticsearch_manager

    assert elasticsearch_manager is not None
    assert isinstance(elasticsearch_manager, ElasticsearchManager)
    assert len(elasticsearch_manager.indices) > 0
