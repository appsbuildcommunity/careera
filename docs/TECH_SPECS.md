# 🛠️ Technical Specifications

This document covers the project structure, database schemas, and API overview for Careera.

For full request/response details, run the backend and visit the auto-generated interactive docs at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

**Table of Contents**
- [Project Structure](#project-structure)
- [Database Schemas](#database-schemas)
- [API Reference](#api-reference)
- [Error Codes](#error-codes)

---

## Project Structure

```
careera/
│
├── frontend/                          # Next.js Application (Port 3000)
│   ├── src/
│   │   ├── app/                       # Next.js pages (App Router)
│   │   │   ├── login/page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── profile/page.tsx       # Upload CV & preferences
│   │   │   ├── analyze/page.tsx       # Career analysis results
│   │   │   ├── paths/
│   │   │   │   ├── page.tsx           # List all paths
│   │   │   │   └── [id]/page.tsx      # Single path details
│   │   │   ├── sessions/
│   │   │   │   ├── project/[id]/page.tsx
│   │   │   │   └── interview/[id]/page.tsx
│   │   │   └── stats/page.tsx         # User stats & leaderboard
│   │   ├── components/                # Reusable React components
│   │   │   ├── ui/                    # shadcn/ui base components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── PathCard.tsx
│   │   │   └── CodeEditor.tsx
│   │   └── lib/
│   │       ├── api.ts                 # Axios API client
│   │       ├── auth.ts                # Auth utilities
│   │       └── types.ts               # TypeScript types
│   ├── .env.example
│   ├── package.json
│   └── next.config.js
│
├── backend/                           # FastAPI Application (Port 8000)
│   └── app/
│       ├── main.py                    # FastAPI entry point and router registration
│       ├── database/                  # Shared MongoDB connection helpers
│       │   └── connection.py
│       ├── auth/                      # Authentication domain
│       │   ├── api/
│       │   ├── model/
│       │   ├── service/               # Auth business logic
│       │   └── utils/
│       ├── profile/                   # User profile domain
│       │   ├── api/
│       │   ├── model/
│       │   ├── service/
│       │   └── utils/
│       ├── career/                    # Career analysis and path domain
│       │   ├── api/
│       │   ├── db/
│       │   ├── model/
│       │   ├── service/
│       │   └── utils/
│       ├── project/                   # Project session domain
│       │   ├── api/
│       │   ├── db/
│       │   ├── model/
│       │   ├── service/
│       │   └── utils/
│       ├── interview/                 # Interview session domain
│       │   ├── api/
│       │   ├── model/
│       │   ├── service/
│       │   └── utils/
│       ├── session/                   # Shared session tracking domain
│       │   ├── api/
│       │   ├── db/
│       │   ├── model/
│       │   ├── service/
│       │   └── utils/
│       └── share/                     # Sharing/export domain
│           ├── api/
│           ├── model/
│           ├── service/
│           └── utils/
│
└── docker-compose.yml
```

The backend now follows a feature-first structure: each domain keeps its own API layer, models, services, and helpers together instead of placing everything in shared top-level folders.

All registered backend routes use the `/api/v1` prefix:

```python
# app/main.py
from app.auth.api import auth

app.include_router(auth.router, prefix="/api/v1")
# Additional category routers are added here as they are implemented.
```

---

## Database Schemas

Careera uses 8 MongoDB collections. All `_id` fields are auto-generated MongoDB ObjectIds.

### `users`

```json
{
  "_id": "ObjectId",
  "email": "String (UNIQUE)",
  "name": "String",
  "avatar": "String",
  "created_at": "Date",
  "last_login": "Date",
  "profile": {
    "cv_parsed_text": "String",
    "linkedin_parsed_text": "String",
    "interests": {
      "roles": ["String"],
      "focus_areas": ["String"]
    }
  },
  "gamification": {
    "total_xp": "Number",
    "level": "Number"
  },
  "analyses_ids": ["ObjectId → analyses._id"],
  "career_paths_ids": ["ObjectId → career_paths._id"]
}
```

Indexes: `{ "email": 1 }` UNIQUE

---

### `analyses`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId → users._id",
  "created_at": "Date",
  "profile_insight": {
    "summary": "String",
    "hard_skills": ["String"],
    "soft_skills": ["String"]
  },
  "recommendations": [
    {
      "rec_index": "Number",
      "title": "String",
      "description": "String",
      "match_score": "Number (0–100)",
      "reasoning": "String",
      "missing_skills": ["String"],
      "tags": ["String"],
      "is_expanded": "Boolean",
      "linked_path_id": "ObjectId → career_paths._id (null if not expanded)"
    }
  ]
}
```

Indexes: `{ "user_id": 1 }`, `{ "created_at": -1 }`

---

### `career_paths`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId → users._id",
  "analysis_id": "ObjectId → analyses._id",
  "recommendation_index": "Number",
  "title": "String",
  "description": "String",
  "tags": ["String"],
  "missing_skills": ["String"],
  "status": "ACTIVE | ARCHIVED | DELETED",
  "deleted_at": "Date",
  "created_at": "Date",
  "nodes": [
    {
      "step": "Number (0, 1, 2...)",
      "title": "String",
      "description": "String",
      "type": "LEARNING | PROJECT | INTERVIEW",
      "difficulty": "EASY | MEDIUM | HARD",
      "tags": ["String"],
      "status": "LOCKED | UNLOCKED | COMPLETED",
      "is_expanded": "Boolean",
      "linked_content_id": "ObjectId → *_templates._id",
      "max_score": "Number",
      "attempts": "Number",
      "xp_gained": "Number",
      "related_sessions": ["ObjectId → *_sessions._id"],
      "completed_at": "Date"
    }
  ]
}
```

Indexes: `{ "user_id": 1 }`, `{ "status": 1 }`, `{ "analysis_id": 1 }`

---

### `learning_templates`

```json
{
  "_id": "ObjectId",
  "title": "String",
  "description": "String",
  "difficulty": "EASY | MEDIUM | HARD",
  "tags": ["String"],
  "estimated_duration": "String",
  "estimated_minutes": "Number",
  "content": {
    "intro_summary": "String",
    "key_concepts": [
      { "concept": "String", "description": "String", "why_learn": "String" }
    ],
    "resources": [
      { "label": "String", "url": "String" }
    ]
  },
  "created_at": "Date"
}
```

Indexes: `{ "tags": 1 }`, `{ "difficulty": 1 }`

---

### `project_templates`

```json
{
  "_id": "ObjectId",
  "title": "String",
  "difficulty": "EASY | MEDIUM | HARD",
  "tags": ["String"],
  "min_pass_score": "Number",
  "estimated_duration": "String",
  "estimated_minutes": "Number",
  "total_tasks": "Number",
  "total_subtasks": "Number",
  "tasks": [
    {
      "task_index": "Number",
      "title": "String",
      "description": "String",
      "subtasks": [
        {
          "subtask_index": "Number",
          "title": "String",
          "description": "String",
          "acceptance_criteria": "String",
          "hint": "String",
          "model_solution": "String (HIDDEN from user)"
        }
      ]
    }
  ],
  "created_at": "Date"
}
```

Indexes: `{ "tags": 1 }`, `{ "difficulty": 1 }`

---

### `project_sessions`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId → users._id",
  "template_id": "ObjectId → project_templates._id",
  "path_id": "ObjectId → career_paths._id (nullable)",
  "node_step": "Number",
  "status": "IN_PROGRESS | PASSED | FAILED | ABANDONED",
  "current_task_index": "Number",
  "current_subtask_index": "Number",
  "total_score": "Number",
  "xp_earned": "Number",
  "attempt_number": "Number",
  "started_at": "Date",
  "completed_at": "Date",
  "duration_seconds": "Number",
  "tasks": [
    {
      "task_index": "Number",
      "status": "PENDING | IN_PROGRESS | COMPLETED",
      "subtasks": [
        {
          "subtask_index": "Number",
          "user_submission": "String",
          "score": "Number",
          "status": "PENDING | PASSED | FAILED | FORFEITED",
          "feedback": "String"
        }
      ]
    }
  ]
}
```

Indexes: `{ "user_id": 1 }`, `{ "template_id": 1 }`, `{ "status": 1 }`, `{ "path_id": 1 }`

---

### `interview_templates`

```json
{
  "_id": "ObjectId",
  "title": "String",
  "difficulty": "EASY | MEDIUM | HARD",
  "tags": ["String"],
  "estimated_duration": "String",
  "estimated_minutes": "Number",
  "min_pass_score": "Number",
  "total_questions": "Number",
  "questions": [
    {
      "question_index": "Number",
      "text": "String",
      "hint": "String",
      "model_answer": "String (HIDDEN from user)"
    }
  ],
  "created_at": "Date"
}
```

Indexes: `{ "tags": 1 }`, `{ "difficulty": 1 }`

---

### `interview_sessions`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId → users._id",
  "template_id": "ObjectId → interview_templates._id",
  "path_id": "ObjectId → career_paths._id (nullable)",
  "node_step": "Number",
  "status": "IN_PROGRESS | PASSED | FAILED | ABANDONED",
  "current_question_index": "Number",
  "average_score": "Number",
  "xp_earned": "Number",
  "attempt_number": "Number",
  "started_at": "Date",
  "completed_at": "Date",
  "duration_seconds": "Number",
  "answers": [
    {
      "question_index": "Number",
      "user_answer": "String",
      "score": "Number",
      "feedback": "String",
      "status": "PENDING | ANSWERED | SKIPPED"
    }
  ]
}
```

Indexes: `{ "user_id": 1 }`, `{ "template_id": 1 }`, `{ "status": 1 }`, `{ "path_id": 1 }`

---

### Enum Values Summary

| Field | Values |
|---|---|
| `career_paths.status` | `ACTIVE`, `ARCHIVED`, `DELETED` |
| `nodes.type` | `LEARNING`, `PROJECT`, `INTERVIEW` |
| `nodes.status` | `LOCKED`, `UNLOCKED`, `COMPLETED` |
| `nodes.difficulty` | `EASY`, `MEDIUM`, `HARD` |
| `*_sessions.status` | `IN_PROGRESS`, `PASSED`, `FAILED`, `ABANDONED` |
| `project_sessions.tasks.status` | `PENDING`, `IN_PROGRESS`, `COMPLETED` |
| `project_sessions.subtasks.status` | `PENDING`, `PASSED`, `FAILED`, `FORFEITED` |
| `interview_sessions.answers.status` | `PENDING`, `ANSWERED`, `SKIPPED` |

---

## API Reference

**Base URL:** `https://api.careera.com/api/v1`

**Authentication:** All endpoints except `/auth/login` require:
```
Authorization: Bearer <access_token>
```

> For full request bodies, response shapes, and live testing — run the backend and open **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

### Module 1 — Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Validate Google `id_token`, create or retrieve user, return access + refresh tokens |
| `POST` | `/auth/refresh` | Exchange a refresh token for a new access token |
| `POST` | `/auth/logout` | Invalidate current tokens and clean up session |

---

### Module 2 — User Profile

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Get authenticated user profile including gamification stats |
| `POST` | `/users/me/upload-cv` | Upload resume PDF (max 5MB), extract and store parsed text |
| `POST` | `/users/me/upload-linkedin` | Upload LinkedIn PDF export, extract and store parsed text |
| `PATCH` | `/users/me/preferences` | Update career interests (roles, focus areas) |

---

### Module 3 — Career Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/careers/analyze` | Run AI analysis on user profile, generate ranked career recommendations |
| `GET` | `/careers/analyses` | List all analyses for the user, sorted newest first |
| `GET` | `/careers/analyses/{analysis_id}` | Get a specific analysis with all recommendations |

---

### Module 4 — Career Paths

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/careers/paths` | Generate a new career path from a selected recommendation |
| `GET` | `/careers/paths` | List all paths with progress stats (filterable by status) |
| `GET` | `/careers/paths/{path_id}` | Get full path details with all nodes |
| `PATCH` | `/careers/paths/{path_id}/archive` | Archive a path (preserves all data) |
| `DELETE` | `/careers/paths/{path_id}` | Soft-delete a path (recoverable) |
| `PATCH` | `/careers/paths/{path_id}/restore` | Restore a soft-deleted path to active |

---

### Module 5 — Node Content

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/careers/paths/{path_id}/nodes/{step}/expand` | AI-generate content for a node (learning materials, project tasks, or interview questions) |
| `PATCH` | `/careers/paths/{path_id}/nodes/{step}/complete` | Mark a learning node complete, award XP, unlock next node |

---

### Module 6 — Project Sessions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/projects/start` | Start a project session from an expanded project node |
| `GET` | `/projects/{session_id}` | Get session details with current task/subtask progress |
| `POST` | `/projects/{session_id}/tasks/{task_index}/subtasks/{subtask_index}/submit` | Submit code for AI grading; advances on pass, awards XP on completion |
| `POST` | `/projects/{session_id}/tasks/{task_index}/subtasks/{subtask_index}/forfeit` | Forfeit subtask, reveal model solution, advance automatically |
| `POST` | `/projects/{session_id}/abandon` | Abandon the session (no XP awarded, kept in history) |

---

### Module 7 — Interview Sessions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/interviews/start` | Start an interview session from an expanded interview node |
| `POST` | `/interviews/{session_id}/submit` | Submit an answer for AI grading; returns next question or final result |
| `GET` | `/interviews/{session_id}` | Get session details with questions summary and progress |
| `GET` | `/interviews/{session_id}/result` | Get full transcript with Q&A pairs, scores, and model answers |
| `POST` | `/interviews/{session_id}/abandon` | Abandon the session (no XP awarded, kept in history) |

---

### Module 8 — Session History

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all sessions (projects + interviews), filterable by type and status, with pagination |
| `GET` | `/sessions/{session_id}` | Redirect to the appropriate project or interview session endpoint |

---

### Module 9 — Gamification & Stats

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me/stats` | Get full stats: XP, level, path counts, session aggregates, time spent |
| `GET` | `/leaderboard` | Get ranked users by XP, filterable by period (weekly / monthly / all-time) |

---

### Module 10 — Share

> 🚧 Endpoints for this module are not yet defined. The `share/` domain is reserved for sharing and exporting career paths or results. Endpoints will be added here as they are designed.

---

## Error Codes

| Code | Description |
|---|---|
| `MISSING_TOKEN` | Missing `id_token` field |
| `INVALID_TOKEN` | Token signature invalid or expired |
| `INVALID_REFRESH` | Refresh token expired or revoked |
| `INVALID_FILE_TYPE` | File must be PDF |
| `FILE_TOO_LARGE` | File exceeds 5MB limit |
| `PROFILE_INCOMPLETE` | User must upload CV before running analysis |
| `AI_SERVICE_ERROR` | AI generation failed |
| `ANALYSIS_NOT_FOUND` | Analysis ID does not exist |
| `RECOMMENDATION_NOT_FOUND` | Recommendation index is invalid |
| `PATH_NOT_FOUND` | Career path not found |
| `PATH_NOT_DELETED` | Path is not in deleted status |
| `NODE_NOT_FOUND` | Node step does not exist |
| `NODE_ALREADY_COMPLETED` | Node was already completed |
| `NODE_NOT_EXPANDED` | Node content must be expanded first |
| `TEMPLATE_NOT_FOUND` | Template does not exist |
| `SESSION_NOT_FOUND` | Session does not exist |
| `SESSION_NOT_COMPLETED` | Session is not yet completed |
| `INVALID_REQUEST` | Request body validation failed |
| `INVALID_TASK_INDEX` | Task index is invalid |
| `INVALID_SUBTASK_INDEX` | Subtask index is invalid |