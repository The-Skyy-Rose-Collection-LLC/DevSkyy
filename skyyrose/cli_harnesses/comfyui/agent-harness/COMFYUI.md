# ComfyUI CLI — Command Reference

Full reference for `comfyui` / `cli-anything-comfyui`.

## system

### `system stats`

Fetch server statistics (CPU, RAM, VRAM, device info).

```bash
comfyui system stats
comfyui --json system stats
```

### `system embeddings`

List all available text embeddings.

```bash
comfyui system embeddings
comfyui --json system embeddings
```

---

## nodes

### `nodes list [--filter TEXT]`

List all registered node types. Optionally filter by substring.

```bash
comfyui nodes list
comfyui nodes list --filter KSampler
comfyui --json nodes list --filter Loader
```

### `nodes info <node_class>`

Show full input/output schema for a node class.

```bash
comfyui nodes info KSampler
comfyui --json nodes info CheckpointLoaderSimple
```

---

## models

### `models list [model_type]`

List models of a given type. If `model_type` is omitted, lists all types first.

```bash
comfyui models list checkpoints
comfyui models list loras
comfyui --json models list vae
```

### `models types`

List all available model type slugs.

```bash
comfyui models types
comfyui --json models types
```

---

## queue

### `queue list`

Show running and pending items in the queue.

```bash
comfyui queue list
comfyui --json queue list
```

### `queue submit <workflow_file>`

Submit a workflow JSON file to the queue. Returns `prompt_id`.

```bash
comfyui queue submit my_workflow.json
comfyui --json queue submit my_workflow.json
```

### `queue interrupt --confirm`

Interrupt the currently executing prompt. Requires `--confirm`.

```bash
comfyui queue interrupt --confirm
```

### `queue clear --confirm`

Clear all pending items from the queue. Requires `--confirm`.

```bash
comfyui queue clear --confirm
```

---

## history

### `history list`

List completed prompts (most recent first).

```bash
comfyui history list
comfyui --json history list
```

### `history show <prompt_id>`

Show details for a specific completed prompt.

```bash
comfyui history show abc123
comfyui --json history show abc123
```

### `history extract-outputs <prompt_id>`

Extract and list all output files (images, videos) from a prompt.

```bash
comfyui history extract-outputs abc123
comfyui --json history extract-outputs abc123
```

### `history clear --confirm [prompt_id]`

Clear history. With `prompt_id` clears one entry; without clears all. Requires `--confirm`.

```bash
comfyui history clear --confirm
comfyui history clear --confirm abc123
```

---

## workflow

### `workflow validate <file>`

Parse and validate a workflow JSON file. Exits 0 if valid, nonzero with error messages if invalid.

```bash
comfyui workflow validate my_workflow.json
```

### `workflow show <file>`

Display the workflow structure in human-readable form.

```bash
comfyui workflow show my_workflow.json
comfyui --json workflow show my_workflow.json
```

### `workflow save <file> [--output PATH]`

Canonicalise and re-save a workflow JSON (normalises formatting).

```bash
comfyui workflow save raw.json --output clean.json
```

### `workflow nodes <file>`

List all node IDs and class types present in the workflow.

```bash
comfyui workflow nodes my_workflow.json
comfyui --json workflow nodes my_workflow.json
```

---

## session

Sessions persist server context (host, history) across invocations.

### `session new`

Create a new session. Returns session ID.

```bash
comfyui session new
comfyui --json session new
```

### `session list`

List all saved sessions.

```bash
comfyui session list
comfyui --json session list
```

### `session show <session_id>`

Show details for a session.

```bash
comfyui session show <id>
comfyui --json session show <id>
```

### `session delete --confirm <session_id>`

Delete a session. Requires `--confirm`.

```bash
comfyui session delete --confirm <id>
```

---

## manifest

Manifests describe batched operations as a plan/apply workflow.

### `manifest plan`

Create a new manifest file interactively.

```bash
comfyui manifest plan
comfyui --json manifest plan
```

### `manifest show <file>`

Display manifest contents.

```bash
comfyui manifest show ops.manifest.json
comfyui --json manifest show ops.manifest.json
```

### `manifest apply --confirm <file>`

Execute all operations in the manifest. Destructive operations are listed before execution. Requires `--confirm`.

```bash
comfyui manifest apply --confirm ops.manifest.json
```

---

## doctor

### `doctor check`

Verify connectivity to the ComfyUI server and report status.

```bash
comfyui doctor check
comfyui --json doctor check
```

### `doctor deps`

Check that all required Python dependencies are installed and report versions.

```bash
comfyui doctor deps
comfyui --json doctor deps
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COMFYUI_HOST` | ComfyUI base URL | `http://127.0.0.1:8188` |
| `COMFYUI_AUTH_TOKEN` | Bearer token | — |
| `COMFYUI_JSON` | Set to `1` for JSON output globally | — |
| `CLI_ANYTHING_HOME` | Override data directory for sessions/manifests | `~/.cli_anything` |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | CLI error (missing `--confirm`, invalid args, backend error) |
| `2` | Usage / argument error (Click default) |
