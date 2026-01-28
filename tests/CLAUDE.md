# DevSkyy Tests

> 90% coverage, fast feedback | 59 files

## Architecture
```
tests/
├── conftest.py              # Shared fixtures
├── test_agents.py           # Agent unit tests
├── test_api/                # Integration tests
├── test_rag_integration.py  # RAG tests
├── orchestration/           # Embedding/reranker
└── performance/             # Load tests
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

## USE THESE TOOLS (MANDATORY)
| Task | Tool |
|------|------|
| Writing tests | **Agent**: `tdd-guide` (ALWAYS) |
| E2E tests | **Agent**: `e2e-runner` for Playwright |
| Test failures | **Agent**: `build-error-resolver` |
| Coverage check | **Command**: `/verify`, `/tdd` |

**"Red-green-refactor. Every. Single. Time."**
