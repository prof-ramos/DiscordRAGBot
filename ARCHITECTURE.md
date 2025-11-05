# Architecture Documentation

## Overview

This Discord RAG Bot is a production-ready application built with modern Python best practices, featuring:

- **Modular Architecture**: Clean separation of concerns with service layer
- **Type Safety**: Comprehensive type hints throughout
- **Dependency Injection**: Testable, loosely coupled components
- **Error Handling**: Custom exception hierarchy
- **Caching**: LRU cache with TTL for performance
- **Logging**: Structured logging with context
- **Testing**: Comprehensive test suite with pytest

## Project Structure

```
DiscordRAGBot/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── config.py                 # Pydantic settings & configuration
│   ├── exceptions.py             # Custom exception hierarchy
│   ├── models.py                 # Pydantic data models
│   ├── cache.py                  # Caching layer with decorators
│   ├── logging_config.py         # Structured logging setup
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── supabase_service.py   # Supabase client management
│   │   ├── vectorstore_service.py # RAG operations
│   │   ├── llm_service.py        # LLM interactions
│   │   └── config_service.py     # Server config management
│   └── bot/                      # Discord bot components
│       ├── __init__.py
│       ├── client.py             # Bot client with DI
│       ├── commands.py           # Slash commands
│       └── handlers.py           # Message handlers
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── test_cache.py
│   ├── test_models.py
│   └── test_services/
├── bot.py                        # Entry point
├── load.py                       # Document indexing script
├── requirements.txt              # Dependencies
├── pytest.ini                    # Pytest configuration
└── pyproject.toml                # Tool configuration
```

## Core Components

### Configuration Management (`src/config.py`)

Uses **Pydantic Settings** for type-safe configuration with automatic validation:

```python
from src.config import get_settings

settings = get_settings()  # Singleton pattern
print(settings.discord_token)  # Type-safe access
```

Features:
- Environment variable support with `.env` file
- Validation at startup (fail-fast)
- Sensible defaults
- Type hints for IDE autocomplete

### Exception Hierarchy (`src/exceptions.py`)

Custom exceptions with context:

```python
class BotError(Exception):
    """Base exception with details and original error tracking"""

class VectorStoreError(BotError):
    """Raised when vectorstore operations fail"""
```

All exceptions include:
- Human-readable message
- Optional details dictionary
- Original exception chaining

### Data Models (`src/models.py`)

Pydantic models for validation:

```python
from src.models import QueryRequest, QueryResult

request = QueryRequest(
    question="What is Python?",
    user_id="12345"
)  # Automatically validated
```

Models include:
- `Document`: Document chunk with metadata
- `QueryRequest`: User query with context
- `QueryResult`: Response with sources
- `ServerConfig`: Server-specific settings
- `RateLimitInfo`: Rate limiting tracking

### Caching Layer (`src/cache.py`)

LRU cache with TTL and async support:

```python
from src.cache import cached

@cached(ttl=3600, key_prefix="query")
async def expensive_function(query: str) -> QueryResult:
    # Automatically cached for 1 hour
    return result
```

Features:
- Automatic LRU eviction
- TTL (time-to-live) support
- Cache statistics
- Async-compatible

### Structured Logging (`src/logging_config.py`)

Context-aware logging with emojis:

```python
from src.logging_config import get_logger

logger = get_logger()
logger.info("User query", action="QUERY", user_id="123", query="test")
# Output: 💬 User query | user_id=123 | query=test
```

Features:
- Automatic log rotation
- Console and file output
- Emoji-based categorization
- Contextual information

### Service Layer (`src/services/`)

#### SupabaseService
Manages Supabase client lifecycle:
- Lazy initialization
- Connection testing
- Error handling

#### VectorStoreService
Handles document retrieval:
- Embedding generation
- Similarity search
- Document addition
- Async operations

#### LLMService
Manages LLM interactions:
- Query processing with RAG
- Prompt template selection
- Response generation
- Automatic caching

#### ConfigService
Server configuration management:
- Load/save configurations
- Filter level management
- Persistence

### Bot Components (`src/bot/`)

#### DiscordRAGBot (client.py)
Main bot class with dependency injection:

```python
bot = DiscordRAGBot(settings, logger)
# Services automatically injected
```

Features:
- Async setup hook
- Proper resource management
- Service initialization

#### Commands (commands.py)
Slash command handlers:
- `/ask` - Query the RAG system
- `/config` - Configure filter level
- `/status` - Show bot status

#### Handlers (handlers.py)
Message event handlers:
- Mention handling
- DM processing
- Long message splitting

## Dependency Injection

The application uses constructor injection for testability:

```python
# Services depend on settings and logger
vectorstore_service = VectorStoreService(
    settings=settings,
    logger=logger,
    supabase_service=supabase_service
)

# Easy to mock for testing
mock_service = VectorStoreService(
    settings=test_settings,
    logger=mock_logger,
    supabase_service=mock_supabase
)
```

Benefits:
- Easy to test (inject mocks)
- Explicit dependencies
- Loose coupling
- Clear initialization order

## Testing Strategy

### Unit Tests
Test individual components in isolation:

```python
def test_cache_set_and_get(cache, sample_result):
    cache.set("key", sample_result)
    result = cache.get("key")
    assert result.answer == "Test answer"
```

### Fixtures
Reusable test components in `conftest.py`:

```python
@pytest.fixture
def test_settings():
    return Settings(discord_token="test_token", ...)
```

### Coverage
Aim for >90% coverage:

```bash
pytest --cov=src --cov-report=html
```

## Error Handling Flow

```
User Action
    ↓
Command/Handler
    ↓
Service Layer (with try/except)
    ↓
Custom Exception (with context)
    ↓
User-friendly Error Message
    ↓
Logged with Details
```

## Performance Optimizations

1. **Caching**: LLM responses cached with LRU eviction
2. **Lazy Loading**: Services initialized on first use
3. **Async Operations**: All I/O is async
4. **Connection Pooling**: Reuse Supabase client

## Configuration

### Environment Variables

Required:
- `DISCORD_TOKEN`: Discord bot token
- `OPENAI_API_KEY`: OpenAI API key
- `OPENROUTER_API_KEY`: OpenRouter API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_API_KEY`: Supabase API key

Optional (with defaults):
- `OPENROUTER_MODEL`: Model name
- `LOG_LEVEL`: Logging level
- `CACHE_ENABLED`: Enable/disable caching
- See `src/config.py` for full list

### Server Configuration

Per-server settings stored in `server_config.json`:

```json
{
  "123456789": {
    "filter_level": "moderado",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

## Best Practices

### Type Hints
All functions have type hints:

```python
def process_query(request: QueryRequest) -> QueryResult:
    ...
```

### Docstrings
All modules, classes, and functions documented:

```python
def process_query(request: QueryRequest) -> QueryResult:
    """Process a user query with RAG.

    Args:
        request: Query request with question and metadata

    Returns:
        Query result with answer and sources

    Raises:
        VectorStoreNotLoadedError: If vector store not loaded
    """
```

### Error Messages
User-friendly with actionable steps:

```python
raise VectorStoreNotLoadedError(
    "⚠️ **Bot ainda não está pronto!**\n\n"
    "O vectorstore não foi carregado. Por favor:\n"
    "1. Adicione arquivos PDF na pasta `data/`\n"
    "2. Execute `python load.py`\n"
    "3. Reinicie o bot"
)
```

## Development Workflow

### Running Tests
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=src          # With coverage
pytest -m "not slow"      # Skip slow tests
```

### Code Quality
```bash
black src/                # Format code
ruff check src/           # Lint code
mypy src/                 # Type checking
```

### Running the Bot
```bash
python bot.py             # Start bot
python load.py            # Index documents
```

## Extending the Bot

### Adding a New Command

1. Create handler in `src/bot/commands.py`:
```python
@bot.tree.command(name="newcommand")
async def newcommand(interaction: discord.Interaction):
    ...
```

2. Add tests in `tests/test_bot/`:
```python
def test_newcommand():
    ...
```

### Adding a New Service

1. Create service in `src/services/`:
```python
class NewService:
    def __init__(self, settings, logger):
        ...
```

2. Inject into bot client:
```python
self.new_service = NewService(self.settings, self.logger)
```

3. Add tests:
```python
def test_new_service():
    ...
```

## Troubleshooting

### Import Errors
Ensure `src/` is in Python path:
```python
sys.path.insert(0, str(Path(__file__).parent))
```

### Pydantic Validation Errors
Check `.env` file has all required variables.

### Vector Store Not Loading
1. Run `python load.py` to index documents
2. Check Supabase credentials
3. Verify documents in `data/` directory

## Performance Monitoring

### Cache Statistics
```python
from src.cache import get_cache

cache = get_cache()
print(cache.stats)
# {'size': 42, 'hits': 120, 'misses': 15, 'hit_rate': '88.89%'}
```

### Log Analysis
Logs include performance metrics:
```
2025-01-01 12:00:00 | INFO | ✅ Query processed | sources=5 | duration=1.2s
```
