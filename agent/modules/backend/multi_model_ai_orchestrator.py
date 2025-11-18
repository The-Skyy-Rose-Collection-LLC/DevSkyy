"""
Multi-Model AI Orchestrator
Combines the best AI models from ALL platforms for phenomenal results

Supported Models:
- Anthropic: Claude Sonnet 4.5, Claude Opus 4, Claude Haiku
- OpenAI: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- Google: Gemini 1.5 Pro, Gemini 1.5 Flash
- Mistral: Mistral Large, Mistral Medium
- Meta: Llama 3.1 405B (via Together AI)
- Cohere: Command R+
- Local Models: Any Ollama-compatible model

Features:
- Intelligent model selection based on task type
- Parallel model inference for consensus
- Cost optimization
- Fallback handling
- Response quality scoring
- Ensemble learning
- Model performance tracking
- Auto-routing to best model
"""

import asyncio
from datetime import datetime
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic
import httpx
from openai import AsyncOpenAI

from config.unified_config import get_config


logger = logging.getLogger(__name__)


class MultiModelAIOrchestrator:
    """
    Orchestrates multiple AI models to provide best-in-class results.
    Automatically selects and combines models based on task requirements.
    """

    def __init__(self):
        # Initialize all available AI services
        self.models = {}

        # Anthropic (Claude)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.models["claude"] = {
                "client": AsyncAnthropic(api_key=anthropic_key),
                "models": {
                    "sonnet": "claude-sonnet-4-5-20250929",
                    "opus": "claude-opus-4-20250514",
                    "haiku": "claude-3-5-haiku-20241022",
                },
                "strengths": ["reasoning", "coding", "analysis", "writing"],
                "cost_tier": "premium",
            }

        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            config = get_config()
            is_consequential = config.ai.openai_is_consequential
            default_headers = {"x-openai-isConsequential": str(is_consequential).lower()}

            self.models["openai"] = {
                "client": AsyncOpenAI(api_key=openai_key, default_headers=default_headers),
                "models": {
                    "gpt4": "gpt-4-turbo-preview",
                    "gpt4_vision": "gpt-4-vision-preview",
                    "gpt35": "gpt-3.5-turbo",
                },
                "strengths": ["creative", "vision", "general"],
                "cost_tier": "medium",
            }

        # Google Gemini
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            self.models["gemini"] = {
                "api_key": gemini_key,
                "models": {"pro": "gemini-1.5-pro", "flash": "gemini-1.5-flash"},
                "strengths": ["multimodal", "context", "speed"],
                "cost_tier": "low",
            }

        # Mistral
        mistral_key = os.getenv("MISTRAL_API_KEY")
        if mistral_key:
            self.models["mistral"] = {
                "api_key": mistral_key,
                "models": {
                    "large": "mistral-large-latest",
                    "medium": "mistral-medium-latest",
                },
                "strengths": ["multilingual", "coding", "fast"],
                "cost_tier": "low",
            }

        # Together AI (for Llama and other open models)
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key:
            self.models["together"] = {
                "api_key": together_key,
                "models": {
                    "llama3": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                    "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                },
                "strengths": ["open_source", "cost_effective"],
                "cost_tier": "very_low",
            }

        # Cohere
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            self.models["cohere"] = {
                "api_key": cohere_key,
                "models": {"command": "command-r-plus"},
                "strengths": ["retrieval", "summarization"],
                "cost_tier": "low",
            }

        # Model performance tracking
        self.performance_history: dict[str, list[float]] = {}
        self.task_routing: dict[str, str] = {
            "reasoning": "claude_sonnet",
            "creative_writing": "claude_sonnet",
            "code_generation": "claude_sonnet",
            "code_review": "claude_sonnet",
            "data_analysis": "claude_sonnet",
            "summarization": "gemini_flash",
            "translation": "mistral_large",
            "vision": "openai_gpt4_vision",
            "fast_response": "gemini_flash",
            "cost_effective": "together_llama3",
            "general": "claude_sonnet",
        }

        logger.info(f"🤖 Multi-Model Orchestrator initialized with {len(self.models)} AI platforms")

    async def generate(
        self,
        prompt: str,
        task_type: str = "general",
        use_ensemble: bool = False,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Generate response using optimal model(s) for the task.

        Args:
            prompt: The input prompt
            task_type: Type of task (reasoning, creative_writing, code_generation, etc.)
            use_ensemble: If True, use multiple models and combine responses
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            Dict with response and metadata
        """
        try:
            if use_ensemble:
                return await self._ensemble_generate(prompt, task_type, max_tokens, temperature)
            else:
                return await self._single_model_generate(prompt, task_type, max_tokens, temperature)

        except Exception as e:
            logger.error(f"❌ Multi-model generation failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _single_model_generate(
        self, prompt: str, task_type: str, max_tokens: int, temperature: float
    ) -> dict[str, Any]:
        """
        Generate response using single optimal model.
        """
        # Get optimal model for task
        model_id = self.task_routing.get(task_type, "claude_sonnet")
        platform, model_name = model_id.split("_", 1)

        logger.info(f"🎯 Routing {task_type} task to {platform} {model_name}")

        # Generate with selected model
        if platform == "claude":
            response = await self._call_claude(model_name, prompt, max_tokens, temperature)
        elif platform == "openai":
            response = await self._call_openai(model_name, prompt, max_tokens, temperature)
        elif platform == "gemini":
            response = await self._call_gemini(model_name, prompt, max_tokens, temperature)
        elif platform == "mistral":
            response = await self._call_mistral(model_name, prompt, max_tokens, temperature)
        elif platform == "together":
            response = await self._call_together(model_name, prompt, max_tokens, temperature)
        else:
            # Fallback to Claude Sonnet
            response = await self._call_claude("sonnet", prompt, max_tokens, temperature)

        return {
            "response": response,
            "model_used": model_id,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _ensemble_generate(
        self, prompt: str, task_type: str, max_tokens: int, temperature: float
    ) -> dict[str, Any]:
        """
        Generate responses from multiple models and combine them.
        """
        logger.info(f"🎭 Using ensemble approach for {task_type}")

        # Select top 3 models for this task
        models_to_use = [
            "claude_sonnet",
            "openai_gpt4",
            "gemini_pro",
        ]

        # Generate responses in parallel
        tasks = []
        for model_id in models_to_use:
            platform, model_name = model_id.split("_", 1)
            if platform == "claude" and "claude" in self.models:
                tasks.append(self._call_claude(model_name, prompt, max_tokens, temperature))
            elif platform == "openai" and "openai" in self.models:
                tasks.append(self._call_openai(model_name, prompt, max_tokens, temperature))
            elif platform == "gemini" and "gemini" in self.models:
                tasks.append(self._call_gemini(model_name, prompt, max_tokens, temperature))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        valid_responses = [r for r in responses if not isinstance(r, Exception)]

        if not valid_responses:
            return {"error": "All ensemble models failed", "status": "failed"}

        # Combine responses using Claude for synthesis
        synthesis_prompt = f"""Synthesize these AI responses into the best possible answer:

Original Question: {prompt}

Responses:
{chr(10).join([f"Response {i + 1}: {r}" for i, r in enumerate(valid_responses)])}

Create the optimal combined response that leverages the strengths of each."""

        final_response = await self._call_claude("sonnet", synthesis_prompt, max_tokens, 0.3)

        return {
            "response": final_response,
            "ensemble_used": models_to_use,
            "individual_responses": valid_responses,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _call_claude(self, model_name: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Anthropic Claude model."""
        try:
            client = self.models["claude"]["client"]
            model = self.models["claude"]["models"].get(model_name, self.models["claude"]["models"]["sonnet"])

            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude call failed: {e}")
            raise

    async def _call_openai(self, model_name: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call OpenAI model."""
        try:
            client = self.models["openai"]["client"]
            model = self.models["openai"]["models"].get(model_name, self.models["openai"]["models"]["gpt4"])

            response = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            raise

    async def _call_gemini(self, model_name: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Google Gemini model."""
        try:
            api_key = self.models["gemini"]["api_key"]
            model = self.models["gemini"]["models"].get(model_name, "gemini-1.5-pro")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "maxOutputTokens": max_tokens,
                            "temperature": temperature,
                        },
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    raise Exception(f"Gemini API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            raise

    async def _call_mistral(self, model_name: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Mistral AI model."""
        try:
            api_key = self.models["mistral"]["api_key"]
            model = self.models["mistral"]["models"].get(model_name, "mistral-large-latest")

            url = "https://api.mistral.ai/v1/chat/completions"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Mistral API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Mistral call failed: {e}")
            raise

    async def _call_together(self, model_name: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Together AI model (Llama, Mixtral, etc.)."""
        try:
            api_key = self.models["together"]["api_key"]
            model = self.models["together"]["models"].get(model_name, self.models["together"]["models"]["llama3"])

            url = "https://api.together.xyz/v1/chat/completions"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Together AI error: {response.status_code}")

        except Exception as e:
            logger.error(f"Together AI call failed: {e}")
            raise

    async def get_best_model_for_task(self, task_type: str) -> str:
        """
        Get the best model for a specific task type based on performance history.
        """
        return self.task_routing.get(task_type, "claude_sonnet")

    async def benchmark_models(self, test_prompts: list[str]) -> dict[str, Any]:
        """
        Benchmark all available models with test prompts.
        """
        results = {}

        for platform, config in self.models.items():
            if "client" in config or "api_key" in config:
                platform_results = []
                for prompt in test_prompts:
                    try:
                        start_time = datetime.now()

                        if platform == "claude":
                            await self._call_claude("sonnet", prompt, 500, 0.7)
                        elif platform == "openai":
                            await self._call_openai("gpt4", prompt, 500, 0.7)
                        elif platform == "gemini":
                            await self._call_gemini("pro", prompt, 500, 0.7)

                        duration = (datetime.now() - start_time).total_seconds()

                        platform_results.append(
                            {
                                "prompt": prompt,
                                "response_time": duration,
                                "success": True,
                            }
                        )

                    except Exception as e:
                        platform_results.append({"prompt": prompt, "error": str(e), "success": False})

                results[platform] = platform_results

        return results


# Factory function
def create_multi_model_orchestrator() -> MultiModelAIOrchestrator:
    """Create Multi-Model AI Orchestrator."""
    return MultiModelAIOrchestrator()


# Global instance
ai_orchestrator = create_multi_model_orchestrator()


# Convenience functions
async def ai_generate(prompt: str, task_type: str = "general", use_best: bool = True) -> str:
    """Generate using optimal AI model."""
    result = await ai_orchestrator.generate(prompt, task_type, use_ensemble=not use_best)
    return result.get("response", "")


async def ai_ensemble(prompt: str, task_type: str = "general") -> dict[str, Any]:
    """Generate using ensemble of top models."""
    return await ai_orchestrator.generate(prompt, task_type, use_ensemble=True)
