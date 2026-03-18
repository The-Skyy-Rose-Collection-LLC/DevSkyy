#!/usr/bin/env python3
"""Scrape → Ingest Pipeline: Official Docs into the RAG Vector Store

Runs docs_scraper (Bright Data SERP API) then feeds the output directly
into the existing DocumentIngestionPipeline (ChromaDB / Pinecone).

After this runs, all agents can query current official documentation
via the RAG context manager with zero additional changes.

Usage:
    # Scrape + ingest your full tech stack (English)
    python scripts/run_docs_pipeline.py \
        --queries "FastAPI,Next.js 16,Three.js,Strawberry GraphQL,LangGraph,WooCommerce REST API"

    # Scrape only — inspect results before committing to vector store
    python scripts/run_docs_pipeline.py --queries "FastAPI" --scrape-only

    # Re-ingest already-scraped docs (skip Bright Data, just re-embed)
    python scripts/run_docs_pipeline.py --ingest-only --scraped-dir scraped_docs/

    # Custom collection (isolate from main knowledge base)
    python scripts/run_docs_pipeline.py --queries "Three.js" --collection tech_stack_docs

Output:
    scraped_docs/                      Markdown + JSON from SERP scraper
    data/vectordb/                     ChromaDB (or Pinecone if configured)

Author: DevSkyy Platform
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path regardless of how this script is invoked
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Target libraries for the full DevSkyy tech stack
DEFAULT_QUERIES = [
    "FastAPI Python framework",
    "Next.js 15 16 documentation",
    "Three.js 3D library",
    "Strawberry GraphQL Python",
    "LangGraph LangChain agents",
    "WooCommerce REST API",
    "WordPress hooks filters PHP",
    "React 19 documentation",
    "ChromaDB vector database",
    "httpx async Python HTTP",
]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape official docs via Bright Data then ingest into RAG vector store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--queries",
        metavar="A,B,...",
        help=f"Comma-separated queries (default: {len(DEFAULT_QUERIES)} core tech-stack libraries)",
    )
    src.add_argument(
        "--queries-file", type=Path, metavar="FILE", help="File with one query per line"
    )

    p.add_argument("--lang", default="en", metavar="CODE", help="Language code (default: en)")
    p.add_argument("--country", default="us", metavar="CODE", help="Country code (default: us)")
    p.add_argument(
        "--scraped-dir",
        type=Path,
        default=Path("scraped_docs"),
        metavar="DIR",
        help="Scraper output / ingestion source (default: scraped_docs/)",
    )
    p.add_argument(
        "--collection",
        default="devskyy_docs",
        metavar="NAME",
        help="ChromaDB collection name (default: devskyy_docs)",
    )
    p.add_argument(
        "--fetch-depth",
        type=int,
        default=5,
        metavar="N",
        help="Official pages to fetch per query (default: 5)",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=2,
        metavar="N",
        help="Max parallel Bright Data requests (default: 2)",
    )
    p.add_argument("--scrape-only", action="store_true", help="Run scraper only, skip ingestion")
    p.add_argument(
        "--ingest-only",
        action="store_true",
        help="Skip scraping, ingest existing scraped_docs/ content",
    )
    p.add_argument("--verbose", action="store_true", help="Enable DEBUG logging")
    return p.parse_args()


async def run_scraper(args: argparse.Namespace, queries: list[str]) -> Path:
    """Run docs_scraper and return the output directory."""
    import os

    # Import inline to avoid circular issues
    from scripts.docs_scraper import (
        BrightDataSERPClient,
        DocsScraper,
        OfficialDocsFilter,
    )

    api_key = os.getenv("BRIGHTDATA_API_KEY")
    zone = os.getenv("BRIGHTDATA_ZONE", "serp_api1")
    unlocker_zone = os.getenv("BRIGHTDATA_UNLOCKER_ZONE")
    if not api_key:
        raise SystemExit("BRIGHTDATA_API_KEY not set in environment — check your .env")

    fetch_mode = f"Web Unlocker ({unlocker_zone})" if unlocker_zone else "SERP snippets"
    logger.info(
        "Phase 1/2 — Scraping %d quer%s | page fetch: %s",
        len(queries),
        "y" if len(queries) == 1 else "ies",
        fetch_mode,
    )

    async with BrightDataSERPClient(
        api_key, zone, unlocker_zone=unlocker_zone, max_concurrency=args.concurrency
    ) as client:
        scraper = DocsScraper(
            client=client,
            output_dir=args.scraped_dir,
            doc_filter=OfficialDocsFilter(),
            fetch_depth=args.fetch_depth,
            search_only=False,
            page_delay=1.0,
        )
        collections = await scraper.run(queries, langs=[args.lang], countries=[args.country])

    total_pages = sum(len(c.pages) for c in collections)
    total_official = sum(len(c.official_results) for c in collections)
    logger.info(
        "Scrape complete — %d official URLs found, %d pages fetched → %s",
        total_official,
        total_pages,
        args.scraped_dir,
    )
    return args.scraped_dir


async def run_ingestion(scraped_dir: Path, collection_name: str) -> dict:
    """Ingest all .md files from scraped_dir into the vector store."""
    from orchestration.document_ingestion import DocumentIngestionPipeline, IngestionConfig
    from orchestration.vector_store import VectorStoreConfig

    if not scraped_dir.exists():
        raise FileNotFoundError(f"Scraped docs directory not found: {scraped_dir}")

    md_count = sum(1 for _ in scraped_dir.rglob("pages/*.md"))
    if md_count == 0:
        logger.warning("No .md files found under %s/*/pages/ — nothing to ingest", scraped_dir)
        return {"total_files": 0, "total_chunks": 0}

    logger.info(
        "Phase 2/2 — Ingesting %d markdown files into '%s' collection", md_count, collection_name
    )

    vs_config = VectorStoreConfig(collection_name=collection_name)
    pipeline = DocumentIngestionPipeline(
        config=IngestionConfig(chunk_size=512, chunk_overlap=50),
    )
    # Override vector store config with our collection name
    from orchestration.vector_store import create_vector_store

    pipeline._vector_store = create_vector_store(vs_config)

    await pipeline.initialize()

    # Ingest only the pages/ subdirs (skip serp_results.json, index.json)
    # We point at the top-level dir and rely on include_patterns=["*.md"]
    result = await pipeline.ingest_directory(scraped_dir, recursive=True)

    stats = await pipeline.get_stats()
    doc_count = stats.get("vector_store", {}).get("document_count", "?")

    logger.info(
        "Ingestion complete — %d chunks from %d files in %.1fs | collection now has %s docs",
        result.total_chunks,
        result.total_documents,
        result.duration_seconds,
        doc_count,
    )

    if result.failed_files:
        logger.warning(
            "%d files failed to ingest: %s", len(result.failed_files), result.failed_files[:5]
        )

    return result.to_dict()


async def smoke_test(collection_name: str) -> None:
    """Quick RAG search to confirm docs are retrievable."""
    from orchestration.document_ingestion import DocumentIngestionPipeline, IngestionConfig
    from orchestration.vector_store import VectorStoreConfig, create_vector_store

    vs_config = VectorStoreConfig(collection_name=collection_name)
    pipeline = DocumentIngestionPipeline(config=IngestionConfig())
    pipeline._vector_store = create_vector_store(vs_config)
    await pipeline.initialize()

    test_queries = [
        "How do I define a FastAPI route with dependency injection?",
        "Three.js scene setup geometry",
        "WooCommerce REST API authentication",
    ]

    print("\n  Smoke test — RAG search on ingested docs:")
    for q in test_queries:
        results = await pipeline.search(q, top_k=1)
        if results:
            doc = results[0].get("document", {})
            src = doc.get("source", "unknown")
            score = results[0].get("score", 0)
            print(f"  ✓ [{score:.3f}] {q[:55]}...")
            print(f"         → {Path(src).name}")
        else:
            print(f"  ✗ No results for: {q[:55]}")


async def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    # Resolve queries
    if args.ingest_only:
        queries = []
    elif args.queries_file:
        queries = [
            q.strip()
            for q in args.queries_file.read_text(encoding="utf-8").splitlines()
            if q.strip() and not q.startswith("#")
        ]
    elif args.queries:
        queries = [q.strip() for q in args.queries.split(",") if q.strip()]
    else:
        queries = DEFAULT_QUERIES
        logger.info(
            "No --queries specified — using default tech stack (%d libraries)", len(queries)
        )

    t0 = time.time()

    # Phase 1: Scrape
    if not args.ingest_only:
        if not queries:
            raise SystemExit("No queries to scrape")
        scraped_dir = await run_scraper(args, queries)
    else:
        scraped_dir = args.scraped_dir
        logger.info("Skipping scrape — using existing %s", scraped_dir)

    # Phase 2: Ingest
    ingest_result: dict = {}
    if not args.scrape_only:
        ingest_result = await run_ingestion(scraped_dir, args.collection)
        await smoke_test(args.collection)

    # Summary
    elapsed = time.time() - t0
    sep = "─" * 54
    print(f"\n{sep}")
    print("  Tech stack docs pipeline complete")
    print(f"  Queries scraped   : {len(queries)}")
    print(f"  Collection        : {args.collection}")
    if ingest_result:
        print(f"  Chunks indexed    : {ingest_result.get('total_chunks', 0):,}")
        print(f"  Files indexed     : {ingest_result.get('total_documents', 0)}")
        print(f"  Failed files      : {len(ingest_result.get('failed_files', []))}")
    print(f"  Total time        : {elapsed:.1f}s")
    print(f"  Vector store      : ./data/vectordb  ({args.collection})")
    print(f"{sep}\n")
    print("  Agents can now query current official docs via:")
    print("  pipeline.get_context_for_question('your question here')\n")


if __name__ == "__main__":
    asyncio.run(main())
