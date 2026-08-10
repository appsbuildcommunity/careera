# Careera — Feature Tracker

This document splits the backend and deployment work into independent, parallelizable features. It is designed so that multiple developers can work on features concurrently without causing merge conflicts. 

> **Rule:** Claim a feature in your project task board or chat before starting. Open a single PR per feature.

---

## 🏗️ Backend Features

### 1. Authentication & Profile
*Deals with `users` collection and JWT issuance.*
- [ ] `POST /auth/login` (Google OAuth validation + issue tokens)
- [ ] `POST /auth/refresh` (Exchange refresh token)
- [ ] `POST /auth/logout` (Invalidate tokens)
- [ ] Auth Middleware (Protect routes with JWT)
- [ ] `GET /users/me`
- [ ] `POST /users/me/upload-cv` (PDF parsing)
- [ ] `POST /users/me/upload-linkedin` (PDF parsing)
- [ ] `PATCH /users/me/preferences`

### 2. Career Analysis & Path Generation
*Deals with `analyses` and `career_paths` collections. Can be mocked initially without LLM.*
- [ ] `POST /careers/analyze` (Trigger async LLM generation)
- [ ] `GET /careers/analyses` & `GET /careers/analyses/{id}` (Polling)
- [ ] `POST /careers/paths` (Generate path from recommendation)
- [ ] `GET /careers/paths` & `GET /careers/paths/{id}`
- [ ] `PATCH /careers/paths/{id}/archive`
- [ ] `DELETE /careers/paths/{id}` & `PATCH /careers/paths/{id}/restore`

### 3. Node Content & Expansion
*Deals with the look-ahead template generation and learning nodes.*
- [ ] Background Task: Look-ahead node expansion logic
- [ ] Internal Endpoint: `POST /careers/paths/{id}/nodes/{step}/expand` (LLM generation for templates)
- [ ] `PATCH /careers/paths/{id}/nodes/{step}/complete` (Learning nodes only)

### 4. Project Sessions
*Deals with `project_templates` and `project_sessions`.*
- [ ] `POST /projects/start` (Resolve template internally)
- [ ] `GET /projects/{session_id}`
- [ ] `POST /projects/{session_id}/submit` (Evaluate code/subtask via LLM)
- [ ] `POST /projects/{session_id}/forfeit`
- [ ] `POST /projects/{session_id}/abandon`

### 5. Interview Sessions
*Deals with `interview_templates` and `interview_sessions`.*
- [ ] `POST /interviews/start` (Resolve template internally)
- [ ] `GET /interviews/{session_id}`
- [ ] `POST /interviews/{session_id}/submit` (Evaluate answer via LLM)
- [ ] `GET /interviews/{session_id}/result` (Full transcript)
- [ ] `POST /interviews/{session_id}/abandon`

### 6. Gamification & History
*Cross-cutting reads across multiple collections.*
- [ ] XP Calculation Engine (Hooked into node/session completion)
- [ ] `GET /sessions` (List paginated project & interview sessions)
- [ ] `GET /users/me/stats` (Aggregated profile stats)
- [ ] `GET /leaderboard` (Monthly & All-time)

---

## 🚀 Deployment Features

### 7. MVP Deployment (PaaS)
*Zero-config free tier deployment for the MVP.*
- [ ] Create MongoDB Atlas Cluster & get connection string
- [ ] Deploy Backend to Render (`requirements.txt` build)
- [ ] Set Backend `.env` variables (MongoDB URL, LLM Key, JWT Secret)
- [ ] *(Frontend generation via AI & Vercel deployment happens here later)*

### 8. Advanced Deployment (VPS / Docker) — *[Optional]*
*For learning DevOps and manual server management.*
- [ ] Write Backend Dockerfile
- [ ] Write Frontend Dockerfile
- [ ] Create `docker-compose.prod.yml`
- [ ] Provision Oracle Cloud ARM / AWS EC2 instance
- [ ] Install Docker & Nginx on VPS
- [ ] Map domains & start containers
