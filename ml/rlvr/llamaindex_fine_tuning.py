"""
LlamaIndex-Powered Fine-Tuning Orchestrator

Standalone implementation using LlamaIndex for training data retrieval
instead of database queries. Works without MCP infrastructure.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Any

from anthropic import Anthropic
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
import openai


logger = logging.getLogger(__name__)


class LlamaIndexFineTuningOrchestrator:
    """
    Standalone fine-tuning orchestrator using LlamaIndex for example retrieval.

    Features:
    - No database required (uses LlamaIndex vector store)
    - No MCP infrastructure needed
    - RAG-based example retrieval
    - Automatic similarity-based example selection

    Architecture:
    1. Index training examples as Documents in LlamaIndex
    2. Use vector search to find best examples (instead of SQL)
    3. Optimize prompts using Claude with retrieved examples
    4. Fine-tune OpenAI models with selected training data
    """

    def __init__(
        self,
        index_dir: str = "./llamaindex_storage",
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None
    ):
        """
        Initialize the LlamaIndex-powered fine-tuning orchestrator.

        Args:
            index_dir: Directory to store LlamaIndex indexes
            openai_api_key: OpenAI API key (defaults to env var)
            anthropic_api_key: Anthropic API key (defaults to env var)
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)

        # API keys with error handling
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.openai_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI operations will fail")
        if not self.anthropic_key:
            logger.warning("ANTHROPIC_API_KEY not set - Claude optimization will fail")

        # Initialize API clients
        self.openai_client = openai.OpenAI(api_key=self.openai_key) if self.openai_key else None
        self.anthropic_client = Anthropic(api_key=self.anthropic_key) if self.anthropic_key else None

        # Configure LlamaIndex settings
        if self.openai_key:
            Settings.llm = LlamaOpenAI(model="gpt-4", api_key=self.openai_key)
            Settings.embed_model = OpenAIEmbedding(api_key=self.openai_key)

        # Training example indexes (one per agent)
        self.indexes: dict[str, VectorStoreIndex] = {}

    def index_training_examples(
        self,
        agent_id: str,
        examples: list[dict[str, Any]],
        force_rebuild: bool = False
    ) -> VectorStoreIndex:
        """
        Index training examples using LlamaIndex vector store.

        Args:
            agent_id: Agent identifier
            examples: List of training examples with 'input', 'output', 'score' fields
            force_rebuild: Rebuild index even if it exists

        Returns:
            VectorStoreIndex for the agent's training data
        """
        agent_index_dir = self.index_dir / agent_id

        # Try to load existing index
        if not force_rebuild and agent_index_dir.exists():
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=str(agent_index_dir)
                )
                index = load_index_from_storage(storage_context)
                self.indexes[agent_id] = index
                logger.info(f"Loaded existing index for agent {agent_id}")
                return index
            except Exception as e:
                logger.warning(f"Failed to load index, rebuilding: {e}")

        # Create documents from training examples
        documents = []
        for i, example in enumerate(examples):
            # Store as structured document with metadata
            doc = Document(
                text=f"Input: {example['input']}\n\nOutput: {example['output']}",
                metadata={
                    "example_id": str(i),
                    "score": example.get("score", 0.0),
                    "input": example["input"],
                    "output": example["output"],
                    "agent_id": agent_id
                }
            )
            documents.append(doc)

        # Build vector index
        index = VectorStoreIndex.from_documents(documents)

        # Persist to disk
        agent_index_dir.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(agent_index_dir))

        self.indexes[agent_id] = index
        logger.info(f"Indexed {len(examples)} examples for agent {agent_id}")

        return index

    def retrieve_best_examples(
        self,
        agent_id: str,
        query: str | None = None,
        top_k: int = 10
    ) -> list[dict[str, Any]]:
        """
        Retrieve best training examples using vector similarity search.

        Args:
            agent_id: Agent identifier
            query: Optional query for semantic search (defaults to "high quality examples")
            top_k: Number of examples to retrieve

        Returns:
            List of best examples sorted by relevance/score
        """
        if agent_id not in self.indexes:
            agent_index_dir = self.index_dir / agent_id
            if not agent_index_dir.exists():
                raise ValueError(f"No index found for agent {agent_id}")

            # Load index
            storage_context = StorageContext.from_defaults(
                persist_dir=str(agent_index_dir)
            )
            self.indexes[agent_id] = load_index_from_storage(storage_context)

        index = self.indexes[agent_id]

        # Create retriever
        retriever = index.as_retriever(similarity_top_k=top_k)

        # Retrieve relevant examples
        query_text = query or "high quality examples with excellent outputs"
        nodes = retriever.retrieve(query_text)

        # Extract and format examples
        examples = []
        for node in nodes:
            metadata = node.node.metadata
            examples.append({
                "input": metadata.get("input", ""),
                "output": metadata.get("output", ""),
                "score": float(metadata.get("score", 0.0)),
                "similarity": node.score  # Vector similarity score
            })

        # Sort by score (descending)
        examples.sort(key=lambda x: x["score"], reverse=True)

        return examples

    async def optimize_prompt_with_claude(
        self,
        agent_id: str,
        current_prompt: str,
        top_k_examples: int = 10
    ) -> dict[str, Any]:
        """
        Optimize agent prompt using Claude with best examples from LlamaIndex.

        Args:
            agent_id: Agent identifier
            current_prompt: Current agent system prompt
            top_k_examples: Number of top examples to use

        Returns:
            Optimization result with new prompt
        """
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized - check ANTHROPIC_API_KEY")

        # Retrieve best examples using RAG
        best_examples = self.retrieve_best_examples(agent_id, top_k=top_k_examples)

        if not best_examples:
            raise ValueError(f"No training examples found for agent {agent_id}")

        # Format examples using XML (Claude best practice)
        examples_xml = self._format_examples_xml(best_examples)

        # Claude optimization prompt with best practices
        optimization_prompt = f"""You are a prompt engineering expert specializing in Claude optimization.

Your task is to analyze successful examples and refine an agent's system prompt to maximize performance.

<current_prompt>
{current_prompt}
</current_prompt>

<successful_examples>
{examples_xml}
</successful_examples>

<instructions>
Follow these steps to optimize the prompt:

1. **Analysis Phase**: Examine the successful examples and identify:
   - Common patterns in high-performing outputs
   - What makes outputs effective (clarity, structure, completeness)
   - Edge cases or challenging scenarios handled well
   - Tone, style, and formatting preferences

2. **Pattern Recognition**: Extract key insights:
   - What instructions would produce these outputs consistently?
   - What constraints or guidelines are implicitly followed?
   - What common mistakes are avoided?

3. **Prompt Refinement**: Create an optimized prompt that:
   - Uses clear, direct instructions (no ambiguity)
   - Employs XML tags to structure sections (like <context>, <instructions>, <examples>)
   - Includes 2-3 few-shot examples from the best performers
   - Encourages step-by-step reasoning for complex tasks
   - Preserves core functionality while improving clarity
   - Adds explicit guidelines based on successful patterns

4. **Quality Checks**: Ensure the optimized prompt:
   - Is more specific and actionable than the original
   - Addresses edge cases identified in examples
   - Uses plain language without jargon
   - Has clear success criteria
</instructions>

<output_format>
Return ONLY the optimized prompt as plain text. Do not include explanations, meta-commentary, or wrapper tags.
The prompt should be ready to use directly as a system prompt.
</output_format>

Think through your analysis step by step, then provide the optimized prompt."""

        # Call Claude for optimization
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            temperature=0.3,
            messages=[{"role": "user", "content": optimization_prompt}]
        )

        optimized_prompt = response.content[0].text

        return {
            "agent_id": agent_id,
            "provider": "anthropic",
            "method": "llamaindex_rag_optimization",
            "model": "claude-3-5-sonnet-20241022",
            "examples_used": len(best_examples),
            "optimized_prompt": optimized_prompt,
            "original_prompt": current_prompt,
            "optimization_technique": "xml_structured_rag_few_shot_cot"
        }

    async def fine_tune_openai(
        self,
        agent_id: str,
        base_model: str = "gpt-3.5-turbo",
        top_k_examples: int = 50,
        hyperparameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Fine-tune OpenAI model using examples from LlamaIndex.

        Args:
            agent_id: Agent identifier
            base_model: Base model to fine-tune
            top_k_examples: Number of examples to use for fine-tuning
            hyperparameters: Training hyperparameters

        Returns:
            Fine-tuning job details
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized - check OPENAI_API_KEY")

        hyperparameters = hyperparameters or {}

        # Retrieve best examples using RAG
        best_examples = self.retrieve_best_examples(agent_id, top_k=top_k_examples)

        if len(best_examples) < 10:
            raise ValueError(f"Need at least 10 examples, found {len(best_examples)}")

        # Export to OpenAI fine-tuning format (JSONL)
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.jsonl',
            prefix=f'openai_ft_{agent_id}_',
            delete=False
        ) as temp_file:
            training_file_path = temp_file.name

            for example in best_examples:
                # OpenAI fine-tuning format
                training_example = {
                    "messages": [
                        {"role": "user", "content": example["input"]},
                        {"role": "assistant", "content": example["output"]}
                    ]
                }
                # Write valid JSON (not Python dict repr)
                temp_file.write(json.dumps(training_example) + "\n")

        try:
            # Upload training file
            with open(training_file_path, "rb") as f:
                training_file = self.openai_client.files.create(
                    file=f,
                    purpose="fine-tune"
                )

            # Create fine-tuning job
            fine_tuning_job = self.openai_client.fine_tuning.jobs.create(
                training_file=training_file.id,
                model=base_model,
                hyperparameters={
                    "n_epochs": hyperparameters.get("epochs", 3),
                    "learning_rate_multiplier": hyperparameters.get("learning_rate", "auto"),
                }
            )

            logger.info(f"OpenAI fine-tuning job created: {fine_tuning_job.id}")

            return {
                "agent_id": agent_id,
                "provider": "openai",
                "job_id": fine_tuning_job.id,
                "base_model": base_model,
                "training_examples": len(best_examples),
                "status": fine_tuning_job.status,
                "method": "llamaindex_rag_selection"
            }

        finally:
            # Clean up temporary file
            if os.path.exists(training_file_path):
                os.unlink(training_file_path)
                logger.info(f"Cleaned up temporary file: {training_file_path}")

    def _format_examples_xml(self, examples: list[dict[str, Any]]) -> str:
        """Format examples with XML tags for Claude optimization."""
        formatted = []
        for i, ex in enumerate(examples, 1):
            formatted.append(f"""
<example id="{i}" score="{ex['score']:.2f}" similarity="{ex.get('similarity', 0):.2f}">
  <input>
{ex['input'][:500]}
  </input>
  <output>
{ex['output'][:500]}
  </output>
</example>""")
        return "\n".join(formatted)


# Standalone usage example
async def main():
    """Example usage of LlamaIndex fine-tuning orchestrator."""

    # Initialize orchestrator (no database needed!)
    orchestrator = LlamaIndexFineTuningOrchestrator(
        index_dir="./training_indexes"
    )

    # Example training data
    training_examples = [
        {
            "input": "What is Python?",
            "output": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "score": 0.95
        },
        {
            "input": "Explain machine learning",
            "output": "Machine learning is a subset of AI where systems learn from data to improve performance on tasks without explicit programming.",
            "score": 0.92
        },
        # Add more examples...
    ]

    agent_id = "example_agent_001"

    # Step 1: Index training examples
    orchestrator.index_training_examples(agent_id, training_examples)

    # Step 2: Optimize prompt with Claude
    current_prompt = "You are a helpful AI assistant."
    result = await orchestrator.optimize_prompt_with_claude(
        agent_id,
        current_prompt,
        top_k_examples=5
    )

    print("Optimized Prompt:")
    print(result["optimized_prompt"])

    # Step 3: Fine-tune OpenAI model (optional)
    # ft_result = await orchestrator.fine_tune_openai(agent_id, top_k_examples=20)
    # print(f"Fine-tuning job: {ft_result['job_id']}")


if __name__ == "__main__":
    asyncio.run(main())
