# Careera — API Reference

**Base URL:** `http://localhost:8000/api/v1` (dev) · `https://careera-api.onrender.com/api/v1` (prod)

**Auth:** All endpoints except `POST /auth/login` require:
```
Authorization: Bearer <access_token>
```

**All resources are user-scoped** — every query is filtered by `user_id`. Users cannot access each other's data.

**Interactive docs:** run the backend and open `http://localhost:8000/docs`

---

## Standard Error Response

All errors return the same shape:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description",
  "status_code": 400
}
```

---

## API Flow

The happy path through the system:

```text
  1. POST  /auth/login
  2. POST  /users/me/upload-cv
  3. POST  /careers/analyze              → async: poll GET /careers/analyses/{id}
  4. POST  /careers/paths                → triggers background template generation for node 0
  ┌─ For each LEARNING node:
  │   5a. PATCH /careers/paths/{id}/nodes/{step}/complete
  ├─ For each PROJECT node:
  │   5b. POST /projects/start  →  POST /projects/{id}/submit  (repeat per subtask)
  └─ For each INTERVIEW node:
      5c. POST /interviews/start  →  POST /interviews/{id}/submit  (repeat per question)
  6. GET   /users/me/stats
```

---

## Table of Contents

- [Module 1 — Authentication](#module-1--authentication)
- [Module 2 — User Profile](#module-2--user-profile)
- [Module 3 — Career Analysis](#module-3--career-analysis)
- [Module 4 — Career Paths](#module-4--career-paths)
- [Module 5 — Node Content](#module-5--node-content)
- [Module 6 — Project Sessions](#module-6--project-sessions)
- [Module 7 — Interview Sessions](#module-7--interview-sessions)
- [Module 8 — Session History](#module-8--session-history)
- [Module 9 — Gamification & Stats](#module-9--gamification--stats)
- [Error Codes](#error-codes)

---

## Module 1 — Authentication

<details>
<summary><strong>POST</strong> <code>/auth/login</code> — Login with Google</summary>

Validates a Google `id_token`, creates or retrieves the user, issues access + refresh tokens.

**Request:**
```json
{ "id_token": "string" }
```

**Response `200`:**
```json
{
  "message": "string",
  "token_type": "bearer",
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "avatar": "string"
  }
}
```

**Errors:** `400 MISSING_TOKEN` · `401 INVALID_TOKEN`

</details>

<details>
<summary><strong>POST</strong> <code>/auth/refresh</code> — Refresh Access Token</summary>

Exchanges a valid refresh token for a new access token.

**Request:**
```json
{ "refresh_token": "string" }
```

**Response `200`:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors:** `401 INVALID_REFRESH`

</details>

<details>
<summary><strong>POST</strong> <code>/auth/logout</code> — Logout</summary>

Blacklists the current access and refresh tokens (MongoDB TTL index handles cleanup).

**Response `200`:**
```json
{ "message": "Successfully logged out" }
```

</details>

---

## Module 2 — User Profile

<details>
<summary><strong>GET</strong> <code>/users/me</code> — Get Current User</summary>

**Response `200`:**
```json
{
  "id": "string",
  "email": "string",
  "name": "string",
  "avatar": "string",
  "created_at": "ISO8601",
  "last_login": "ISO8601",
  "profile": {
    "cv_parsed_text": "string",
    "linkedin_parsed_text": "string",
    "interests": {
      "roles": ["string"],
      "focus_areas": ["string"]
    }
  },
  "gamification": {
    "total_xp": 0,
    "level": 1
  }
}
```

</details>

<details>
<summary><strong>POST</strong> <code>/users/me/upload-cv</code> — Upload Resume (CV)</summary>

`Content-Type: multipart/form-data` · PDF only · max 5 MB

**Request:** `file: <resume.pdf>`

**Response `200`:**
```json
{
  "message": "CV parsed successfully",
  "data_preview": {
    "file_name": "string",
    "text_length": 0,
    "snippet": "string"
  }
}
```

**Errors:** `400 INVALID_FILE_TYPE` · `413 FILE_TOO_LARGE`

</details>

<details>
<summary><strong>POST</strong> <code>/users/me/upload-linkedin</code> — Upload LinkedIn PDF</summary>

`Content-Type: multipart/form-data` · PDF only · max 5 MB

**Request:** `file: <linkedin.pdf>`

**Response `200`:**
```json
{
  "message": "LinkedIn profile parsed successfully",
  "data_preview": {
    "file_name": "string",
    "text_length": 0,
    "snippet": "string"
  }
}
```

**Errors:** `400 INVALID_FILE_TYPE` · `413 FILE_TOO_LARGE`

</details>

<details>
<summary><strong>PATCH</strong> <code>/users/me/preferences</code> — Update Preferences</summary>

**Request:**
```json
{
  "interests": {
    "roles": ["string"],
    "focus_areas": ["string"]
  }
}
```

**Response `200`:**
```json
{
  "message": "Preferences updated successfully",
  "interests": {
    "roles": ["string"],
    "focus_areas": ["string"]
  }
}
```

</details>

---

## Module 3 — Career Analysis

<details>
<summary><strong>POST</strong> <code>/careers/analyze</code> — Analyze Profile (async)</summary>

> ⚡ **Async** — returns immediately with `202`. Poll `GET /careers/analyses/{analysis_id}` until `status = READY`.
> Requires CV to be uploaded first.

**Request** _(optional body)_:
```json
{
  "preferences": {
    "focus_areas": ["string"],
    "excluded_roles": ["string"]
  }
}
```

**Response `202`:**
```json
{
  "analysis_id": "string",
  "status": "PENDING",
  "message": "Analysis started. Poll GET /careers/analyses/{analysis_id} for results."
}
```

**Errors:** `400 PROFILE_INCOMPLETE` · `500 AI_SERVICE_ERROR`

</details>

<details>
<summary><strong>GET</strong> <code>/careers/analyses</code> — List Analyses</summary>

Returns all analyses for the authenticated user, newest first.

**Response `200`:**
```json
{
  "analyses": [
    {
      "analysis_id": "string",
      "status": "READY",
      "created_at": "ISO8601",
      "profile_insight": {
        "summary": "string",
        "hard_skills": ["string"],
        "soft_skills": ["string"]
      },
      "recommendations_count": 0
    }
  ]
}
```

</details>

<details>
<summary><strong>GET</strong> <code>/careers/analyses/{analysis_id}</code> — Get Analysis</summary>

Full analysis with all recommendations. Use this to poll after `POST /careers/analyze`.

**Response `200`:**
```json
{
  "analysis_id": "string",
  "status": "READY",
  "created_at": "ISO8601",
  "profile_insight": {
    "summary": "string",
    "hard_skills": ["string"],
    "soft_skills": ["string"]
  },
  "recommendations": [
    {
      "rec_index": 0,
      "title": "string",
      "description": "string",
      "match_score": 0,
      "reasoning": "string",
      "missing_skills": ["string"],
      "tags": ["string"],
      "is_expanded": false,
      "linked_path_id": null
    }
  ]
}
```

> `profile_insight` and `recommendations` are only populated when `status = READY`.

**Errors:** `404 ANALYSIS_NOT_FOUND`

</details>

---

## Module 4 — Career Paths

<details>
<summary><strong>POST</strong> <code>/careers/paths</code> — Create Career Path</summary>

Generates a career path from a selected recommendation. Synchronous — returns the full path.
After creation, a background task generates the Node 0 template automatically.

**Request:**
```json
{
  "analysis_id": "string",
  "rec_index": 0
}
```

**Response `201`:**
```json
{
  "path_id": "string",
  "title": "string",
  "description": "string",
  "tags": ["string"],
  "missing_skills": ["string"],
  "status": "ACTIVE",
  "total_nodes": 0,
  "completed_at": null,
  "created_at": "ISO8601",
  "nodes": [
    {
      "step": 0,
      "title": "string",
      "description": "string",
      "type": "LEARNING",
      "difficulty": "EASY",
      "tags": ["string"],
      "status": "UNLOCKED",
      "is_expanded": false,
      "linked_content_id": null,
      "linked_content_collection": null,
      "max_score": 0,
      "attempts": 0,
      "xp_gained": 0,
      "completed_at": null
    }
  ]
}
```

**Errors:** `400 INVALID_REQUEST` · `404 ANALYSIS_NOT_FOUND` · `404 RECOMMENDATION_NOT_FOUND`

</details>

<details>
<summary><strong>GET</strong> <code>/careers/paths</code> — List Career Paths</summary>

**Query params:** `status` (optional) — `ACTIVE` | `ARCHIVED` | `DELETED`

**Response `200`:**
```json
{
  "paths": [
    {
      "path_id": "string",
      "title": "string",
      "status": "ACTIVE",
      "total_nodes": 0,
      "completed_at": null,
      "created_at": "ISO8601",
      "deleted_at": null,
      "progress": {
        "completed_nodes": 0,
        "percentage": 0
      }
    }
  ]
}
```

</details>

<details>
<summary><strong>GET</strong> <code>/careers/paths/{path_id}</code> — Get Path Details</summary>

**Response `200`:**
```json
{
  "path_id": "string",
  "title": "string",
  "description": "string",
  "status": "ACTIVE",
  "tags": ["string"],
  "missing_skills": ["string"],
  "total_nodes": 0,
  "completed_at": null,
  "created_at": "ISO8601",
  "deleted_at": null,
  "analysis_id": "string",
  "recommendation_index": 0,
  "nodes": [
    {
      "step": 0,
      "title": "string",
      "description": "string",
      "type": "LEARNING",
      "difficulty": "EASY",
      "tags": ["string"],
      "status": "UNLOCKED",
      "is_expanded": false,
      "linked_content_id": null,
      "linked_content_collection": null,
      "max_score": 0,
      "attempts": 0,
      "xp_gained": 0,
      "completed_at": null
    }
  ]
}
```

**Errors:** `404 PATH_NOT_FOUND`

</details>

<details>
<summary><strong>PATCH</strong> <code>/careers/paths/{path_id}/archive</code> — Archive Path</summary>

**Response `200`:**
```json
{
  "message": "Career path archived successfully",
  "path_id": "string",
  "status": "ARCHIVED"
}
```

**Errors:** `404 PATH_NOT_FOUND`

</details>

<details>
<summary><strong>DELETE</strong> <code>/careers/paths/{path_id}</code> — Soft Delete Path</summary>

**Response `200`:**
```json
{
  "message": "Career path deleted successfully",
  "path_id": "string",
  "status": "DELETED",
  "deleted_at": "ISO8601"
}
```

**Errors:** `404 PATH_NOT_FOUND`

</details>

<details>
<summary><strong>PATCH</strong> <code>/careers/paths/{path_id}/restore</code> — Restore Deleted Path</summary>

**Response `200`:**
```json
{
  "message": "Career path restored successfully",
  "path_id": "string",
  "status": "ACTIVE",
  "deleted_at": null
}
```

**Errors:** `404 PATH_NOT_FOUND` · `400 PATH_NOT_DELETED`

</details>

---

## Module 5 — Node Content

<details>
<summary><strong>PATCH</strong> <code>/careers/paths/{path_id}/nodes/{step}/complete</code> — Complete Learning Node</summary>

Marks a `LEARNING` node as complete, awards XP, unlocks the next node, and triggers a background task to generate the next node's template.

> Only applicable to `LEARNING` nodes. `PROJECT` and `INTERVIEW` nodes are completed via their respective session flows.

**Response `200`:**
```json
{
  "message": "Node completed successfully",
  "xp_earned": 0,
  "total_xp": 0,
  "level": 1,
  "next_node_unlocked": true,
  "path_complete": false,
  "next_node": {
    "step": 1,
    "title": "string",
    "type": "PROJECT"
  }
}
```

**Errors:** `404 PATH_NOT_FOUND` · `404 NODE_NOT_FOUND` · `400 NODE_ALREADY_COMPLETED` · `400 NODE_NOT_EXPANDED`

</details>

> ℹ️ **`POST /careers/paths/{path_id}/nodes/{step}/expand`** is an **internal endpoint** — not called by the frontend. Templates are generated automatically in the background after path creation and after each node is completed (look-ahead by 1). The frontend only reads `node.is_expanded` to decide whether to show a loading state.

---

## Module 6 — Project Sessions

<details>
<summary><strong>POST</strong> <code>/projects/start</code> — Start Project Session</summary>

The server resolves the template internally from `path_id + node_step`. Do not pass `template_id`.

**Request:**
```json
{
  "path_id": "string",
  "node_step": 0
}
```

**Response `200`:**
```json
{
  "session_id": "string",
  "title": "string",
  "difficulty": "EASY",
  "min_pass_score": 0,
  "total_tasks": 0,
  "total_subtasks": 0,
  "current_task_index": 0,
  "current_subtask_index": 0,
  "attempt_number": 1,
  "expires_at": "ISO8601",
  "current_task": {
    "task_index": 0,
    "title": "string",
    "description": "string"
  },
  "current_subtask": {
    "subtask_index": 0,
    "title": "string",
    "description": "string",
    "acceptance_criteria": "string",
    "hint": "string"
  }
}
```

**Errors:** `404 PATH_NOT_FOUND` · `404 NODE_NOT_FOUND` · `400 NODE_NOT_EXPANDED`

</details>

<details>
<summary><strong>GET</strong> <code>/projects/{session_id}</code> — Get Project Session</summary>

All previous subtasks are shown read-only. Only the current subtask is actionable.

**Response `200`:**
```json
{
  "session_id": "string",
  "title": "string",
  "difficulty": "EASY",
  "status": "IN_PROGRESS",
  "current_task_index": 0,
  "current_subtask_index": 0,
  "total_tasks": 0,
  "average_score": 0,
  "attempt_number": 1,
  "started_at": "ISO8601",
  "completed_at": null,
  "expires_at": "ISO8601",
  "duration_seconds": 0,
  "tasks": [
    {
      "task_index": 0,
      "title": "string",
      "status": "IN_PROGRESS",
      "subtasks": [
        {
          "subtask_index": 0,
          "title": "string",
          "description": "string",
          "acceptance_criteria": "string",
          "hint": "string",
          "status": "PENDING",
          "score": null,
          "feedback": null,
          "user_submission": null
        }
      ]
    }
  ]
}
```

**Errors:** `404 SESSION_NOT_FOUND`

</details>

<details>
<summary><strong>POST</strong> <code>/projects/{session_id}/submit</code> — Submit Current Subtask</summary>

> The server tracks position. Do not pass task/subtask indices.

**Request:**
```json
{ "code": "string" }
```

**Response `200` — Subtask PASSED (more subtasks remaining):**
```json
{
  "result": "PASSED",
  "score": 0,
  "feedback": "string",
  "is_session_complete": false,
  "next_subtask": {
    "subtask_index": 0,
    "title": "string",
    "description": "string",
    "acceptance_criteria": "string",
    "hint": "string"
  }
}
```

**Response `200` — Subtask FAILED (retry):**
```json
{
  "result": "FAILED",
  "score": 0,
  "feedback": "string",
  "is_session_complete": false
}
```

**Response `200` — Session complete:**
```json
{
  "result": "PASSED",
  "score": 0,
  "feedback": "string",
  "is_session_complete": true,
  "session_status": "PASSED",
  "average_score": 0,
  "xp_earned": 0,
  "total_xp": 0,
  "level": 1,
  "path_complete": false,
  "next_node_unlocked": {
    "step": 1,
    "title": "string",
    "type": "INTERVIEW"
  }
}
```

**Errors:** `404 SESSION_NOT_FOUND` · `400 INVALID_REQUEST`

</details>

<details>
<summary><strong>POST</strong> <code>/projects/{session_id}/forfeit</code> — Forfeit Current Subtask</summary>

> The server tracks position. Forfeited subtasks cannot be re-attempted (cheat guard).

**Response `200`:**
```json
{
  "result": "FORFEITED",
  "score": 0,
  "model_solution": "string",
  "is_session_complete": false,
  "next_subtask": {
    "subtask_index": 0,
    "title": "string",
    "description": "string",
    "acceptance_criteria": "string",
    "hint": "string"
  }
}
```

**Errors:** `404 SESSION_NOT_FOUND` · `400 INVALID_REQUEST`

</details>

<details>
<summary><strong>POST</strong> <code>/projects/{session_id}/abandon</code> — Abandon Project Session</summary>

0 XP awarded. Session stays in history.

**Response `200`:**
```json
{
  "message": "Project session abandoned",
  "status": "ABANDONED",
  "session_id": "string"
}
```

**Errors:** `404 SESSION_NOT_FOUND`

</details>

---

## Module 7 — Interview Sessions

<details>
<summary><strong>POST</strong> <code>/interviews/start</code> — Start Interview Session</summary>

The server resolves the template internally from `path_id + node_step`. Do not pass `template_id`.

**Request:**
```json
{
  "path_id": "string",
  "node_step": 0
}
```

**Response `200`:**
```json
{
  "session_id": "string",
  "title": "string",
  "difficulty": "EASY",
  "min_pass_score": 0,
  "total_questions": 0,
  "current_question_index": 0,
  "attempt_number": 1,
  "expires_at": "ISO8601",
  "question": {
    "question_index": 0,
    "text": "string",
    "hint": "string"
  }
}
```

**Errors:** `404 PATH_NOT_FOUND` · `404 NODE_NOT_FOUND` · `400 NODE_NOT_EXPANDED`

</details>

<details>
<summary><strong>GET</strong> <code>/interviews/{session_id}</code> — Get Interview Session</summary>

**Response `200`:**
```json
{
  "session_id": "string",
  "title": "string",
  "difficulty": "EASY",
  "status": "IN_PROGRESS",
  "current_question_index": 0,
  "total_questions": 0,
  "average_score": 0,
  "attempt_number": 1,
  "started_at": "ISO8601",
  "completed_at": null,
  "expires_at": "ISO8601",
  "questions_summary": [
    {
      "question_index": 0,
      "status": "ANSWERED",
      "score": 0
    }
  ]
}
```

**Errors:** `404 SESSION_NOT_FOUND`

</details>

<details>
<summary><strong>POST</strong> <code>/interviews/{session_id}/submit</code> — Submit Answer</summary>

**Request:**
```json
{ "answer": "string" }
```

**Response `200` — More questions remaining:**
```json
{
  "grade": {
    "score": 0,
    "feedback": "string"
  },
  "is_finished": false,
  "next_question": {
    "question_index": 0,
    "text": "string",
    "hint": "string"
  }
}
```

**Response `200` — Interview complete:**
```json
{
  "grade": {
    "score": 0,
    "feedback": "string"
  },
  "is_finished": true,
  "result": {
    "session_status": "PASSED",
    "average_score": 0,
    "xp_earned": 0,
    "total_xp": 0,
    "level": 1,
    "path_complete": false,
    "next_node_unlocked": {
      "step": 2,
      "title": "string",
      "type": "PROJECT"
    }
  }
}
```

**Errors:** `404 SESSION_NOT_FOUND`

</details>

<details>
<summary><strong>GET</strong> <code>/interviews/{session_id}/result</code> — Get Interview Result</summary>

Full transcript with Q&A pairs, scores, feedback, and model answers. Only available after session is complete.

**Response `200`:**
```json
{
  "session_id": "string",
  "title": "string",
  "status": "PASSED",
  "difficulty": "EASY",
  "average_score": 0,
  "min_pass_score": 0,
  "passed": true,
  "duration_seconds": 0,
  "xp_earned": 0,
  "total_xp": 0,
  "level": 1,
  "attempt_number": 1,
  "completed_at": "ISO8601",
  "transcript": [
    {
      "question_index": 0,
      "question": "string",
      "your_answer": "string",
      "model_answer": "string",
      "score": 0,
      "feedback": "string"
    }
  ]
}
```

**Errors:** `404 SESSION_NOT_FOUND` · `400 SESSION_NOT_COMPLETED`

</details>

<details>
<summary><strong>POST</strong> <code>/interviews/{session_id}/abandon</code> — Abandon Interview Session</summary>

0 XP awarded. Session stays in history.

**Response `200`:**
```json
{
  "message": "Interview session abandoned",
  "status": "ABANDONED",
  "session_id": "string"
}
```

**Errors:** `404 SESSION_NOT_FOUND`

</details>

---

## Module 8 — Session History

<details>
<summary><strong>GET</strong> <code>/sessions</code> — List All Sessions</summary>

Returns project and interview sessions combined, newest first.
Frontend uses `type` to route directly to `/projects/{id}` or `/interviews/{id}`.

**Query params:**
- `type` (optional) — `project` | `interview`
- `status` (optional) — `IN_PROGRESS` | `PASSED` | `FAILED` | `ABANDONED`
- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

**Response `200`:**
```json
{
  "total": 0,
  "sessions": [
    {
      "session_id": "string",
      "type": "PROJECT",
      "title": "string",
      "status": "PASSED",
      "average_score": 0,
      "passed": true,
      "started_at": "ISO8601",
      "completed_at": "ISO8601",
      "duration_seconds": 0,
      "xp_earned": 0,
      "attempt_number": 1
    }
  ]
}
```

</details>

---

## Module 9 — Gamification & Stats

<details>
<summary><strong>GET</strong> <code>/users/me/stats</code> — Get User Statistics</summary>

**Response `200`:**
```json
{
  "user_id": "string",
  "gamification": {
    "total_xp": 0,
    "level": 1,
    "xp_to_next_level": 0
  },
  "career_paths": {
    "active": 0,
    "archived": 0,
    "completed": 0,
    "total_nodes_completed": 0
  },
  "sessions": {
    "projects": {
      "total": 0,
      "passed": 0,
      "failed": 0,
      "abandoned": 0,
      "average_score": 0
    },
    "interviews": {
      "total": 0,
      "passed": 0,
      "failed": 0,
      "abandoned": 0,
      "average_score": 0
    }
  },
  "activity": {
    "last_active": "ISO8601",
    "total_time_spent_minutes": 0
  }
}
```

</details>

<details>
<summary><strong>GET</strong> <code>/leaderboard</code> — Get Leaderboard</summary>

**Query params:**
- `period` (optional) — `weekly` | `monthly` | `all-time` (default: `all-time`)
- `limit` (optional, default: 10)

**Response `200`:**
```json
{
  "period": "all-time",
  "updated_at": "ISO8601",
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "string",
      "name": "string",
      "avatar": "string",
      "xp": 0,
      "level": 1
    }
  ],
  "your_rank": 0
}
```

</details>

---

## Error Codes

| Code | HTTP | Description |
|---|---|---|
| `MISSING_TOKEN` | 400 | Missing `id_token` in request body |
| `INVALID_TOKEN` | 401 | Google `id_token` signature invalid or expired |
| `INVALID_REFRESH` | 401 | Refresh token expired or revoked |
| `INVALID_FILE_TYPE` | 400 | File must be PDF |
| `FILE_TOO_LARGE` | 413 | File exceeds 5 MB limit |
| `PROFILE_INCOMPLETE` | 400 | CV must be uploaded before running analysis |
| `AI_SERVICE_ERROR` | 500 | LLM generation failed |
| `ANALYSIS_NOT_FOUND` | 404 | Analysis ID does not exist or does not belong to user |
| `RECOMMENDATION_NOT_FOUND` | 404 | `rec_index` is out of range |
| `PATH_NOT_FOUND` | 404 | Career path does not exist or does not belong to user |
| `PATH_NOT_DELETED` | 400 | Path is not in `DELETED` status — cannot restore |
| `NODE_NOT_FOUND` | 404 | Node step does not exist on this path |
| `NODE_ALREADY_COMPLETED` | 400 | Node was already completed |
| `NODE_NOT_EXPANDED` | 400 | Node template not yet generated — try again shortly |
| `TEMPLATE_NOT_FOUND` | 404 | Template document does not exist |
| `SESSION_NOT_FOUND` | 404 | Session does not exist or does not belong to user |
| `SESSION_NOT_COMPLETED` | 400 | Session must be completed to access result |
| `INVALID_REQUEST` | 400 | Request body failed Pydantic validation |
| `INVALID_TASK_INDEX` | 400 | (Legacy — server now tracks position internally) |
| `INVALID_SUBTASK_INDEX` | 400 | (Legacy — server now tracks position internally) |
