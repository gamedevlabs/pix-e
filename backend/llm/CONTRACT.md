# LLM Consumer Contract

## Core Principle

**Consumer code never constructs the LLM infrastructure — it always receives one.**

Every module that needs an LLM gets its `ModelManager` injected. The only place
`ModelManager` is created is in `UserLLMOrchestratorMixin`, driven by the
authenticated request. No constructors, no globals, no env-var fallbacks.

---

## Rule 1: Views use `UserLLMOrchestratorMixin`

```python
from llm.mixins import UserLLMOrchestratorMixin

class MyView(UserLLMOrchestratorMixin, APIView):
    def post(self, request):
        orchestrator = self.get_llm_orchestrator(request)
        # Use orchestrator.execute() or pass orchestrator.model_manager
```

- The mixin extracts the encryption key from the session (derived from the
  user's password at login via PBKDF2).
- If the key is missing or expired, `get_llm_orchestrator()` raises
  `NotAuthenticated` (401), which the frontend catches to show the
  password re-entry modal.
- **Never** call `LLMOrchestrator()` or `ModelManager()` in a view.

## Rule 2: Workflows/services receive `model_manager` as parameter

```python
from llm.providers.manager import ModelManager

class MyWorkflow:
    def __init__(self, model_manager: ModelManager):
        self._model_manager = model_manager

def my_service(*, model_manager: ModelManager, ...):
    ...
```

- Never call `ModelManager()` or `LLMOrchestrator()` internally.
- Type-annotate the parameter: `model_manager: ModelManager`.
- Tests inject a `Mock(spec=ModelManager)` instead.

## Rule 3: Use `LLMProviderAdapter` for strategies/generators

```python
from llm.llm_adapter import LLMProviderAdapter

adapter = LLMProviderAdapter(
    model_manager=some_model_manager,  # required
    model_name="gpt-4o-mini",
    temperature=0,
)
```

- `model_manager` is required. Passing `None` raises `TypeError`.
- `create_llm_provider(model_manager=..., ...)` is the convenience factory.
- The adapter duck-types the `LLMProvider` protocol (`.generate(prompt) -> str`)
  used by context strategies and evaluators.

---

## Reference Patterns

### New View

```python
# File: my_app/views.py
from rest_framework.views import APIView
from llm.mixins import UserLLMOrchestratorMixin

class MyNewView(UserLLMOrchestratorMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        orchestrator = self.get_llm_orchestrator(request)
        # Done — orchestrator.model_manager is ready
```

### New Workflow

```python
# File: my_app/workflows.py
from llm.providers.manager import ModelManager

class MyWorkflow:
    def __init__(self, model_manager: ModelManager):
        self._model_manager = model_manager

    def run(self, data: dict):
        result = self._model_manager.generate_with_model(
            model_name="gpt-4o-mini",
            prompt=data["prompt"],
        )
        return result.text
```

Then in the view:

```python
workflow = MyWorkflow(model_manager=orchestrator.model_manager)
```

### New Management Command

```python
# File: my_app/management/commands/my_command.py
from django.core.management.base import BaseCommand
from accounts.management_utils import add_user_argument, get_model_manager_for_user

class Command(BaseCommand):
    help = "My command"

    def add_arguments(self, parser):
        add_user_argument(parser)
        # ... other args

    def handle(self, *args, **options):
        model_manager = get_model_manager_for_user(
            username=options["user"],
            password_from_stdin=options.get("password_from_stdin", False),
        )
        # Use model_manager for LLM operations
```

The password is prompted interactively. For scripting:

```bash
echo "password" | python manage.py my_command --user myname --password-from-stdin
```

---

## Rationale

### Why no global API keys?

The system previously supported two parallel paths: global keys from
environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`) and per-user
keys from the `UserApiKey` model. This created security gaps and a
maintenance burden. Now every LLM call is explicitly scoped to a user.

### Why password prompt in management commands?

The Fernet encryption key used to decrypt `UserApiKey` records is derived
from the user's password via PBKDF2-SHA256 and stored **only** in the
Django session. Management commands have no session, so the only way to
re-derive the key is to prompt for the password.
`--password-from-stdin` supports scripting use cases.
