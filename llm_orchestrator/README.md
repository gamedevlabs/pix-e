# LLM Orchestrator

A unified, model-agnostic interface for all LLM interactions in pix:e.

## Overview

The LLM Orchestrator provides a clean abstraction layer between pix:e features (pillars, SPARC, moodboards) and LLM providers (Ollama, OpenAI, Gemini). It supports both:

- **Monolithic mode**: Single-prompt baseline execution
- **Agentic mode**: Multi-agent parallel execution with specialized agents (planned for thesis research)

## Why This Matters

**Before:** Each feature had its own LLM integration code → duplication, inconsistency, hard to maintain

**After:** One unified interface → all features use the same API, easy to switch models, track performance, and add new features

## Architecture

```
llm_orchestrator/
├── core/                    # Core orchestration
│   ├── orchestrator.py      # Main LLMOrchestrator class
│   ├── operation_handler.py # Base handler for operations
│   └── handler_registry.py  # Handler registration system
├── operations/              # Feature-specific operations
│   └── pillars/            # Pillar operations
│       ├── handlers.py      # Operation handlers
│       ├── prompts.py       # Prompt templates
│       └── schemas.py       # Response schemas (Pydantic)
├── models/                  # Model provider layer
│   ├── manager.py          # ModelManager for provider abstraction
│   └── providers/          # Provider implementations
│       ├── ollama.py        # Local models (Llama, Mistral, etc.)
│       ├── openai_provider.py  # GPT-4, GPT-3.5, etc.
│       └── gemini_provider.py  # Gemini 2.0, Gemini 1.5, etc.
├── types.py                # Type definitions (LLMRequest, LLMResponse)
├── exceptions.py           # Custom exception hierarchy
└── config.py              # Configuration management
```

## Status

✅ **Monolithic Mode Complete** - This is ready:

- [x] Type definitions (LLMRequest, LLMResponse, metadata)
- [x] Exception handling (14 error types with proper HTTP mapping)
- [x] Configuration management (env vars, Django integration)
- [x] Model provider layer (Ollama, OpenAI, Gemini)
- [x] Operation handler framework
- [x] Pillar operations (operations: validate, improve, evaluate_*, suggest_additions)
- [x] Execution time tracking & performance metrics
- [x] Model alias system (gemini → gemini-2.0-flash-exp, etc.)
- [x] Structured output support (Pydantic schemas)

🚧 **Agentic Mode** - Planned for thesis research:

- [ ] Agent framework
- [ ] Multi-agent orchestration
- [ ] Parallel execution
- [ ] Agent-to-agent communication

## Quick Start

### Basic Usage

```python
from llm_orchestrator import LLMOrchestrator, LLMRequest

# Initialize orchestrator (loads config from .env)
orchestrator = LLMOrchestrator()

# Create a request
request = LLMRequest(
    feature="pillars",
    operation="validate",
    data={"name": "Core Mechanic", "description": "Players solve puzzles"},
    model_id="gemini-2.0-flash-exp"  # or use alias: "gemini"
)

# Execute
response = orchestrator.execute(request)

# Access results
print(response.results)
# {'is_valid': True, 'feedback': 'Clear and concise...', 'improved_version': {...}}

print(response.metadata.execution_time_ms)
# 1247

print(response.metadata.models_used)
# ['gemini-2.0-flash-exp']
```

### Available Operations

**Pillars Feature:**
- `pillars.validate` - Validate pillar structure and clarity
- `pillars.improve` - Generate improved version of pillar
- `pillars.evaluate_completeness` - Check if pillars cover game design adequately
- `pillars.evaluate_contradictions` - Find contradictions between pillars
- `pillars.suggest_additions` - Suggest additional pillars
- `pillars.evaluate_context` - Evaluate alignment with context

## Configuration

### Environment Variables (.env file)

```bash
# Required for cloud providers
OPENAI_API_KEY=***
GEMINI_API_KEY=***

# Optional - Ollama settings (for local models)
OLLAMA_BASE_URL=http://localhost:11434  # default

# Optional - Execution mode
LLM_ORCHESTRATOR_DEFAULT_EXECUTION_MODE=monolithic  # or "agentic"

# Optional - Timeouts
LLM_ORCHESTRATOR_DEFAULT_TIMEOUT_MS=120000  # 2 minutes
```

### Model Aliases

Hardcoded in `config.py` for convenience:
- `"gemini"` → `"gemini-2.0-flash-exp"`
- `"openai"` → `"gpt-4o-mini"`

You can use either the alias or full model ID in requests.

## Design Principles

1. **Feature-agnostic**: Same API for all pix:e features
2. **Mode-flexible**: Supports monolithic and agentic execution
3. **Model-agnostic**: Works with local and cloud providers transparently
4. **Type-safe**: Full Pydantic validation for requests/responses
5. **Extensible**: Easy to add new features, operations, and providers
6. **Observable**: Rich metadata for evaluation and debugging

## Extending the Orchestrator

### Adding a New Operation

**Example: Adding a "summarize" operation to the pillars feature**

1. **Define response schema** in `operations/pillars/schemas.py`:
```python
from pydantic import BaseModel

class PillarSummaryResponse(BaseModel):
    summary: str
    key_points: list[str]
    word_count: int
```

2. **Create prompt template** in `operations/pillars/prompts.py`:
```python
SummarizePrompt = """
Summarize this game design pillar in 2-3 sentences:

Name: %s
Description: %s

Focus on the core essence and key mechanics.
"""
```

3. **Create handler** in `operations/pillars/handlers.py`:
```python
class SummarizePillarHandler(BaseOperationHandler):
    """Summarize a game design pillar."""

    operation_id = "pillars.summarize"
    response_schema = PillarSummaryResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return SummarizePrompt % (data['name'], data['description'])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if 'name' not in data or 'description' not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'name' and 'description'"
            )
```

4. **Register handler** in `register_all_handlers()` function:
```python
def register_all_handlers():
    # ... existing handlers ...
    register_handler("pillars.summarize", SummarizePillarHandler)
```

5. **Use from Django views**:
```python
from llm_orchestrator import LLMOrchestrator, LLMRequest

orchestrator = LLMOrchestrator()
request = LLMRequest(
    feature="pillars",
    operation="summarize",
    data={"name": pillar.name, "description": pillar.description},
    model_id="gemini"
)
response = orchestrator.execute(request)
summary = response.results['summary']
```

### Adding a New Feature

**Example: Adding "moodboards" features**

1. **Create feature directory**:
```bash
mkdir -p llm_orchestrator/operations/moodboards
touch llm_orchestrator/operations/moodboards/{__init__.py,handlers.py,prompts.py,schemas.py}
```

2. **Define schemas** in `schemas.py`:
```python
from pydantic import BaseModel

class MoodboardAnalysis(BaseModel):
    style: str
    mood: str
    color_palette: list[str]
    suggestions: list[str]
```

3. **Create prompts** in `prompts.py`:
```python
AnalyzeMoodboardPrompt = """
Analyze this moodboard description and extract:
- Visual style
- Mood/atmosphere
- Color palette
- Suggestions for improvement

Moodboard: %s
"""
```

4. **Implement handlers** in `handlers.py`:
```python
from llm_orchestrator.core import BaseOperationHandler, register_handler
from llm_orchestrator.exceptions import InvalidRequestError
from .prompts import AnalyzeMoodboardPrompt
from .schemas import MoodboardAnalysis

class AnalyzeMoodboardHandler(BaseOperationHandler):
    operation_id = "moodboards.analyze"
    response_schema = MoodboardAnalysis

    def build_prompt(self, data: dict) -> str:
        return AnalyzeMoodboardPrompt % data['description']

    def validate_input(self, data: dict) -> None:
        if 'description' not in data:
            raise InvalidRequestError(message="Missing 'description'")

def register_all_handlers():
    register_handler("moodboards.analyze", AnalyzeMoodboardHandler)

# Auto-register on import
register_all_handlers()
```

5. **Import in Django views** to trigger registration:
```python
# This import registers all moodboard handlers
import llm_orchestrator.operations.moodboards.handlers

# Now use it
orchestrator = LLMOrchestrator()
request = LLMRequest(
    feature="moodboards",
    operation="analyze",
    data={"description": moodboard.description},
    model_id="gemini"
)
response = orchestrator.execute(request)
```

### Adding a New Provider

**Example: Adding Anthropic Claude support**

1. **Create provider class** in `models/providers/anthropic_provider.py`:
```python
from typing import Any, Dict, List, Optional
from anthropic import Anthropic  # pip install anthropic
from llm_orchestrator.models.providers.base import BaseProvider
from llm_orchestrator.types import ModelDetails, ProviderType
from llm_orchestrator.exceptions import ProviderError

class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def provider_type(self) -> ProviderType:
        return "cloud"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key")
        if not api_key:
            raise ProviderError(
                provider="anthropic",
                message="API key is required"
            )
        self.client = Anthropic(api_key=api_key)

    def generate_text(self, model_name: str, prompt: str, **kwargs) -> str:
        response = self.client.messages.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 1024),
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.content[0].text

    # Implement other required methods...
```

2. **Add configuration** in `config.py`:
```python
@dataclass
class Config:
    # ... existing fields ...

    # Anthropic settings
    anthropic_api_key: Optional[str] = None
    anthropic_timeout_seconds: int = 60

    # Update model_aliases
    model_aliases: dict = field(default_factory=lambda: {
        "gemini": "gemini-2.0-flash-exp",
        "openai": "gpt-4o-mini",
        "claude": "claude-3-5-sonnet-20241022"  # New alias
    })
```

3. **Register in ModelManager** (`models/manager.py`):
```python
from llm_orchestrator.models.providers.anthropic_provider import AnthropicProvider

class ModelManager:
    def __init__(self, config: Config):
        # ... existing providers ...

        # Register Anthropic
        if config.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(
                config.get_provider_config("anthropic")
            )
```

4. **Add to provider config getter** in `config.py`:
```python
def get_provider_config(self, provider: str) -> dict:
    # ... existing providers ...
    elif provider == "anthropic":
        return {
            "api_key": self.anthropic_api_key,
            "timeout_seconds": self.anthropic_timeout_seconds,
        }
```

5. **Use it**:
```python
# .env file
ANTHROPIC_API_KEY=***

# In code
request = LLMRequest(
    feature="pillars",
    operation="validate",
    data={...},
    model_id="claude"  # or "claude-3-5-sonnet-20241022"
)
```

## Integration with Django

The orchestrator integrates seamlessly with Django:

```python
# backend/llm/views.py
from llm_orchestrator import LLMOrchestrator, LLMRequest
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def validate_pillar(request):
    """Validate a game design pillar using LLM."""
    orchestrator = LLMOrchestrator()

    llm_request = LLMRequest(
        feature="pillars",
        operation="validate",
        data={
            "name": request.data.get("name"),
            "description": request.data.get("description")
        },
        model_id=request.data.get("model", "gemini")
    )

    llm_response = orchestrator.execute(llm_request)

    return Response({
        "results": llm_response.results,
        "execution_time_ms": llm_response.metadata.execution_time_ms,
        "model_used": llm_response.metadata.models_used[0]
    })
```

## Project Structure Philosophy

- **`orchestrator/core/`**: Framework code - don't modify unless adding core features
- **`orchestrator/operations/{feature}/`**: Feature-specific code - add new features here
- **`orchestrator/models/providers/`**: Provider implementations - add new LLM providers here
- **`backend/llm/`**: Django integration - views that use the orchestrator

## Error Handling

The orchestrator provides structured error handling with 14 error types:

**Client Errors (4xx):**
- `InvalidRequestError` (400) - Malformed request
- `ValidationError` (400) - Data validation failed
- `UnknownFeatureError` (400) - Feature not found
- `UnknownOperationError` (400) - Operation not found
- `AuthenticationError` (401) - Invalid credentials
- `PermissionDeniedError` (403) - Insufficient permissions
- `RunNotFoundError` (404) - Run ID not found
- `IdempotencyConflictError` (409) - Idempotency key conflict
- `RateLimitError` (429) - Rate limit exceeded

**Server Errors (5xx):**
- `AgentFailureError` (500) - Agent execution failed
- `ProviderError` (502) - Upstream provider error
- `ModelUnavailableError` (503) - Model not available
- `InsufficientResourcesError` (503) - Out of resources
- `TimeoutError` (504) - Operation timed out

All errors include:
- Clear error message
- Error code
- Context (provider, model, operation, etc.)
- Suggestions for resolution (where applicable)

## Performance & Monitoring

Every request tracks:
- **Execution time** (`metadata.execution_time_ms`)
- **Models used** (`metadata.models_used`)
- **Execution mode** (`metadata.execution_mode`)
- **Operation metadata** (depends on operation)

Example:
```python
response = orchestrator.execute(request)
print(f"Completed in {response.metadata.execution_time_ms}ms")
print(f"Used model: {response.metadata.models_used[0]}")
```

## Testing

Run tests from project root:
```bash
# Run all tests
python -m pytest llm_orchestrator/tests/ -v

# Run specific test file
python -m pytest llm_orchestrator/tests/test_handlers.py -v

# Run with coverage
python -m pytest llm_orchestrator/tests/ --cov=llm_orchestrator
```