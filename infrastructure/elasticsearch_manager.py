from dataclasses import dataclass
from datetime import datetime
import logging
import time
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ApiError as ElasticsearchException, NotFoundError, RequestError


"""
Enterprise Elasticsearch Manager - Search & Analytics Engine
Implements full-text search, real-time analytics, and fashion industry specific indexing
Target: <2-second query response times with relevance scoring
"""

logger = logging.getLogger(__name__)


@dataclass
class SearchMetrics:
    """Search performance metrics"""

    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    last_updated: datetime = None

    @property
    def success_rate(self) -> float:
        """Calculate query success rate"""
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "last_updated": (self.last_updated.isoformat() if self.last_updated else None),
        }


class ElasticsearchManager:
    """Enterprise Elasticsearch manager with fashion industry optimization"""

    def __init__(
        self,
        hosts: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
        use_ssl: bool = True,
        verify_certs: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        retry_on_timeout: bool = True,
    ):
        self.hosts = hosts or ["http://localhost:9200"]
        self.username = username
        self.password = password

        # Initialize Elasticsearch client
        client_config = {
            "hosts": self.hosts,
            "request_timeout": timeout,
        }

        if username and password:
            client_config["basic_auth"] = (username, password)

        if use_ssl:
            client_config["verify_certs"] = verify_certs

        self.client = AsyncElasticsearch(**client_config)
        self.metrics = SearchMetrics()
        self.is_connected = False

        # Fashion industry specific indices
        self.indices = {
            "logs": "devskyy-logs",
            "metrics": "devskyy-metrics",
            "user_data": "devskyy-users",
            "fashion_trends": "devskyy-fashion-trends",
            "products": "devskyy-products",
            "analytics": "devskyy-analytics",
            "recommendations": "devskyy-recommendations",
            "inventory": "devskyy-inventory",
            "user_behavior": "devskyy-user-behavior",
        }

        # Index mappings for fashion e-commerce
        self.index_mappings = self._get_index_mappings()

        # ILM policies for automated index lifecycle management
        self.ilm_policies = self._get_ilm_policies()

        logger.info(f"Elasticsearch manager initialized - Hosts: {self.hosts}")

    def _get_index_mappings(self) -> dict[str, dict]:
        """Get index mappings for fashion e-commerce"""
        return {
            "logs": {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "logger": {"type": "keyword"},
                        "message": {"type": "text", "analyzer": "standard"},
                        "correlation_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "endpoint": {"type": "keyword"},
                        "method": {"type": "keyword"},
                        "status_code": {"type": "integer"},
                        "response_time": {"type": "float"},
                        "error_details": {"type": "object"},
                        "fashion_context": {"type": "object"},
                    }
                }
            },
            "fashion_trends": {
                "mappings": {
                    "properties": {
                        "trend_id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "category": {"type": "keyword"},
                        "subcategory": {"type": "keyword"},
                        "season": {"type": "keyword"},
                        "year": {"type": "integer"},
                        "popularity_score": {"type": "float"},
                        "color_palette": {"type": "keyword"},
                        "materials": {"type": "keyword"},
                        "target_demographic": {"type": "keyword"},
                        "price_range": {"type": "keyword"},
                        "sustainability_score": {"type": "float"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "tags": {"type": "keyword"},
                        "location": {"type": "geo_point"},
                        "social_mentions": {"type": "integer"},
                        "influencer_endorsements": {"type": "keyword"},
                    }
                }
            },
            "products": {
                "mappings": {
                    "properties": {
                        "product_id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "brand": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "subcategory": {"type": "keyword"},
                        "price": {"type": "float"},
                        "currency": {"type": "keyword"},
                        "sizes": {"type": "keyword"},
                        "colors": {"type": "keyword"},
                        "materials": {"type": "keyword"},
                        "care_instructions": {"type": "text"},
                        "sustainability_rating": {"type": "float"},
                        "availability": {"type": "boolean"},
                        "stock_quantity": {"type": "integer"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "tags": {"type": "keyword"},
                        "fashion_trends": {"type": "keyword"},
                        "seasonal_relevance": {"type": "keyword"},
                        "target_audience": {"type": "keyword"},
                        "image_urls": {"type": "keyword"},
                        "reviews_count": {"type": "integer"},
                        "average_rating": {"type": "float"},
                    }
                }
            },
            "user_behavior": {
                "mappings": {
                    "properties": {
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "action": {"type": "keyword"},
                        "page": {"type": "keyword"},
                        "product_id": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "search_query": {"type": "text", "analyzer": "standard"},
                        "filters_applied": {"type": "object"},
                        "time_spent": {"type": "integer"},
                        "device_type": {"type": "keyword"},
                        "location": {"type": "geo_point"},
                        "referrer": {"type": "keyword"},
                        "conversion_event": {"type": "boolean"},
                        "fashion_preferences": {"type": "object"},
                        "seasonal_context": {"type": "keyword"},
                    }
                }
            },
            "analytics": {
                "mappings": {
                    "properties": {
                        "metric_name": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "value": {"type": "float"},
                        "dimensions": {"type": "object"},
                        "category": {"type": "keyword"},
                        "subcategory": {"type": "keyword"},
                        "user_segment": {"type": "keyword"},
                        "fashion_context": {"type": "object"},
                        "seasonal_factor": {"type": "float"},
                        "trend_correlation": {"type": "float"},
                        "business_impact": {"type": "keyword"},
                        "data_source": {"type": "keyword"},
                    }
                }
            },
        }

    def _get_ilm_policies(self) -> dict[str, dict]:
        """Get Index Lifecycle Management policies"""
        return {
            "logs_policy": {
                "policy": {
                    "phases": {
                        "hot": {
                            "actions": {
                                "rollover": {"max_size": "10GB", "max_age": "7d"},
                                "set_priority": {"priority": 100},
                            }
                        },
                        "warm": {
                            "min_age": "7d",
                            "actions": {
                                "allocate": {"number_of_replicas": 0},
                                "forcemerge": {"max_num_segments": 1},
                                "set_priority": {"priority": 50},
                            },
                        },
                        "cold": {
                            "min_age": "30d",
                            "actions": {
                                "allocate": {"number_of_replicas": 0},
                                "set_priority": {"priority": 0},
                            },
                        },
                        "delete": {"min_age": "90d"},
                    }
                }
            },
            "analytics_policy": {
                "policy": {
                    "phases": {
                        "hot": {"actions": {"rollover": {"max_size": "5GB", "max_age": "1d"}}},
                        "warm": {
                            "min_age": "1d",
                            "actions": {"forcemerge": {"max_num_segments": 1}},
                        },
                        "cold": {
                            "min_age": "7d",
                            "actions": {"allocate": {"number_of_replicas": 0}},
                        },
                        "delete": {"min_age": "365d"},  # Keep analytics data for 1 year
                    }
                }
            },
            "fashion_trends_policy": {
                "policy": {
                    "phases": {
                        "hot": {"actions": {"rollover": {"max_size": "2GB", "max_age": "30d"}}},
                        "warm": {
                            "min_age": "30d",
                            "actions": {"forcemerge": {"max_num_segments": 1}},
                        },
                        "delete": {"min_age": "2y"},  # Keep fashion trends for 2 years
                    }
                }
            },
        }

    async def connect(self) -> bool:
        """Establish Elasticsearch connection and verify connectivity"""
        try:
            # Test connection
            info = await self.client.info()
            self.is_connected = True

            logger.info(f"✅ Elasticsearch connected: {info['version']['number']}")

            # Initialize indices and ILM policies
            await self._initialize_indices()
            await self._setup_ilm_policies()

            return True

        except ElasticsearchException as e:
            logger.error(f"❌ Elasticsearch connection failed: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close Elasticsearch connection"""
        try:
            await self.client.close()
            self.is_connected = False
            logger.info("Elasticsearch connection closed")
        except Exception as e:
            logger.error(f"Error closing Elasticsearch connection: {e}")

    async def _initialize_indices(self):
        """Initialize indices with proper mappings"""
        for index_name, index_config in self.index_mappings.items():
            full_index_name = self.indices[index_name]

            try:
                # Check if index exists
                exists = await self.client.indices.exists(index=full_index_name)

                if not exists:
                    # Create index with mapping
                    await self.client.indices.create(index=full_index_name, body=index_config)
                    logger.info(f"Created index: {full_index_name}")
                else:
                    logger.debug(f"Index already exists: {full_index_name}")

            except RequestError as e:
                logger.error(f"Error creating index {full_index_name}: {e}")

    async def _setup_ilm_policies(self):
        """Setup Index Lifecycle Management policies"""
        for policy_name, policy_config in self.ilm_policies.items():
            try:
                # Check if policy exists
                try:
                    await self.client.ilm.get_lifecycle(policy=policy_name)
                    logger.debug(f"ILM policy already exists: {policy_name}")
                except NotFoundError:
                    # Create policy
                    await self.client.ilm.put_lifecycle(policy=policy_name, body=policy_config)
                    logger.info(f"Created ILM policy: {policy_name}")

            except RequestError as e:
                logger.error(f"Error creating ILM policy {policy_name}: {e}")

    async def _record_metrics(self, response_time: float, success: bool):
        """Record search performance metrics"""
        self.metrics.total_queries += 1
        self.metrics.total_response_time += response_time

        if success:
            self.metrics.successful_queries += 1
        else:
            self.metrics.failed_queries += 1

        self.metrics.avg_response_time = self.metrics.total_response_time / self.metrics.total_queries
        self.metrics.last_updated = datetime.now()

    async def index_document(self, index_type: str, document: dict[str, Any], doc_id: str | None = None) -> bool:
        """Index a document"""
        start_time = time.time()

        try:
            index_name = self.indices.get(index_type)
            if not index_name:
                raise ValueError(f"Unknown index type: {index_type}")

            # Add timestamp if not present
            if "timestamp" not in document:
                document["timestamp"] = datetime.now().isoformat()

            # Index document
            response = await self.client.index(index=index_name, body=document, id=doc_id)

            response_time = (time.time() - start_time) * 1000
            await self._record_metrics(response_time, True)

            logger.debug(f"Document indexed: {index_name}/{response['_id']}")
            return True

        except ElasticsearchException as e:
            response_time = (time.time() - start_time) * 1000
            await self._record_metrics(response_time, False)
            logger.error(f"Error indexing document: {e}")
            return False

    async def search(
        self,
        index_type: str,
        query: dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Perform search query"""
        start_time = time.time()

        try:
            index_name = self.indices.get(index_type)
            if not index_name:
                raise ValueError(f"Unknown index type: {index_type}")

            search_body = {"query": query, "size": size, "from": from_}

            if sort:
                search_body["sort"] = sort

            response = await self.client.search(index=index_name, body=search_body)

            response_time = (time.time() - start_time) * 1000
            await self._record_metrics(response_time, True)

            # Check if response time meets target (<2 seconds)
            if response_time > 2000:
                logger.warning(f"Search query exceeded target response time: {response_time:.2f}ms")

            return {
                "hits": response["hits"]["hits"],
                "total": response["hits"]["total"]["value"],
                "max_score": response["hits"]["max_score"],
                "took": response["took"],
                "response_time_ms": response_time,
            }

        except ElasticsearchException as e:
            response_time = (time.time() - start_time) * 1000
            await self._record_metrics(response_time, False)
            logger.error(f"Search error: {e}")
            return {
                "hits": [],
                "total": 0,
                "max_score": 0,
                "error": str(e),
                "response_time_ms": response_time,
            }

    async def full_text_search(
        self,
        index_type: str,
        search_text: str,
        fields: list[str] | None = None,
        size: int = 10,
        min_score: float = 0.1,
    ) -> dict[str, Any]:
        """Perform full-text search with relevance scoring"""

        # Default fields for fashion e-commerce
        if not fields:
            if index_type == "fashion_trends":
                fields = ["name^3", "description^2", "category", "tags"]
            elif index_type == "products":
                fields = ["name^3", "description^2", "brand^2", "category", "tags"]
            else:
                fields = ["*"]

        query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": search_text,
                            "fields": fields,
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    },
                    {"match_phrase": {"description": {"query": search_text, "boost": 2}}},
                ],
                "minimum_should_match": 1,
            }
        }

        # Add minimum score filter
        if min_score > 0:
            query["bool"]["filter"] = {"range": {"_score": {"gte": min_score}}}

        return await self.search(
            index_type=index_type,
            query=query,
            size=size,
            sort=[{"_score": {"order": "desc"}}],
        )

    async def fashion_trend_search(
        self,
        search_text: str,
        season: str | None = None,
        category: str | None = None,
        year: int | None = None,
        min_popularity: float = 0.0,
    ) -> dict[str, Any]:
        """Fashion-specific trend search"""

        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": search_text,
                            "fields": ["name^3", "description^2", "tags^2", "category"],
                            "fuzziness": "AUTO",
                        }
                    }
                ],
                "filter": [],
            }
        }

        # Add filters
        if season:
            query["bool"]["filter"].append({"term": {"season": season}})

        if category:
            query["bool"]["filter"].append({"term": {"category": category}})

        if year:
            query["bool"]["filter"].append({"term": {"year": year}})

        if min_popularity > 0:
            query["bool"]["filter"].append({"range": {"popularity_score": {"gte": min_popularity}}})

        return await self.search(
            index_type="fashion_trends",
            query=query,
            sort=[
                {"popularity_score": {"order": "desc"}},
                {"_score": {"order": "desc"}},
            ],
        )

    async def get_analytics_data(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        aggregation: str = "avg",
        interval: str = "1h",
    ) -> dict[str, Any]:
        """Get analytics data with time-based aggregation"""

        query = {
            "bool": {
                "must": [
                    {"term": {"metric_name": metric_name}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat(),
                            }
                        }
                    },
                ]
            }
        }

        aggs = {
            "time_series": {
                "date_histogram": {"field": "timestamp", "fixed_interval": interval},
                "aggs": {"metric_value": {aggregation: {"field": "value"}}},
            }
        }

        try:
            response = await self.client.search(
                index=self.indices["analytics"],
                body={"query": query, "aggs": aggs, "size": 0},
            )

            buckets = response["aggregations"]["time_series"]["buckets"]

            return {
                "metric_name": metric_name,
                "aggregation": aggregation,
                "interval": interval,
                "data_points": [
                    {
                        "timestamp": bucket["key_as_string"],
                        "value": bucket["metric_value"]["value"],
                    }
                    for bucket in buckets
                ],
                "total_points": len(buckets),
            }

        except ElasticsearchException as e:
            logger.error(f"Analytics query error: {e}")
            return {"error": str(e)}

    async def get_metrics(self) -> dict[str, Any]:
        """Get search performance metrics"""
        cluster_health = None
        indices_stats = None

        try:
            cluster_health = await self.client.cluster.health()
            indices_stats = await self.client.indices.stats()
        except ElasticsearchException as e:
            logger.error(f"Error getting cluster metrics: {e}")

        return {
            "search_metrics": self.metrics.to_dict(),
            "cluster_health": cluster_health,
            "indices_stats": indices_stats,
            "is_connected": self.is_connected,
            "configured_indices": list(self.indices.keys()),
        }

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check"""
        start_time = time.time()

        try:
            # Test basic connectivity
            cluster_health = await self.client.cluster.health()

            # Test search operation
            test_query = {"match_all": {}}
            search_result = await self.search("logs", test_query, size=1)

            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "cluster_status": cluster_health["status"],
                "number_of_nodes": cluster_health["number_of_nodes"],
                "active_shards": cluster_health["active_shards"],
                "target_response_time": "<2000ms",
                "meets_target": response_time < 2000,
                "search_test": "passed" if "error" not in search_result else "failed",
                "metrics": await self.get_metrics(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000,
            }


# Global Elasticsearch manager instance
elasticsearch_manager = ElasticsearchManager()
