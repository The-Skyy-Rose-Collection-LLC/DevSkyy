"""
Tests for GraphQL Product Schema
==================================

Tests for GraphQL product queries using schema.execute() directly.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.graphql.schema import schema


@pytest.mark.unit
@pytest.mark.asyncio
class TestGraphQLProductQuery:
    """Test GraphQL product query operations via schema.execute()"""

    async def test_query_single_product_by_sku(self):
        """
        Test: query { product(sku: "br-001") { id sku name price collection } }
        """
        query = """
        query {
            product(sku: "br-001") {
                id
                sku
                name
                price
                collection
            }
        }
        """

        mock_product = MagicMock()
        mock_product.id = "prod-001"
        mock_product.sku = "br-001"
        mock_product.name = "Black Rose Crewneck"
        mock_product.price = 79.99
        mock_product.collection = "black-rose"
        mock_product.description = "Luxury embroidered crewneck"
        mock_product.compare_price = None
        mock_product.is_active = True
        mock_product.images_json = '["br-001-front.jpg"]'

        with patch(
            "api.graphql.schema.ProductDataLoader"
        ) as mock_loader_cls:
            mock_loader = MagicMock()
            mock_loader.load = AsyncMock(return_value=mock_product)
            mock_loader_cls.return_value = mock_loader

            result = await schema.execute(
                query,
                context_value={"product_loader": mock_loader},
            )

            assert result.errors is None
            assert result.data["product"]["sku"] == "br-001"
            assert result.data["product"]["name"] == "Black Rose Crewneck"
            assert result.data["product"]["price"] == 79.99
            assert result.data["product"]["collection"] == "black-rose"

    async def test_query_product_not_found(self):
        """
        Test: product(sku: "nonexistent") returns null (not an error)
        """
        query = """
        query {
            product(sku: "nonexistent-999") {
                id
                sku
            }
        }
        """

        with patch("api.graphql.schema.ProductDataLoader") as mock_loader_cls:
            mock_loader = MagicMock()
            mock_loader.load = AsyncMock(return_value=None)
            mock_loader_cls.return_value = mock_loader

            result = await schema.execute(
                query,
                context_value={"product_loader": mock_loader},
            )

            assert result.errors is None
            assert result.data["product"] is None

    async def test_query_products_list(self):
        """
        Test: products(limit: 10) returns list of products
        """
        query = """
        query {
            products(limit: 2) {
                sku
                name
                price
            }
        }
        """

        def make_mock_product(sku: str, name: str, price: float) -> MagicMock:
            p = MagicMock()
            p.id = f"id-{sku}"
            p.sku = sku
            p.name = name
            p.price = price
            p.collection = "black-rose"
            p.description = "desc"
            p.compare_price = None
            p.is_active = True
            p.images_json = "[]"
            return p

        mock_products = [
            make_mock_product("br-001", "Black Rose Crewneck", 79.99),
            make_mock_product("br-002", "Black Rose Hoodie", 89.99),
        ]

        with patch(
            "api.graphql.resolvers.product_resolver.get_products_from_db",
            new_callable=AsyncMock,
        ) as mock_get, patch(
            "api.graphql.schema.get_products_from_db",
            new_callable=AsyncMock,
        ) as mock_get2:
            mock_get.return_value = mock_products
            mock_get2.return_value = mock_products

            result = await schema.execute(query)

            assert result.errors is None
            assert len(result.data["products"]) == 2
            assert result.data["products"][0]["sku"] == "br-001"
            assert result.data["products"][1]["sku"] == "br-002"

    async def test_query_products_filtered_by_collection(self):
        """
        Test: products(collection: "black-rose") filters by collection
        """
        query = """
        query {
            products(collection: "black-rose", limit: 10) {
                sku
                collection
            }
        }
        """

        def make_mock(sku: str) -> MagicMock:
            p = MagicMock()
            p.id = sku
            p.sku = sku
            p.name = f"Product {sku}"
            p.price = 79.99
            p.collection = "black-rose"
            p.description = None
            p.compare_price = None
            p.is_active = True
            p.images_json = "[]"
            return p

        mock_products = [make_mock("br-001"), make_mock("br-002")]

        with patch("api.graphql.schema.get_products_from_db", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_products

            result = await schema.execute(
                query,
                variable_values={"collection": "black-rose"},
            )

            assert result.errors is None
            for product in result.data["products"]:
                assert product["collection"] == "black-rose"

    async def test_product_images_deserialized_from_json(self):
        """
        Test that images are properly deserialized from images_json column
        """
        query = """
        query {
            product(sku: "br-001") {
                sku
                images
            }
        }
        """

        mock_product = MagicMock()
        mock_product.id = "prod-001"
        mock_product.sku = "br-001"
        mock_product.name = "Black Rose Crewneck"
        mock_product.price = 79.99
        mock_product.collection = "black-rose"
        mock_product.description = None
        mock_product.compare_price = None
        mock_product.is_active = True
        mock_product.images_json = '["br-001-front.jpg", "br-001-back.jpg"]'

        with patch("api.graphql.schema.ProductDataLoader") as mock_loader_cls:
            mock_loader = MagicMock()
            mock_loader.load = AsyncMock(return_value=mock_product)
            mock_loader_cls.return_value = mock_loader

            result = await schema.execute(
                query,
                context_value={"product_loader": mock_loader},
            )

            assert result.errors is None
            assert result.data["product"]["images"] == ["br-001-front.jpg", "br-001-back.jpg"]

    async def test_graphql_introspection(self):
        """
        Test: GraphQL schema introspection works (required for GraphiQL)
        """
        query = """
        query {
            __schema {
                queryType {
                    name
                }
                types {
                    name
                }
            }
        }
        """

        result = await schema.execute(query)

        assert result.errors is None
        assert result.data["__schema"]["queryType"]["name"] == "Query"
        type_names = [t["name"] for t in result.data["__schema"]["types"]]
        assert "ProductType" in type_names
        assert "Query" in type_names
