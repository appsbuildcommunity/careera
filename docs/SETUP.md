# ⚙️ Setup Guide

Fastest path to getting Careera running locally for development.

---

## 1. Prerequisites
- Node v18+
- Python v3.11+
- Docker (for MongoDB)

---

## 2. Start Database
Use the provided `docker-compose.yml` to spin up MongoDB and Mongo Express (UI):
```bash
docker-compose up -d
```
*Mongo Express UI available at http://localhost:8081*

---

## 3. Start Backend
```bash
cd backend
poetry install                # installs runtime + dev deps into .venv (in-project)

cp .env.example .env      # Fill in your keys
```

**`backend/.env` Requirements:**
```env
MONGODB_URI=mongodb://localhost:27017
DB_NAME=careera_db
JWT_SECRET=<your_jwt_secret>
GOOGLE_CLIENT_ID=<your_google_client_id>
LLM_API_KEY=<your_llm_key>
ALLOWED_ORIGINS=http://localhost:3000
```

Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```
*API Docs available at http://localhost:8000/docs*

---

## 4. Start Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
```

**`frontend/.env.local` Requirements:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Run the server:
```bash
npm run dev
```
*App available at http://localhost:3000*

---

## 🔄 Daily Workflow
1. `docker-compose up -d`
2. `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
3. `cd frontend && npm run dev`
