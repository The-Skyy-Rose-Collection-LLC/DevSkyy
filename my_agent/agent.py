"""
SkyyRose Multi-LLM Agent
========================

Agent supporting multiple LLM providers via LiteLLM:
- Google Gemini (default)
- OpenAI (GPT-4)
- Claude (Anthropic)
- Groq (Llama 3.3)
- Mistral
- Cohere
- Hugging Face

Usage:
    adk run my_agent

Environment Variables:
    GOOGLE_API_KEY - For Gemini models
    OPENAI_API_KEY - For OpenAI models
    ANTHROPIC_API_KEY - For Claude models
    GROQ_API_KEY - For Groq models
    MISTRAL_API_KEY - For Mistral models
    COHERE_API_KEY - For Cohere models
    HUGGINGFACE_API_KEY - For Hugging Face models

    MODEL_PROVIDER - Set to: gemini, openai, claude, groq, mistral, cohere, huggingface
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")


# =============================================================================
# Tool Implementations
# =============================================================================


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    import datetime

    # Mock timezone offsets for demo
    timezone_offsets = {
        "new york": -5,
        "los angeles": -8,
        "london": 0,
        "paris": 1,
        "tokyo": 9,
        "sydney": 11,
    }

    city_lower = city.lower()
    offset = timezone_offsets.get(city_lower, 0)

    utc_now = datetime.datetime.now(datetime.UTC)
    local_time = utc_now + datetime.timedelta(hours=offset)

    return {
        "status": "success",
        "city": city,
        "time": local_time.strftime("%I:%M %p"),
        "date": local_time.strftime("%Y-%m-%d"),
    }


def get_skyyrose_products(collection: str = "all") -> dict:
    """Returns SkyyRose products by collection."""
    products = {
        "BLACK_ROSE": [
            {"name": "Heart aRose Bomber", "price": 299.99, "sku": "BR-BOMB-001"},
            {"name": "Midnight Rose Hoodie", "price": 189.99, "sku": "BR-HOOD-001"},
            {"name": "Shadow Rose Tee", "price": 79.99, "sku": "BR-TEE-001"},
        ],
        "LOVE_HURTS": [
            {"name": "Heartbreak Hoodie", "price": 179.99, "sku": "LH-HOOD-001"},
            {"name": "Thorns & Roses Jacket", "price": 249.99, "sku": "LH-JACK-001"},
        ],
        "SIGNATURE": [
            {"name": "Classic Rose Logo Tee", "price": 69.99, "sku": "SIG-TEE-001"},
            {"name": "Signature Hoodie", "price": 149.99, "sku": "SIG-HOOD-001"},
            {"name": "Essential Joggers", "price": 119.99, "sku": "SIG-JOG-001"},
        ],
    }

    if collection.upper() == "ALL":
        return {"status": "success", "products": products}

    collection_products = products.get(collection.upper(), [])
    return {
        "status": "success",
        "collection": collection,
        "products": collection_products,
    }


def check_inventory(sku: str) -> dict:
    """Check inventory status for a product SKU."""
    # Mock inventory data
    inventory = {
        "BR-BOMB-001": {"in_stock": True, "quantity": 45, "sizes": ["S", "M", "L", "XL"]},
        "BR-HOOD-001": {"in_stock": True, "quantity": 120, "sizes": ["S", "M", "L", "XL", "XXL"]},
        "BR-TEE-001": {"in_stock": True, "quantity": 200, "sizes": ["S", "M", "L", "XL"]},
        "LH-HOOD-001": {"in_stock": False, "quantity": 0, "sizes": []},
        "SIG-TEE-001": {"in_stock": True, "quantity": 500, "sizes": ["XS", "S", "M", "L", "XL", "XXL"]},
    }

    item = inventory.get(sku)
    if not item:
        return {"status": "error", "message": f"SKU {sku} not found"}

    return {"status": "success", "sku": sku, **item}


# =============================================================================
# RAG Tools (Knowledge Base)
# =============================================================================

# Global RAG pipeline instance
_rag_pipeline = None


async def _get_rag_pipeline():
    """Get or initialize the RAG pipeline."""
    global _rag_pipeline
    if _rag_pipeline is None:
        try:
            import os
            import sys
            from pathlib import Path

            # Add parent directory to path
            repo_root = Path(__file__).parent.parent
            sys.path.insert(0, str(repo_root))

            # Change to repo root so relative paths work
            os.chdir(repo_root)

            from orchestration.document_ingestion import DocumentIngestionPipeline
            from orchestration.vector_store import ChromaVectorStore, VectorStoreConfig

            # Use absolute path for vector store
            vector_config = VectorStoreConfig(
                persist_directory=str(repo_root / "data" / "vectordb")
            )
            vector_store = ChromaVectorStore(config=vector_config)
            _rag_pipeline = DocumentIngestionPipeline(vector_store=vector_store)
            await _rag_pipeline.initialize()
        except Exception as e:
            return None, str(e)
    return _rag_pipeline, None


def search_knowledge_base(query: str, top_k: int = 5) -> dict:
    """
    Search the SkyyRose knowledge base for relevant information.

    Use this tool to find documentation, product details, brand guidelines,
    or any other information from the indexed knowledge base.

    Args:
        query: The search query (e.g., "BLACK ROSE collection details")
        top_k: Number of results to return (default: 5)

    Returns:
        Search results with relevant document chunks and sources.
    """
    import asyncio

    async def _search():
        pipeline, error = await _get_rag_pipeline()
        if error:
            return {"status": "error", "message": f"RAG not available: {error}"}

        try:
            results = await pipeline.search(query=query, top_k=top_k)
            return {
                "status": "success",
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, _search()).result()
        else:
            return asyncio.run(_search())
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_product_documentation(product_name: str) -> dict:
    """
    Get detailed documentation for a specific SkyyRose product.

    Use this tool to find detailed information about a product including
    materials, care instructions, sizing, and design details.

    Args:
        product_name: Name of the product (e.g., "Heart aRose Bomber")

    Returns:
        Product documentation and related information.
    """
    return search_knowledge_base(f"product documentation {product_name}", top_k=3)


def search_brand_guidelines(topic: str) -> dict:
    """
    Search SkyyRose brand guidelines and documentation.

    Use this tool to find information about brand voice, style guidelines,
    collection themes, or company policies.

    Args:
        topic: The topic to search for (e.g., "brand voice", "BLACK ROSE theme")

    Returns:
        Relevant brand guideline information.
    """
    return search_knowledge_base(f"brand guidelines {topic}", top_k=3)


# =============================================================================
# Model Selection
# =============================================================================

# Available models per provider
MODELS = {
    "gemini": "gemini-2.0-flash",
    "openai": "openai/gpt-4o",
    "claude": "anthropic/claude-sonnet-4-20250514",
    "groq": "groq/llama-3.3-70b-versatile",
    "mistral": "mistral/mistral-large-2411",
    "cohere": "cohere/command-r7b-12-2024",
    # HuggingFace via Sambanova provider - 70B model with function calling support
    "huggingface": "huggingface/sambanova/meta-llama/Llama-3.3-70B-Instruct",
}

def get_model():
    """Get the model based on MODEL_PROVIDER env var."""
    provider = os.environ.get("MODEL_PROVIDER", "groq").lower()

    if provider == "gemini":
        # Native Gemini - no wrapper needed
        return MODELS["gemini"]
    elif provider in MODELS:
        # Use LiteLLM wrapper for other providers
        return LiteLlm(model=MODELS[provider])
    else:
        print(f"Unknown provider: {provider}, defaulting to Groq")
        return LiteLlm(model=MODELS["groq"])


# =============================================================================
# Agent Definition
# =============================================================================

root_agent = Agent(
    model=get_model(),
    name="skyyrose_agent",
    description="SkyyRose luxury streetwear assistant with product, inventory, and knowledge base tools.",
    instruction="""You are a helpful assistant for SkyyRose, a luxury streetwear brand.

Brand Collections:
- BLACK ROSE: Limited edition dark elegance pieces
- LOVE HURTS: Emotional expression collection
- SIGNATURE: Foundation wardrobe essentials

Guidelines:
- Always maintain a luxury brand voice
- Be helpful and professional
- Focus on customer satisfaction
- Use available tools to get accurate information

Tool Usage:
- get_skyyrose_products: Get product listings by collection
- check_inventory: Check stock status for a specific SKU
- get_current_time: Get current time in a city
- search_knowledge_base: Search documentation and knowledge base
- get_product_documentation: Get detailed product info
- search_brand_guidelines: Find brand guidelines and policies

When asked about products, use get_skyyrose_products.
When asked about inventory/stock, use check_inventory.
When asked about time, use get_current_time.
When asked about detailed documentation, brand info, or anything not in the product catalog, use search_knowledge_base.
""",
    tools=[
        get_current_time,
        get_skyyrose_products,
        check_inventory,
        search_knowledge_base,
        get_product_documentation,
        search_brand_guidelines,
    ],
)


# For direct execution
if __name__ == "__main__":
    provider = os.environ.get("MODEL_PROVIDER", "groq")
    print(f"Agent: {root_agent.name}")
    print(f"Provider: {provider}")
    print(f"Model: {MODELS.get(provider, MODELS['groq'])}")
    print(f"Tools: {[t.__name__ for t in root_agent.tools]}")
    print("\nAvailable providers: gemini, openai, claude, groq, mistral, cohere, huggingface")
    print("\nSet provider: export MODEL_PROVIDER=openai")
    print("Run with: adk run my_agent")

