# Careera — Architecture Decisions & Future

> This document captures **why** the system is built this way and **what's next**.
> It serves as a historical record of technical decisions and a roadmap for future architecture.

---

## 1. Infrastructure Choices

| Layer | Choice | Rationale |
|---|---|---|
| **Backend** | FastAPI (Python) | Fast to build, natively async, auto-generates OpenAPI docs (`/docs`) which serve as the exact contract for AI frontend generation. Managed via Poetry. |
| **Database** | MongoDB | LLM output is deeply nested, document-shaped data (variable fields, arrays of objects). A relational schema would require many joins and complex migrations every time an LLM prompt changes. MongoDB embraces this flexibility natively. |
| **LLM Provider** | Multi-Provider via LangChain (`mock`, `gemini`, `openai`, `anthropic`, `deepseek`) | Provider-agnostic abstraction layer with deterministic offline mock engine for testing and configurable cloud providers for production. |
| **Deployment** | TBD | Will evaluate free-tier platforms suitable for FastAPI, Next.js, and MongoDB. |

---

## 2. Data Model Rules

*   **Polymorphic References:** Nodes have a `linked_content_id` that points to one of three template collections (`learning_templates`, `project_templates`, `interview_templates`). A companion field `linked_content_collection` acts as a discriminator and is validated at write time to match `node.type`.
*   **Soft Delete:** Career paths use soft deletes (`status = DELETED` + `deleted_at`). Hard deletes are not exposed.
*   **Node Unlock Order:** Completing step `N` sets step `N+1` status from `LOCKED` to `UNLOCKED`.
*   **Hidden Fields:** `model_solution` and `model_answer` in templates are stripped out by the API before returning data to the client.
*   **Server-Owned Position:** `current_task_index`, `current_subtask_index`, and `current_question_index` in sessions are tracked exclusively by the server. Clients do not pass these in URLs (e.g., `/submit/{task}/{subtask}` is rejected) to prevent cheating/skipping.

---

## 3. Schema Decisions

*   **Removed `users.analyses_ids` & `users.career_paths_ids`:** Maintaining parallel arrays adds unnecessary writes. We query `WHERE user_id = X` instead.
*   **Removed `nodes.related_sessions`:** This creates a fragile write-on-every-session-start coupling. We derive this at read time by querying sessions `WHERE path_id = X AND node_step = N`.
*   **Added `analyses.status`:** Set to `PENDING | READY | FAILED`. Required because `/careers/analyze` is an async operation.
*   **Added `career_paths.total_nodes`:** Set once at creation. Used to efficiently detect when the final node is reached.
*   **Added `sessions.expires_at`:** Frontend-driven timeout to clean up abandoned sessions.
*   **Renamed `total_score` → `average_score`:** In project sessions, this better reflects the 0–100 scale (matching interview sessions).

---

## 4. API Decisions

*   **Async Profile Analysis:** `POST /careers/analyze` returns `202 Accepted` immediately because LLM generation can take 5–15 seconds, risking HTTP timeouts. Clients must poll.
*   **Simplified Session Start:** `POST /projects/start` takes only `{ path_id, node_step }`. The server resolves the `template_id` internally, reducing client payload complexity and preventing spoofing.
*   **Internal Node Expansion:** `/expand` is not exposed as a user action. Templates generate automatically via a look-ahead background task to eliminate loading states for users.
*   **Removed `GET /sessions/{id}` redirect:** The sessions list already returns the session `type`. The frontend routes directly to the correct project/interview page, making a server redirect unnecessary overhead.

---

## 5. Rejected Alternatives

| Idea | Verdict | Reason |
|---|---|---|
| PostgreSQL instead of MongoDB | ❌ | LLM output is deeply nested document-shaped data. A relational schema would require many joins and a rigid migration for every LLM prompt change. |
| Dedicated Job Queue (Celery + RabbitMQ/Redis) | ❌ | FastAPI `BackgroundTasks` is sufficient at MVP scale. A real job queue adds infrastructure (message broker + worker nodes) and devops overhead for no immediate benefit. |
| GraphQL | ❌ | REST + OpenAPI is the best contract for AI code generation (Cursor/v0). GraphQL adds schema complexity with no advantage here. |
| Separate `nodes` collection | ❌ | Nodes are never queried independently. Embedding in `career_paths` avoids joins and is the correct MongoDB access pattern. |
| Redis for token blacklist | ❌ | MongoDB TTL index achieves the same result with zero extra infrastructure. |
| Single merged `templates` collection | ❌ | Three separate collections with a `linked_content_collection` discriminator is much cleaner than a merged collection with massive, mutually-exclusive schema variants. |
| Eager template generation (all at once) | ❌ | Too slow at path creation + wastes expensive LLM credits on nodes the user never reaches. |
| Client-controlled task indices | ❌ | Cheat surface. Server tracks current position internally. |

---

## 6. Future Improvements

These features are architecturally supported but excluded from the initial MVP to guarantee delivery speed:

*   **Cross-User Template Reuse (Deduplication):** If two users get the exact same career path node, the system currently generates two identical templates. The architecture supports checking for an existing template hash before generating a new one to save LLM credits.
*   **Real Job Queue:** Profile analysis (`/analyze`) and background template generation currently use FastAPI `BackgroundTasks`. As the system scales, these should be moved to a robust job queue (e.g., Celery with RabbitMQ or Redis) to ensure fault tolerance, retries across server restarts, and better observability for async jobs.
