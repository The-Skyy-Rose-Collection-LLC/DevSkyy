---
name: rag-ingest
description: Batch document ingestion into RAG system with validation and monitoring
tags: [rag, knowledge-base, ingestion, automation]
---

# DevSkyy RAG Batch Ingestion

I'll ingest documents into the **RAG knowledge base** with validation, chunking, and quality verification.

## 🎯 Ingestion Pipeline

```
Discover → Validate → Chunk → Embed → Ingest → Verify → Log
```

**Parameters**:
- `--directory`: Target directory (default: `./docs`)
- `--recursive`: Scan subdirectories (default: `true`)
- `--embedding-provider`: `sentence_transformers` or `openai` (default: auto-detect)

---

## Phase 1: Discover Documents 🔍

Scanning for ingestible files (.md, .txt, .pdf)...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "find ./docs -type f \\( -name '*.md' -o -name '*.txt' -o -name '*.pdf' \\) 2>&1 | head -50 || echo 'No docs directory found'",
  "description": "Discover markdown, text, and PDF files",
  "timeout": 20000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "find . -type f \\( -name 'README.md' -o -name 'CLAUDE.md' \\) 2>&1 | head -20",
  "description": "Find critical documentation files",
  "timeout": 15000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== DOCUMENT INVENTORY ===' && echo '' && echo 'Markdown:' && find ./docs -name '*.md' -type f 2>&1 | wc -l && echo 'Text:' && find ./docs -name '*.txt' -type f 2>&1 | wc -l && echo 'PDF:' && find ./docs -name '*.pdf' -type f 2>&1 | wc -l || echo 'No docs directory'",
  "description": "Count documents by type",
  "timeout": 20000
}
</params>
</tool_call>

---

## Phase 2: Validate Files 📋

Checking file sizes, formats, and accessibility...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== FILE VALIDATION ===' && for file in $(find ./docs -type f \\( -name '*.md' -o -name '*.txt' -o -name '*.pdf' \\) 2>&1 | head -20); do size=$(du -h \"$file\" 2>&1 | awk '{print $1}'); echo \"$file: $size\"; done || echo 'No files to validate'",
  "description": "Check file sizes",
  "timeout": 30000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== LARGE FILES (>1MB) ===' && find ./docs -type f \\( -name '*.md' -o -name '*.txt' -o -name '*.pdf' \\) -size +1M 2>&1 | while read file; do size=$(du -h \"$file\" | awk '{print $1}'); echo \"⚠️  $file: $size (may require chunking)\"; done || echo 'No large files detected'",
  "description": "Identify large files needing special handling",
  "timeout": 20000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== ACCESSIBILITY CHECK ===' && for file in $(find ./docs -type f \\( -name '*.md' -o -name '*.txt' -o -name '*.pdf' \\) 2>&1 | head -10); do if [ -r \"$file\" ]; then echo \"✅ $file\"; else echo \"❌ $file (not readable)\"; fi; done || echo 'Check complete'",
  "description": "Verify file read permissions",
  "timeout": 20000
}
</params>
</tool_call>

---

## Phase 3: Prepare Ingestion Context 📊

Checking RAG server status and configuration...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f mcp_servers/rag_server.py ]; then echo '✅ RAG server found at mcp_servers/rag_server.py' && grep -E '(DEFAULT_TOP_K|CHUNK_SIZE|CHUNK_OVERLAP)' mcp_servers/rag_server.py | head -10 || echo 'Configuration variables not found in expected location'; else echo '⚠️  RAG server not found - check installation'; fi",
  "description": "Verify RAG server availability",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f orchestration/vector_store.py ]; then echo '✅ Vector store found' && grep -E '(ChromaDB|Pinecone|collection_name)' orchestration/vector_store.py | head -10; else echo '⚠️  Vector store module not found'; fi",
  "description": "Check vector store configuration",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== EMBEDDING PROVIDER CHECK ===' && if python3 -c 'import sentence_transformers' 2>/dev/null; then echo '✅ sentence-transformers available'; else echo '⚠️  sentence-transformers not installed'; fi && if python3 -c 'import openai' 2>/dev/null; then echo '✅ openai available'; else echo '⚠️  openai not installed'; fi",
  "description": "Check embedding providers",
  "timeout": 15000
}
</params>
</tool_call>

---

## Phase 4: Batch Ingestion 🚀

Ingesting documents into vector store...

### 4.1: Ingest Markdown Files

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "python3 << 'PYTHON_EOF'\nimport os\nimport json\nfrom pathlib import Path\n\n# Simulate ingestion (actual implementation uses RAG MCP server)\nmarkdown_files = list(Path('./docs').rglob('*.md'))\nprint(f\"Found {len(markdown_files)} markdown files to ingest\")\n\nfor i, file_path in enumerate(markdown_files[:10], 1):\n    try:\n        with open(file_path, 'r', encoding='utf-8') as f:\n            content = f.read()\n            word_count = len(content.split())\n            print(f\"{i}. {file_path} ({word_count} words)\")\n    except Exception as e:\n        print(f\"❌ {file_path}: {e}\")\n\nif len(markdown_files) > 10:\n    print(f\"... and {len(markdown_files) - 10} more files\")\nPYTHON_EOF",
  "description": "List markdown files for ingestion",
  "timeout": 30000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== INGESTION SIMULATION ===' && echo '' && echo 'Chunking Strategy:' && echo '  - Chunk size: 512 tokens' && echo '  - Overlap: 50 tokens' && echo '  - Embedding model: sentence-transformers/all-MiniLM-L6-v2' && echo '' && echo 'Vector Store:' && echo '  - Backend: ChromaDB' && echo '  - Collection: devskyy_docs' && echo '  - Persist: ./data/vectordb'",
  "description": "Display ingestion configuration",
  "timeout": 5000
}
</params>
</tool_call>

### 4.2: Ingest Text Files

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "python3 << 'PYTHON_EOF'\nimport os\nfrom pathlib import Path\n\ntext_files = list(Path('./docs').rglob('*.txt'))\nprint(f\"Found {len(text_files)} text files to ingest\")\n\nfor file_path in text_files[:5]:\n    try:\n        size = os.path.getsize(file_path)\n        print(f\"  - {file_path} ({size} bytes)\")\n    except Exception as e:\n        print(f\"  ❌ {file_path}: {e}\")\nPYTHON_EOF",
  "description": "List text files for ingestion",
  "timeout": 20000
}
</params>
</tool_call>

### 4.3: Ingest PDF Files (if available)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "python3 << 'PYTHON_EOF'\nimport os\nfrom pathlib import Path\n\npdf_files = list(Path('./docs').rglob('*.pdf'))\nprint(f\"Found {len(pdf_files)} PDF files\")\n\nif pdf_files:\n    try:\n        import pypdf\n        print(\"✅ pypdf available for PDF processing\")\n        for file_path in pdf_files[:5]:\n            size = os.path.getsize(file_path)\n            print(f\"  - {file_path} ({size} bytes)\")\n    except ImportError:\n        print(\"⚠️  pypdf not installed - cannot process PDFs\")\n        print(\"   Install: pip install pypdf\")\nelse:\n    print(\"No PDF files to process\")\nPYTHON_EOF",
  "description": "Check PDF processing capability",
  "timeout": 20000
}
</params>
</tool_call>

---

## Phase 5: Actual RAG Ingestion (MCP Tool) 🔧

**Note**: The following uses the RAG MCP server's `rag_ingest` tool.

If RAG MCP server is running, this will perform actual ingestion:

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== RAG INGESTION INSTRUCTIONS ===' && echo '' && echo 'To ingest documents, use the RAG MCP server:' && echo '' && echo 'Method 1: Via MCP Tool (if server running)' && echo '  mcp__devskyy_rag__rag_ingest({' && echo '    \"documents\": [\"path/to/file1.md\", \"path/to/file2.md\"],' && echo '    \"metadata\": {\"source\": \"docs\", \"version\": \"1.0.0\"}' && echo '  })' && echo '' && echo 'Method 2: Direct Python API' && echo '  from orchestration.document_ingestion import DocumentIngestionPipeline' && echo '  pipeline = DocumentIngestionPipeline.get_instance()' && echo '  await pipeline.ingest_file(\"path/to/file.md\")' && echo '' && echo 'Method 3: Batch via script' && echo '  python scripts/ingest_docs.py --directory ./docs --recursive'",
  "description": "Display ingestion methods",
  "timeout": 5000
}
</params>
</tool_call>

### Critical Documentation Files

Ingest high-priority files first:

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== CRITICAL FILES TO INGEST ===' && echo '' && for file in README.md CLAUDE.md docs/MCP_ARCHITECTURE.md docs/ZERO_TRUST_ARCHITECTURE.md; do if [ -f \"$file\" ]; then wc -l \"$file\" | awk -v f=\"$file\" '{print \"✅ \" f \" (\" $1 \" lines)\"}'; else echo \"⚠️  $file not found\"; fi; done",
  "description": "Identify critical documentation",
  "timeout": 10000
}
</params>
</tool_call>

---

## Phase 6: Verify Ingestion ✅

Checking vector store stats and quality...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== INGESTION VERIFICATION ===' && echo '' && echo 'Expected Results:' && echo '  - Documents in vector store: TBD' && echo '  - Embeddings generated: TBD' && echo '  - Average chunk size: ~512 tokens' && echo '  - Collection: devskyy_docs' && echo '' && echo 'To verify ingestion success, use:' && echo '  mcp__devskyy_rag__rag_stats()' && echo '' && echo 'Query Example:' && echo '  mcp__devskyy_rag__rag_query({' && echo '    \"query\": \"What is DevSkyy architecture?\",' && echo '    \"top_k\": 5' && echo '  })'",
  "description": "Display verification instructions",
  "timeout": 5000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -d ./data/vectordb ]; then echo '✅ Vector database directory exists' && du -sh ./data/vectordb 2>&1 | awk '{print \"Size: \" $1}' && echo '' && find ./data/vectordb -type f 2>&1 | wc -l | xargs echo 'Files:'; else echo '⚠️  Vector database directory not found - ingestion may not have occurred'; fi",
  "description": "Check vector store persistence",
  "timeout": 15000
}
</params>
</tool_call>

---

## Phase 7: Update Ingestion Log 📝

Recording ingestion metadata...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "mkdir -p .claude/hooks/logs && log_file=\".claude/hooks/logs/rag-ingestion.jsonl\" && timestamp=$(date -u +\"%Y-%m-%dT%H:%M:%SZ\") && doc_count=$(find ./docs -type f \\( -name '*.md' -o -name '*.txt' -o -name '*.pdf' \\) 2>&1 | wc -l | tr -d ' ') && cat << EOF >> \"$log_file\"\n{\"timestamp\": \"$timestamp\", \"action\": \"batch_ingest\", \"directory\": \"./docs\", \"document_count\": $doc_count, \"status\": \"simulated\", \"notes\": \"Ingestion instructions provided - actual ingestion requires RAG MCP server\"}\nEOF\necho \"✅ Logged to $log_file\" && tail -1 \"$log_file\" | jq .",
  "description": "Log ingestion event",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f .claude/hooks/logs/rag-ingestion.jsonl ]; then echo '=== RECENT INGESTION HISTORY ===' && tail -5 .claude/hooks/logs/rag-ingestion.jsonl | jq -r '\"\\(.timestamp): \\(.document_count) docs (\\(.status))\"' 2>&1; else echo 'No ingestion history yet'; fi",
  "description": "Show ingestion history",
  "timeout": 10000
}
</params>
</tool_call>

---

## Phase 8: Quality Checks 🔬

Validating ingestion quality...

### 8.1: Embedding Quality

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== EMBEDDING QUALITY METRICS ===' && echo '' && echo 'Recommended checks:' && echo '  1. Vector dimensionality: 384 (MiniLM) or 1536 (OpenAI)' && echo '  2. Cosine similarity range: -1 to 1' && echo '  3. Average document similarity: 0.3-0.7 (diverse)' && echo '  4. Duplicate detection: < 5% similarity > 0.95' && echo '' && echo 'Run quality check:' && echo '  python scripts/check_embedding_quality.py'",
  "description": "Display embedding quality guidelines",
  "timeout": 5000
}
</params>
</tool_call>

### 8.2: Retrieval Quality

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== RETRIEVAL QUALITY TEST ===' && echo '' && echo 'Sample queries to validate:' && echo '  1. \"What is DevSkyy?\" → Should return README.md chunks' && echo '  2. \"How do MCP servers work?\" → Should return MCP docs' && echo '  3. \"Security architecture\" → Should return security docs' && echo '  4. \"SuperAgent capabilities\" → Should return agent docs' && echo '' && echo 'Expected metrics:' && echo '  - Top result relevance score: > 0.7' && echo '  - Results diversity: Multiple sources' && echo '  - Retrieval latency: < 500ms'",
  "description": "Display retrieval quality tests",
  "timeout": 5000
}
</params>
</tool_call>

---

## ✅ Success Criteria

**MUST PASS (Blocking):**

- [ ] All target documents discovered
- [ ] No file accessibility errors
- [ ] RAG server available (or instructions provided)
- [ ] Ingestion logged successfully

**SHOULD PASS (Quality):**

- [ ] Embedding provider available
- [ ] Vector store accessible
- [ ] Chunking parameters validated
- [ ] Ingestion verified via rag_stats

**OPTIMAL (Enterprise):**

- [ ] PDF processing available (pypdf installed)
- [ ] Embedding quality metrics collected
- [ ] Retrieval quality tested
- [ ] Duplicate detection run

---

## 🚨 Troubleshooting

**Missing dependencies:**
```bash
pip install chromadb sentence-transformers pypdf
```

**RAG server not responding:**
```bash
# Check MCP server status
python mcp_servers/rag_server.py --help

# Verify ChromaDB
python -c "import chromadb; print('ChromaDB version:', chromadb.__version__)"
```

**Large PDF processing fails:**
- Increase chunk size in vector_store.py
- Enable streaming mode for large files
- Split PDFs into smaller documents

**Low retrieval quality:**
- Adjust similarity threshold (lower for broader results)
- Try different embedding models
- Enable query rewriting (rag_query_rewrite)

---

## 📋 Next Steps

1. Verify ingestion: `rag_stats()` via MCP tool
2. Test retrieval: `rag_query("test query")` via MCP tool
3. Monitor quality: Check embedding similarity scores
4. Update documentation: Document ingested content sources

---

## 🔄 Re-ingestion

To re-ingest updated documents:

```bash
# Clear existing collection (if needed)
# WARNING: This deletes all vectors!
# rm -rf ./data/vectordb

# Re-run ingestion
/rag-ingest
```

**Note**: Incremental updates are preferred over full re-ingestion. Only clear vector store if schema changes or corruption occurs.

---

**RAG Ingestion Version:** 1.0.0
**DevSkyy Compliance:** Enterprise knowledge base standards
**Embedding Strategy:** Semantic search with 512-token chunks
