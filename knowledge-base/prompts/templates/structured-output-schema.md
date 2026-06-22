# Template: Structured-Output Schema Block

Reusable JSON/YAML output-schema fragment to drop into agent system prompts that need structured returns. Anchors the model to a canonical shape so downstream parsers don't have to do free-form extraction.

## Pattern

Append to the end of any agent system prompt:

```
Return ONLY a JSON object with this exact shape:

{
  "<field-name>": "<type>",          // <one-line constraint>
  "<field-name>": "<type>",
  ...
}

Rules:
- Output the JSON object and nothing else. No prose before or after.
- Use double quotes, never single. No trailing commas.
- If a value is unknown, use null, not "" or "unknown".
- Use lowercase booleans (true/false), never True/False or "true".
- Numbers are unquoted; strings are quoted.
```

## When to use

- Agent returns are consumed by `json.loads()` / `JSON.parse()` downstream.
- You need the model to commit to a schema instead of "creative" output.
- You're orchestrating multi-step pipelines where the next step parses the previous step's output.

## When NOT to use

- Free-form copywriting (brand-writer, marketing prose).
- Interactive conversation (assistant replies that humans read).
- Cases where the model needs flexibility to express uncertainty in prose.

## Anti-patterns

- **Don't** use this template AND ask for `"reasoning": "..."` in the schema. Models pad reasoning fields with hedging that defeats the structured-output discipline.
- **Don't** ship a schema with optional fields. Make them required-with-null-allowed. Optional fields are skipped when the model isn't sure, which silently corrupts downstream parsers.
- **Don't** put example output inside ` ``` ` fenced blocks if your pipeline strips fenced blocks — the example becomes invisible to the model.

## Linked prompts using this template

- `mcp-skyyrose-tools` — multiple tool returns expect structured JSON
- `data-analyst` — eval output schema
