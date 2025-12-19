"""
TypeScript Analysis Tools for Coding Architect Agent (Python SDK)

MCP tools for TypeScript/JavaScript code analysis, type checking,
and project configuration validation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""

    content: str
    is_error: bool = False


class TypeScriptTools:
    """
    TypeScript Analysis Tools

    Provides methods for:
    - Type checking and validation
    - TSConfig analysis
    - Dependency auditing
    - Code complexity analysis
    - ESLint integration
    """

    @staticmethod
    def type_check(
        target: str = ".",
        strict: bool = True,
        no_emit: bool = True,
    ) -> dict[str, Any]:
        """
        Run TypeScript type checking on a file or project.

        Args:
            target: File path or directory to type check
            strict: Enable strict mode
            no_emit: Only check types, don't emit JavaScript

        Returns:
            Command and configuration for type checking
        """
        flags = []
        if strict:
            flags.append("--strict")
        if no_emit:
            flags.append("--noEmit")

        command = f"npx tsc {' '.join(flags)} {target if target != '.' else ''}"

        return {
            "command": command.strip(),
            "description": f"Type check {target} with{'out' if not strict else ''} strict mode",
            "instructions": "Execute this command to run type checking. Parse output for errors.",
        }

    @staticmethod
    def analyze_config(config_path: str = "tsconfig.json") -> dict[str, Any]:
        """
        Analyze tsconfig.json for best practices.

        Args:
            config_path: Path to tsconfig.json file

        Returns:
            Best practices and recommendations
        """
        return {
            "configPath": config_path,
            "bestPractices": {
                "compilerOptions": {
                    "strict": {
                        "recommended": True,
                        "description": "Enables all strict type checking options",
                    },
                    "noUncheckedIndexedAccess": {
                        "recommended": True,
                        "description": "Adds undefined to index signature results",
                    },
                    "noImplicitReturns": {
                        "recommended": True,
                        "description": "Ensures all code paths return a value",
                    },
                    "noFallthroughCasesInSwitch": {
                        "recommended": True,
                        "description": "Prevents accidental switch case fallthrough",
                    },
                    "exactOptionalPropertyTypes": {
                        "recommended": True,
                        "description": "Distinguishes undefined from missing properties",
                    },
                    "moduleResolution": {
                        "recommended": "NodeNext",
                        "description": "Modern module resolution for ESM support",
                    },
                    "module": {
                        "recommended": "NodeNext",
                        "description": "ESM module output",
                    },
                    "target": {
                        "recommended": "ES2022",
                        "description": "Modern JavaScript features",
                    },
                }
            },
            "instructions": "Compare tsconfig.json against these best practices.",
        }

    @staticmethod
    def dependency_audit(
        package_json_path: str = "package.json",
        check_types: bool = True,
        check_outdated: bool = True,
        check_security: bool = True,
    ) -> dict[str, Any]:
        """
        Audit TypeScript project dependencies.

        Args:
            package_json_path: Path to package.json
            check_types: Check for missing @types packages
            check_outdated: Check for outdated packages
            check_security: Run npm audit

        Returns:
            Commands and guidelines for dependency audit
        """
        commands = []

        if check_outdated:
            commands.append({
                "name": "Check outdated packages",
                "command": "npm outdated --json",
            })

        if check_security:
            commands.append({
                "name": "Security audit",
                "command": "npm audit --json",
            })

        commands.append({
            "name": "List installed packages",
            "command": "npm ls --json --depth=0",
        })

        return {
            "packageJsonPath": package_json_path,
            "commands": commands,
            "typeCheckingGuidelines": {
                "missingTypes": "Check if @types/{package} exists",
                "bundledTypes": "Modern packages often include types",
                "typeVersions": "Ensure @types versions match main package",
            },
        }

    @staticmethod
    def analyze_complexity(
        file_path: str,
        cyclomatic_threshold: int = 10,
        lines_per_function: int = 50,
        parameters_per_function: int = 4,
    ) -> dict[str, Any]:
        """
        Analyze code complexity metrics.

        Args:
            file_path: Path to TypeScript file
            cyclomatic_threshold: Max cyclomatic complexity
            lines_per_function: Max lines per function
            parameters_per_function: Max parameters per function

        Returns:
            Complexity metrics and thresholds
        """
        return {
            "filePath": file_path,
            "metrics": {
                "cyclomaticComplexity": {
                    "description": "Number of independent paths through code",
                    "thresholds": {
                        "low": "1-5: Simple, easy to test",
                        "moderate": "6-10: Moderate complexity",
                        "high": "11-20: Complex, consider refactoring",
                        "veryHigh": "20+: Very complex, refactoring recommended",
                    },
                },
                "cognitiveComplexity": {
                    "description": "Measures how difficult code is to understand",
                },
                "maintainabilityIndex": {
                    "description": "Composite metric (0-100, higher is better)",
                },
            },
            "thresholds": {
                "cyclomaticComplexity": cyclomatic_threshold,
                "linesPerFunction": lines_per_function,
                "parametersPerFunction": parameters_per_function,
            },
        }

    @staticmethod
    def lint_check(
        target: str,
        fix: bool = False,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Run ESLint/Biome analysis.

        Args:
            target: File or directory to lint
            fix: Auto-fix fixable issues
            output_format: Output format (stylish, json, compact)

        Returns:
            Linting commands and recommended rules
        """
        eslint_cmd = f"npx eslint {target} --format {output_format}"
        if fix:
            eslint_cmd += " --fix"

        biome_cmd = f"npx biome check {target}"
        if fix:
            biome_cmd += " --apply"

        return {
            "commands": {
                "eslint": eslint_cmd,
                "biome": biome_cmd,
            },
            "recommendedRules": {
                "typescript": [
                    "@typescript-eslint/no-explicit-any",
                    "@typescript-eslint/explicit-function-return-type",
                    "@typescript-eslint/no-unused-vars",
                    "@typescript-eslint/strict-boolean-expressions",
                    "@typescript-eslint/no-floating-promises",
                ],
                "general": [
                    "no-console",
                    "prefer-const",
                    "no-var",
                    "eqeqeq",
                ],
            },
        }

    @staticmethod
    def generate_types(
        source: str,
        input_path: str,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate TypeScript type definitions.

        Args:
            source: Source type (json, api, graphql, prisma)
            input_path: Input file path or URL
            output_path: Output path for generated types

        Returns:
            Generation commands and alternatives
        """
        generators = {
            "json": {
                "tool": "quicktype",
                "command": f"npx quicktype {input_path} -o {output_path or 'types.ts'} -l typescript --just-types",
                "description": "Generate types from JSON samples",
            },
            "api": {
                "tool": "openapi-typescript",
                "command": f"npx openapi-typescript {input_path} -o {output_path or 'api-types.ts'}",
                "description": "Generate types from OpenAPI specifications",
            },
            "graphql": {
                "tool": "graphql-codegen",
                "command": "npx graphql-codegen --config codegen.yml",
                "description": "Generate types from GraphQL schema",
            },
            "prisma": {
                "tool": "prisma",
                "command": "npx prisma generate",
                "description": "Generate Prisma client types",
            },
        }

        return {
            "source": source,
            "generator": generators.get(source, {}),
            "alternatives": generators,
            "bestPractices": [
                "Keep generated types in a separate directory",
                "Add generated files to .gitignore if regenerated on build",
                "Use strict type checking on generated types",
            ],
        }
