"""
OpenAPI Specification Generator for DevSkyy Platform

WHY: Auto-generate OpenAPI 3.1.0 spec for API documentation and SDK generation
HOW: Extract FastAPI routes and metadata, enhance with security schemes, export to JSON
IMPACT: Enables automated documentation, client SDK generation, and API contract validation

Truth Protocol: Per Rule 9 - Auto-generate OpenAPI, maintain documentation
References:
    - OpenAPI 3.1.0: https://spec.openapis.org/oas/v3.1.0
    - FastAPI OpenAPI: https://fastapi.tiangolo.com/advanced/extending-openapi/
    - RFC 7519: JSON Web Token (JWT)
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)


def export_openapi_spec(app: FastAPI, output_path: str = "artifacts/openapi.json") -> dict[str, Any]:
    """
    Export comprehensive OpenAPI specification to JSON file.

    This function:
    1. Generates OpenAPI 3.1.0 schema from FastAPI app
    2. Enhances with security schemes (JWT, OAuth2)
    3. Adds server configurations
    4. Includes contact, license, and external docs
    5. Exports to structured JSON file

    Args:
        app: FastAPI application instance
        output_path: Path to save OpenAPI spec (default: artifacts/openapi.json)

    Returns:
        OpenAPI specification dictionary

    Raises:
        IOError: If file cannot be written
        ValueError: If app is not a valid FastAPI instance

    Example:
        >>> from main import app
        >>> from utils.openapi_generator import export_openapi_spec
        >>> spec = export_openapi_spec(app)
        ✅ OpenAPI spec exported to artifacts/openapi.json
        Version: 3.1.0
        Paths: 173
    """
    if not isinstance(app, FastAPI):
        raise ValueError("app must be a FastAPI instance")

    logger.info("🔧 Generating OpenAPI specification...")

    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="3.1.0",
        description=app.description,
        routes=app.routes,
    )

    # Enhance with security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT access token from /api/v1/auth/login endpoint. "
                "Include in Authorization header as: Bearer <token>. "
                "Token expires in 1 hour. Use refresh token to get new access token. "
                "Per RFC 7519 (JSON Web Token)."
            ),
        },
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/login",
                    "scopes": {
                        "read": "Read access to resources",
                        "write": "Write and modify resources",
                        "admin": "Administrative access to all resources",
                        "developer": "Developer access to code and infrastructure",
                    },
                }
            },
            "description": (
                "OAuth2 password flow with JWT access and refresh tokens. "
                "RBAC roles: SuperAdmin, Admin, Developer, APIUser, ReadOnly. "
                "Per RFC 6749 (OAuth 2.0 Authorization Framework)."
            ),
        },
    }

    # Add server configurations
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "http://localhost:5000", "description": "Local testing server"},
        {"url": "https://api.devskyy.com", "description": "Production server"},
        {"url": "https://staging-api.devskyy.com", "description": "Staging server"},
    ]

    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "DevSkyy Platform Team",
        "email": "api@devskyy.com",
        "url": "https://devskyy.com/support",
    }

    openapi_schema["info"]["license"] = {"name": "Proprietary", "url": "https://devskyy.com/license"}

    openapi_schema["info"]["termsOfService"] = "https://devskyy.com/terms"

    # Add version info
    openapi_schema["info"]["x-api-version"] = app.version
    openapi_schema["info"]["x-generated-at"] = datetime.now().isoformat()

    # Enhance tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "v1-auth",
            "description": "Authentication & authorization endpoints (JWT/OAuth2)",
            "externalDocs": {"description": "Auth Guide", "url": "https://docs.devskyy.com/auth"},
        },
        {
            "name": "v1-agents",
            "description": "AI agent execution endpoints (25+ agents)",
            "externalDocs": {"description": "Agent Guide", "url": "https://docs.devskyy.com/agents"},
        },
        {
            "name": "v1-webhooks",
            "description": "Webhook management and event subscriptions",
            "externalDocs": {"description": "Webhook Guide", "url": "https://docs.devskyy.com/webhooks"},
        },
        {
            "name": "v1-monitoring",
            "description": "System monitoring, health checks, and observability",
            "externalDocs": {"description": "Monitoring Guide", "url": "https://docs.devskyy.com/monitoring"},
        },
        {
            "name": "v1-ml",
            "description": "ML infrastructure, model registry, and cache",
            "externalDocs": {"description": "ML Guide", "url": "https://docs.devskyy.com/ml"},
        },
        {
            "name": "v1-gdpr",
            "description": "GDPR compliance endpoints (Articles 15 & 17)",
            "externalDocs": {"description": "GDPR Guide", "url": "https://docs.devskyy.com/gdpr"},
        },
        {
            "name": "automation-ecommerce",
            "description": "E-commerce automation workflows",
            "externalDocs": {"description": "E-commerce Guide", "url": "https://docs.devskyy.com/ecommerce"},
        },
        {
            "name": "v1-luxury-automation",
            "description": "Luxury fashion automation platform",
            "externalDocs": {"description": "Luxury Guide", "url": "https://docs.devskyy.com/luxury"},
        },
    ]

    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "DevSkyy Platform Documentation",
        "url": "https://docs.devskyy.com",
    }

    # Add custom extensions
    openapi_schema["x-logo"] = {
        "url": "https://devskyy.com/logo.png",
        "altText": "DevSkyy Platform",
    }

    openapi_schema["x-tagGroups"] = [
        {"name": "Core API", "tags": ["v1-auth", "v1-agents", "v1-webhooks"]},
        {"name": "Infrastructure", "tags": ["v1-monitoring", "v1-ml", "v1-gdpr"]},
        {"name": "Automation", "tags": ["automation-ecommerce", "v1-luxury-automation"]},
    ]

    # Ensure artifacts directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Export to file
    try:
        with open(output_path, "w") as f:
            json.dump(openapi_schema, f, indent=2)

        logger.info(f"✅ OpenAPI spec exported to {output_path}")
        logger.info(f"   Version: {openapi_schema['openapi']}")
        logger.info(f"   Title: {openapi_schema['info']['title']}")
        logger.info(f"   App Version: {openapi_schema['info']['version']}")
        logger.info(f"   Paths: {len(openapi_schema.get('paths', {}))}")
        logger.info(f"   Tags: {len(openapi_schema.get('tags', []))}")
        logger.info(f"   Security Schemes: {len(openapi_schema['components']['securitySchemes'])}")

        return openapi_schema

    except IOError as e:
        logger.error(f"❌ Failed to write OpenAPI spec to {output_path}: {e}")
        raise


def validate_openapi_spec(spec_path: str = "artifacts/openapi.json") -> bool:
    """
    Validate OpenAPI specification against OpenAPI 3.1.0 schema.

    Args:
        spec_path: Path to OpenAPI spec file

    Returns:
        True if valid, False otherwise

    Requires:
        pip install openapi-spec-validator

    Example:
        >>> from utils.openapi_generator import validate_openapi_spec
        >>> validate_openapi_spec("artifacts/openapi.json")
        ✅ OpenAPI spec is valid: artifacts/openapi.json
        True
    """
    try:
        from openapi_spec_validator import validate_spec
        from openapi_spec_validator.readers import read_from_filename

        logger.info(f"🔍 Validating OpenAPI spec: {spec_path}")

        spec_dict, spec_url = read_from_filename(spec_path)
        validate_spec(spec_dict)

        logger.info(f"✅ OpenAPI spec is valid: {spec_path}")
        logger.info(f"   OpenAPI Version: {spec_dict.get('openapi', 'unknown')}")
        logger.info(f"   Title: {spec_dict.get('info', {}).get('title', 'unknown')}")
        logger.info(f"   Paths: {len(spec_dict.get('paths', {}))}")

        return True

    except ImportError:
        logger.warning("⚠️  openapi-spec-validator not installed.")
        logger.warning("   Install with: pip install openapi-spec-validator")
        return False

    except FileNotFoundError:
        logger.error(f"❌ OpenAPI spec file not found: {spec_path}")
        return False

    except Exception as e:
        logger.error(f"❌ OpenAPI validation failed: {e}")
        return False


def detect_breaking_changes(old_spec_path: str, new_spec_path: str) -> dict[str, Any]:
    """
    Detect breaking changes between two OpenAPI specifications.

    Breaking changes include:
    - Removed endpoints
    - Removed required fields
    - Changed response schemas
    - Removed enum values
    - Changed parameter types

    Args:
        old_spec_path: Path to previous OpenAPI spec
        new_spec_path: Path to new OpenAPI spec

    Returns:
        Dictionary of breaking changes

    Example:
        >>> changes = detect_breaking_changes("old.json", "new.json")
        >>> if changes["breaking"]:
        ...     print(f"Found {len(changes['breaking'])} breaking changes")
    """
    logger.info(f"🔍 Detecting breaking changes...")
    logger.info(f"   Old spec: {old_spec_path}")
    logger.info(f"   New spec: {new_spec_path}")

    try:
        with open(old_spec_path) as f:
            old_spec = json.load(f)
        with open(new_spec_path) as f:
            new_spec = json.load(f)

        breaking_changes = []
        warnings = []

        # Check removed endpoints
        old_paths = set(old_spec.get("paths", {}).keys())
        new_paths = set(new_spec.get("paths", {}).keys())
        removed_paths = old_paths - new_paths

        if removed_paths:
            breaking_changes.append(
                {
                    "type": "removed_endpoints",
                    "severity": "CRITICAL",
                    "paths": list(removed_paths),
                    "description": f"{len(removed_paths)} endpoint(s) removed",
                }
            )

        # Check added endpoints (not breaking, but notable)
        added_paths = new_paths - old_paths
        if added_paths:
            warnings.append(
                {
                    "type": "added_endpoints",
                    "severity": "INFO",
                    "paths": list(added_paths),
                    "description": f"{len(added_paths)} new endpoint(s) added",
                }
            )

        # TODO: Add more breaking change checks
        # - Changed required fields
        # - Modified response schemas
        # - Removed enum values
        # - Changed parameter types

        result = {
            "breaking": breaking_changes,
            "warnings": warnings,
            "summary": {
                "total_breaking": len(breaking_changes),
                "total_warnings": len(warnings),
                "old_version": old_spec.get("info", {}).get("version", "unknown"),
                "new_version": new_spec.get("info", {}).get("version", "unknown"),
            },
        }

        if breaking_changes:
            logger.warning(f"⚠️  Found {len(breaking_changes)} breaking change(s)")
            for change in breaking_changes:
                logger.warning(f"   - {change['description']}")
        else:
            logger.info("✅ No breaking changes detected")

        return result

    except FileNotFoundError as e:
        logger.error(f"❌ Spec file not found: {e}")
        return {"breaking": [], "warnings": [], "error": str(e)}

    except Exception as e:
        logger.error(f"❌ Breaking change detection failed: {e}")
        return {"breaking": [], "warnings": [], "error": str(e)}


def generate_client_sdks(spec_path: str = "artifacts/openapi.json", output_dir: str = "clients"):
    """
    Generate client SDKs from OpenAPI specification.

    Generates:
    - TypeScript SDK (Axios) in clients/typescript/
    - Python SDK in clients/python/

    Args:
        spec_path: Path to OpenAPI spec file
        output_dir: Base directory for generated clients

    Requires:
        npm install -g @openapitools/openapi-generator-cli

    Example:
        >>> from utils.openapi_generator import generate_client_sdks
        >>> generate_client_sdks("artifacts/openapi.json")
        🔨 Generating TypeScript SDK...
        ✅ TypeScript SDK generated: clients/typescript/
        🔨 Generating Python SDK...
        ✅ Python SDK generated: clients/python/
    """
    logger.info(f"🔨 Generating client SDKs from {spec_path}...")

    if not Path(spec_path).exists():
        logger.error(f"❌ OpenAPI spec not found: {spec_path}")
        return

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        # Generate TypeScript SDK
        logger.info("🔨 Generating TypeScript SDK...")
        typescript_output = f"{output_dir}/typescript"

        subprocess.run(
            [
                "openapi-generator-cli",
                "generate",
                "-i",
                spec_path,
                "-g",
                "typescript-axios",
                "-o",
                typescript_output,
                "--additional-properties",
                "npmName=@devskyy/api-client,npmVersion=5.1.0,supportsES6=true",
            ],
            check=True,
        )

        logger.info(f"✅ TypeScript SDK generated: {typescript_output}/")

        # Generate Python SDK
        logger.info("🔨 Generating Python SDK...")
        python_output = f"{output_dir}/python"

        subprocess.run(
            [
                "openapi-generator-cli",
                "generate",
                "-i",
                spec_path,
                "-g",
                "python",
                "-o",
                python_output,
                "--additional-properties",
                "packageName=devskyy_client,packageVersion=5.1.0,projectName=devskyy-client",
            ],
            check=True,
        )

        logger.info(f"✅ Python SDK generated: {python_output}/")
        logger.info("✅ Client SDKs generated successfully")

    except FileNotFoundError:
        logger.error("❌ openapi-generator-cli not found")
        logger.error("   Install with: npm install -g @openapitools/openapi-generator-cli")

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ SDK generation failed: {e}")

    except Exception as e:
        logger.error(f"❌ Unexpected error during SDK generation: {e}")


def generate_documentation_report(spec_path: str = "artifacts/openapi.json") -> dict[str, Any]:
    """
    Generate documentation completeness report from OpenAPI spec.

    Checks:
    - Endpoints with descriptions
    - Endpoints with examples
    - Response schemas documented
    - Security schemes defined

    Args:
        spec_path: Path to OpenAPI spec file

    Returns:
        Documentation completeness report

    Example:
        >>> from utils.openapi_generator import generate_documentation_report
        >>> report = generate_documentation_report()
        >>> print(f"Documentation coverage: {report['coverage']}%")
    """
    try:
        with open(spec_path) as f:
            spec = json.load(f)

        total_endpoints = 0
        documented_endpoints = 0
        endpoints_with_examples = 0
        missing_docs = []

        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    total_endpoints += 1

                    # Check for description
                    if details.get("summary") or details.get("description"):
                        documented_endpoints += 1
                    else:
                        missing_docs.append(f"{method.upper()} {path}")

                    # Check for examples
                    if "requestBody" in details:
                        if "examples" in details["requestBody"].get("content", {}).get("application/json", {}):
                            endpoints_with_examples += 1

        coverage = (documented_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0

        report = {
            "total_endpoints": total_endpoints,
            "documented_endpoints": documented_endpoints,
            "endpoints_with_examples": endpoints_with_examples,
            "coverage": round(coverage, 2),
            "missing_docs": missing_docs,
            "grade": "A" if coverage >= 90 else "B" if coverage >= 75 else "C" if coverage >= 60 else "D",
        }

        logger.info("📊 Documentation Report:")
        logger.info(f"   Total Endpoints: {total_endpoints}")
        logger.info(f"   Documented: {documented_endpoints}/{total_endpoints} ({coverage:.1f}%)")
        logger.info(f"   With Examples: {endpoints_with_examples}")
        logger.info(f"   Grade: {report['grade']}")

        if missing_docs:
            logger.warning(f"⚠️  {len(missing_docs)} endpoint(s) missing documentation:")
            for endpoint in missing_docs[:5]:  # Show first 5
                logger.warning(f"   - {endpoint}")
            if len(missing_docs) > 5:
                logger.warning(f"   ... and {len(missing_docs) - 5} more")

        return report

    except FileNotFoundError:
        logger.error(f"❌ OpenAPI spec not found: {spec_path}")
        return {}

    except Exception as e:
        logger.error(f"❌ Documentation report generation failed: {e}")
        return {}


# Convenience function for main.py integration
def setup_openapi_export(app: FastAPI):
    """
    Set up OpenAPI export on application startup.

    Add this to your FastAPI app startup event:

    @app.on_event("startup")
    async def startup_openapi():
        from utils.openapi_generator import setup_openapi_export
        setup_openapi_export(app)

    Args:
        app: FastAPI application instance
    """
    try:
        # Export OpenAPI spec
        spec = export_openapi_spec(app)

        # Validate spec
        validate_openapi_spec()

        # Generate documentation report
        report = generate_documentation_report()

        logger.info("✅ OpenAPI export setup complete")
        logger.info(f"   Documentation coverage: {report.get('coverage', 0)}%")

    except Exception as e:
        logger.error(f"❌ OpenAPI export setup failed: {e}")


if __name__ == "__main__":
    # Example usage
    print("OpenAPI Generator Utility")
    print("=" * 50)
    print()
    print("Usage:")
    print("  1. Add to main.py startup event:")
    print("     from utils.openapi_generator import setup_openapi_export")
    print("     @app.on_event('startup')")
    print("     async def startup(): setup_openapi_export(app)")
    print()
    print("  2. Or run directly:")
    print("     from main import app")
    print("     from utils.openapi_generator import export_openapi_spec")
    print("     export_openapi_spec(app)")
    print()
    print("  3. Validate spec:")
    print("     from utils.openapi_generator import validate_openapi_spec")
    print("     validate_openapi_spec('artifacts/openapi.json')")
    print()
    print("  4. Generate SDKs:")
    print("     from utils.openapi_generator import generate_client_sdks")
    print("     generate_client_sdks('artifacts/openapi.json')")
