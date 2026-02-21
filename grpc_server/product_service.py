"""
gRPC Product Service
=====================

High-performance inter-service product API using gRPC + Protocol Buffers.

Why gRPC over REST for internal calls?
- Binary encoding (protobuf) is 3–10x smaller than JSON
- HTTP/2 multiplexing: many requests over one connection
- Strongly typed contracts via .proto files
- Built-in streaming support

Usage:
    # Start server
    python -m grpc_server.product_service

    # In another service
    channel = grpc.aio.insecure_channel("localhost:50051")
    stub = product_pb2_grpc.ProductServiceStub(channel)
    product = await stub.GetProduct(GetProductRequest(sku="br-001"))
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from database.db import DatabaseManager, Product  # noqa: E402 — module-level for patchability

logger = logging.getLogger(__name__)

# Default gRPC port
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
GRPC_MAX_WORKERS = int(os.getenv("GRPC_MAX_WORKERS", "10"))


# ---------------------------------------------------------------------------
# ProductServicer — implements the ProductService RPC contract
# ---------------------------------------------------------------------------


class ProductServicer:
    """
    Implements the ProductService gRPC contract.

    Inherits from the generated servicer base class when running with
    real protobuf stubs. In tests, this class is instantiated directly
    and its methods are called with mock request/context objects.

    The servicer is stateless — all data access goes through the
    DatabaseManager session pattern.
    """

    async def GetProduct(self, request: Any, context: Any) -> dict[str, Any]:
        """
        Fetch a single product by SKU.

        Returns the product or sets NOT_FOUND status on the context.
        Using gRPC status codes (not HTTP) — the client maps these to
        appropriate errors for the calling service.
        """
        from sqlalchemy import select

        try:
            db = DatabaseManager()
            async with db.session() as session:
                result = await session.execute(
                    select(Product).where(
                        Product.sku == request.sku,
                        Product.is_active.is_(True),
                    )
                )
                product = result.scalar_one_or_none()

            if product is None:
                await self._set_not_found(context, f"Product {request.sku!r} not found")
                return {}

            return self._product_to_dict(product)

        except Exception as exc:
            logger.error(f"GetProduct error for sku={request.sku!r}: {exc}", exc_info=True)
            await self._set_internal_error(context, "Internal server error")
            return {}

    async def ListProducts(self, request: Any, context: Any) -> dict[str, Any]:
        """
        List products with optional collection filter.

        Uses offset pagination. For cursor-based pagination at scale,
        extend with a `cursor` field in ListProductsRequest.
        """
        from sqlalchemy import select

        try:
            limit = max(1, min(getattr(request, "limit", 20) or 20, 100))
            offset = max(0, getattr(request, "offset", 0) or 0)
            collection = getattr(request, "collection", "") or ""

            db = DatabaseManager()
            async with db.session() as session:
                query = select(Product).where(Product.is_active.is_(True))
                if collection:
                    query = query.where(Product.collection == collection)
                query = query.limit(limit).offset(offset)

                result = await session.execute(query)
                products = list(result.scalars().all())

            return {
                "products": [self._product_to_dict(p) for p in products],
                "total": len(products),
            }

        except Exception as exc:
            logger.error(f"ListProducts error: {exc}", exc_info=True)
            await self._set_internal_error(context, "Internal server error")
            return {"products": [], "total": 0}

    async def CreateProduct(self, request: Any, context: Any) -> dict[str, Any]:
        """
        Create a new product via the CQRS Command Bus.

        Routes through the CommandBus so the creation is:
        1. Validated by the handler
        2. Recorded as a ProductCreated event
        3. Projected to the read model
        """
        from core.cqrs.command_bus import Command, CommandBus, create_product_handler

        try:
            bus = CommandBus()
            bus.register_handler("CreateProduct", create_product_handler)

            images = list(getattr(request, "images", []) or [])
            cmd = Command(
                command_type="CreateProduct",
                data={
                    "sku": request.sku,
                    "name": request.name,
                    "description": getattr(request, "description", "") or "",
                    "price": request.price,
                    "compare_price": getattr(request, "compare_price", 0.0) or 0.0,
                    "collection": getattr(request, "collection", "") or "",
                    "images": images,
                },
                user_id="grpc-service",
            )

            await bus.execute(cmd)
            # Return the newly created product
            return await self.GetProduct(
                _SimpleRequest(sku=request.sku), context
            )

        except ValueError as exc:
            await self._set_invalid_argument(context, str(exc))
            return {}
        except Exception as exc:
            logger.error(f"CreateProduct error: {exc}", exc_info=True)
            await self._set_internal_error(context, "Internal server error")
            return {}

    async def UpdateProductPrice(self, request: Any, context: Any) -> dict[str, Any]:
        """
        Update product price via event sourcing.

        Emits a ProductPriceChanged event which:
        1. Gets persisted to the event store (immutable audit log)
        2. Updates the read model projection
        """
        from core.cqrs.command_bus import Command, CommandBus
        from core.events.event_store import Event, EventStore

        try:
            event = Event(
                event_type="ProductPriceChanged",
                aggregate_id=request.sku,
                data={
                    "sku": request.sku,
                    "new_price": request.new_price,
                    "user_id": getattr(request, "user_id", "grpc-service"),
                },
                user_id=getattr(request, "user_id", "grpc-service"),
            )

            store = EventStore()
            await store.append(event)

            return await self.GetProduct(
                _SimpleRequest(sku=request.sku), context
            )

        except Exception as exc:
            logger.error(f"UpdateProductPrice error: {exc}", exc_info=True)
            await self._set_internal_error(context, "Internal server error")
            return {}

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _product_to_dict(self, product: Any) -> dict[str, Any]:
        """Convert ORM Product to a plain dict (proto-compatible)."""
        try:
            images = json.loads(product.images_json) if getattr(product, "images_json", None) else []
        except (json.JSONDecodeError, TypeError):
            images = []

        return {
            "id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "description": getattr(product, "description", "") or "",
            "price": float(product.price),
            "compare_price": float(getattr(product, "compare_price", 0.0) or 0.0),
            "collection": getattr(product, "collection", "") or "",
            "is_active": bool(product.is_active),
            "images": images,
        }

    @staticmethod
    async def _set_not_found(context: Any, detail: str) -> None:
        """Set gRPC NOT_FOUND status if context supports it."""
        if context is not None and hasattr(context, "set_code"):
            try:
                import grpc
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(detail)
            except ImportError:
                pass

    @staticmethod
    async def _set_invalid_argument(context: Any, detail: str) -> None:
        """Set gRPC INVALID_ARGUMENT status if context supports it."""
        if context is not None and hasattr(context, "set_code"):
            try:
                import grpc
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(detail)
            except ImportError:
                pass

    @staticmethod
    async def _set_internal_error(context: Any, detail: str) -> None:
        """Set gRPC INTERNAL status if context supports it."""
        if context is not None and hasattr(context, "set_code"):
            try:
                import grpc
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(detail)
            except ImportError:
                pass


class _SimpleRequest:
    """Lightweight request object for internal re-use of servicer methods."""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------


async def serve(port: int = GRPC_PORT) -> None:
    """
    Start the async gRPC server.

    Uses grpc.aio (asyncio-native) rather than the legacy threaded API.

    TLS is enabled automatically when both GRPC_TLS_CERT and GRPC_TLS_KEY
    environment variables point to valid certificate/key files.
    In production (Kubernetes), mount TLS certs as secrets and set these vars.
    Without TLS env vars, the server falls back to insecure mode with a warning
    — acceptable for local dev / inter-pod communication with mTLS at the mesh level.
    """
    try:
        import grpc
        import grpc.aio

        server = grpc.aio.server()

        # Attempt to load generated stubs and add servicer
        # Falls back gracefully if protos haven't been compiled yet
        try:
            from grpc_server.generated import product_pb2_grpc

            product_pb2_grpc.add_ProductServiceServicer_to_server(
                ProductServicer(), server
            )
            logger.info("gRPC ProductService registered with generated stubs")
        except ImportError:
            logger.warning(
                "Generated gRPC stubs not found. "
                "Run: python -m grpc_tools.protoc -I grpc_server/proto "
                "--python_out=grpc_server/generated "
                "--grpc_python_out=grpc_server/generated "
                "grpc_server/proto/product.proto"
            )

        # TLS configuration — read cert/key from env-specified paths
        tls_cert_path = os.getenv("GRPC_TLS_CERT")
        tls_key_path = os.getenv("GRPC_TLS_KEY")

        if tls_cert_path and tls_key_path:
            try:
                with open(tls_cert_path, "rb") as f:
                    certificate_chain = f.read()
                with open(tls_key_path, "rb") as f:
                    private_key = f.read()
                server_credentials = grpc.ssl_server_credentials(
                    [(private_key, certificate_chain)]
                )
                server.add_secure_port(f"0.0.0.0:{port}", server_credentials)
                logger.info(f"gRPC server started with TLS on port {port}")
            except (OSError, IOError) as tls_err:
                logger.error(f"Failed to load TLS certificates: {tls_err}")
                raise
        else:
            server.add_insecure_port(f"0.0.0.0:{port}")
            logger.warning(
                f"gRPC server started WITHOUT TLS on port {port}. "
                "Set GRPC_TLS_CERT and GRPC_TLS_KEY for production use."
            )
        await server.start()
        logger.info(f"gRPC server started on port {port}")
        await server.wait_for_termination()

    except ImportError:
        logger.error(
            "grpcio not installed. Install with: pip install grpcio grpcio-tools protobuf"
        )
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())
