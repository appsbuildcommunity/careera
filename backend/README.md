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
Unit tests run entirely in-memory using the `FakeDB` test fixtures provided in `app/conftest.py`. They do not require MongoDB or any API keys.

```bash
# Run all unit tests
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
Integration tests make real external LLM API calls and write output to `backend/integration_results/`. They require live API keys in `backend/.env`.

```bash
# Run integration tests only
poetry run pytest -m integration -s
```

### 3. Test Standards for Contributors
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
