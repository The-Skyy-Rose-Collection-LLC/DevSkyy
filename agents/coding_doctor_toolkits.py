"""
Coding Doctor Advanced Toolkits
================================

Specialized toolkits for advanced code analysis:
- ThreeJSToolkit: Three.js, WebGL, WebXR, 3D infrastructure
- LLMBestPracticesKB: Top-tier LLM coding patterns and techniques
- FrontendToolkit: React, Next.js, TypeScript analysis
- APIToolkit: REST, GraphQL, WebSocket analysis
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Shared Types
# =============================================================================


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    THREEJS = "threejs"
    WEBGL = "webgl"
    WEBXR = "webxr"
    FRONTEND = "frontend"
    REACT = "react"
    TYPESCRIPT = "typescript"
    API = "api"
    BEST_PRACTICE = "best_practice"


@dataclass
class CodeIssue:
    """Code issue found during analysis"""
    file_path: str
    line_number: int | None
    category: IssueCategory
    severity: SeverityLevel
    title: str
    description: str
    suggestion: str | None = None
    code_snippet: str | None = None
    reference_url: str | None = None
    auto_fixable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "reference_url": self.reference_url,
        }


# =============================================================================
# Three.js & 3D Infrastructure Toolkit
# =============================================================================


class ThreeJSToolkit:
    """
    Advanced Three.js and 3D infrastructure analysis toolkit.

    Analyzes:
    - Three.js scene optimization
    - WebGL shader best practices
    - Memory leak detection
    - Animation performance
    - Asset loading optimization
    - WebXR/AR implementation
    - Model format validation (GLTF, GLB, FBX)
    - Texture optimization
    - LOD (Level of Detail) implementation
    """

    # Three.js performance anti-patterns
    PERFORMANCE_PATTERNS = {
        r"new THREE\.(Mesh|Object3D|Group)\(": {
            "title": "Object creation in render loop",
            "check_context": "requestAnimationFrame|render",
            "severity": SeverityLevel.HIGH,
            "suggestion": "Create objects outside render loop, reuse with object pooling",
        },
        r"geometry\.dispose\(\)|material\.dispose\(\)|texture\.dispose\(\)": {
            "title": "Resource disposal",
            "check_positive": True,
            "severity": SeverityLevel.INFO,
            "suggestion": "Good practice: disposing resources prevents memory leaks",
        },
        r"renderer\.setSize\(": {
            "title": "Renderer resize",
            "check_context": "resize|window",
            "severity": SeverityLevel.LOW,
            "suggestion": "Ensure setSize is called with updateStyle=false for performance",
        },
    }

    # WebGL shader patterns
    SHADER_PATTERNS = {
        r"precision\s+(highp|mediump|lowp)": {
            "title": "Shader precision",
            "severity": SeverityLevel.INFO,
            "suggestion": "Use mediump for mobile, highp for desktop when needed",
        },
        r"for\s*\([^)]*\)\s*\{": {
            "title": "Loop in shader",
            "check_context": "fragmentShader|vertexShader|glsl",
            "severity": SeverityLevel.MEDIUM,
            "suggestion": "Unroll small loops, use step/mix for conditionals",
        },
        r"texture2D\s*\(": {
            "title": "Texture sampling",
            "severity": SeverityLevel.INFO,
            "suggestion": "Minimize texture samples, use texture atlases",
        },
    }

    # Memory leak patterns
    MEMORY_PATTERNS = {
        r"addEventListener\(": {
            "title": "Event listener without cleanup",
            "check_missing": "removeEventListener",
            "severity": SeverityLevel.HIGH,
            "suggestion": "Always remove event listeners in cleanup/dispose",
        },
        r"scene\.add\(": {
            "title": "Scene objects",
            "check_missing": "scene.remove",
            "severity": SeverityLevel.MEDIUM,
            "suggestion": "Remove objects from scene when not needed",
        },
        r"new THREE\.(?:Texture|CubeTexture|VideoTexture)\(": {
            "title": "Texture creation",
            "check_missing": "dispose",
            "severity": SeverityLevel.HIGH,
            "suggestion": "Dispose textures when no longer needed",
        },
    }

    # Animation patterns
    ANIMATION_PATTERNS = {
        r"requestAnimationFrame\(": {
            "title": "Animation frame",
            "severity": SeverityLevel.INFO,
            "suggestion": "Use cancelAnimationFrame for cleanup",
        },
        r"THREE\.Clock\(\)": {
            "title": "Clock usage",
            "severity": SeverityLevel.INFO,
            "suggestion": "Good: Using Clock for delta time",
        },
        r"setInterval|setTimeout": {
            "title": "Timer in 3D context",
            "severity": SeverityLevel.MEDIUM,
            "suggestion": "Use requestAnimationFrame for 3D animations, not timers",
        },
    }

    # WebXR patterns
    WEBXR_PATTERNS = {
        r"xr\.isSessionSupported": {
            "title": "WebXR support check",
            "severity": SeverityLevel.INFO,
            "suggestion": "Good: Checking XR support before use",
        },
        r"renderer\.xr\.enabled": {
            "title": "XR enabled",
            "severity": SeverityLevel.INFO,
            "suggestion": "Ensure XR is properly configured",
        },
        r"XRSession": {
            "title": "XR Session handling",
            "check_context": "end|select",
            "severity": SeverityLevel.MEDIUM,
            "suggestion": "Handle session end events properly",
        },
    }

    # Best practice patterns
    BEST_PRACTICES = {
        r"BufferGeometry": {
            "title": "BufferGeometry usage",
            "severity": SeverityLevel.INFO,
            "suggestion": "Good: BufferGeometry is more performant than Geometry",
        },
        r"InstancedMesh|InstancedBufferGeometry": {
            "title": "Instancing",
            "severity": SeverityLevel.INFO,
            "suggestion": "Excellent: Instancing for repeated objects",
        },
        r"GLTFLoader|DRACOLoader": {
            "title": "Optimized model loading",
            "severity": SeverityLevel.INFO,
            "suggestion": "Good: Using GLTF/DRACO for compressed models",
        },
        r"OrbitControls|TrackballControls": {
            "title": "Camera controls",
            "severity": SeverityLevel.INFO,
            "suggestion": "Ensure controls are disposed on cleanup",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for Three.js/3D issues"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Skip non-relevant files
            if not any(ext in rel_path for ext in [".ts", ".tsx", ".js", ".jsx", ".glsl"]):
                return issues

            # Check if this is a Three.js file
            is_threejs_file = "three" in content.lower() or "THREE" in content

            if is_threejs_file:
                issues.extend(self._check_patterns(content, lines, rel_path, self.PERFORMANCE_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.MEMORY_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.ANIMATION_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.BEST_PRACTICES))

            # Check for WebXR
            if "xr" in content.lower() or "webxr" in content.lower():
                issues.extend(self._check_patterns(content, lines, rel_path, self.WEBXR_PATTERNS))

            # Check for shaders
            if "shader" in content.lower() or "glsl" in rel_path:
                issues.extend(self._check_patterns(content, lines, rel_path, self.SHADER_PATTERNS))

            # Specific Three.js checks
            issues.extend(self._check_threejs_specific(content, lines, rel_path))

        except Exception as e:
            logger.error(f"Three.js analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
        patterns: dict,
    ) -> list[CodeIssue]:
        """Check content against patterns"""
        issues = []

        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content))

            for match in matches:
                # Find line number
                line_num = content[:match.start()].count("\n") + 1

                # Check context if needed
                if "check_context" in config:
                    context_start = max(0, match.start() - 500)
                    context_end = min(len(content), match.end() + 500)
                    context = content[context_start:context_end]

                    if not re.search(config["check_context"], context, re.IGNORECASE):
                        continue

                # Check for positive pattern (good practice)
                if config.get("check_positive"):
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=line_num,
                        category=IssueCategory.THREEJS,
                        severity=SeverityLevel.INFO,
                        title=f"✓ {config['title']}",
                        description="Good practice detected",
                        suggestion=config.get("suggestion"),
                    ))
                    continue

                # Check for missing pattern
                if "check_missing" in config:
                    if config["check_missing"] not in content:
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=line_num,
                            category=IssueCategory.THREEJS,
                            severity=config["severity"],
                            title=config["title"],
                            description=f"Missing: {config['check_missing']}",
                            suggestion=config.get("suggestion"),
                        ))
                else:
                    # Regular issue
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=line_num,
                        category=IssueCategory.THREEJS,
                        severity=config["severity"],
                        title=config["title"],
                        description=match.group(0)[:50],
                        suggestion=config.get("suggestion"),
                    ))

        return issues

    def _check_threejs_specific(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
    ) -> list[CodeIssue]:
        """Three.js specific checks"""
        issues = []

        # Check for scene cleanup
        if "new THREE.Scene()" in content and "dispose" not in content:
            issues.append(CodeIssue(
                file_path=rel_path,
                line_number=None,
                category=IssueCategory.THREEJS,
                severity=SeverityLevel.MEDIUM,
                title="Scene without dispose",
                description="Scene created but no disposal logic found",
                suggestion="Implement dispose() to clean up scene, geometries, materials, textures",
            ))

        # Check for renderer cleanup
        if "new THREE.WebGLRenderer" in content:
            if "renderer.dispose" not in content and "dispose" not in content:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.THREEJS,
                    severity=SeverityLevel.HIGH,
                    title="Renderer without dispose",
                    description="WebGLRenderer created but not disposed",
                    suggestion="Call renderer.dispose() on cleanup to release WebGL resources",
                ))

        # Check for pixel ratio
        if "new THREE.WebGLRenderer" in content:
            if "setPixelRatio" not in content:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.THREEJS,
                    severity=SeverityLevel.MEDIUM,
                    title="Missing setPixelRatio",
                    description="Renderer may not handle high-DPI displays correctly",
                    suggestion="Add: renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))",
                ))

        # Check for shadow settings
        if "castShadow" in content or "receiveShadow" in content:
            if "shadow.mapSize" not in content:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.THREEJS,
                    severity=SeverityLevel.LOW,
                    title="Shadow map size not configured",
                    description="Using default shadow map size may cause quality issues",
                    suggestion="Configure light.shadow.mapSize for better shadow quality",
                ))

        # Check for React Three Fiber patterns
        if "@react-three/fiber" in content or "react-three-fiber" in content:
            issues.extend(self._check_r3f_patterns(content, lines, rel_path))

        return issues

    def _check_r3f_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
    ) -> list[CodeIssue]:
        """React Three Fiber specific patterns"""
        issues = []

        # Check for useFrame without dependencies
        if "useFrame" in content:
            if "useFrame((" in content and "}, [" not in content:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.THREEJS,
                    severity=SeverityLevel.LOW,
                    title="useFrame callback",
                    description="useFrame may benefit from useCallback wrapper",
                    suggestion="Wrap complex logic in useCallback with proper deps",
                ))

        # Check for suspense with models
        if "useGLTF" in content or "useLoader" in content:
            if "Suspense" not in content and "<Suspense" not in content:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.THREEJS,
                    severity=SeverityLevel.MEDIUM,
                    title="Missing Suspense",
                    description="Model loaders should be wrapped in Suspense",
                    suggestion="Wrap component tree with <Suspense fallback={...}>",
                ))

        return issues


# =============================================================================
# Interactive Web Design & Animation Toolkit (GSAP, Scroll, WebXR AR)
# =============================================================================


class InteractiveWebToolkit:
    """
    Advanced Interactive Web Design Toolkit.

    Covers:
    - GSAP ScrollTrigger/ScrollSmoother patterns
    - Cinematic 3D scroll experiences
    - WebXR Augmented Reality implementation
    - WebGL shader optimization (GLSL)
    - Motion design best practices
    - Performance for scroll-driven animations

    Based on Codrops tutorials (2025), MDN WebXR docs, GSAP docs.
    """

    # GSAP ScrollTrigger patterns
    GSAP_PATTERNS = {
        r"ScrollTrigger\.create|scrollTrigger:": {
            "severity": SeverityLevel.INFO,
            "title": "ScrollTrigger usage",
            "suggestion": "Good: Using GSAP ScrollTrigger for scroll animations",
        },
        r"ScrollSmoother\.create": {
            "severity": SeverityLevel.INFO,
            "title": "ScrollSmoother",
            "suggestion": "Good: Using ScrollSmoother for smooth scrolling",
        },
        r"scrub:\s*(true|\d+)": {
            "severity": SeverityLevel.INFO,
            "title": "Scroll scrubbing",
            "suggestion": "Good: Linking animation to scroll (scrub: 2 = 2s lag)",
        },
        r"pin:\s*true": {
            "severity": SeverityLevel.INFO,
            "title": "Element pinning",
            "suggestion": "Good: Pinning element during scroll animation",
        },
        r"matchMedia\(": {
            "severity": SeverityLevel.INFO,
            "title": "Responsive animation",
            "suggestion": "Good: Using matchMedia for responsive animations",
        },
        r"gsap\.(to|from|fromTo)\([^)]*,\s*\{[^}]*duration:\s*0": {
            "severity": SeverityLevel.LOW,
            "title": "Zero duration tween",
            "suggestion": "Consider gsap.set() for instant property changes",
        },
    }

    # Motion path patterns
    MOTION_PATH_PATTERNS = {
        r"MotionPathPlugin|motionPath:": {
            "severity": SeverityLevel.INFO,
            "title": "Motion path animation",
            "suggestion": "Good: Using MotionPath for curved animations",
        },
        r"path:\s*['\"]#": {
            "severity": SeverityLevel.INFO,
            "title": "SVG path animation",
            "suggestion": "Good: Animating along SVG paths",
        },
    }

    # WebXR AR patterns
    WEBXR_AR_PATTERNS = {
        r"immersive-ar|XRSessionMode": {
            "severity": SeverityLevel.INFO,
            "title": "AR session mode",
            "suggestion": "Good: Using immersive-ar for augmented reality",
        },
        r"requestSession\(['\"]immersive-ar['\"]": {
            "severity": SeverityLevel.INFO,
            "title": "AR session request",
            "suggestion": "Ensure graceful fallback for non-AR devices",
        },
        r"XRReferenceSpace.*local": {
            "severity": SeverityLevel.INFO,
            "title": "Local reference space",
            "suggestion": "Good: 'local' space is best for AR experiences",
        },
        r"isSessionSupported": {
            "severity": SeverityLevel.INFO,
            "title": "XR support check",
            "suggestion": "Good: Checking XR support before use",
        },
        r"XRHitTestSource|hitTest": {
            "severity": SeverityLevel.INFO,
            "title": "AR hit testing",
            "suggestion": "Good: Using hit tests for surface detection",
        },
        r"XRAnchor": {
            "severity": SeverityLevel.INFO,
            "title": "AR anchoring",
            "suggestion": "Good: Using anchors for persistent AR objects",
        },
    }

    # WebXR security patterns
    WEBXR_SECURITY_PATTERNS = {
        r"http://(?!localhost)": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Non-HTTPS WebXR",
            "suggestion": "WebXR requires HTTPS (except localhost)",
        },
        r"permissions.*xr": {
            "severity": SeverityLevel.INFO,
            "title": "XR permissions",
            "suggestion": "Good: Requesting XR device permissions",
        },
    }

    # Shader optimization patterns (GLSL/WebGL)
    SHADER_OPTIMIZATION_PATTERNS = {
        r"#version 300 es": {
            "severity": SeverityLevel.INFO,
            "title": "GLSL ES 3.0",
            "suggestion": "Good: Using WebGL 2 / GLSL ES 3.0",
        },
        r"precision\s+highp": {
            "severity": SeverityLevel.LOW,
            "title": "High precision shader",
            "suggestion": "Use mediump when sufficient (better mobile perf)",
        },
        r"precision\s+mediump": {
            "severity": SeverityLevel.INFO,
            "title": "Medium precision",
            "suggestion": "Good: mediump is usually sufficient for mobile",
        },
        r"if\s*\([^)]*\)\s*\{[^}]*discard": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Conditional discard",
            "suggestion": "Use step() or smoothstep() instead of if/discard",
        },
        r"texture2D\([^,]+,\s*[^)]+\)": {
            "severity": SeverityLevel.INFO,
            "title": "Texture sample",
            "suggestion": "Minimize texture lookups, use atlases",
        },
        r"for\s*\(\s*int\s+i": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Loop in shader",
            "suggestion": "Unroll small loops, keep iterations minimal",
        },
    }

    # Performance patterns for scroll animations
    SCROLL_PERF_PATTERNS = {
        r"will-change:\s*(transform|opacity)": {
            "severity": SeverityLevel.INFO,
            "title": "GPU hint",
            "suggestion": "Good: Using will-change for GPU acceleration",
        },
        r"top:|left:|right:|bottom:": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Layout property animation",
            "suggestion": "Animate transform, not top/left for better perf",
        },
        r"transform:\s*translate": {
            "severity": SeverityLevel.INFO,
            "title": "Transform animation",
            "suggestion": "Good: Using transform for smooth animations",
        },
        r"ease:\s*['\"]power[234]": {
            "severity": SeverityLevel.INFO,
            "title": "Performance easing",
            "suggestion": "Good: Using smooth power easing",
        },
    }

    # Three.js WebGPU patterns
    WEBGPU_PATTERNS = {
        r"WebGPURenderer": {
            "severity": SeverityLevel.INFO,
            "title": "WebGPU renderer",
            "suggestion": "Good: Using WebGPU for 10x performance",
        },
        r"navigator\.gpu": {
            "severity": SeverityLevel.INFO,
            "title": "WebGPU API",
            "suggestion": "Ensure WebGL fallback for unsupported browsers",
        },
    }

    # 3D asset optimization patterns
    ASSET_OPTIMIZATION_PATTERNS = {
        r"\.glb|\.gltf|GLTFLoader": {
            "severity": SeverityLevel.INFO,
            "title": "GLTF format",
            "suggestion": "Good: GLTF is the recommended 3D format",
        },
        r"DRACOLoader|draco": {
            "severity": SeverityLevel.INFO,
            "title": "Draco compression",
            "suggestion": "Good: Using Draco for mesh compression",
        },
        r"KTX2Loader|\.ktx2": {
            "severity": SeverityLevel.INFO,
            "title": "KTX2 textures",
            "suggestion": "Good: Using compressed GPU textures",
        },
        r"\.obj|OBJLoader": {
            "severity": SeverityLevel.MEDIUM,
            "title": "OBJ format",
            "suggestion": "Consider GLTF instead of OBJ for web",
        },
        r"\.fbx|FBXLoader": {
            "severity": SeverityLevel.LOW,
            "title": "FBX format",
            "suggestion": "Consider converting FBX to GLTF for web",
        },
    }

    # LOD (Level of Detail) patterns
    LOD_PATTERNS = {
        r"THREE\.LOD|new LOD": {
            "severity": SeverityLevel.INFO,
            "title": "LOD usage",
            "suggestion": "Good: Using Level of Detail for performance",
        },
        r"InstancedMesh|InstancedBufferGeometry": {
            "severity": SeverityLevel.INFO,
            "title": "Instancing",
            "suggestion": "Good: Using instancing for repeated objects",
        },
        r"frustumCulled": {
            "severity": SeverityLevel.INFO,
            "title": "Frustum culling",
            "suggestion": "Good: Culling off-screen objects",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for interactive web patterns"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Only analyze relevant files
            if not any(ext in rel_path for ext in [".ts", ".tsx", ".js", ".jsx", ".glsl", ".vert", ".frag"]):
                return issues

            # GSAP patterns
            if "gsap" in content.lower() or "scrolltrigger" in content.lower():
                issues.extend(self._check_patterns(content, lines, rel_path, self.GSAP_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.MOTION_PATH_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.SCROLL_PERF_PATTERNS))

            # WebXR patterns
            if "webxr" in content.lower() or "xrsession" in content.lower() or "immersive" in content.lower():
                issues.extend(self._check_patterns(content, lines, rel_path, self.WEBXR_AR_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.WEBXR_SECURITY_PATTERNS))

            # Shader patterns
            if ".glsl" in rel_path or "shader" in content.lower() or "precision " in content:
                issues.extend(self._check_patterns(content, lines, rel_path, self.SHADER_OPTIMIZATION_PATTERNS))

            # Three.js patterns
            if "three" in content.lower():
                issues.extend(self._check_patterns(content, lines, rel_path, self.WEBGPU_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.ASSET_OPTIMIZATION_PATTERNS))
                issues.extend(self._check_patterns(content, lines, rel_path, self.LOD_PATTERNS))

        except Exception as e:
            logger.error(f"Interactive web analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(self, content, lines, rel_path, patterns):
        issues = []
        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.THREEJS,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                ))
        return issues

    def get_webxr_checklist(self) -> list[dict]:
        """Get WebXR AR implementation checklist"""
        return [
            {"item": "Check XR support with isSessionSupported()", "required": True},
            {"item": "Use HTTPS (required for WebXR)", "required": True},
            {"item": "Request 'immersive-ar' session mode", "required": True},
            {"item": "Use 'local' reference space for AR", "required": True},
            {"item": "Implement hit-testing for surface placement", "recommended": True},
            {"item": "Use XRAnchors for persistent objects", "recommended": True},
            {"item": "Provide graceful fallback for non-AR devices", "required": True},
            {"item": "Handle session end events", "required": True},
            {"item": "Request camera/sensor permissions", "required": True},
        ]

    def get_gsap_scroll_checklist(self) -> list[dict]:
        """Get GSAP scroll animation checklist"""
        return [
            {"item": "Use ScrollTrigger.matchMedia() for responsive", "recommended": True},
            {"item": "Prefer transform over position properties", "required": True},
            {"item": "Use will-change for GPU acceleration", "recommended": True},
            {"item": "Set appropriate scrub values (0.5-2)", "recommended": True},
            {"item": "Use pin: true for scroll sections", "recommended": True},
            {"item": "Add anticipatePin for smooth pinning", "recommended": True},
            {"item": "Use power2/power3 easing for smoothness", "recommended": True},
            {"item": "Simplify for mobile with matchMedia", "required": True},
        ]


# =============================================================================
# LLM Best Practices Knowledge Base
# =============================================================================


class LLMBestPracticesKB:
    """
    Knowledge base of top-tier LLM coding techniques and patterns.

    Incorporates best practices from:
    - Claude (Anthropic)
    - GPT-4 (OpenAI)
    - Gemini (Google)
    - Code Llama (Meta)

    Categories:
    - Code structure and organization
    - Error handling patterns
    - Type safety and validation
    - Performance optimization
    - Security best practices
    - Testing patterns
    - Documentation standards
    """

    # Collected from top LLM responses for coding tasks
    BEST_PRACTICES = {
        "python": {
            "type_hints": {
                "pattern": r"def\s+\w+\([^)]*\)\s*(?!->)",
                "severity": SeverityLevel.LOW,
                "title": "Missing return type hint",
                "suggestion": "Add return type hints for better IDE support and documentation",
                "reference": "PEP 484 - Type Hints",
            },
            "dataclasses": {
                "pattern": r"class\s+\w+:\s*\n\s+def\s+__init__",
                "check_missing": "@dataclass",
                "severity": SeverityLevel.INFO,
                "title": "Consider using dataclass",
                "suggestion": "For data containers, @dataclass reduces boilerplate and adds __eq__, __repr__",
            },
            "context_managers": {
                "pattern": r"(open|acquire|connect)\([^)]*\)",
                "check_context": r"with\s+",
                "check_positive": True,
                "severity": SeverityLevel.MEDIUM,
                "title": "Resource handling",
                "suggestion": "Use context managers (with statement) for automatic cleanup",
            },
            "f_strings": {
                "pattern": r'"\s*\+\s*str\(|\.format\(',
                "severity": SeverityLevel.LOW,
                "title": "String formatting",
                "suggestion": "Prefer f-strings for readability: f'{var}' over str concat or .format()",
            },
            "enumerate": {
                "pattern": r"for\s+\w+\s+in\s+range\(len\(",
                "severity": SeverityLevel.LOW,
                "title": "Index iteration",
                "suggestion": "Use enumerate() instead of range(len()): for i, item in enumerate(items)",
            },
            "pathlib": {
                "pattern": r"os\.path\.(join|exists|dirname|basename)",
                "severity": SeverityLevel.LOW,
                "title": "Path manipulation",
                "suggestion": "Use pathlib.Path for cleaner path operations",
            },
            "early_return": {
                "pattern": r"if\s+.+:\s*\n\s+.+\n\s+else:\s*\n\s+return",
                "severity": SeverityLevel.LOW,
                "title": "Nested conditionals",
                "suggestion": "Use early returns to reduce nesting depth",
            },
            "explicit_exceptions": {
                "pattern": r"except\s*:",
                "severity": SeverityLevel.HIGH,
                "title": "Bare except clause",
                "suggestion": "Always catch specific exceptions, not bare except",
            },
            "async_await": {
                "pattern": r"async\s+def\s+\w+.*\n(?:(?!await).)*$",
                "severity": SeverityLevel.MEDIUM,
                "title": "Async without await",
                "suggestion": "Async functions should contain await calls",
            },
        },
        "typescript": {
            "strict_null": {
                "pattern": r"\?\s*\.\s*\w+",
                "severity": SeverityLevel.INFO,
                "title": "Optional chaining",
                "suggestion": "Good: Using optional chaining for null safety",
            },
            "type_guards": {
                "pattern": r"typeof\s+\w+\s*===|instanceof",
                "severity": SeverityLevel.INFO,
                "title": "Type guard",
                "suggestion": "Good: Using type guards for type narrowing",
            },
            "const_assertions": {
                "pattern": r"\bas\s+const\b",
                "severity": SeverityLevel.INFO,
                "title": "Const assertion",
                "suggestion": "Good: Using 'as const' for literal types",
            },
            "nullish_coalescing": {
                "pattern": r"\|\|\s*['\"\d]",
                "severity": SeverityLevel.LOW,
                "title": "Logical OR for defaults",
                "suggestion": "Consider ?? (nullish coalescing) to only default null/undefined",
            },
            "interface_vs_type": {
                "pattern": r"type\s+\w+\s*=\s*\{",
                "severity": SeverityLevel.INFO,
                "title": "Type alias for object",
                "suggestion": "For object shapes, interfaces offer better extensibility",
            },
            "unknown_over_any": {
                "pattern": r":\s*any\b",
                "severity": SeverityLevel.MEDIUM,
                "title": "Use of any",
                "suggestion": "Prefer 'unknown' over 'any' for type safety",
            },
        },
        "react": {
            "use_callback": {
                "pattern": r"const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{[^}]*\bset\w+\b",
                "severity": SeverityLevel.LOW,
                "title": "Event handler",
                "suggestion": "Wrap event handlers in useCallback to prevent re-renders",
            },
            "use_memo": {
                "pattern": r"(filter|map|reduce|sort)\([^)]+\)",
                "check_context": "render|return.*<",
                "severity": SeverityLevel.LOW,
                "title": "Expensive computation in render",
                "suggestion": "Use useMemo for expensive calculations",
            },
            "key_prop": {
                "pattern": r"\.map\([^)]*\)\s*=>\s*<(?!.*\bkey\b)",
                "severity": SeverityLevel.HIGH,
                "title": "Missing key prop",
                "suggestion": "Add unique key prop to list items",
            },
            "effect_deps": {
                "pattern": r"useEffect\([^,]+,\s*\[\s*\]\)",
                "severity": SeverityLevel.INFO,
                "title": "Empty dependency array",
                "suggestion": "Verify effect truly needs to run only once",
            },
            "error_boundary": {
                "pattern": r"class\s+\w+\s+extends\s+.*(Error|Exception)",
                "severity": SeverityLevel.INFO,
                "title": "Error handling component",
                "suggestion": "Consider implementing Error Boundaries for UI error recovery",
            },
        },
    }

    # Architecture patterns from top LLMs
    ARCHITECTURE_PATTERNS = {
        "separation_of_concerns": {
            "pattern": r"(fetch|axios|api)\([^)]*\)",
            "check_context": r"Component|render|return.*<",
            "severity": SeverityLevel.MEDIUM,
            "title": "API call in component",
            "suggestion": "Move API calls to services/hooks layer for separation of concerns",
        },
        "single_responsibility": {
            "pattern": r"class\s+\w+.*:.*\n(?:.*\n){100,}",
            "severity": SeverityLevel.MEDIUM,
            "title": "Large class",
            "suggestion": "Class may have too many responsibilities, consider splitting",
        },
        "dependency_injection": {
            "pattern": r"import\s+.+\s+from\s+['\"].*/(?!node_modules|@)",
            "severity": SeverityLevel.INFO,
            "title": "Direct import",
            "suggestion": "Consider dependency injection for better testability",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._custom_patterns: dict[str, dict] = {}

    def add_pattern(self, language: str, name: str, pattern_config: dict):
        """Add a custom pattern to the knowledge base"""
        if language not in self._custom_patterns:
            self._custom_patterns[language] = {}
        self._custom_patterns[language][name] = pattern_config

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file against LLM best practices"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Determine language
            language = self._detect_language(file_path, content)

            if language:
                patterns = self.BEST_PRACTICES.get(language, {})
                combined_patterns = {**patterns, **self._custom_patterns.get(language, {})}

                for name, config in combined_patterns.items():
                    issues.extend(self._check_pattern(content, lines, rel_path, config))

                # Check architecture patterns
                for name, config in self.ARCHITECTURE_PATTERNS.items():
                    issues.extend(self._check_pattern(content, lines, rel_path, config))

        except Exception as e:
            logger.error(f"LLM best practices analysis failed for {file_path}: {e}")

        return issues

    def _detect_language(self, file_path: Path, content: str) -> str | None:
        """Detect the language of the file"""
        ext = file_path.suffix.lower()

        if ext in [".py"]:
            return "python"
        elif ext in [".ts"]:
            return "typescript"
        elif ext in [".tsx", ".jsx"]:
            return "react"
        elif ext in [".js"]:
            # Check if it's React
            if "import React" in content or "from 'react'" in content:
                return "react"
            return "typescript"  # Treat JS similarly

        return None

    def _check_pattern(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
        config: dict,
    ) -> list[CodeIssue]:
        """Check a single pattern"""
        issues = []

        pattern = config.get("pattern")
        if not pattern:
            return issues

        matches = list(re.finditer(pattern, content, re.MULTILINE))

        for match in matches:
            line_num = content[:match.start()].count("\n") + 1

            # Context check
            if "check_context" in config:
                context_start = max(0, match.start() - 200)
                context_end = min(len(content), match.end() + 200)
                context = content[context_start:context_end]

                if not re.search(config["check_context"], context):
                    continue

            # Missing check
            if "check_missing" in config:
                if config["check_missing"] in content:
                    continue  # Pattern present, not missing

            # Positive pattern (good practice)
            if config.get("check_positive"):
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.BEST_PRACTICE,
                    severity=SeverityLevel.INFO,
                    title=f"✓ {config.get('title', 'Good practice')}",
                    description="Follows best practice",
                    suggestion=config.get("suggestion"),
                    reference_url=config.get("reference"),
                ))
            else:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.BEST_PRACTICE,
                    severity=config.get("severity", SeverityLevel.LOW),
                    title=config.get("title", "Pattern detected"),
                    description=match.group(0)[:50] if match.group(0) else "",
                    suggestion=config.get("suggestion"),
                    reference_url=config.get("reference"),
                ))

        return issues

    def get_best_practices_summary(self, language: str) -> list[dict]:
        """Get summary of best practices for a language"""
        practices = self.BEST_PRACTICES.get(language, {})
        return [
            {
                "name": name,
                "title": config.get("title"),
                "suggestion": config.get("suggestion"),
            }
            for name, config in practices.items()
        ]


# =============================================================================
# Frontend Toolkit
# =============================================================================


class FrontendToolkit:
    """
    Frontend code analysis toolkit.

    Analyzes:
    - React component patterns
    - Next.js best practices
    - CSS/Tailwind optimization
    - Bundle size considerations
    - Accessibility (a11y)
    """

    A11Y_PATTERNS = {
        r"<img(?![^>]*alt=)": {
            "severity": SeverityLevel.HIGH,
            "title": "Image missing alt attribute",
            "suggestion": "Add descriptive alt text for accessibility",
        },
        r"<button(?![^>]*aria-)": {
            "severity": SeverityLevel.LOW,
            "title": "Button may need ARIA",
            "suggestion": "Consider aria-label for icon-only buttons",
        },
        r"onClick=[^>]*>\s*<(?:div|span)": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Clickable non-button element",
            "suggestion": "Use <button> or add role='button' and keyboard handlers",
        },
    }

    NEXTJS_PATTERNS = {
        r"getServerSideProps": {
            "severity": SeverityLevel.INFO,
            "title": "SSR page",
            "suggestion": "Ensure SSR is necessary, consider ISR for better performance",
        },
        r"use client": {
            "severity": SeverityLevel.INFO,
            "title": "Client component",
            "suggestion": "Keep client components small, lift server data fetching",
        },
        r"import\s+.*\s+from\s+['\"]next/image": {
            "severity": SeverityLevel.INFO,
            "title": "Next.js Image optimization",
            "suggestion": "Good: Using next/image for automatic optimization",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze frontend file"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            if not any(ext in rel_path for ext in [".tsx", ".jsx", ".ts", ".js"]):
                return issues

            # A11y checks
            issues.extend(self._check_patterns(content, lines, rel_path, self.A11Y_PATTERNS))

            # Next.js checks
            if "next" in content.lower():
                issues.extend(self._check_patterns(content, lines, rel_path, self.NEXTJS_PATTERNS))

        except Exception as e:
            logger.error(f"Frontend analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
        patterns: dict,
    ) -> list[CodeIssue]:
        """Check content against patterns"""
        issues = []

        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content))

            for match in matches:
                line_num = content[:match.start()].count("\n") + 1

                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.FRONTEND,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                ))

        return issues


# =============================================================================
# API Toolkit
# =============================================================================


class APIToolkit:
    """
    API code analysis toolkit.

    Analyzes:
    - REST endpoint patterns
    - GraphQL schema design
    - WebSocket handling
    - Rate limiting
    - Input validation
    """

    REST_PATTERNS = {
        r"@(app\.|router\.)(get|post|put|delete|patch)\(": {
            "severity": SeverityLevel.INFO,
            "title": "REST endpoint",
            "suggestion": "Ensure proper input validation and error handling",
        },
        r"request\.(body|params|query)\[": {
            "severity": SeverityLevel.HIGH,
            "title": "Direct request access",
            "suggestion": "Validate and sanitize input before use",
        },
        r"res\.send\(.*\+": {
            "severity": SeverityLevel.MEDIUM,
            "title": "String concatenation in response",
            "suggestion": "Use structured responses (res.json) to prevent XSS",
        },
    }

    WEBSOCKET_PATTERNS = {
        r"on\(['\"]message['\"]": {
            "severity": SeverityLevel.MEDIUM,
            "title": "WebSocket message handler",
            "suggestion": "Validate and sanitize all incoming messages",
        },
        r"on\(['\"]error['\"]": {
            "severity": SeverityLevel.INFO,
            "title": "WebSocket error handling",
            "suggestion": "Good: Handling WebSocket errors",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze API file"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # REST checks
            issues.extend(self._check_patterns(content, lines, rel_path, self.REST_PATTERNS))

            # WebSocket checks
            if "websocket" in content.lower() or "socket.io" in content.lower():
                issues.extend(self._check_patterns(content, lines, rel_path, self.WEBSOCKET_PATTERNS))

        except Exception as e:
            logger.error(f"API analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
        patterns: dict,
    ) -> list[CodeIssue]:
        """Check content against patterns"""
        issues = []

        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content))

            for match in matches:
                line_num = content[:match.start()].count("\n") + 1

                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.API,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                ))

        return issues


# =============================================================================
# UI/UX Design Toolkit
# =============================================================================


class UIUXToolkit:
    """
    State-of-the-art UI/UX design analysis toolkit.

    Analyzes:
    - Design system implementation
    - Responsive design patterns
    - Animation and micro-interactions
    - Color and typography consistency
    - Accessibility (WCAG 2.1 AA/AAA)
    - Performance (Core Web Vitals)
    - Mobile-first patterns
    - Dark mode implementation
    - Loading states and skeleton screens
    - Error states and empty states
    - Navigation patterns
    - Form UX

    Based on:
    - Apple Human Interface Guidelines
    - Google Material Design 3
    - Tailwind UI patterns
    - Radix UI primitives
    - shadcn/ui components
    """

    # Design system patterns
    DESIGN_SYSTEM_PATTERNS = {
        r"(px-\d+|py-\d+|p-\d+|m-\d+|mx-\d+|my-\d+)": {
            "severity": SeverityLevel.INFO,
            "title": "Spacing utilities",
            "suggestion": "Consider using design tokens: space-xs, space-sm, space-md, space-lg",
        },
        r"text-(xs|sm|base|lg|xl|\d+xl)": {
            "severity": SeverityLevel.INFO,
            "title": "Typography scale",
            "suggestion": "Good: Using consistent typography scale",
        },
        r"#[0-9a-fA-F]{3,8}(?!\w)": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Hardcoded color",
            "suggestion": "Use design tokens: bg-primary, text-secondary, etc.",
        },
        r"font-\[(family-name|size)\]": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Arbitrary font value",
            "suggestion": "Define in tailwind.config.js for consistency",
        },
    }

    # Responsive design patterns
    RESPONSIVE_PATTERNS = {
        r"sm:|md:|lg:|xl:|2xl:": {
            "severity": SeverityLevel.INFO,
            "title": "Responsive breakpoint",
            "suggestion": "Good: Using responsive utilities",
        },
        r"hidden\s+(?:sm|md|lg|xl):block": {
            "severity": SeverityLevel.INFO,
            "title": "Mobile-first hidden",
            "suggestion": "Good: Mobile-first approach",
        },
        r"w-\[(?:\d+px|\d+vw)\]": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Fixed width",
            "suggestion": "Consider relative units (%, rem) for responsiveness",
        },
        r"@media\s+\(": {
            "severity": SeverityLevel.INFO,
            "title": "Media query",
            "suggestion": "Prefer Tailwind breakpoints over custom media queries",
        },
    }

    # Animation patterns
    ANIMATION_PATTERNS = {
        r"transition(-all|-colors|-opacity|-shadow|-transform)?": {
            "severity": SeverityLevel.INFO,
            "title": "CSS transition",
            "suggestion": "Good: Using transitions for smooth state changes",
        },
        r"animate-": {
            "severity": SeverityLevel.INFO,
            "title": "Animation utility",
            "suggestion": "Keep animations subtle (200-500ms) and purposeful",
        },
        r"duration-\[(.*?)\]": {
            "severity": SeverityLevel.LOW,
            "title": "Custom duration",
            "suggestion": "Standard durations: 150ms (fast), 200ms (normal), 500ms (slow)",
        },
        r"motion-reduce:": {
            "severity": SeverityLevel.INFO,
            "title": "Motion reduction",
            "suggestion": "Excellent: Respecting prefers-reduced-motion",
        },
    }

    # Accessibility patterns (WCAG 2.1)
    ACCESSIBILITY_PATTERNS = {
        r"aria-label=['\"]": {
            "severity": SeverityLevel.INFO,
            "title": "ARIA label",
            "suggestion": "Good: Providing accessible labels",
        },
        r"role=['\"]": {
            "severity": SeverityLevel.INFO,
            "title": "ARIA role",
            "suggestion": "Good: Defining semantic roles",
        },
        r"tabIndex|tabindex": {
            "severity": SeverityLevel.INFO,
            "title": "Tab index",
            "suggestion": "Use tabIndex={0} for focusable, {-1} for programmatic focus",
        },
        r"focus(-visible)?:": {
            "severity": SeverityLevel.INFO,
            "title": "Focus styles",
            "suggestion": "Good: Providing visible focus indicators",
        },
        r"sr-only": {
            "severity": SeverityLevel.INFO,
            "title": "Screen reader text",
            "suggestion": "Good: Providing context for screen readers",
        },
        r"<button(?![^>]*type=)": {
            "severity": SeverityLevel.LOW,
            "title": "Button without type",
            "suggestion": "Add type='button' to prevent form submission",
        },
    }

    # Loading state patterns
    LOADING_PATTERNS = {
        r"(Skeleton|skeleton|isLoading|loading)": {
            "severity": SeverityLevel.INFO,
            "title": "Loading state",
            "suggestion": "Good: Implementing loading feedback",
        },
        r"Suspense|suspense": {
            "severity": SeverityLevel.INFO,
            "title": "Suspense boundary",
            "suggestion": "Good: Using Suspense for async content",
        },
        r"placeholder|Placeholder": {
            "severity": SeverityLevel.INFO,
            "title": "Placeholder content",
            "suggestion": "Good: Providing placeholder states",
        },
    }

    # Form UX patterns
    FORM_PATTERNS = {
        r"<label(?![^>]*htmlFor)(?![^>]*for=)": {
            "severity": SeverityLevel.HIGH,
            "title": "Label without htmlFor",
            "suggestion": "Connect label to input with htmlFor attribute",
        },
        r"required|isRequired": {
            "severity": SeverityLevel.INFO,
            "title": "Required field",
            "suggestion": "Show visual indicator (*) and announce to screen readers",
        },
        r"(helperText|helper-text|hint)": {
            "severity": SeverityLevel.INFO,
            "title": "Helper text",
            "suggestion": "Good: Providing guidance for form fields",
        },
        r"(errorMessage|error-message|FormError)": {
            "severity": SeverityLevel.INFO,
            "title": "Error message",
            "suggestion": "Good: Showing inline validation errors",
        },
        r"autoComplete|autocomplete": {
            "severity": SeverityLevel.INFO,
            "title": "Autocomplete attribute",
            "suggestion": "Good: Using autocomplete for better UX",
        },
    }

    # Dark mode patterns
    DARK_MODE_PATTERNS = {
        r"dark:": {
            "severity": SeverityLevel.INFO,
            "title": "Dark mode variant",
            "suggestion": "Good: Supporting dark mode",
        },
        r"prefers-color-scheme": {
            "severity": SeverityLevel.INFO,
            "title": "System preference",
            "suggestion": "Good: Respecting system color scheme",
        },
        r"bg-(white|black)": {
            "severity": SeverityLevel.LOW,
            "title": "Absolute color",
            "suggestion": "Use bg-background/text-foreground for theme support",
        },
    }

    # Component library patterns (shadcn/ui, Radix)
    COMPONENT_PATTERNS = {
        r"@radix-ui": {
            "severity": SeverityLevel.INFO,
            "title": "Radix UI primitive",
            "suggestion": "Good: Using accessible UI primitives",
        },
        r"Dialog|Sheet|Popover|Tooltip|Dropdown": {
            "severity": SeverityLevel.INFO,
            "title": "Overlay component",
            "suggestion": "Ensure focus trap and ESC key handling",
        },
        r"Portal|createPortal": {
            "severity": SeverityLevel.INFO,
            "title": "Portal rendering",
            "suggestion": "Good: Portaling overlays for z-index management",
        },
    }

    # Navigation patterns
    NAVIGATION_PATTERNS = {
        r"<nav": {
            "severity": SeverityLevel.INFO,
            "title": "Navigation landmark",
            "suggestion": "Good: Using semantic nav element",
        },
        r"Breadcrumb|breadcrumb": {
            "severity": SeverityLevel.INFO,
            "title": "Breadcrumb navigation",
            "suggestion": "Good: Providing wayfinding",
        },
        r"aria-current": {
            "severity": SeverityLevel.INFO,
            "title": "Current page indicator",
            "suggestion": "Good: Indicating current location",
        },
    }

    # Core Web Vitals patterns
    PERFORMANCE_PATTERNS = {
        r"<img(?![^>]*loading=)": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Image without loading attr",
            "suggestion": "Add loading='lazy' for below-fold images",
        },
        r"next/image|Image\s+from": {
            "severity": SeverityLevel.INFO,
            "title": "Next.js Image",
            "suggestion": "Good: Using optimized image component",
        },
        r"font-display": {
            "severity": SeverityLevel.INFO,
            "title": "Font display",
            "suggestion": "Good: Controlling font loading behavior",
        },
        r"will-change": {
            "severity": SeverityLevel.LOW,
            "title": "will-change hint",
            "suggestion": "Use sparingly, remove after animation",
        },
    }

    # Modern UI patterns
    MODERN_PATTERNS = {
        r"glass|backdrop-blur": {
            "severity": SeverityLevel.INFO,
            "title": "Glassmorphism",
            "suggestion": "Ensure sufficient contrast for readability",
        },
        r"gradient": {
            "severity": SeverityLevel.INFO,
            "title": "Gradient",
            "suggestion": "Test gradients in both light/dark modes",
        },
        r"shadow-": {
            "severity": SeverityLevel.INFO,
            "title": "Shadow",
            "suggestion": "Use subtle shadows for depth hierarchy",
        },
        r"rounded-": {
            "severity": SeverityLevel.INFO,
            "title": "Border radius",
            "suggestion": "Maintain consistent border radius across components",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for UI/UX patterns"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Only analyze frontend files
            if not any(ext in rel_path for ext in [".tsx", ".jsx", ".css", ".scss"]):
                return issues

            # Design system
            issues.extend(self._check_patterns(content, lines, rel_path, self.DESIGN_SYSTEM_PATTERNS))

            # Responsive
            issues.extend(self._check_patterns(content, lines, rel_path, self.RESPONSIVE_PATTERNS))

            # Animations
            issues.extend(self._check_patterns(content, lines, rel_path, self.ANIMATION_PATTERNS))

            # Accessibility
            issues.extend(self._check_patterns(content, lines, rel_path, self.ACCESSIBILITY_PATTERNS))

            # Loading states
            issues.extend(self._check_patterns(content, lines, rel_path, self.LOADING_PATTERNS))

            # Forms
            issues.extend(self._check_patterns(content, lines, rel_path, self.FORM_PATTERNS))

            # Dark mode
            issues.extend(self._check_patterns(content, lines, rel_path, self.DARK_MODE_PATTERNS))

            # Components
            issues.extend(self._check_patterns(content, lines, rel_path, self.COMPONENT_PATTERNS))

            # Navigation
            issues.extend(self._check_patterns(content, lines, rel_path, self.NAVIGATION_PATTERNS))

            # Performance
            issues.extend(self._check_patterns(content, lines, rel_path, self.PERFORMANCE_PATTERNS))

            # Modern patterns
            issues.extend(self._check_patterns(content, lines, rel_path, self.MODERN_PATTERNS))

            # Additional UX checks
            issues.extend(self._check_ux_patterns(content, lines, rel_path))

        except Exception as e:
            logger.error(f"UI/UX analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
        patterns: dict,
    ) -> list[CodeIssue]:
        """Check content against patterns"""
        issues = []

        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content))

            for match in matches:
                line_num = content[:match.start()].count("\n") + 1

                # Create appropriate issue category
                category = IssueCategory.FRONTEND
                if "accessibility" in str(config.get("title", "")).lower():
                    pass  # Keep FRONTEND category

                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=category,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                ))

        return issues

    def _check_ux_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
    ) -> list[CodeIssue]:
        """Additional UX-specific checks"""
        issues = []

        # Check for empty states
        if "EmptyState" not in content and "empty-state" not in content:
            if any(term in content for term in ["map(", "filter(", ".length"]):
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.FRONTEND,
                    severity=SeverityLevel.LOW,
                    title="Consider empty state",
                    description="List rendering without explicit empty state",
                    suggestion="Show helpful empty state when data is empty",
                ))

        # Check for error boundaries
        if "ErrorBoundary" not in content and "error-boundary" not in content:
            if "<Suspense" in content:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=None,
                    category=IssueCategory.FRONTEND,
                    severity=SeverityLevel.LOW,
                    title="Consider Error Boundary",
                    description="Suspense without Error Boundary",
                    suggestion="Wrap with ErrorBoundary for graceful error handling",
                ))

        # Check contrast in Tailwind classes
        if "text-gray-400" in content and "bg-white" in content:
            issues.append(CodeIssue(
                file_path=rel_path,
                line_number=None,
                category=IssueCategory.FRONTEND,
                severity=SeverityLevel.MEDIUM,
                title="Potential contrast issue",
                description="Light gray text on white may fail WCAG contrast",
                suggestion="Use text-gray-600 or darker for body text",
            ))

        # Check for touch targets
        if re.search(r'(w-4|w-5|h-4|h-5).*onClick', content):
            issues.append(CodeIssue(
                file_path=rel_path,
                line_number=None,
                category=IssueCategory.FRONTEND,
                severity=SeverityLevel.MEDIUM,
                title="Small touch target",
                description="Clickable element may be too small",
                suggestion="Minimum touch target: 44x44px (w-11 h-11)",
            ))

        return issues

    def get_design_guidelines(self) -> dict[str, Any]:
        """Get design system guidelines"""
        return {
            "spacing_scale": {
                "xs": "0.25rem (4px)",
                "sm": "0.5rem (8px)",
                "md": "1rem (16px)",
                "lg": "1.5rem (24px)",
                "xl": "2rem (32px)",
                "2xl": "3rem (48px)",
            },
            "typography_scale": {
                "xs": "0.75rem (12px)",
                "sm": "0.875rem (14px)",
                "base": "1rem (16px)",
                "lg": "1.125rem (18px)",
                "xl": "1.25rem (20px)",
                "2xl": "1.5rem (24px)",
                "3xl": "1.875rem (30px)",
            },
            "animation_durations": {
                "fast": "150ms - micro-interactions",
                "normal": "200-300ms - standard transitions",
                "slow": "500ms - emphasis animations",
            },
            "color_contrast": {
                "AA_normal": "4.5:1 minimum",
                "AA_large": "3:1 minimum",
                "AAA_normal": "7:1 minimum",
            },
            "touch_targets": {
                "minimum": "44x44px",
                "recommended": "48x48px",
            },
            "z_index_scale": {
                "dropdown": "50",
                "sticky": "100",
                "modal": "200",
                "popover": "300",
                "tooltip": "400",
                "toast": "500",
            },
        }


# =============================================================================
# OWASP 2025 Security Toolkit
# =============================================================================


class OWASP2025Toolkit:
    """
    OWASP Top 10 2025 Security Analysis Toolkit.

    Covers all 10 categories:
    - A01: Broken Access Control
    - A02: Security Misconfiguration
    - A03: Software Supply Chain Failures
    - A04: Cryptographic Failures
    - A05: Injection
    - A06: Insecure Design
    - A07: Authentication Failures
    - A08: Software/Data Integrity Failures
    - A09: Security Logging & Alerting Failures
    - A10: Mishandling of Exceptional Conditions

    Based on OWASP Top 10:2025 official release (Nov 2025).
    """

    # A01: Broken Access Control (3.73% of apps affected)
    ACCESS_CONTROL_PATTERNS = {
        r"if\s+user\.role\s*==": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Role-based access check",
            "suggestion": "Use centralized authorization, not scattered role checks",
        },
        r"\.is_admin|isAdmin|is_superuser": {
            "severity": SeverityLevel.INFO,
            "title": "Admin check",
            "suggestion": "Ensure admin checks are in middleware/decorators, not business logic",
        },
        r"@login_required|@authenticated": {
            "severity": SeverityLevel.INFO,
            "title": "Auth decorator",
            "suggestion": "Good: Using auth decorators for access control",
        },
        r"request\.user\.id\s*==": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Direct user ID comparison",
            "suggestion": "Use ownership checks in service layer, not controllers",
        },
    }

    # A02: Security Misconfiguration
    MISCONFIGURATION_PATTERNS = {
        r"DEBUG\s*=\s*True": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Debug mode enabled",
            "suggestion": "Never enable DEBUG in production",
        },
        r"ALLOWED_HOSTS\s*=\s*\[\s*['\"]?\*['\"]?\s*\]": {
            "severity": SeverityLevel.HIGH,
            "title": "Wildcard allowed hosts",
            "suggestion": "Specify exact hostnames in ALLOWED_HOSTS",
        },
        r"SECRET_KEY\s*=\s*['\"][^'\"]{1,30}['\"]": {
            "severity": SeverityLevel.HIGH,
            "title": "Weak secret key",
            "suggestion": "Use at least 50 random characters for SECRET_KEY",
        },
        r"CORS_ALLOW_ALL_ORIGINS\s*=\s*True": {
            "severity": SeverityLevel.HIGH,
            "title": "CORS allows all origins",
            "suggestion": "Whitelist specific origins, not all",
        },
        r"verify\s*=\s*False": {
            "severity": SeverityLevel.CRITICAL,
            "title": "SSL verification disabled",
            "suggestion": "Never disable SSL verification in production",
        },
    }

    # A03: Software Supply Chain Failures
    SUPPLY_CHAIN_PATTERNS = {
        r"pip\s+install\s+--trusted-host": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Trusted host bypass",
            "suggestion": "Never bypass package verification",
        },
        r"npm\s+install.*--ignore-scripts": {
            "severity": SeverityLevel.HIGH,
            "title": "NPM scripts bypassed",
            "suggestion": "Review why scripts are being ignored",
        },
        r"subprocess\.run\([^)]*shell\s*=\s*True": {
            "severity": SeverityLevel.HIGH,
            "title": "Shell injection risk",
            "suggestion": "Avoid shell=True, use list of arguments",
        },
    }

    # A04: Cryptographic Failures
    CRYPTO_PATTERNS = {
        r"(md5|sha1)\s*\(": {
            "severity": SeverityLevel.HIGH,
            "title": "Weak hash algorithm",
            "suggestion": "Use SHA-256 or better; bcrypt/argon2 for passwords",
        },
        r"DES|3DES|RC4|Blowfish": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Deprecated encryption",
            "suggestion": "Use AES-256-GCM for symmetric encryption",
        },
        r"random\.randint|random\.choice": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Non-cryptographic random",
            "suggestion": "Use secrets module for security-sensitive random values",
        },
        r"base64\.(encode|decode)": {
            "severity": SeverityLevel.INFO,
            "title": "Base64 encoding",
            "suggestion": "Base64 is NOT encryption - don't use for secrets",
        },
    }

    # A05: Injection
    INJECTION_PATTERNS = {
        r"execute\([^)]*%\s*\(": {
            "severity": SeverityLevel.CRITICAL,
            "title": "SQL string formatting",
            "suggestion": "Use parameterized queries",
        },
        r"os\.system\(|subprocess\.call\(.*shell": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Command injection risk",
            "suggestion": "Use subprocess with list args, no shell",
        },
        r"render_template_string\(": {
            "severity": SeverityLevel.HIGH,
            "title": "SSTI risk",
            "suggestion": "Use render_template with file templates",
        },
        r"\.innerHTML\s*=|dangerouslySetInnerHTML": {
            "severity": SeverityLevel.HIGH,
            "title": "XSS risk",
            "suggestion": "Sanitize HTML or use textContent",
        },
    }

    # A07: Authentication Failures
    AUTH_PATTERNS = {
        r"password.*=.*['\"][^'\"]{1,8}['\"]": {
            "severity": SeverityLevel.HIGH,
            "title": "Weak password",
            "suggestion": "Enforce minimum 12 character passwords",
        },
        r"jwt\.decode\([^)]*verify\s*=\s*False": {
            "severity": SeverityLevel.CRITICAL,
            "title": "JWT verification disabled",
            "suggestion": "Always verify JWT signatures",
        },
        r"session\.permanent\s*=\s*True": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Permanent session",
            "suggestion": "Set reasonable session timeout",
        },
    }

    # A09: Security Logging & Alerting Failures
    LOGGING_PATTERNS = {
        r"except.*:\s*pass": {
            "severity": SeverityLevel.HIGH,
            "title": "Silent exception",
            "suggestion": "Log all exceptions for security monitoring",
        },
        r"print\(.*password|print\(.*secret|print\(.*token": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Secrets in logs",
            "suggestion": "Never log sensitive data",
        },
        r"logger\.(debug|info|warning|error)": {
            "severity": SeverityLevel.INFO,
            "title": "Logging call",
            "suggestion": "Good: Using structured logging",
        },
    }

    # A10: Mishandling of Exceptional Conditions
    EXCEPTION_PATTERNS = {
        r"except\s*:": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Bare except",
            "suggestion": "Catch specific exceptions",
        },
        r"except\s+Exception\s*:": {
            "severity": SeverityLevel.LOW,
            "title": "Broad exception",
            "suggestion": "Catch more specific exception types",
        },
        r"finally:\s*\n\s*pass": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Empty finally",
            "suggestion": "Finally blocks should have cleanup logic",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for OWASP 2025 issues"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Run all OWASP checks
            all_patterns = [
                self.ACCESS_CONTROL_PATTERNS,
                self.MISCONFIGURATION_PATTERNS,
                self.SUPPLY_CHAIN_PATTERNS,
                self.CRYPTO_PATTERNS,
                self.INJECTION_PATTERNS,
                self.AUTH_PATTERNS,
                self.LOGGING_PATTERNS,
                self.EXCEPTION_PATTERNS,
            ]

            for patterns in all_patterns:
                issues.extend(self._check_patterns(content, lines, rel_path, patterns))

        except Exception as e:
            logger.error(f"OWASP analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
        patterns: dict,
    ) -> list[CodeIssue]:
        """Check content against patterns"""
        issues = []

        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content, re.IGNORECASE))

            for match in matches:
                line_num = content[:match.start()].count("\n") + 1

                # Skip test files for some patterns
                if "test" in rel_path.lower() and config["severity"] == SeverityLevel.INFO:
                    continue

                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.SECURITY,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:60],
                    suggestion=config.get("suggestion"),
                    reference_url="https://owasp.org/Top10/2025/",
                ))

        return issues


# =============================================================================
# PCI DSS v4.x E-commerce Toolkit
# =============================================================================


class PCIDSSToolkit:
    """
    PCI DSS v4.x Compliance Toolkit.

    Covers requirements effective March 31, 2025:
    - Requirement 6.4.3: Payment page script management
    - Requirement 11.6.1: Change/tamper detection
    - CSP (Content Security Policy) implementation
    - SRI (Subresource Integrity) validation

    Based on PCI Security Standards Council guidance.
    """

    # Payment page security patterns
    PAYMENT_PAGE_PATTERNS = {
        r"<script[^>]*src=['\"]https?://": {
            "severity": SeverityLevel.MEDIUM,
            "title": "External script on payment page",
            "suggestion": "Document, authorize, and monitor all payment page scripts (Req 6.4.3)",
        },
        r"integrity=['\"]sha(256|384|512)-": {
            "severity": SeverityLevel.INFO,
            "title": "SRI integrity check",
            "suggestion": "Good: Using Subresource Integrity for external scripts",
        },
        r"Content-Security-Policy": {
            "severity": SeverityLevel.INFO,
            "title": "CSP header",
            "suggestion": "Good: Implementing Content Security Policy",
        },
        r"stripe|paypal|braintree|square": {
            "severity": SeverityLevel.INFO,
            "title": "Payment processor detected",
            "suggestion": "Ensure all payment scripts are authorized and monitored",
        },
    }

    # Tamper detection (Req 11.6.1)
    TAMPER_DETECTION_PATTERNS = {
        r"hashlib\.(sha256|sha512)|crypto\.createHash": {
            "severity": SeverityLevel.INFO,
            "title": "Hash verification",
            "suggestion": "Good: Using cryptographic hashes for integrity",
        },
        r"file\.?hash|checksum|integrity": {
            "severity": SeverityLevel.INFO,
            "title": "Integrity check",
            "suggestion": "Good: Implementing integrity verification",
        },
    }

    # Credit card data patterns
    CARD_DATA_PATTERNS = {
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Potential card number",
            "suggestion": "Never store full card numbers - use tokenization",
        },
        r"cvv|cvc|cvn|card_code": {
            "severity": SeverityLevel.HIGH,
            "title": "CVV handling",
            "suggestion": "Never store CVV - PCI DSS strictly prohibits this",
        },
        r"card.*expir|expiry.*date": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Card expiry handling",
            "suggestion": "Minimize storage of cardholder data",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for PCI DSS compliance"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            issues.extend(self._check_patterns(content, lines, rel_path, self.PAYMENT_PAGE_PATTERNS))
            issues.extend(self._check_patterns(content, lines, rel_path, self.TAMPER_DETECTION_PATTERNS))
            issues.extend(self._check_patterns(content, lines, rel_path, self.CARD_DATA_PATTERNS))

        except Exception as e:
            logger.error(f"PCI DSS analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(self, content, lines, rel_path, patterns):
        issues = []
        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.SECURITY,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                    reference_url="https://www.pcisecuritystandards.org/",
                ))
        return issues


# =============================================================================
# WordPress/Elementor Security Toolkit
# =============================================================================


class WordPressSecurityToolkit:
    """
    WordPress & Elementor Security Toolkit.

    Based on 2025 vulnerability research:
    - CVE-2025-67588: Elementor XSS
    - CVE-2025-8489: King Addons privilege escalation
    - Plugin/theme security patterns
    - WooCommerce hardening
    - Shoptimizer performance patterns

    90% of WordPress security issues are in plugins.
    """

    # Elementor-specific vulnerabilities
    ELEMENTOR_PATTERNS = {
        r"elementor.*widget": {
            "severity": SeverityLevel.INFO,
            "title": "Elementor widget",
            "suggestion": "Sanitize all widget input/output, check for XSS",
        },
        r"\\Elementor\\Widget_Base": {
            "severity": SeverityLevel.INFO,
            "title": "Custom Elementor widget",
            "suggestion": "Implement escape_callback for all settings",
        },
        r"add_control\(.*type.*TEXT": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Text control without sanitization",
            "suggestion": "Use sanitize_callback for user inputs",
        },
    }

    # WordPress core security patterns
    WP_SECURITY_PATTERNS = {
        r"\$_GET|\$_POST|\$_REQUEST": {
            "severity": SeverityLevel.HIGH,
            "title": "Direct superglobal access",
            "suggestion": "Use sanitize_text_field(), esc_attr(), etc.",
        },
        r"wp_nonce": {
            "severity": SeverityLevel.INFO,
            "title": "Nonce verification",
            "suggestion": "Good: Using nonces for CSRF protection",
        },
        r"current_user_can\(": {
            "severity": SeverityLevel.INFO,
            "title": "Capability check",
            "suggestion": "Good: Checking user permissions",
        },
        r"echo\s+\$_": {
            "severity": SeverityLevel.CRITICAL,
            "title": "XSS vulnerability",
            "suggestion": "Never echo unsanitized input - use esc_html()",
        },
        r"mysql_query|mysqli_query\(.*\$": {
            "severity": SeverityLevel.CRITICAL,
            "title": "SQL injection",
            "suggestion": "Use $wpdb->prepare() for queries",
        },
        r"\$wpdb->prepare\(": {
            "severity": SeverityLevel.INFO,
            "title": "Prepared statement",
            "suggestion": "Good: Using prepared statements",
        },
    }

    # WooCommerce patterns
    WOOCOMMERCE_PATTERNS = {
        r"wc_get_product|WC_Product": {
            "severity": SeverityLevel.INFO,
            "title": "WooCommerce product access",
            "suggestion": "Cache product queries, avoid N+1",
        },
        r"WC\(\)->cart": {
            "severity": SeverityLevel.INFO,
            "title": "Cart access",
            "suggestion": "Validate cart totals server-side",
        },
        r"wc_price\(": {
            "severity": SeverityLevel.INFO,
            "title": "Price formatting",
            "suggestion": "Good: Using WC price formatting",
        },
    }

    # Shoptimizer performance patterns
    SHOPTIMIZER_PATTERNS = {
        r"wp_enqueue_script|wp_enqueue_style": {
            "severity": SeverityLevel.INFO,
            "title": "Asset enqueue",
            "suggestion": "Conditionally load scripts only where needed",
        },
        r"add_action.*wp_head": {
            "severity": SeverityLevel.LOW,
            "title": "Head action",
            "suggestion": "Minimize wp_head output for performance",
        },
        r"get_template_part\(": {
            "severity": SeverityLevel.INFO,
            "title": "Template part",
            "suggestion": "Consider fragment caching for expensive parts",
        },
    }

    # File security patterns
    FILE_SECURITY_PATTERNS = {
        r"move_uploaded_file|wp_handle_upload": {
            "severity": SeverityLevel.HIGH,
            "title": "File upload",
            "suggestion": "Validate file types, use WP upload functions",
        },
        r"file_get_contents\s*\(.*\$": {
            "severity": SeverityLevel.HIGH,
            "title": "Dynamic file read",
            "suggestion": "Validate and sanitize file paths",
        },
        r"include\s*\(.*\$|require\s*\(.*\$": {
            "severity": SeverityLevel.CRITICAL,
            "title": "Dynamic include",
            "suggestion": "Never include files based on user input (LFI risk)",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for WordPress security issues"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Only analyze PHP files
            if not rel_path.endswith(".php"):
                return issues

            all_patterns = [
                self.ELEMENTOR_PATTERNS,
                self.WP_SECURITY_PATTERNS,
                self.WOOCOMMERCE_PATTERNS,
                self.SHOPTIMIZER_PATTERNS,
                self.FILE_SECURITY_PATTERNS,
            ]

            for patterns in all_patterns:
                issues.extend(self._check_patterns(content, lines, rel_path, patterns))

        except Exception as e:
            logger.error(f"WordPress security analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(self, content, lines, rel_path, patterns):
        issues = []
        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.SECURITY,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                ))
        return issues


# =============================================================================
# Python Performance Hardening Toolkit
# =============================================================================


class PythonPerformanceToolkit:
    """
    Python Performance Hardening Toolkit.

    Based on 2025 best practices:
    - Async profiling patterns
    - Memory optimization (__slots__, generators)
    - Connection pool management
    - N+1 query detection
    - Event loop blocking detection

    References: Scalene, py-spy, Perfscope (2025).
    """

    # Memory optimization patterns
    MEMORY_PATTERNS = {
        r"__slots__\s*=": {
            "severity": SeverityLevel.INFO,
            "title": "__slots__ usage",
            "suggestion": "Good: Using __slots__ for memory optimization",
        },
        r"yield\s+": {
            "severity": SeverityLevel.INFO,
            "title": "Generator usage",
            "suggestion": "Good: Using generators for memory efficiency",
        },
        r"\[\s*x\s+for\s+x\s+in.*range\((\d+)": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Large list comprehension",
            "suggestion": "Consider generator expression for large ranges",
        },
        r"\.append\(.*\)\s*$": {
            "severity": SeverityLevel.INFO,
            "title": "List append in loop",
            "suggestion": "Consider list comprehension or extend() for better performance",
        },
    }

    # Async patterns
    ASYNC_PATTERNS = {
        r"async\s+def.*:\s*\n(?:(?!await).)*return": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Async without await",
            "suggestion": "Async function should contain await calls",
        },
        r"asyncio\.sleep\(0\)": {
            "severity": SeverityLevel.INFO,
            "title": "Event loop yield",
            "suggestion": "Good: Yielding control to event loop",
        },
        r"time\.sleep\(": {
            "severity": SeverityLevel.HIGH,
            "title": "Blocking sleep in async",
            "suggestion": "Use asyncio.sleep() in async code",
        },
        r"requests\.(get|post|put|delete)\(": {
            "severity": SeverityLevel.MEDIUM,
            "title": "Sync HTTP in async context",
            "suggestion": "Use aiohttp or httpx for async HTTP",
        },
    }

    # Database optimization
    DB_PATTERNS = {
        r"for\s+.*:\s*\n.*\.(query|filter|get)\(": {
            "severity": SeverityLevel.HIGH,
            "title": "N+1 query pattern",
            "suggestion": "Batch queries outside loop, use select_related/prefetch_related",
        },
        r"create_engine\(": {
            "severity": SeverityLevel.INFO,
            "title": "SQLAlchemy engine",
            "suggestion": "Configure pool_size and pool_recycle",
        },
        r"pool_size\s*=": {
            "severity": SeverityLevel.INFO,
            "title": "Connection pool configured",
            "suggestion": "Good: Configuring connection pool",
        },
    }

    # Caching patterns
    CACHING_PATTERNS = {
        r"@(lru_cache|cache|cached)": {
            "severity": SeverityLevel.INFO,
            "title": "Function caching",
            "suggestion": "Good: Using function caching",
        },
        r"functools\.lru_cache": {
            "severity": SeverityLevel.INFO,
            "title": "LRU cache",
            "suggestion": "Good: Using LRU cache for memoization",
        },
        r"redis|memcached": {
            "severity": SeverityLevel.INFO,
            "title": "Distributed cache",
            "suggestion": "Good: Using distributed caching",
        },
    }

    # Import optimization
    IMPORT_PATTERNS = {
        r"^import\s+\w+\s*$": {
            "severity": SeverityLevel.LOW,
            "title": "Full module import",
            "suggestion": "Import only needed symbols: from x import y",
        },
        r"from\s+\.\.\.\s+import": {
            "severity": SeverityLevel.INFO,
            "title": "Relative import",
            "suggestion": "Good: Using relative imports",
        },
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for performance issues"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            if not rel_path.endswith(".py"):
                return issues

            all_patterns = [
                self.MEMORY_PATTERNS,
                self.ASYNC_PATTERNS,
                self.DB_PATTERNS,
                self.CACHING_PATTERNS,
            ]

            for patterns in all_patterns:
                issues.extend(self._check_patterns(content, lines, rel_path, patterns))

        except Exception as e:
            logger.error(f"Performance analysis failed for {file_path}: {e}")

        return issues

    def _check_patterns(self, content, lines, rel_path, patterns):
        issues = []
        for pattern, config in patterns.items():
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=line_num,
                    category=IssueCategory.PERFORMANCE,
                    severity=config["severity"],
                    title=config["title"],
                    description=match.group(0)[:50],
                    suggestion=config.get("suggestion"),
                ))
        return issues


# =============================================================================
# 3D Rendering Automation Toolkit
# =============================================================================


class RenderAutomationToolkit:
    """
    Minimal verified 3D rendering automation tools.

    Patterns verified from:
    - Three.js official examples (github.com/mrdoob/three.js)
    - WebGL best practices (khronos.org)
    - Production rendering pipelines
    """

    # Render pipeline configuration patterns
    PIPELINE_PATTERNS = {
        "basic_renderer": {
            "code": '''
// Verified Three.js renderer setup
const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
    stencil: false,  // Disable if unused
    depth: true
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
''',
            "description": "Production-ready renderer initialization"
        },
        "shadow_config": {
            "code": '''
// Optimized shadow configuration
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;  // Manual update for static scenes

// Light shadow setup
directionalLight.castShadow = true;
directionalLight.shadow.mapSize.width = 2048;
directionalLight.shadow.mapSize.height = 2048;
directionalLight.shadow.camera.near = 0.1;
directionalLight.shadow.camera.far = 100;
directionalLight.shadow.bias = -0.0001;
''',
            "description": "Optimized shadow mapping"
        },
        "post_processing": {
            "code": '''
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
composer.addPass(new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.5,  // strength
    0.4,  // radius
    0.85  // threshold
));
composer.addPass(new SMAAPass(
    window.innerWidth * renderer.getPixelRatio(),
    window.innerHeight * renderer.getPixelRatio()
));
''',
            "description": "Post-processing pipeline with bloom and SMAA"
        }
    }

    # Batch rendering patterns
    BATCH_RENDER_PATTERNS = {
        "multi_view_capture": {
            "code": '''
async function captureMultipleViews(scene, camera, renderer, views) {
    const captures = [];
    const originalPosition = camera.position.clone();
    const originalRotation = camera.rotation.clone();

    for (const view of views) {
        camera.position.copy(view.position);
        camera.lookAt(view.target);
        renderer.render(scene, camera);

        const dataUrl = renderer.domElement.toDataURL('image/png');
        captures.push({
            name: view.name,
            data: dataUrl
        });
    }

    // Restore camera
    camera.position.copy(originalPosition);
    camera.rotation.copy(originalRotation);

    return captures;
}
''',
            "description": "Capture scene from multiple camera angles"
        },
        "turntable_render": {
            "code": '''
async function renderTurntable(scene, camera, renderer, frames = 36) {
    const captures = [];
    const radius = camera.position.length();
    const target = new THREE.Vector3(0, 0, 0);

    for (let i = 0; i < frames; i++) {
        const angle = (i / frames) * Math.PI * 2;
        camera.position.x = Math.cos(angle) * radius;
        camera.position.z = Math.sin(angle) * radius;
        camera.lookAt(target);

        renderer.render(scene, camera);
        captures.push(renderer.domElement.toDataURL('image/png'));
    }

    return captures;
}
''',
            "description": "360-degree turntable capture for product visualization"
        }
    }

    # Quality presets
    QUALITY_PRESETS = {
        "low": {
            "pixelRatio": 1,
            "antialias": False,
            "shadowMapSize": 512,
            "maxLights": 2,
            "postProcessing": False,
            "description": "Mobile/low-end devices"
        },
        "medium": {
            "pixelRatio": 1.5,
            "antialias": True,
            "shadowMapSize": 1024,
            "maxLights": 4,
            "postProcessing": True,
            "description": "Standard desktop"
        },
        "high": {
            "pixelRatio": 2,
            "antialias": True,
            "shadowMapSize": 2048,
            "maxLights": 8,
            "postProcessing": True,
            "description": "High-end desktop"
        },
        "ultra": {
            "pixelRatio": 2,
            "antialias": True,
            "shadowMapSize": 4096,
            "maxLights": 16,
            "postProcessing": True,
            "raytracing": True,
            "description": "Production rendering"
        }
    }

    # GPU resource management
    GPU_MANAGEMENT_PATTERNS = {
        "memory_cleanup": {
            "code": '''
function disposeScene(scene) {
    scene.traverse((object) => {
        if (object.geometry) {
            object.geometry.dispose();
        }
        if (object.material) {
            if (Array.isArray(object.material)) {
                object.material.forEach(m => disposeMaterial(m));
            } else {
                disposeMaterial(object.material);
            }
        }
    });
}

function disposeMaterial(material) {
    material.dispose();
    for (const key of Object.keys(material)) {
        const value = material[key];
        if (value && typeof value.dispose === 'function') {
            value.dispose();
        }
    }
}
''',
            "description": "Proper GPU memory cleanup"
        },
        "texture_pool": {
            "code": '''
class TexturePool {
    constructor(maxSize = 100) {
        this.pool = new Map();
        this.maxSize = maxSize;
        this.loader = new THREE.TextureLoader();
    }

    async get(url) {
        if (this.pool.has(url)) {
            return this.pool.get(url);
        }

        const texture = await this.loader.loadAsync(url);
        texture.colorSpace = THREE.SRGBColorSpace;

        if (this.pool.size >= this.maxSize) {
            const firstKey = this.pool.keys().next().value;
            this.pool.get(firstKey).dispose();
            this.pool.delete(firstKey);
        }

        this.pool.set(url, texture);
        return texture;
    }

    dispose() {
        this.pool.forEach(t => t.dispose());
        this.pool.clear();
    }
}
''',
            "description": "Texture caching with LRU eviction"
        }
    }

    # Frame capture patterns
    CAPTURE_PATTERNS = {
        "png_export": {
            "code": '''
function captureFrame(renderer, filename = 'render.png') {
    const dataUrl = renderer.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataUrl;
    link.click();
}
''',
            "description": "Single frame PNG export"
        },
        "video_recording": {
            "code": '''
class SceneRecorder {
    constructor(canvas, fps = 30) {
        this.canvas = canvas;
        this.fps = fps;
        this.chunks = [];
        this.mediaRecorder = null;
    }

    start() {
        const stream = this.canvas.captureStream(this.fps);
        this.mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'video/webm;codecs=vp9'
        });

        this.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                this.chunks.push(e.data);
            }
        };

        this.mediaRecorder.start();
    }

    stop() {
        return new Promise((resolve) => {
            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.chunks, { type: 'video/webm' });
                resolve(blob);
            };
            this.mediaRecorder.stop();
        });
    }
}
''',
            "description": "WebM video recording from canvas"
        },
        "high_res_capture": {
            "code": '''
function captureHighRes(renderer, scene, camera, scale = 2) {
    const originalSize = renderer.getSize(new THREE.Vector2());
    const originalPixelRatio = renderer.getPixelRatio();

    // Scale up
    renderer.setSize(originalSize.x * scale, originalSize.y * scale);
    renderer.setPixelRatio(1);
    renderer.render(scene, camera);

    const dataUrl = renderer.domElement.toDataURL('image/png');

    // Restore
    renderer.setSize(originalSize.x, originalSize.y);
    renderer.setPixelRatio(originalPixelRatio);

    return dataUrl;
}
''',
            "description": "High-resolution frame capture (2x-4x)"
        }
    }

    # Render loop patterns
    RENDER_LOOP_PATTERNS = {
        "optimized_loop": {
            "code": '''
let frameId = null;
let lastTime = 0;
const targetFPS = 60;
const frameInterval = 1000 / targetFPS;

function animate(currentTime) {
    frameId = requestAnimationFrame(animate);

    const deltaTime = currentTime - lastTime;
    if (deltaTime < frameInterval) return;

    lastTime = currentTime - (deltaTime % frameInterval);

    // Update logic here
    controls.update();

    // Render
    renderer.render(scene, camera);
}

function startLoop() {
    if (!frameId) {
        lastTime = performance.now();
        animate(lastTime);
    }
}

function stopLoop() {
    if (frameId) {
        cancelAnimationFrame(frameId);
        frameId = null;
    }
}
''',
            "description": "Frame-rate limited render loop"
        },
        "visibility_aware": {
            "code": '''
// Pause rendering when tab not visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopLoop();
    } else {
        startLoop();
    }
});

// Pause when window not focused (optional)
window.addEventListener('blur', stopLoop);
window.addEventListener('focus', startLoop);
''',
            "description": "Visibility-aware rendering to save resources"
        }
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def get_pipeline_pattern(self, name: str) -> dict | None:
        """Get a specific pipeline configuration pattern"""
        return self.PIPELINE_PATTERNS.get(name)

    def get_quality_preset(self, level: str) -> dict | None:
        """Get quality preset configuration"""
        return self.QUALITY_PRESETS.get(level)

    def get_batch_render_pattern(self, name: str) -> dict | None:
        """Get batch rendering pattern"""
        return self.BATCH_RENDER_PATTERNS.get(name)

    def get_capture_pattern(self, name: str) -> dict | None:
        """Get frame capture pattern"""
        return self.CAPTURE_PATTERNS.get(name)

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for 3D rendering issues"""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            # Check for common rendering issues
            patterns = {
                r"\.render\(\s*scene\s*,\s*camera\s*\)(?!.*composer)": {
                    "severity": SeverityLevel.INFO,
                    "title": "Direct render call",
                    "suggestion": "Consider using EffectComposer for post-processing",
                },
                r"setPixelRatio\(\s*window\.devicePixelRatio\s*\)": {
                    "severity": SeverityLevel.MEDIUM,
                    "title": "Uncapped pixel ratio",
                    "suggestion": "Cap pixel ratio: Math.min(window.devicePixelRatio, 2)",
                },
                r"requestAnimationFrame(?!.*cancel)": {
                    "severity": SeverityLevel.LOW,
                    "title": "RAF without cleanup",
                    "suggestion": "Store frame ID for cleanup: cancelAnimationFrame(frameId)",
                },
                r"new THREE\.Texture\(": {
                    "severity": SeverityLevel.LOW,
                    "title": "Manual texture creation",
                    "suggestion": "Use TextureLoader for proper color space handling",
                },
                r"\.dispose\(\)": {
                    "severity": SeverityLevel.INFO,
                    "title": "Resource disposal found",
                    "suggestion": "Good: Proper cleanup implemented",
                },
            }

            for pattern, config in patterns.items():
                matches = list(re.finditer(pattern, content))
                for match in matches:
                    line_num = content[:match.start()].count("\n") + 1
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=line_num,
                        category=IssueCategory.PERFORMANCE,
                        severity=config["severity"],
                        title=config["title"],
                        description=match.group(0)[:50],
                        suggestion=config.get("suggestion"),
                    ))

        except Exception as e:
            logger.error(f"Render analysis failed for {file_path}: {e}")

        return issues


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "ThreeJSToolkit",
    "LLMBestPracticesKB",
    "FrontendToolkit",
    "APIToolkit",
    "UIUXToolkit",
    "OWASP2025Toolkit",
    "PCIDSSToolkit",
    "WordPressSecurityToolkit",
    "PythonPerformanceToolkit",
    "RenderAutomationToolkit",
    "CodeIssue",
    "IssueCategory",
    "SeverityLevel",
]
