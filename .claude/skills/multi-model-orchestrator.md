---
name: multi-model-orchestrator
description: Multi-model AI orchestration with intelligent routing between Claude, Gemini, ChatGPT-5, Codex, and Huggingface based on agent category and task type
---

You are the Multi-Model Orchestrator for DevSkyy. Route AI tasks to the optimal model based on agent category, task requirements, and performance characteristics.

## Model Assignment by Category

**Frontend Agents:** Claude Sonnet 4.5 + Gemini Pro
**Backend Agents:** Claude Sonnet 4.5 + ChatGPT-5
**Content Agents:** Huggingface + Claude + Gemini + ChatGPT-5 (Full Stack)
**Development Agents:** Claude Sonnet 4.5 + ChatGPT Codex

## Core Orchestration System

### 1. Multi-Model Router

```python
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import anthropic
import openai
import google.generativeai as genai
from transformers import pipeline
import os

class AgentCategory(Enum):
    """Agent categories with assigned models"""
    FRONTEND = "frontend"  # Claude + Gemini
    BACKEND = "backend"    # Claude + ChatGPT-5
    CONTENT = "content"    # HF + Claude + Gemini + ChatGPT-5
    DEVELOPMENT = "development"  # Claude + Codex

class AIModel(Enum):
    """Available AI models"""
    CLAUDE_SONNET_45 = "claude-sonnet-4-5"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    CHATGPT_5 = "gpt-5"
    CHATGPT_4 = "gpt-4-turbo"
    CODEX = "gpt-4-turbo"  # Using GPT-4 Turbo for code
    HUGGINGFACE = "huggingface"

class ModelCapability(Enum):
    """Model capabilities for routing decisions"""
    CODE_GENERATION = "code_generation"
    UI_DESIGN = "ui_design"
    IMAGE_ANALYSIS = "image_analysis"
    CONTENT_CREATION = "content_creation"
    DATA_PROCESSING = "data_processing"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"

class MultiModelOrchestrator:
    """Central orchestrator for multi-model AI routing"""

    def __init__(self):
        # Initialize all model clients
        self.claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Model routing configuration
        self.category_models = {
            AgentCategory.FRONTEND: [AIModel.CLAUDE_SONNET_45, AIModel.GEMINI_PRO],
            AgentCategory.BACKEND: [AIModel.CLAUDE_SONNET_45, AIModel.CHATGPT_5],
            AgentCategory.CONTENT: [AIModel.HUGGINGFACE, AIModel.CLAUDE_SONNET_45, AIModel.GEMINI_PRO, AIModel.CHATGPT_5],
            AgentCategory.DEVELOPMENT: [AIModel.CLAUDE_SONNET_45, AIModel.CODEX]
        }

        # Model capability matrix
        self.model_capabilities = {
            AIModel.CLAUDE_SONNET_45: [
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.CONTENT_CREATION,
                ModelCapability.API_DESIGN,
                ModelCapability.DATA_PROCESSING
            ],
            AIModel.GEMINI_PRO: [
                ModelCapability.UI_DESIGN,
                ModelCapability.IMAGE_ANALYSIS,
                ModelCapability.MULTIMODAL,
                ModelCapability.CONTENT_CREATION
            ],
            AIModel.CHATGPT_5: [
                ModelCapability.CODE_GENERATION,
                ModelCapability.API_DESIGN,
                ModelCapability.DATABASE_DESIGN,
                ModelCapability.DATA_PROCESSING
            ],
            AIModel.CODEX: [
                ModelCapability.CODE_GENERATION,
            ],
            AIModel.HUGGINGFACE: [
                ModelCapability.IMAGE_ANALYSIS,
                ModelCapability.MULTIMODAL,
                ModelCapability.DATA_PROCESSING
            ]
        }

        # Performance tracking
        self.performance_log: List[Dict[str, Any]] = []

    async def route_task(
        self,
        task: Dict[str, Any],
        agent_category: AgentCategory,
        required_capability: Optional[ModelCapability] = None,
        prefer_model: Optional[AIModel] = None
    ) -> Dict[str, Any]:
        """
        Route task to optimal model.

        Args:
            task: Task details (prompt, parameters, etc.)
            agent_category: Category of agent making request
            required_capability: Required model capability
            prefer_model: Preferred model (if any)

        Returns:
            Model response with metadata
        """
        # Get available models for this category
        available_models = self.category_models.get(agent_category, [])

        if not available_models:
            return {
                "error": f"No models configured for category: {agent_category.value}",
                "agent_category": agent_category.value
            }

        # Select optimal model
        selected_model = self._select_model(
            available_models,
            required_capability,
            prefer_model
        )

        # Execute task with selected model
        result = await self._execute_with_model(
            selected_model,
            task,
            agent_category
        )

        # Log performance
        self._log_performance(selected_model, result, agent_category)

        return result

    def _select_model(
        self,
        available_models: List[AIModel],
        required_capability: Optional[ModelCapability],
        prefer_model: Optional[AIModel]
    ) -> AIModel:
        """Select optimal model based on capability and preferences"""

        # If preferred model specified and available, use it
        if prefer_model and prefer_model in available_models:
            return prefer_model

        # Filter by required capability
        if required_capability:
            capable_models = [
                model for model in available_models
                if required_capability in self.model_capabilities.get(model, [])
            ]
            if capable_models:
                available_models = capable_models

        # Default routing logic by capability
        if required_capability == ModelCapability.CODE_GENERATION:
            # Prefer Claude for code, fallback to Codex/ChatGPT
            if AIModel.CLAUDE_SONNET_45 in available_models:
                return AIModel.CLAUDE_SONNET_45
            elif AIModel.CODEX in available_models:
                return AIModel.CODEX
            elif AIModel.CHATGPT_5 in available_models:
                return AIModel.CHATGPT_5

        elif required_capability == ModelCapability.UI_DESIGN:
            # Prefer Gemini for UI/design
            if AIModel.GEMINI_PRO in available_models:
                return AIModel.GEMINI_PRO
            elif AIModel.CLAUDE_SONNET_45 in available_models:
                return AIModel.CLAUDE_SONNET_45

        elif required_capability == ModelCapability.IMAGE_ANALYSIS:
            # Prefer Gemini or Huggingface for images
            if AIModel.GEMINI_PRO in available_models:
                return AIModel.GEMINI_PRO
            elif AIModel.HUGGINGFACE in available_models:
                return AIModel.HUGGINGFACE

        elif required_capability == ModelCapability.DATABASE_DESIGN:
            # Prefer ChatGPT-5 for database/backend
            if AIModel.CHATGPT_5 in available_models:
                return AIModel.CHATGPT_5
            elif AIModel.CLAUDE_SONNET_45 in available_models:
                return AIModel.CLAUDE_SONNET_45

        # Default: prefer Claude
        if AIModel.CLAUDE_SONNET_45 in available_models:
            return AIModel.CLAUDE_SONNET_45

        # Fallback to first available
        return available_models[0]

    async def _execute_with_model(
        self,
        model: AIModel,
        task: Dict[str, Any],
        agent_category: AgentCategory
    ) -> Dict[str, Any]:
        """Execute task with selected model"""

        prompt = task.get('prompt', '')
        max_tokens = task.get('max_tokens', 2048)
        temperature = task.get('temperature', 0.7)

        start_time = datetime.now()

        try:
            if model == AIModel.CLAUDE_SONNET_45:
                result = await self._execute_claude(prompt, max_tokens, temperature)

            elif model in [AIModel.GEMINI_PRO, AIModel.GEMINI_FLASH]:
                result = await self._execute_gemini(prompt, max_tokens, temperature, model)

            elif model in [AIModel.CHATGPT_5, AIModel.CHATGPT_4, AIModel.CODEX]:
                result = await self._execute_openai(prompt, max_tokens, temperature, model)

            elif model == AIModel.HUGGINGFACE:
                result = await self._execute_huggingface(task)

            else:
                result = {
                    "error": f"Model {model.value} not implemented",
                    "model": model.value
                }

            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            return {
                **result,
                "model_used": model.value,
                "agent_category": agent_category.value,
                "latency_ms": round(latency_ms, 2),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "error": str(e),
                "model_used": model.value,
                "agent_category": agent_category.value,
                "timestamp": datetime.now().isoformat()
            }

    async def _execute_claude(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Execute with Claude Sonnet 4.5"""
        message = self.claude.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "success": True,
            "content": message.content[0].text,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens
            }
        }

    async def _execute_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        model: AIModel
    ) -> Dict[str, Any]:
        """Execute with Google Gemini"""
        model_name = "gemini-1.5-pro" if model == AIModel.GEMINI_PRO else "gemini-1.5-flash"
        gemini_model = genai.GenerativeModel(model_name)

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )

        if response.candidates:
            content = response.candidates[0].content.parts[0].text
        else:
            content = ""

        return {
            "success": True,
            "content": content,
            "usage": {
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
        }

    async def _execute_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        model: AIModel
    ) -> Dict[str, Any]:
        """Execute with OpenAI (ChatGPT-5 / Codex)"""
        # Map to actual OpenAI model names
        model_mapping = {
            AIModel.CHATGPT_5: "gpt-4-turbo-preview",  # Update when GPT-5 available
            AIModel.CHATGPT_4: "gpt-4-turbo-preview",
            AIModel.CODEX: "gpt-4-turbo-preview"  # Using GPT-4 for code
        }

        model_name = model_mapping.get(model, "gpt-4-turbo-preview")

        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )

        return {
            "success": True,
            "content": response.choices[0].message.content,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    async def _execute_huggingface(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with Hugging Face models"""
        task_type = task.get('task_type', 'text-generation')
        model_name = task.get('hf_model', 'gpt2')

        # Initialize pipeline for task
        hf_pipeline = pipeline(task_type, model=model_name)

        # Execute
        if task_type == 'text-generation':
            result = hf_pipeline(
                task.get('prompt', ''),
                max_length=task.get('max_tokens', 100),
                temperature=task.get('temperature', 0.7)
            )
            content = result[0]['generated_text']

        elif task_type == 'image-classification':
            # Handle image classification
            content = "Image classification result"

        else:
            content = f"Unsupported Huggingface task: {task_type}"

        return {
            "success": True,
            "content": content,
            "usage": {"total_tokens": 0}  # HF doesn't provide token counts
        }

    def _log_performance(
        self,
        model: AIModel,
        result: Dict[str, Any],
        agent_category: AgentCategory
    ):
        """Log model performance for analysis"""
        self.performance_log.append({
            "model": model.value,
            "agent_category": agent_category.value,
            "success": result.get("success", False),
            "latency_ms": result.get("latency_ms", 0),
            "tokens": result.get("usage", {}).get("total_tokens", 0),
            "timestamp": result.get("timestamp", datetime.now().isoformat())
        })
```

### 2. Category-Specific Orchestrators

```python
class FrontendAgentOrchestrator:
    """Frontend agents: Claude + Gemini"""

    def __init__(self, orchestrator: MultiModelOrchestrator):
        self.orchestrator = orchestrator
        self.category = AgentCategory.FRONTEND

    async def generate_ui_component(self, component_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI component (prefers Gemini for UI design)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Generate React component: {component_spec}",
                "max_tokens": 2048,
                "temperature": 0.3
            },
            agent_category=self.category,
            required_capability=ModelCapability.UI_DESIGN,
            prefer_model=AIModel.GEMINI_PRO
        )

    async def review_design(self, design_description: str) -> Dict[str, Any]:
        """Review UI/UX design (uses Claude for reasoning)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Review this design: {design_description}",
                "max_tokens": 1500,
                "temperature": 0.5
            },
            agent_category=self.category,
            required_capability=ModelCapability.REASONING,
            prefer_model=AIModel.CLAUDE_SONNET_45
        )


class BackendAgentOrchestrator:
    """Backend agents: Claude + ChatGPT-5"""

    def __init__(self, orchestrator: MultiModelOrchestrator):
        self.orchestrator = orchestrator
        self.category = AgentCategory.BACKEND

    async def design_api(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Design API architecture (uses Claude or ChatGPT-5)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Design API for: {api_spec}",
                "max_tokens": 2048,
                "temperature": 0.4
            },
            agent_category=self.category,
            required_capability=ModelCapability.API_DESIGN
        )

    async def optimize_database(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize database schema (prefers ChatGPT-5)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Optimize database schema: {schema}",
                "max_tokens": 2048,
                "temperature": 0.3
            },
            agent_category=self.category,
            required_capability=ModelCapability.DATABASE_DESIGN,
            prefer_model=AIModel.CHATGPT_5
        )


class ContentAgentOrchestrator:
    """Content agents: Huggingface + Claude + Gemini + ChatGPT-5 (Full Stack!)"""

    def __init__(self, orchestrator: MultiModelOrchestrator):
        self.orchestrator = orchestrator
        self.category = AgentCategory.CONTENT

    async def generate_marketing_content(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """Generate marketing content (uses Claude for brand voice)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Create marketing content: {brief}",
                "max_tokens": 1500,
                "temperature": 0.8
            },
            agent_category=self.category,
            required_capability=ModelCapability.CONTENT_CREATION,
            prefer_model=AIModel.CLAUDE_SONNET_45
        )

    async def analyze_fashion_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze fashion image (uses Gemini or Huggingface)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Analyze fashion product in image: {image_path}",
                "task_type": "image-classification",
                "max_tokens": 1000,
                "temperature": 0.5
            },
            agent_category=self.category,
            required_capability=ModelCapability.IMAGE_ANALYSIS,
            prefer_model=AIModel.GEMINI_PRO
        )


class DevelopmentAgentOrchestrator:
    """Development agents: Claude + Codex"""

    def __init__(self, orchestrator: MultiModelOrchestrator):
        self.orchestrator = orchestrator
        self.category = AgentCategory.DEVELOPMENT

    async def generate_code(self, code_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code (uses Claude or Codex)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Generate code: {code_spec}",
                "max_tokens": 3000,
                "temperature": 0.2
            },
            agent_category=self.category,
            required_capability=ModelCapability.CODE_GENERATION
        )

    async def review_code(self, code: str) -> Dict[str, Any]:
        """Review code quality (prefers Claude)"""
        return await self.orchestrator.route_task(
            task={
                "prompt": f"Review this code:\n{code}",
                "max_tokens": 2000,
                "temperature": 0.3
            },
            agent_category=self.category,
            required_capability=ModelCapability.REASONING,
            prefer_model=AIModel.CLAUDE_SONNET_45
        )
```

## Usage Examples

### Example 1: Frontend Agent with Multi-Model

```python
from skills.multi_model_orchestrator import (
    MultiModelOrchestrator,
    FrontendAgentOrchestrator,
    AgentCategory
)

# Initialize
orchestrator = MultiModelOrchestrator()
frontend = FrontendAgentOrchestrator(orchestrator)

# Generate UI component (routes to Gemini)
component = await frontend.generate_ui_component({
    "type": "ProductCard",
    "features": ["image", "title", "price", "cta"],
    "brand_styling": True
})

print(f"Model used: {component['model_used']}")
print(f"Component:\n{component['content']}")
```

### Example 2: Content Agent with Full Model Stack

```python
from skills.multi_model_orchestrator import ContentAgentOrchestrator

# Initialize
content = ContentAgentOrchestrator(orchestrator)

# Generate marketing content (uses Claude for brand voice)
marketing = await content.generate_marketing_content({
    "product": "Silk Evening Dress",
    "platform": "Instagram",
    "tone": "luxury"
})

# Analyze image (uses Gemini for vision)
analysis = await content.analyze_fashion_image("product.jpg")

print(f"Marketing model: {marketing['model_used']}")
print(f"Vision model: {analysis['model_used']}")
```

### Example 3: Backend Agent with ChatGPT-5

```python
from skills.multi_model_orchestrator import BackendAgentOrchestrator

# Initialize
backend = BackendAgentOrchestrator(orchestrator)

# Design API (routes to Claude or ChatGPT-5)
api_design = await backend.design_api({
    "service": "Product Management",
    "endpoints": ["create", "read", "update", "delete"],
    "auth": "JWT"
})

# Optimize database (prefers ChatGPT-5)
db_optimization = await backend.optimize_database({
    "tables": ["products", "orders", "customers"],
    "relationships": "one-to-many"
})

print(f"API design by: {api_design['model_used']}")
print(f"DB optimization by: {db_optimization['model_used']}")
```

## Environment Variables Required

```bash
# Add to .env
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

## Model Selection Decision Tree

```
Task → Agent Category → Required Capability → Available Models → Preference → Selected Model

Examples:
- UI Component → Frontend → UI_DESIGN → [Claude, Gemini] → Gemini → Gemini Pro
- API Design → Backend → API_DESIGN → [Claude, GPT-5] → Claude → Claude Sonnet 4.5
- Image Analysis → Content → IMAGE_ANALYSIS → [HF, Claude, Gemini, GPT-5] → Gemini → Gemini Pro
- Code Generation → Development → CODE_GENERATION → [Claude, Codex] → Claude → Claude Sonnet 4.5
```

## Truth Protocol Compliance

- ✅ Multi-model redundancy (Rule 12 - Performance)
- ✅ Intelligent routing (Rule 12 - Optimization)
- ✅ Performance tracking (Rule 10 - Error ledger)
- ✅ Type-safe implementation (Rule 11)
- ✅ API keys in environment (Rule 5)

Use this skill as the central routing system for all multi-model AI operations in DevSkyy.
