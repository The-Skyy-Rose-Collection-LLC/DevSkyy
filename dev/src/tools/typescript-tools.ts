/**
 * TypeScript Analysis Tools for Coding Architect Agent
 *
 * MCP tools for TypeScript/JavaScript code analysis, type checking,
 * and project configuration validation.
 */

import { createSdkMcpServer, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

/**
 * TypeScript Analysis MCP Server
 *
 * Provides tools for:
 * - Type checking and validation
 * - TSConfig analysis
 * - Dependency auditing
 * - Code complexity analysis
 * - ESLint integration
 */
export const typescriptToolsServer = createSdkMcpServer({
  name: "typescript-tools",
  version: "1.0.0",
  tools: [
    tool(
      "ts_type_check",
      "Run TypeScript type checking on a file or project. Returns type errors with file locations and suggestions.",
      {
        target: z
          .string()
          .describe(
            "File path or directory to type check. Use '.' for current directory."
          ),
        strict: z
          .boolean()
          .default(true)
          .describe("Enable strict mode for thorough checking"),
        noEmit: z
          .boolean()
          .default(true)
          .describe("Only check types, don't emit JavaScript"),
      },
      async (args) => {
        const { target, strict, noEmit } = args;

        const flags = [];
        if (strict) flags.push("--strict");
        if (noEmit) flags.push("--noEmit");

        const command = `npx tsc ${flags.join(" ")} ${target === "." ? "" : target}`;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  command,
                  description: `Type check ${target} with${strict ? "" : "out"} strict mode`,
                  instructions:
                    "Execute this command to run type checking. Parse the output for any type errors.",
                },
                null,
                2
              ),
            },
          ],
        };
      }
    ),

    tool(
      "ts_analyze_config",
      "Analyze a tsconfig.json file for best practices, potential issues, and optimization opportunities.",
      {
        configPath: z
          .string()
          .default("tsconfig.json")
          .describe("Path to tsconfig.json file"),
      },
      async (args) => {
        const bestPractices = {
          compilerOptions: {
            strict: {
              recommended: true,
              description: "Enables all strict type checking options",
            },
            noUncheckedIndexedAccess: {
              recommended: true,
              description:
                "Adds undefined to index signature results for safer array/object access",
            },
            noImplicitReturns: {
              recommended: true,
              description: "Ensures all code paths return a value",
            },
            noFallthroughCasesInSwitch: {
              recommended: true,
              description: "Prevents accidental switch case fallthrough",
            },
            exactOptionalPropertyTypes: {
              recommended: true,
              description:
                "Distinguishes between undefined and missing properties",
            },
            noPropertyAccessFromIndexSignature: {
              recommended: true,
              description: "Forces bracket notation for index signature access",
            },
            forceConsistentCasingInFileNames: {
              recommended: true,
              description: "Prevents case-sensitivity issues across platforms",
            },
            skipLibCheck: {
              recommended: true,
              description:
                "Skips type checking .d.ts files for faster compilation",
            },
            moduleResolution: {
              recommended: "NodeNext",
              description: "Modern module resolution for ESM support",
            },
            module: {
              recommended: "NodeNext",
              description: "ESM module output for modern JavaScript",
            },
            target: {
              recommended: "ES2022",
              description: "Modern JavaScript features with good browser support",
            },
          },
        };

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  configPath: args.configPath,
                  bestPractices,
                  instructions:
                    "Read the tsconfig.json file and compare against these best practices. Report any missing or suboptimal settings.",
                },
                null,
                2
              ),
            },
          ],
        };
      }
    ),

    tool(
      "ts_dependency_audit",
      "Audit TypeScript project dependencies for type coverage, outdated packages, and security issues.",
      {
        packageJsonPath: z
          .string()
          .default("package.json")
          .describe("Path to package.json file"),
        checkTypes: z
          .boolean()
          .default(true)
          .describe("Check for missing @types packages"),
        checkOutdated: z
          .boolean()
          .default(true)
          .describe("Check for outdated packages"),
        checkSecurity: z
          .boolean()
          .default(true)
          .describe("Run npm audit for security issues"),
      },
      async (args) => {
        const commands = [];

        if (args.checkOutdated) {
          commands.push({
            name: "Check outdated packages",
            command: "npm outdated --json",
          });
        }

        if (args.checkSecurity) {
          commands.push({
            name: "Security audit",
            command: "npm audit --json",
          });
        }

        commands.push({
          name: "List installed packages",
          command: "npm ls --json --depth=0",
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  packageJsonPath: args.packageJsonPath,
                  commands,
                  typeCheckingGuidelines: {
                    missingTypes:
                      "For packages without built-in types, check if @types/{package} exists",
                    bundledTypes:
                      "Modern packages often include types - check 'types' or 'typings' field in package.json",
                    typeVersions:
                      "Ensure @types versions match the main package version",
                  },
                },
                null,
                2
              ),
            },
          ],
        };
      }
    ),

    tool(
      "ts_analyze_complexity",
      "Analyze code complexity metrics including cyclomatic complexity, cognitive complexity, and lines of code.",
      {
        filePath: z.string().describe("Path to the TypeScript file to analyze"),
        thresholds: z
          .object({
            cyclomaticComplexity: z.number().default(10),
            linesPerFunction: z.number().default(50),
            parametersPerFunction: z.number().default(4),
          })
          .optional()
          .describe("Complexity thresholds for warnings"),
      },
      async (args) => {
        const metrics = {
          cyclomaticComplexity: {
            description:
              "Number of linearly independent paths through code. High values indicate complex logic.",
            calculation:
              "Count: if, else if, case, for, while, &&, ||, ?, catch",
            thresholds: {
              low: "1-5: Simple, easy to test",
              moderate: "6-10: Moderate complexity",
              high: "11-20: Complex, consider refactoring",
              veryHigh: "20+: Very complex, refactoring recommended",
            },
          },
          cognitiveComplexity: {
            description:
              "Measures how difficult code is to understand. Accounts for nesting depth.",
            factors:
              "Nesting, breaks in linear flow, recursion, boolean operators",
          },
          maintainabilityIndex: {
            description:
              "Composite metric combining Halstead volume, cyclomatic complexity, and LOC",
            scale: "0-100, higher is better. Below 65 indicates maintenance risk.",
          },
        };

        const defaultThresholds = {
          cyclomaticComplexity: 10,
          linesPerFunction: 50,
          parametersPerFunction: 4,
        };

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  filePath: args.filePath,
                  metrics,
                  thresholds: args.thresholds ?? defaultThresholds,
                  instructions:
                    "Analyze the file and calculate these metrics. Report functions exceeding thresholds.",
                },
                null,
                2
              ),
            },
          ],
        };
      }
    ),

    tool(
      "ts_lint_check",
      "Run ESLint/Biome analysis on TypeScript files with recommended rules.",
      {
        target: z.string().describe("File or directory to lint"),
        fix: z.boolean().default(false).describe("Auto-fix fixable issues"),
        format: z
          .enum(["stylish", "json", "compact"])
          .default("json")
          .describe("Output format"),
      },
      async (args) => {
        const eslintCommand = `npx eslint ${args.target} --format ${args.format}${args.fix ? " --fix" : ""}`;
        const biomeCommand = `npx biome check ${args.target}${args.fix ? " --apply" : ""}`;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  commands: {
                    eslint: eslintCommand,
                    biome: biomeCommand,
                  },
                  recommendedRules: {
                    typescript: [
                      "@typescript-eslint/no-explicit-any",
                      "@typescript-eslint/explicit-function-return-type",
                      "@typescript-eslint/no-unused-vars",
                      "@typescript-eslint/strict-boolean-expressions",
                      "@typescript-eslint/no-floating-promises",
                    ],
                    general: [
                      "no-console",
                      "prefer-const",
                      "no-var",
                      "eqeqeq",
                    ],
                  },
                  instructions:
                    "Run one of these linting commands based on project configuration.",
                },
                null,
                2
              ),
            },
          ],
        };
      }
    ),

    tool(
      "ts_generate_types",
      "Generate TypeScript type definitions from various sources.",
      {
        source: z
          .enum(["json", "api", "graphql", "prisma"])
          .describe("Source type to generate from"),
        input: z
          .string()
          .describe("Input file path or URL for type generation"),
        outputPath: z
          .string()
          .optional()
          .describe("Output path for generated types"),
      },
      async (args) => {
        const generators: Record<
          string,
          { tool: string; command: string; description: string }
        > = {
          json: {
            tool: "quicktype",
            command: `npx quicktype ${args.input} -o ${args.outputPath || "types.ts"} -l typescript --just-types`,
            description:
              "Generate types from JSON samples using quicktype",
          },
          api: {
            tool: "openapi-typescript",
            command: `npx openapi-typescript ${args.input} -o ${args.outputPath || "api-types.ts"}`,
            description:
              "Generate types from OpenAPI/Swagger specifications",
          },
          graphql: {
            tool: "graphql-codegen",
            command: `npx graphql-codegen --config codegen.yml`,
            description:
              "Generate types from GraphQL schema (requires codegen.yml)",
          },
          prisma: {
            tool: "prisma",
            command: "npx prisma generate",
            description: "Generate Prisma client types from schema.prisma",
          },
        };

        const generator = generators[args.source];

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  source: args.source,
                  generator,
                  alternatives: generators,
                  bestPractices: [
                    "Keep generated types in a separate directory",
                    "Add generated files to .gitignore if regenerated on build",
                    "Use strict type checking on generated types",
                    "Consider runtime validation with zod for external data",
                  ],
                },
                null,
                2
              ),
            },
          ],
        };
      }
    ),
  ],
});

export default typescriptToolsServer;
