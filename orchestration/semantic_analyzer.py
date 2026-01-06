"""
Semantic Code Analyzer
=======================

Provides deep semantic understanding of code beyond syntax.

Features:
- AST-based code analysis (classes, functions, relationships)
- Pattern detection (design patterns, anti-patterns)
- Code flow and dependency analysis
- Semantic embeddings for code similarity
- Integration with RAG for context-aware analysis

Pattern from:
- Static analysis tools (pylint, mypy, radon)
- Code2Vec/CodeBERT semantic embeddings
- Enterprise code search (GitHub CodeQL)

Usage:
    analyzer = SemanticCodeAnalyzer()
    analysis = await analyzer.analyze_file("agents/commerce_agent.py")
    similar_code = await analyzer.find_similar_code(code_snippet)
"""

from __future__ import annotations

import ast
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CodePatternType(str, Enum):
    """Design pattern categories"""

    # Design Patterns
    SINGLETON = "singleton"
    FACTORY = "factory"
    STRATEGY = "strategy"
    OBSERVER = "observer"
    DECORATOR = "decorator"

    # Anti-Patterns
    GOD_CLASS = "god_class"
    LONG_METHOD = "long_method"
    DEAD_CODE = "dead_code"
    DUPLICATE_CODE = "duplicate_code"
    CIRCULAR_DEPENDENCY = "circular_dependency"

    # Code Smells
    MAGIC_NUMBER = "magic_number"
    EXCESSIVE_PARAMS = "excessive_params"
    DEEP_NESTING = "deep_nesting"
    UNUSED_VARIABLE = "unused_variable"


@dataclass
class CodeSymbol:
    """Represents a code symbol (class, function, variable)"""

    name: str
    type: str  # "class", "function", "method", "variable"
    file_path: str
    line_number: int
    col_offset: int
    docstring: str | None = None
    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = field(default_factory=list)
    async_func: bool = False
    complexity: int = 0  # Cyclomatic complexity
    dependencies: list[str] = field(default_factory=list)


@dataclass
class CodePattern:
    """Detected code pattern"""

    pattern_type: CodePatternType
    file_path: str
    line_number: int
    severity: str  # "info", "warning", "error", "critical"
    description: str
    suggestion: str | None = None
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class SemanticAnalysis:
    """Complete semantic analysis result"""

    file_path: str
    analyzed_at: datetime
    symbols: list[CodeSymbol] = field(default_factory=list)
    patterns: list[CodePattern] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    lines_of_code: int = 0
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    embedding: list[float] | None = None  # Semantic embedding vector


class SemanticCodeAnalyzer:
    """
    Deep semantic code analysis using AST and pattern detection.

    Capabilities:
    - Symbol extraction (classes, functions, variables)
    - Pattern detection (design patterns, anti-patterns)
    - Complexity analysis (cyclomatic, maintainability)
    - Dependency graph construction
    - Semantic similarity via embeddings
    """

    __slots__ = ("cache", "_embedding_model")

    def __init__(self) -> None:
        """Initialize semantic analyzer"""
        self.cache: dict[str, SemanticAnalysis] = {}
        self._embedding_model: Any = None  # Lazy load sentence-transformers

    async def analyze_file(self, file_path: str | Path) -> SemanticAnalysis:
        """
        Perform deep semantic analysis on a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            SemanticAnalysis with symbols, patterns, metrics

        Raises:
            FileNotFoundError: If file doesn't exist
            SyntaxError: If file contains invalid Python
        """
        file_path = Path(file_path)

        # Check cache (invalidate if file modified)
        cache_key = self._get_cache_key(file_path)
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {file_path}")
            return self.cache[cache_key]

        logger.info(f"Analyzing {file_path}...")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        with open(file_path, encoding="utf-8") as f:
            source_code = f.read()

        # Parse AST
        try:
            tree = ast.parse(source_code, filename=str(file_path))
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            raise

        # Extract semantic information
        analysis = SemanticAnalysis(
            file_path=str(file_path),
            analyzed_at=datetime.now(UTC),
        )

        # 1. Extract symbols (classes, functions)
        analysis.symbols = self._extract_symbols(tree, file_path)

        # 2. Extract imports
        analysis.imports = self._extract_imports(tree)

        # 3. Detect patterns
        analysis.patterns = self._detect_patterns(tree, file_path, source_code)

        # 4. Calculate metrics
        analysis.lines_of_code = len(source_code.splitlines())
        analysis.complexity_score = self._calculate_complexity(tree)
        analysis.maintainability_index = self._calculate_maintainability(
            analysis.complexity_score, analysis.lines_of_code
        )

        # 5. Generate semantic embedding
        analysis.embedding = await self._generate_embedding(source_code)

        # 6. Extract top-level entities
        analysis.classes = [s.name for s in analysis.symbols if s.type == "class"]
        analysis.functions = [
            s.name for s in analysis.symbols if s.type in ("function", "method")
        ]

        # Cache result
        self.cache[cache_key] = analysis

        logger.info(
            f"✅ Analyzed {file_path}: "
            f"{len(analysis.symbols)} symbols, "
            f"{len(analysis.patterns)} patterns, "
            f"complexity={analysis.complexity_score:.1f}"
        )

        return analysis

    def _extract_symbols(self, tree: ast.AST, file_path: Path) -> list[CodeSymbol]:
        """Extract all code symbols from AST"""
        symbols: list[CodeSymbol] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract class
                symbols.append(
                    CodeSymbol(
                        name=node.name,
                        type="class",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        col_offset=node.col_offset,
                        docstring=ast.get_docstring(node),
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    )
                )

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Extract function/method
                symbols.append(
                    CodeSymbol(
                        name=node.name,
                        type="function" if isinstance(node, ast.FunctionDef) else "method",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        col_offset=node.col_offset,
                        docstring=ast.get_docstring(node),
                        parameters=[arg.arg for arg in node.args.args],
                        return_type=self._get_return_annotation(node),
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                        async_func=isinstance(node, ast.AsyncFunctionDef),
                        complexity=self._calculate_function_complexity(node),
                    )
                )

        return symbols

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extract all import statements"""
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    def _detect_patterns(
        self, tree: ast.AST, file_path: Path, source_code: str
    ) -> list[CodePattern]:
        """Detect design patterns and anti-patterns"""
        patterns: list[CodePattern] = []

        # 1. Detect God Class (class with >15 methods)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(
                    1
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                if method_count > 15:
                    patterns.append(
                        CodePattern(
                            pattern_type=CodePatternType.GOD_CLASS,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            severity="warning",
                            description=f"Class '{node.name}' has {method_count} methods (anti-pattern: God Class)",
                            suggestion="Consider splitting into smaller, focused classes",
                            confidence=0.9,
                        )
                    )

        # 2. Detect Long Methods (>50 lines)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, "end_lineno"):
                    method_length = node.end_lineno - node.lineno
                    if method_length > 50:
                        patterns.append(
                            CodePattern(
                                pattern_type=CodePatternType.LONG_METHOD,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                severity="warning",
                                description=f"Function '{node.name}' is {method_length} lines (anti-pattern: Long Method)",
                                suggestion="Break into smaller functions",
                                confidence=0.85,
                            )
                        )

        # 3. Detect Excessive Parameters (>5 params)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args)
                if param_count > 5:
                    patterns.append(
                        CodePattern(
                            pattern_type=CodePatternType.EXCESSIVE_PARAMS,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            severity="info",
                            description=f"Function '{node.name}' has {param_count} parameters",
                            suggestion="Consider using a config object or **kwargs",
                            confidence=0.8,
                        )
                    )

        # 4. Detect Magic Numbers
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if node.value not in (0, 1, -1, 100):  # Exclude common values
                        patterns.append(
                            CodePattern(
                                pattern_type=CodePatternType.MAGIC_NUMBER,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                severity="info",
                                description=f"Magic number: {node.value}",
                                suggestion="Extract to named constant",
                                confidence=0.7,
                            )
                        )

        return patterns

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate average cyclomatic complexity"""
        complexities: list[int] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexities.append(self._calculate_function_complexity(node))

        return sum(complexities) / len(complexities) if complexities else 1.0

    def _calculate_function_complexity(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Each decision point adds 1
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator adds 1
                complexity += len(child.values) - 1

        return complexity

    def _calculate_maintainability(self, complexity: float, loc: int) -> float:
        """
        Calculate maintainability index (0-100 scale)

        MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)

        Simplified version based on complexity and LOC
        """
        import math

        if loc == 0:
            return 100.0

        # Simplified maintainability index
        mi = 171 - 5.2 * math.log(max(loc, 1)) - 0.23 * complexity

        # Normalize to 0-100
        mi = max(0.0, min(100.0, mi))

        return mi

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return "unknown"

    def _get_return_annotation(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
        """Extract return type annotation"""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return str(node.returns.value)
        return None

    async def _generate_embedding(self, source_code: str) -> list[float] | None:
        """
        Generate semantic embedding for code.

        Uses sentence-transformers (MiniLM) for code similarity.
        """
        try:
            if self._embedding_model is None:
                # Lazy load sentence-transformers
                from sentence_transformers import SentenceTransformer

                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence-transformers model")

            # Generate embedding
            embedding = self._embedding_model.encode(source_code)
            return embedding.tolist()

        except ImportError:
            logger.warning("sentence-transformers not installed - embeddings disabled")
            return None
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key based on file path and modification time"""
        mtime = file_path.stat().st_mtime
        return hashlib.md5(f"{file_path}:{mtime}".encode()).hexdigest()

    async def find_similar_code(
        self, code_snippet: str, threshold: float = 0.7
    ) -> list[tuple[str, float]]:
        """
        Find similar code across analyzed files using semantic embeddings.

        Args:
            code_snippet: Code to find similar matches for
            threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of (file_path, similarity_score) tuples
        """
        if not self._embedding_model:
            logger.warning("Embeddings not available - cannot find similar code")
            return []

        # Generate embedding for query snippet
        query_embedding = await self._generate_embedding(code_snippet)

        if query_embedding is None:
            return []

        # Calculate similarity with cached analyses
        results: list[tuple[str, float]] = []

        for analysis in self.cache.values():
            if analysis.embedding is None:
                continue

            # Cosine similarity
            similarity = self._cosine_similarity(query_embedding, analysis.embedding)

            if similarity >= threshold:
                results.append((analysis.file_path, similarity))

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def clear_cache(self) -> None:
        """Clear analysis cache"""
        self.cache.clear()
        logger.info("Semantic analysis cache cleared")


# Singleton instance
_semantic_analyzer: SemanticCodeAnalyzer | None = None


def get_semantic_analyzer() -> SemanticCodeAnalyzer:
    """Get singleton semantic analyzer instance"""
    global _semantic_analyzer
    if _semantic_analyzer is None:
        _semantic_analyzer = SemanticCodeAnalyzer()
    return _semantic_analyzer
