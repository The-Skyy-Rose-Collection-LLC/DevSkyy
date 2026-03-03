# DevSkyy Tests

> 90%+ coverage required | 129 test files | 20 subdirectories

## Structure

```
tests/
├── conftest.py              # Shared fixtures
├── agents/                  # Agent unit tests
├── analytics/               # Stream processor tests
├── api/                     # API endpoint tests (analytics, assets, etc.)
├── cli/                     # CLI tool tests (prompt_enhance)
├── core/                    # Core module tests (feature flags, interfaces, cache, CQRS, events)
├── gateway/                 # API gateway tests
├── grpc/                    # gRPC servicer tests
├── integration/             # Cross-module integration tests (GraphQL+Cache, security ops)
├── integrations/            # Enterprise workflow tests
├── llm/                     # LLM provider tests (classification, verification, deepseek)
├── mcp_servers/             # MCP infrastructure tests
├── orchestration/           # Embedding, reranker tests
├── scripts/                 # Script tests
├── security/                # Security tests (nonce cache, vulnerability scanner)
├── services/                # Service tests (ML, analytics, 3D, image pipeline)
├── sync/                    # WordPress sync tests
└── unit/                    # Isolated unit tests (redis flags, telemetry)
```

## Running Tests

```bash
# All tests (from repo root)
cd /Users/theceo/DevSkyy && pytest tests/ -v

# With coverage
pytest tests/ --cov --cov-report=term-missing

# By marker
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m security -v

# Single module
pytest tests/core/test_feature_flags.py -v
```

## Pattern

```python
@pytest.fixture
async def mock_rag_manager(tmp_path):
    config = VectorStoreConfig(db_type="chromadb", persist_directory=str(tmp_path))
    yield await create_rag_context_manager(config)

@pytest.mark.asyncio
async def test_rag_retrieval(mock_rag_manager):
    await mock_rag_manager.ingest("Test document")
    context = await mock_rag_manager.get_context("test")
    assert len(context.documents) > 0
```

## Gotchas

- `pytest` from wrong cwd collects 0 tests silently — always `cd` to repo root first
- `tests/api/` has encryption-key import errors at collection — use `tests/integration/` for cross-module tests
- Some tests skip when optional deps missing (pyotp, freezegun, hvac, google-adk)

**"Red-green-refactor. Every. Single. Time."**
