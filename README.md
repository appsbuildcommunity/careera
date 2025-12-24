# Careera

AI-powered career development platform with personalized learning paths and skill assessment.

**Tech Stack:** Next.js 14, FastAPI, MongoDB, Google Gemini AI

---

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker Desktop

---

## Quick Start

### 1. Start MongoDB
```bash
docker-compose up -d
```

### 2. Setup Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate    # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env            # Edit with your API keys
uvicorn app.main:app --reload --port 8000
```

### 3. Setup Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### 4. Access
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Daily Usage

**Start all services:**
```bash
# Terminal 1: MongoDB
docker-compose up -d

# Terminal 2: Backend
cd backend
source venv/Scripts/activate    # Windows Git Bash
uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm run dev
```

**Stop services:**
```bash
# Stop backend/frontend: CTRL+C in their terminals
docker-compose down              # Stop MongoDB
```

---

## Environment Variables

**Backend** (`backend/.env`):
```env
MONGODB_URI=mongodb://localhost:27017
DB_NAME=careera_db
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
---

