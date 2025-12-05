"""
Quick Start Demo: LlamaIndex RAG without OpenAI API

This demo shows how to use LlamaIndex with local embeddings
when OpenAI API is unavailable.
"""

import asyncio

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# Use local embeddings instead of OpenAI
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")  # Fast, good quality

# If OpenAI LLM is also unavailable, you can use Ollama or another local LLM
# Settings.llm = Ollama(model="llama2")


async def demo_local_rag():
    """Demo: RAG with local embeddings on README.md"""

    documents = SimpleDirectoryReader(input_files=["./README.md"]).load_data()


    index = VectorStoreIndex.from_documents(documents)


    # Create query engine
    query_engine = index.as_query_engine()

    # Example queries
    queries = ["What is DevSkyy?", "What technologies does DevSkyy use?", "How does the fine-tuning system work?"]

    for query in queries:

        query_engine.query(query)


if __name__ == "__main__":
    # Download the embedding model first
    asyncio.run(demo_local_rag())
