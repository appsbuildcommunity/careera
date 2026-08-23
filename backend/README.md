# Careera — Backend

This backend follows a **feature-first (domain-driven)** structure. Each domain owns its own API endpoints, data models, and services.

## Domain Map

```text
backend/app/
├── main.py              # Registers all routers with /api/v1 prefix
├── database/            # Shared MongoDB connection
├── auth/                # Google OAuth + JWTs
├── profile/             # Users collection
├── career/              # Analyses & Career Paths collections
├── project/             # Project Templates & Sessions
├── interview/           # Interview Templates & Sessions
├── session/             # Cross-domain session history
└── share/               # Cross-cutting shared services (LLM engine, API errors)
```

## Development Rules

To ensure a robust and consistent architecture, all backend code must adhere to the following standards:

### 1. Layered Architecture
Inside each domain folder, strictly separate concerns:
*   **`router.py`**: Handles HTTP requests, path parameters, and response serialization. **No business logic here.**
*   **`service.py`**: Contains the core business logic, LLM orchestrations, and validations.
*   **`models.py` / `schemas.py`**: Pydantic models for request/response validation and MongoDB document mapping.

### 2. Error Handling
*   Never return generic `500 Internal Server Error` for predictable failures.
*   Always raise FastAPI `HTTPException` using the exact custom Error Codes defined in [API_REFERENCE.md](../docs/API_REFERENCE.md#error-codes) (e.g., `404 PATH_NOT_FOUND`, `400 NODE_NOT_EXPANDED`).

### 3. Typing & Validation
*   **Strict Type Hinting:** Every function argument and return value must have Python type hints (`-> dict`, `-> list[str]`).
*   **Pydantic Everywhere:** Use Pydantic models for *all* incoming request bodies and outgoing responses. Never use raw Python dictionaries for I/O.
*   **Enums:** Never use hardcoded strings for statuses, types, or roles. Always use Python `Enum` classes that strictly match the values documented in [DB_SCHEMA.md](../docs/DB_SCHEMA.md).

### 4. Cross-Domain Isolation
*   Domains should not directly query another domain's database collection.
*   If the `project` domain needs user data, it should import a helper function from the `profile.service` layer, rather than executing a MongoDB query against the `users` collection directly.

### 5. Documentation Consistency (Single Source of Truth)
*   The API and Database markdown files are the absolute contracts for this project.
*   If you change a route, payload, response, or database field in the backend code, **you must update the corresponding documentation (e.g., `API_REFERENCE.md`, `DB_SCHEMA.md`) in the same Pull Request.**

---

## 🧪 Testing Guidelines & Instructions

Backend tests are written using `pytest` and `pytest-asyncio`. Tests are divided into **fast in-memory unit tests** and **live integration tests**.

### 1. Running Unit Tests (Default)
Unit tests run entirely in-memory using the `FakeDB` test fixtures provided in `app/conftest.py` and `MockChatModel`. They do not require MongoDB or any API keys, run in ~1–2s, and cost $0.00. `pytest.ini` automatically ignores integration tests by default.

```bash
# Run all unit tests (fast, offline, mocked)
poetry run pytest

# Run with verbose output and print statements
poetry run pytest -v -s

# Run tests for a specific domain
poetry run pytest app/auth/
poetry run pytest app/profile/
poetry run pytest app/career/
poetry run pytest app/share/

# Run a single test file
poetry run pytest app/profile/service/test_profile.py -v

# Run a specific test case by name
poetry run pytest app/profile/service/test_profile.py -k "test_get_profile"
```

### 2. Running Live Integration Tests
Integration tests make real external LLM API calls against the configured cloud provider (`LLM_PROVIDER`), validate the response against Pydantic blueprints, and save the live JSON output to `backend/integration_results/career_analysis_live.json` for developer inspection.

Requires `LLM_PROVIDER` and `LLM_API_KEY` to be set in `backend/.env` (skips automatically if unset).

```bash
# Run live integration tests only
poetry run pytest -m integration -s

# Inspect the saved live AI analysis result
cat integration_results/career_analysis_live.json
```

### 3. Relevant Types of Calls to Test

When implementing features, tests must cover the following categories of operations:

| Category | Target Endpoints / Functions | What to Test |
|---|---|---|
| **Auth & Security** | `POST /auth/google`, `POST /auth/refresh`, `POST /auth/logout` | Token signing, user upsert on login, blacklist revocation in MongoDB `refresh_tokens`, expired token rejection, middleware protection (`get_current_user`). |
| **Profile & Files** | `GET /users/me`, `POST /users/me/upload-cv`, `PATCH /users/me/preferences` | User profile retrieval, PDF file validation and text extraction via `pypdf`, partial preference updates, error on non-PDF formats. |
| **LLM Generation** | Domain services using `generate_json()` | Prompt construction, schema validation with Pydantic blueprints, error propagation (`LLMProviderError`), fallback behavior with `MockChatModel`. |
| **Async Background Tasks** | `POST /careers/analyze`, `POST /careers/paths` | `BackgroundTasks` lifecycle (`PENDING` → `READY` or `FAILED`), polling accuracy, and background error handling. |
| **Database & Multi-Tenancy** | Domain CRUD operations | Multi-tenant isolation (`user_id` filtering), sorting newest-first, and ensuring cross-domain calls use service layers rather than raw foreign queries. |

### 4. Test Standards for Contributors
*   **Fixture Usage:** Always use the `fake_db` fixture from `conftest.py` for database mocking.
*   **No Real Network Calls in Unit Tests:** All unit tests must be self-contained and run in milliseconds.
*   **Coverage Rule:** Every new service function, data model validation, and endpoint must include corresponding unit tests in its domain's test files.

---

## References

For detailed backend context, refer to the main documentation:
- 📖 [API Reference](../docs/API_REFERENCE.md) — All endpoints, requests, and responses
- 🤖 [LLM Integration Guide](../docs/LLM_INTEGRATION.md) — LLM provider configuration and service usage
- 💾 [Database Schema](../docs/DB_SCHEMA.md) — MongoDB collections and field types
- 🏗️ [Architecture](../docs/ARCHITECTURE.md) — Session state machines and XP formula
- ✅ [Feature Tracker](../docs/FEATURES.md) — Task breakdown for backend development
