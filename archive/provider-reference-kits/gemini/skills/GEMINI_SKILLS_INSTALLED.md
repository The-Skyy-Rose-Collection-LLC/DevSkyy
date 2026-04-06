# 🎓 Gemini Skills Installation Complete

**Date:** February 16, 2026
**Installed:** gemini-api-dev skill
**Location:** `~/.agents/skills/gemini-api-dev/`

---

## ✅ What's Been Installed

### Gemini API Development Skill
**Package:** `google-gemini/gemini-skills`
**Skill:** `gemini-api-dev`
**Installed for:** Antigravity, Claude Code, Codex, Gemini CLI, OpenCode

**Purpose:** Expert guidance for building applications with Gemini models, multimodal content processing, function calling, structured outputs, and SDK usage.

---

## 🚀 Capabilities

### Core Features
- 📝 **Text Generation** - Chat, completion, summarization
- 🎨 **Multimodal Understanding** - Images, audio, video, documents
- 🔧 **Function Calling** - Let models invoke your functions
- 📊 **Structured Output** - Generate valid JSON matching schemas
- 💻 **Code Execution** - Run Python in sandboxed environment
- 🗄️ **Context Caching** - Cache large contexts for efficiency
- 🔍 **Embeddings** - Generate text embeddings for semantic search

### Supported Languages
- ✅ **Python** - `google-genai`
- ✅ **JavaScript/TypeScript** - `@google/genai`
- ✅ **Go** - `google.golang.org/genai`
- ✅ **Java** - `com.google.genai:google-genai`

---

## 🎯 Available Gemini Models (Official Latest)

> **IMPORTANT:** The skill reveals that Gemini 3 models are now available!

### Current Models (Gemini 3)
- **`gemini-3-pro-preview`** - 1M tokens, complex reasoning, coding, research
- **`gemini-3-flash-preview`** - 1M tokens, fast, balanced, multimodal
- **`gemini-3-pro-image-preview`** - 65k/32k tokens, image generation & editing

### Legacy Models (Deprecated)
- ⚠️ `gemini-2.5-*` - Deprecated
- ⚠️ `gemini-2.0-*` - Deprecated
- ⚠️ `gemini-1.5-*` - Deprecated

> **Note:** Our current integration uses `gemini-2.5-flash` which still works but consider migrating to Gemini 3 models.

---

## 🔄 SDK Migration Required

### Old SDKs (Deprecated)
❌ `google-generativeai` (Python)
❌ `@google/generative-ai` (JavaScript)

### New SDKs (Required)
✅ `google-genai` (Python)
✅ `@google/genai` (JavaScript/TypeScript)

**Action:** Update our Gemini integration to use new SDKs

---

## 📚 Quick Start Examples

### Python (New SDK)
```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain quantum computing"
)
print(response.text)
```

### JavaScript (New SDK)
```typescript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});
const response = await ai.models.generateContent({
  model: "gemini-3-flash-preview",
  contents: "Explain quantum computing"
});
console.log(response.text);
```

### Go
```go
import (
    "context"
    "google.golang.org/genai"
)

client, _ := genai.NewClient(context.Background(), nil)
resp, _ := client.Models.GenerateContent(
    ctx,
    "gemini-3-flash-preview",
    genai.Text("Explain quantum computing"),
    nil
)
fmt.Println(resp.Text)
```

---

## 🔗 API Documentation

### Official Docs Index
**llms.txt:** `https://ai.google.dev/gemini-api/docs/llms.txt`

### Key Documentation Pages
All available in `.md.txt` format for LLM consumption:

- **Models**: https://ai.google.dev/gemini-api/docs/models.md.txt
- **AI Studio Quickstart**: https://ai.google.dev/gemini-api/docs/ai-studio-quickstart.md.txt
- **Image Generation**: https://ai.google.dev/gemini-api/docs/image-generation.md.txt
- **Function Calling**: https://ai.google.dev/gemini-api/docs/function-calling.md.txt
- **Structured Outputs**: https://ai.google.dev/gemini-api/docs/structured-output.md.txt
- **Text Generation**: https://ai.google.dev/gemini-api/docs/text-generation.md.txt
- **Image Understanding**: https://ai.google.dev/gemini-api/docs/image-understanding.md.txt
- **Embeddings**: https://ai.google.dev/gemini-api/docs/embeddings.md.txt
- **SDK Migration**: https://ai.google.dev/gemini-api/docs/migrate.md.txt

### REST API Specs
- **v1beta** (default): `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta`
- **v1**: `https://generativelanguage.googleapis.com/$discovery/rest?version=v1`

---

## ⚠️ Action Items for Our Integration

### 1. Update SDK (Required)
```bash
# Current (deprecated)
npm uninstall @google/generative-ai

# New (required)
npm install @google/genai
```

### 2. Update Python Client
```bash
# Current (deprecated)
pip uninstall google-generativeai

# New (required)
pip install google-genai
```

### 3. Update Code
Our current `gemini-client.js` uses deprecated SDK. Need to migrate:
- Change imports from `@google/generative-ai` to `@google/genai`
- Update API calls to match new SDK
- Test with `gemini-3-flash-preview` model

### 4. Update Configuration
Update `config/models.json` to include Gemini 3 models:
- `gemini-3-pro-preview`
- `gemini-3-flash-preview`
- `gemini-3-pro-image-preview`

---

## 🎯 Where This Skill is Available

The `gemini-api-dev` skill is now accessible in:

### Universal Installation
- ✅ **Codex** - Ready to use
- ✅ **Gemini CLI** - Ready to use
- ✅ **OpenCode** - Ready to use

### Symlinked Installation
- ✅ **Antigravity** - Ready to use
- ✅ **Claude Code** - Ready to use

**Location:** `~/.agents/skills/gemini-api-dev/SKILL.md`

---

## 🔧 Using the Skill

### Automatic Activation
The skill activates automatically when you ask about:
- Building Gemini applications
- Working with multimodal content
- Implementing function calling
- Using structured outputs
- SDK usage and migration

### Manual Reference
```bash
# View skill contents
cat ~/.agents/skills/gemini-api-dev/SKILL.md
```

### Example Prompts That Trigger This Skill
- "How do I implement function calling with Gemini?"
- "Show me how to process images with the new Gemini SDK"
- "Help me migrate from google-generativeai to google-genai"
- "What's the best Gemini model for code generation?"
- "How do I generate structured JSON output with Gemini?"

---

## 📊 Integration Status

| Component | Current Status | Action Needed |
|-----------|---------------|---------------|
| **SDK (Node.js)** | ⚠️ Deprecated (`@google/generative-ai`) | Migrate to `@google/genai` |
| **SDK (Python)** | ⚠️ Deprecated (`google-generativeai`) | Migrate to `google-genai` |
| **Models** | ⚠️ Using `gemini-2.5-flash` | Update to `gemini-3-flash-preview` |
| **Skill** | ✅ Installed | Ready to use |
| **API Key** | ✅ Configured | Working |
| **Documentation** | ✅ Complete | Up to date |

---

## 🚀 Next Steps

### Immediate Actions

1. **Migrate to New SDK** (High Priority)
   ```bash
   cd ~/DevSkyy/gemini/clients/node
   npm uninstall @google/generative-ai
   npm install @google/genai
   # Update gemini-client.js
   ```

2. **Add Gemini 3 Models** (High Priority)
   ```bash
   # Update config/models.json
   # Add gemini-3-pro-preview, gemini-3-flash-preview
   ```

3. **Test New Models**
   ```bash
   node -e "
   const { GoogleGenAI } = require('@google/genai');
   const ai = new GoogleGenAI({});
   ai.models.generateContent({
     model: 'gemini-3-flash-preview',
     contents: 'Hello Gemini 3!'
   }).then(r => console.log(r.text));
   "
   ```

4. **Update Documentation**
   - Update README.md with new SDK info
   - Update QUICKSTART.md with Gemini 3 examples
   - Add migration guide

### Future Enhancements

- Implement structured output examples
- Add code execution examples
- Create context caching utilities
- Build embeddings service
- Update wordpress-copilot integration

---

## 📖 Resources

### Installed Skill
- **Location:** `~/.agents/skills/gemini-api-dev/SKILL.md`
- **Source:** https://github.com/google-gemini/gemini-skills

### Official Documentation
- **Docs Index:** https://ai.google.dev/gemini-api/docs/llms.txt
- **Main Docs:** https://ai.google.dev/gemini-api/docs/
- **API Reference:** https://ai.google.dev/api
- **Migration Guide:** https://ai.google.dev/gemini-api/docs/migrate.md.txt

### SDK Documentation
- **Python SDK:** https://github.com/google/genai-python
- **JavaScript SDK:** https://github.com/google/genai-js
- **Go SDK:** https://github.com/google/genai-go
- **Java SDK:** https://central.sonatype.com/artifact/com.google.genai/google-genai

---

## 🎉 Summary

✅ **Installed:** gemini-api-dev skill
✅ **Available in:** 5 AI development environments
✅ **Provides:** Expert Gemini API guidance
✅ **Covers:** All SDKs, models, and capabilities

⚠️ **Action Required:** Migrate to new SDKs (`@google/genai`, `google-genai`)
⚠️ **Update Needed:** Add Gemini 3 models to integration

**Status:** Skill installed and active, SDK migration recommended

---

**Quick Reference:**
- Skill file: `cat ~/.agents/skills/gemini-api-dev/SKILL.md`
- List skills: `npx skills list`
- Current integration: `~/DevSkyy/gemini/`
- Migration guide: https://ai.google.dev/gemini-api/docs/migrate.md.txt
