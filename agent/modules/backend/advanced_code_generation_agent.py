from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from string import Template as StringTemplate
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, validator

try:  # Optional dependency for LLM-backed generation
    import openai  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - allow running without OpenAI SDK
    openai = None  # type: ignore[assignment]

from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/codegen", tags=["advanced-code-generation"])

SUPPORTED_ARTIFACTS = {"react_component", "fastapi_endpoint", "wordpress_plugin"}


@dataclass
class TemplateDefinition:
    """Container for code template definitions."""

    name: str
    description: str
    body: StringTemplate


class CodeGenerationRequest(BaseModel):
    """Request model for code generation operations."""

    artifact_type: str = Field(
        ..., description="Type of artifact to generate (react_component, fastapi_endpoint, wordpress_plugin).",
    )
    name: str = Field(..., description="Primary identifier for the generated artifact.")
    requirements: Dict[str, Any] = Field(default_factory=dict)
    use_model: bool = Field(
        default=False,
        description="When True and an OpenAI key is available, the agent will attempt to enrich the template using the model.",
    )

    @validator("artifact_type")
    def validate_artifact(cls, value: str) -> str:  # noqa: D417 - pydantic validator
        lowered = value.lower().strip()
        if lowered not in SUPPORTED_ARTIFACTS:
            raise ValueError(
                f"Unsupported artifact_type '{value}'. Supported types: {', '.join(sorted(SUPPORTED_ARTIFACTS))}."
            )
        return lowered


class CodeGenerationResponse(BaseModel):
    """Standard response payload for code generation."""

    artifact_type: str
    name: str
    content: Dict[str, Any]
    used_model: bool
    summary: str


class AdvancedCodeGenerationAgent:
    """Enterprise-focused code generation helper with optional LLM enrichment."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._initialise_openai()
        self.templates = self._build_templates()

    def _initialise_openai(self) -> None:
        if not openai:
            logger.debug("OpenAI SDK not installed; operating in template-only mode.")
            return
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.debug("OpenAI API key not provided; skipping model-backed generation.")

    def _build_templates(self) -> Dict[str, TemplateDefinition]:
        return {
            "react_component": TemplateDefinition(
                name="React Component",
                description="Luxury-themed React functional component with Emotion styling.",
                body=StringTemplate(
                    """import React from 'react';\nimport PropTypes from 'prop-types';\n\nexport const ${component_name} = (${props}) => {{\n  return (\n    <section className=\"luxury-container\">\n      <header>\n        <h2>${heading}</h2>\n        <p>${tagline}</p>\n      </header>\n      <div className=\"content\">${content}</div>\n    </section>\n  );\n}};\n\n${component_name}.propTypes = ${prop_types};\n"""
                ),
            ),
            "fastapi_endpoint": TemplateDefinition(
                name="FastAPI Endpoint",
                description="Secure FastAPI endpoint with request/response models and dependency injection.",
                body=StringTemplate(
                    """from fastapi import APIRouter, Depends, HTTPException, status\nfrom pydantic import BaseModel\n\nrouter = APIRouter(prefix='${route}', tags=['${tag}'])\n\nclass ${name}Request(BaseModel):\n    ${request_fields}\n\nclass ${name}Response(BaseModel):\n    ${response_fields}\n\n@router.${method}("", response_model=${name}Response, status_code=status.HTTP_200_OK)\nasync def ${function_name}(payload: ${name}Request, current_user=Depends(${auth_dependency})):\n    \"\"\"${doc}\"\"\"\n    if not current_user:\n        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')\n    return ${success_payload}\n"""
                ),
            ),
            "wordpress_plugin": TemplateDefinition(
                name="WordPress Plugin",
                description="Starter WordPress plugin with luxury branding hooks.",
                body=StringTemplate(
                    """<?php\n/**\n * Plugin Name: ${name}\n * Description: ${description}\n * Version: 1.0.0\n */\n\nif (!defined('ABSPATH')) {{\n    exit;\n}}\n\nfunction ${slug}_register_hooks() {{\n    add_action('init', '${slug}_register_post_type');\n}}\n\nfunction ${slug}_register_post_type() {{\n    register_post_type('${slug}', array(\n        'label' => '${label}',\n        'public' => true,\n        'supports' => array('title', 'editor', 'thumbnail')\n    ));\n}}\n\nregister_activation_hook(__FILE__, '${slug}_register_hooks');\n"""
                ),
            ),
        }

    async def generate(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        artifact = request.artifact_type
        template = self.templates[artifact]
        logger.info("Generating %s '%s' (model=%s)", artifact, request.name, request.use_model)

        rendered = self._render_template(artifact, request)
        enriched = await self._maybe_enrich(rendered, request) if request.use_model else rendered

        return CodeGenerationResponse(
            artifact_type=artifact,
            name=request.name,
            content=enriched,
            used_model=request.use_model and bool(self.api_key and openai),
            summary=self._summarise(artifact, request.requirements),
        )

    def _render_template(self, artifact: str, request: CodeGenerationRequest) -> Dict[str, Any]:
        requirements = request.requirements
        if artifact == "react_component":
            react_template = self.templates[artifact]
            return {
                "component": react_template.body.safe_substitute(
                    component_name=request.name,
                    props=requirements.get("props", "props"),
                    heading=requirements.get("heading", "Welcome to Skyy Rose"),
                    tagline=requirements.get("tagline", "Timeless luxury for modern icons"),
                    content=requirements.get("content", "{/* TODO: add content blocks */}"),
                    prop_types=requirements.get("prop_types", "{}"),
                )
            }

        if artifact == "fastapi_endpoint":
            endpoint_template = self.templates[artifact]
            defaults = {
                "route": requirements.get("route", f"/api/{request.name.lower()}"),
                "tag": requirements.get("tag", request.name.lower()),
                "request_fields": requirements.get("request_fields", "value: str"),
                "response_fields": requirements.get("response_fields", "message: str"),
                "method": requirements.get("method", "post").lower(),
                "function_name": requirements.get("function_name", request.name.lower()),
                "auth_dependency": requirements.get("auth_dependency", "get_current_user"),
                "doc": requirements.get("docstring", "Endpoint generated by AdvancedCodeGenerationAgent"),
                "success_payload": requirements.get("success_payload", "{'message': 'success'}"),
            }
            return {"endpoint": endpoint_template.body.safe_substitute(name=request.name, **defaults)}

        if artifact == "wordpress_plugin":
            plugin_template = self.templates[artifact]
            slug = requirements.get("slug", request.name.lower().replace(" ", "_"))
            return {
                "plugin": plugin_template.body.safe_substitute(
                    name=request.name,
                    description=requirements.get("description", "Luxury automation plugin"),
                    slug=slug,
                    label=requirements.get("label", request.name),
                )
            }

        raise ValueError(f"Unsupported artifact type: {artifact}")

    async def _maybe_enrich(
        self, generated: Dict[str, Any], request: CodeGenerationRequest
    ) -> Dict[str, Any]:
        if not (openai and self.api_key):
            return generated

        prompt = (
            "Improve the following {artifact} for a luxury fashion brand.\n"
            "Requirements: {requirements}\n"
            "Content:\n{content}\n"
        ).format(
            artifact=request.artifact_type.replace("_", " "),
            requirements=request.requirements,
            content="\n".join(f"## {k}\n{v}" for k, v in generated.items()),
        )

        try:
            logger.debug("Sending enrichment prompt to OpenAI")
            response = await self._call_openai(prompt)
            enriched = response or generated
        except Exception as exc:  # pragma: no cover - best effort enrichment
            logger.warning("Model enrichment failed: %s", exc)
            enriched = generated
        return enriched

    async def _call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not (openai and self.api_key):
            return None

        completion = await openai.Completion.acreate(  # type: ignore[attr-defined]
            engine="gpt-4-turbo",
            prompt=prompt,
            max_tokens=800,
            temperature=0.3,
        )
        text = completion.choices[0].text.strip()
        return {"generated": text}

    def _summarise(self, artifact: str, requirements: Dict[str, Any]) -> str:
        highlights = ", ".join(sorted(requirements.keys())) or "default configuration"
        return f"Generated {artifact.replace('_', ' ')} covering: {highlights}."


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_artifact(
    payload: CodeGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CodeGenerationResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    agent = AdvancedCodeGenerationAgent()
    response = await agent.generate(payload)
    return CodeGenerationResponse(**jsonable_encoder(response))
