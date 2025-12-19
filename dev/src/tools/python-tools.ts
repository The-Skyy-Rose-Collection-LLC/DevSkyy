/**
 * Python Analysis Tools for Coding Architect Agent (TypeScript SDK)
 *
 * MCP tools for Python code analysis, type checking,
 * linting, and project configuration validation.
 */

import { createSdkMcpServer, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

/**
 * Python Analysis MCP Server
 *
 * Provides tools for:
 * - Type checking with mypy/pyright
 * - Linting with ruff/pylint/flake8
 * - Dependency analysis
 * - Code complexity metrics
 * - Virtual environment management
 */
export const pythonToolsServer = createSdkMcpServer({
  name: "python-tools",
  version: "1.0.0",
  tools: [
    tool(
      "py_type_check",
      "Run Python type checking using mypy or pyright. Returns type errors with file locations.",
      {
        target: z
          .string()
          .describe("File path or directory to type check"),
        checker: z
          .enum(["mypy", "pyright", "basedpyright"])
          .default("mypy")
          .describe("Type checker to use"),
        strict: z
          .boolean()
          .default(true)
          .describe("Enable strict mode for thorough checking"),
      },
      async (args) => {
        const { target, checker, strict } = args;

        const commands: Record<string, { cmd: string; install: string }> = {
          mypy: {
            cmd: `mypy ${strict ? "--strict" : ""} ${target}`,
            install: "pip install mypy",
          },
          pyright: {
            cmd: `pyright ${strict ? "--strict" : ""} ${target}`,
            install: "pip install pyright",
          },
          basedpyright: {
            cmd: `basedpyright ${strict ? "--strict" : ""} ${target}`,
            install: "pip install basedpyright",
          },
        };

        const selected = commands[checker];

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  checker,
                  command: selected.cmd,
                  install: selected.install,
                  strictModeSettings: {
                    mypy: [
                      "--disallow-untyped-defs",
                      "--disallow-incomplete-defs",
                      "--check-untyped-defs",
                      "--disallow-untyped-decorators",
                      "--no-implicit-optional",
                      "--warn-redundant-casts",
                      "--warn-unused-ignores",
                      "--warn-return-any",
                    ],
                    pyright: {
                      typeCheckingMode: "strict",
                      reportMissingTypeStubs: true,
                      reportUnknownMemberType: true,
                    },
                  },
                  instructions:
                    "Execute the command and parse output for type errors.",
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
      "py_lint",
      "Run Python linting using ruff, pylint, or flake8.",
      {
        target: z.string().describe("File or directory to lint"),
        linter: z
          .enum(["ruff", "pylint", "flake8"])
          .default("ruff")
          .describe("Linter to use (ruff is fastest and most modern)"),
        fix: z
          .boolean()
          .default(false)
          .describe("Auto-fix fixable issues (ruff only)"),
        format: z
          .enum(["text", "json", "github"])
          .default("json")
          .describe("Output format"),
      },
      async (args) => {
        const { target, linter, fix, format } = args;

        const commands: Record<
          string,
          { check: string; fix?: string; install: string }
        > = {
          ruff: {
            check: `ruff check ${target} --output-format ${format}`,
            fix: `ruff check ${target} --fix`,
            install: "pip install ruff",
          },
          pylint: {
            check: `pylint ${target} --output-format=${format === "json" ? "json" : "text"}`,
            install: "pip install pylint",
          },
          flake8: {
            check: `flake8 ${target} --format=${format === "json" ? "json" : "default"}`,
            install: "pip install flake8",
          },
        };

        const selected = commands[linter];
        const cmd = fix && selected.fix ? selected.fix : selected.check;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  linter,
                  command: cmd,
                  install: selected.install,
                  recommendedRuffRules: {
                    enabled: ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "T10", "SIM"],
                    description: {
                      E: "pycodestyle errors",
                      F: "pyflakes",
                      W: "pycodestyle warnings",
                      I: "isort",
                      N: "pep8-naming",
                      UP: "pyupgrade",
                      B: "flake8-bugbear",
                      A: "flake8-builtins",
                      C4: "flake8-comprehensions",
                      T10: "flake8-debugger",
                      SIM: "flake8-simplify",
                    },
                  },
                  pyprojectTomlExample: `[tool.ruff]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4"]
target-version = "py311"
line-length = 88

[tool.ruff.isort]
known-first-party = ["your_package"]`,
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
      "py_format",
      "Format Python code using black, ruff format, or isort.",
      {
        target: z.string().describe("File or directory to format"),
        formatter: z
          .enum(["black", "ruff", "autopep8"])
          .default("ruff")
          .describe("Formatter to use"),
        check: z
          .boolean()
          .default(false)
          .describe("Check only, don't modify files"),
        lineLength: z
          .number()
          .default(88)
          .describe("Maximum line length"),
      },
      async (args) => {
        const { target, formatter, check, lineLength } = args;

        const commands: Record<string, { cmd: string; install: string }> = {
          black: {
            cmd: `black ${check ? "--check" : ""} --line-length ${lineLength} ${target}`,
            install: "pip install black",
          },
          ruff: {
            cmd: `ruff format ${check ? "--check" : ""} --line-length ${lineLength} ${target}`,
            install: "pip install ruff",
          },
          autopep8: {
            cmd: `autopep8 ${check ? "--diff" : "--in-place"} --max-line-length ${lineLength} ${target}`,
            install: "pip install autopep8",
          },
        };

        const selected = commands[formatter];

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  formatter,
                  command: selected.cmd,
                  install: selected.install,
                  isortIntegration: {
                    command: `isort ${check ? "--check-only" : ""} ${target}`,
                    ruffHasIsort:
                      "Ruff includes isort functionality with the 'I' rule",
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
      "py_dependency_audit",
      "Audit Python project dependencies for security vulnerabilities and outdated packages.",
      {
        requirementsPath: z
          .string()
          .default("requirements.txt")
          .describe("Path to requirements file"),
        checkSecurity: z
          .boolean()
          .default(true)
          .describe("Run safety/pip-audit for security issues"),
        checkOutdated: z
          .boolean()
          .default(true)
          .describe("Check for outdated packages"),
      },
      async (args) => {
        const commands = [];

        if (args.checkOutdated) {
          commands.push({
            name: "Check outdated packages",
            command: "pip list --outdated --format json",
          });
        }

        if (args.checkSecurity) {
          commands.push({
            name: "Security audit (pip-audit)",
            command: "pip-audit --format json",
            install: "pip install pip-audit",
          });
          commands.push({
            name: "Security audit (safety)",
            command: `safety check -r ${args.requirementsPath} --json`,
            install: "pip install safety",
          });
        }

        commands.push({
          name: "Dependency tree",
          command: "pipdeptree --json",
          install: "pip install pipdeptree",
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  requirementsPath: args.requirementsPath,
                  commands,
                  bestPractices: [
                    "Pin exact versions in production (package==1.2.3)",
                    "Use >= for development dependencies",
                    "Regularly run pip-audit for security updates",
                    "Consider using poetry or pip-tools for lock files",
                    "Separate dev and prod requirements",
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

    tool(
      "py_venv_info",
      "Get information about Python virtual environments and package installations.",
      {
        pythonPath: z
          .string()
          .optional()
          .describe("Path to Python interpreter"),
      },
      async (args) => {
        const commands = [
          {
            name: "Python version",
            command: `${args.pythonPath || "python3"} --version`,
          },
          {
            name: "Pip version",
            command: `${args.pythonPath || "python3"} -m pip --version`,
          },
          {
            name: "Virtual env location",
            command: `${args.pythonPath || "python3"} -c "import sys; print(sys.prefix)"`,
          },
          {
            name: "Installed packages",
            command: `${args.pythonPath || "python3"} -m pip list --format json`,
          },
          {
            name: "Site packages path",
            command: `${args.pythonPath || "python3"} -c "import site; print(site.getsitepackages())"`,
          },
        ];

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  commands,
                  venvCreation: {
                    venv: "python3 -m venv .venv",
                    virtualenv: "virtualenv .venv",
                    conda: "conda create -n myenv python=3.11",
                    uv: "uv venv .venv",
                  },
                  activation: {
                    unix: "source .venv/bin/activate",
                    windows: ".venv\\Scripts\\activate",
                    fish: "source .venv/bin/activate.fish",
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
      "py_analyze_complexity",
      "Analyze Python code complexity using radon or mccabe.",
      {
        target: z.string().describe("File or directory to analyze"),
        metrics: z
          .array(z.enum(["cc", "mi", "raw", "hal"]))
          .default(["cc", "mi"])
          .describe(
            "Metrics to compute: cc=cyclomatic, mi=maintainability, raw=LOC, hal=Halstead"
          ),
      },
      async (args) => {
        const { target, metrics } = args;

        const metricCommands: Record<
          string,
          { cmd: string; description: string }
        > = {
          cc: {
            cmd: `radon cc ${target} -a -j`,
            description: "Cyclomatic Complexity - measures code paths",
          },
          mi: {
            cmd: `radon mi ${target} -j`,
            description:
              "Maintainability Index - composite metric (0-100, higher is better)",
          },
          raw: {
            cmd: `radon raw ${target} -j`,
            description: "Raw metrics - LOC, LLOC, SLOC, comments, etc.",
          },
          hal: {
            cmd: `radon hal ${target} -j`,
            description:
              "Halstead metrics - operators/operands complexity",
          },
        };

        const commands = metrics.map((m) => ({
          metric: m,
          ...metricCommands[m],
        }));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  target,
                  commands,
                  install: "pip install radon",
                  complexityGrades: {
                    A: "1-5: Low complexity, easy to maintain",
                    B: "6-10: Moderate complexity",
                    C: "11-20: High complexity, consider refactoring",
                    D: "21-30: Very high complexity",
                    E: "31-40: Extremely complex",
                    F: "40+: Unmaintainable, refactoring required",
                  },
                  maintainabilityIndex: {
                    "100-80": "Excellent maintainability",
                    "79-50": "Moderate maintainability",
                    "49-20": "Poor maintainability",
                    "19-0": "Very poor, high risk",
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
      "py_test_runner",
      "Run Python tests using pytest with various options.",
      {
        target: z
          .string()
          .default("tests/")
          .describe("Test directory or file"),
        verbose: z.boolean().default(true).describe("Verbose output"),
        coverage: z.boolean().default(true).describe("Run with coverage"),
        markers: z
          .string()
          .optional()
          .describe("Pytest markers to filter tests (e.g., 'not slow')"),
        parallel: z
          .boolean()
          .default(false)
          .describe("Run tests in parallel with pytest-xdist"),
      },
      async (args) => {
        const { target, verbose, coverage, markers, parallel } = args;

        const flags = [];
        if (verbose) flags.push("-v");
        if (coverage) flags.push("--cov=. --cov-report=term-missing");
        if (markers) flags.push(`-m "${markers}"`);
        if (parallel) flags.push("-n auto");

        const command = `pytest ${target} ${flags.join(" ")}`;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  command,
                  install: coverage
                    ? "pip install pytest pytest-cov" +
                      (parallel ? " pytest-xdist" : "")
                    : "pip install pytest",
                  usefulFlags: {
                    "-x": "Stop on first failure",
                    "-s": "Show print statements",
                    "--lf": "Run last failed tests only",
                    "--ff": "Run failed tests first",
                    "-k 'pattern'": "Run tests matching pattern",
                    "--durations=10": "Show 10 slowest tests",
                  },
                  pytestIniExample: `[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: integration tests`,
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
      "py_generate_stubs",
      "Generate type stubs for Python packages or code.",
      {
        package: z.string().describe("Package name or path to generate stubs for"),
        output: z
          .string()
          .optional()
          .describe("Output directory for stubs"),
      },
      async (args) => {
        const { package: pkg, output } = args;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  commands: {
                    stubgen: {
                      command: `stubgen ${pkg} ${output ? `-o ${output}` : ""}`,
                      description: "Generate stubs from source code (mypy)",
                      install: "pip install mypy",
                    },
                    pyright: {
                      command: `pyright --createstub ${pkg}`,
                      description: "Generate stubs using pyright",
                      install: "pip install pyright",
                    },
                    monkeytype: {
                      command: `monkeytype stub ${pkg}`,
                      description: "Generate stubs from runtime type collection",
                      install: "pip install monkeytype",
                    },
                  },
                  typeshed: {
                    description:
                      "Check if stubs exist in typeshed before generating",
                    searchCommand: `pip search types-${pkg} || pip install types-${pkg}`,
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
  ],
});

export default pythonToolsServer;
